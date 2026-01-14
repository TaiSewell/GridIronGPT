"""
=============================================================
 File: sync.py
 Author: Tai Sewell
 Description:
     Synchronizes data from the Sleeper API into the local
     SQLite database. Also includes a small inspector CLI
     for viewing DB contents after sync.
=============================================================
"""
from __future__ import annotations
import argparse
import json
import logging
from typing import Any
from backend.data_client import DataClient
from backend.db import get_conn, initialize_db, fetch_all, fetch_one, upsert_league, upsert_user, upsert_roster, upsert_player, upsert_matchup, upsert_scoring_settings, upsert_player_week_meta, upsert_player_weekly_proj_stat, upsert_projection_adjustment, upsert_dst_weekly_points
from backend.app.config import settings
import re

LOG = logging.getLogger("gridiron.sync")
logging.basicConfig(level=logging.INFO)


# ----------------- Core sync helpers -----------------
def _safe_get_player_name(p: dict[str, Any], player_id: str) -> str:
    return p.get("full_name") or p.get("name") or p.get("player_name") or str(player_id)


def _extract_roster_points(
    roster_settings: dict[str, Any],
    roster_payload: dict[str, Any],
    points_key: str,
    decimal_key: str,
) -> float:
    """
    Build a float from Sleeper roster points and decimal fields.
    """
    points_value = roster_settings.get(points_key, roster_payload.get(points_key, 0))
    decimal_value = roster_settings.get(decimal_key, roster_payload.get(decimal_key, 0))

    points_float = 0.0
    try:
        points_float = float(points_value)
    except (TypeError, ValueError):
        points_float = 0.0

    decimal_float = 0.0
    try:
        decimal_float = float(decimal_value) / 100.0
    except (TypeError, ValueError):
        decimal_float = 0.0

    return round(points_float + decimal_float, 2)

def sync_players(client: DataClient) -> int:
    """
    Fetch all players from Sleeper and upsert into the DB.

    Returns the number of players processed.
    """
    LOG.info("Fetching all players from Sleeper...")
    data = client.get_all_players()

    # Sleeper returns a mapping of player_id -> player_obj
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        # some providers may return a list
        items = [(p.get("player_id") or p.get("id"), p) for p in data]
    else:
        raise RuntimeError("Unexpected players payload")

    count = 0
    with get_conn() as conn:
        for pid, pobj in items:
            if pid is None:
                continue

            name = _safe_get_player_name(pobj, pid)
            team = (
                pobj.get("team")
                or pobj.get("team_abbr")
                or pobj.get("team_id")
                or ""
            )
            position = pobj.get("position") or pobj.get("pos") or ""
            status = pobj.get("status") or pobj.get("injury_status") or ""

            upsert_player(conn, pid, name, team, position, status)
            count += 1

    LOG.info("Upserted %d players", count)
    return count


def sync_league(client: DataClient, league_id: str) -> None:
    """
    Sync league metadata, users, rosters, and scoring settings.
    """
    LOG.info("Syncing league %s", league_id)
    league = client.get_league(league_id)

    # league object may be a dict or list with single dict; handle both.
    if isinstance(league, list) and league:
        league = league[0]

    season = league.get("season") or league.get("year") or None
    name = league.get("name") or league.get("league_name") or ""
    status = league.get("status") or ""
    scoring_settings = league.get("scoring_settings") or {}

    with get_conn() as conn:
        upsert_league(
            conn,
            league_id,
            name,
            season,
            status,
            json.dumps(scoring_settings),
        )

        # scoring settings may be a mapping of stat_key -> weight
        if isinstance(scoring_settings, dict):
            for stat_key, weight in scoring_settings.items():
                try:
                    upsert_scoring_settings(conn, league_id, stat_key, float(weight))
                except Exception as e:
                    LOG.warning(
                        "Failed to store scoring setting %s=%r for league %s: %s",
                        stat_key,
                        weight,
                        league_id,
                        e,
                    )
                    continue

        # users
        users = client.get_users(league_id) or []
        for u in users:
            uid = u.get("user_id") or u.get("id")
            if not uid:
                continue

            display_name = u.get("display_name") or u.get("username") or ""
            avatar = u.get("avatar") or ""
            metadata = u.get("metadata") or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}

            if isinstance(metadata, dict):
                team_name = metadata.get("team_name") or ""
            else:
                team_name = ""

            if not team_name:
                team_name = u.get("team_name") or ""

            metadata_json = json.dumps(metadata if isinstance(metadata, dict) else {})
            upsert_user(conn, uid, display_name, avatar, team_name, metadata_json)

        # rosters
        rosters = client.get_rosters(league_id) or []
        for r in rosters:
            roster_id = r.get("roster_id") or r.get("id")
            owner_id = r.get("owner_id") or r.get("user_id") or r.get("owner")
            players = r.get("players") or []
            starters = r.get("starters") or []
            roster_settings = r.get("settings") or {}

            starters_set = set(starters)
            bench = [p for p in players if p not in starters_set]

            starters_json = json.dumps(starters)
            bench_json = json.dumps(bench)

            wins = roster_settings.get("wins", r.get("wins", 0))
            losses = roster_settings.get("losses", r.get("losses", 0))
            ties = roster_settings.get("ties", r.get("ties", 0))
            waiver_position = roster_settings.get(
                "waiver_position",
                r.get("waiver_position"),
            )
            total_moves = roster_settings.get("total_moves", r.get("total_moves", 0))

            fpts = _extract_roster_points(
                roster_settings,
                r,
                "fpts",
                "fpts_decimal",
            )
            fpts_against = _extract_roster_points(
                roster_settings,
                r,
                "fpts_against",
                "fpts_against_decimal",
            )

            upsert_roster(
                conn,
                league_id,
                roster_id,
                owner_id,
                starters_json,
                bench_json,
                wins,
                losses,
                ties,
                waiver_position,
                total_moves,
                fpts,
                fpts_against,
            )

    LOG.info("Finished syncing league %s", league_id)


def sync_matchups(client: DataClient, league_id: str, week: int) -> int:
    """
    Fetch matchups for a league/week and persist them.
    """
    LOG.info("Fetching matchups for league %s week %s", league_id, week)
    data = client.get_matchups(league_id, week) or []

    # Get season from leagues table
    league_row = fetch_one(
        "SELECT season FROM leagues WHERE league_id = ?",
        (league_id,),
    )
    league_season = league_row["season"] if league_row else None

    if league_season is None:
        LOG.warning(
            "No season found for league %s in leagues table; did you run sync_league first?",
            league_id,
        )

    count = 0
    with get_conn() as conn:
        for m in data:
            roster_id = m.get("roster_id")
            matchup_id = m.get("matchup_id") or m.get("week_matchup_id")
            points = m.get("points")
            players = m.get("players") or []
            players_json = json.dumps(players)

            # Use season from matchup if present, otherwise fall back to league season
            season = m.get("season") or league_season
            if season is None:
                # As a last resort skip
                LOG.warning(
                    "Skipping matchup with roster_id=%r because season is missing",
                    roster_id,
                )
                continue

            upsert_matchup(
                conn,
                league_id,
                season,
                week,
                roster_id,
                matchup_id,
                players_json,
                points,
            )
            count += 1

    LOG.info("Upserted %d matchup rows", count)
    return count


def initialize_and_sync_all_players() -> None:
    """
    Convenience helper: create schema and sync all players.
    """
    initialize_db()
    client = DataClient()
    sync_players(client)

def sync_weekly_projections(client: DataClient, season: int, week: int) -> int:
    """
    Fetch weekly projections from SportsDataIO and store them
    in player_weekly_proj_stats as raw stat_key/value pairs.
    """
    LOG.info("Syncing weekly projections for season %s week %s", season, week)
    offense_rows = client.get_weekly_offensive_projections(season, week) or []
    defense_rows = client.get_weekly_defensive_projections(season, week) or []

    offense_stat_map = {
        "PassingYards": "pass_yd",
        "PassingTouchdowns": "pass_td",
        "PassingInterceptions": "pass_int",
        "Passing2PointConversions": "pass_2pt",
        "RushingYards": "rush_yd",
        "RushingTouchdowns": "rush_td",
        "Rushing2PointConversions": "rush_2pt",
        "Receptions": "rec",
        "ReceivingYards": "rec_yd",
        "ReceivingTouchdowns": "rec_td",
        "Receiving2PointConversions": "rec_2pt",
        "FumblesLost": "fum_lost",
    }
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (name or "").lower())

    def _build_player_index():
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT player_id, player_name, team, position FROM players"
            ).fetchall()

        index: dict[str, list[dict[str, str]]] = {}
        dst_index: dict[str, str] = {}
        for row in rows:
            player_name = row["player_name"] or ""
            team = row["team"] or ""
            position = row["position"] or ""
            player_id = row["player_id"]

            key = _normalize_name(player_name)
            if key:
                index.setdefault(key, []).append(
                    {
                        "player_id": player_id,
                        "team": team,
                        "position": position,
                    }
                )

            if position.upper() == "DST" and team:
                dst_index[team.upper()] = player_id

        return index, dst_index

    def _resolve_player_id(
        name: str | None,
        team: str | None,
        position: str | None,
        index: dict[str, list[dict[str, str]]],
    ) -> str | None:
        if not name:
            return None

        key = _normalize_name(name)
        candidates = index.get(key, [])
        if not candidates:
            return None

        if team:
            team_upper = team.upper()
            filtered = [c for c in candidates if (c["team"] or "").upper() == team_upper]
            if filtered:
                candidates = filtered

        if position:
            pos_upper = position.upper()
            filtered = [c for c in candidates if (c["position"] or "").upper() == pos_upper]
            if filtered:
                candidates = filtered

        return candidates[0]["player_id"] if candidates else None

    count = 0
    player_index, dst_index = _build_player_index()

    with get_conn() as conn:
        for row in offense_rows:
            name = row.get("Name") or row.get("PlayerName") or row.get("FullName")
            team = row.get("Team") or row.get("TeamAbbr")
            position = row.get("Position")
            player_id = _resolve_player_id(name, team, position, player_index)
            if not player_id:
                continue

            for sd_key, stat_key in offense_stat_map.items():
                if sd_key not in row:
                    continue
                value = row.get(sd_key)
                if value is None:
                    continue
                upsert_player_weekly_proj_stat(
                    conn,
                    season=season,
                    week=week,
                    player_id=player_id,
                    stat_key=stat_key,
                    value=float(value or 0),
                    source="sportsdataio",
                )
                count += 1

        for row in defense_rows:
            team = row.get("Team") or row.get("TeamAbbr")
            if not team:
                continue

            team_upper = team.upper()
            player_id = dst_index.get(team_upper)
            if not player_id:
                player_id = f"DST-{team_upper}"
                upsert_player(conn, player_id, f"{team_upper} DST", team_upper, "DST", "active")

            points = row.get("FantasyPoints")
            if points is None:
                continue

            # Store raw DST fantasy projection as a single stat key.
            upsert_player_weekly_proj_stat(
                conn,
                season=season,
                week=week,
                player_id=player_id,
                stat_key="dst_fp",
                value=float(points),
                source="sportsdataio",
            )
            upsert_dst_weekly_points(
                conn,
                season=season,
                week=week,
                dst_team=team_upper,
                projected_points=float(points),
                actual_points=None,
                source="sportsdataio",
            )
            count += 1

    LOG.info("Upserted %d projection stat rows", count)
    return count


def sync_player_week_meta(client: DataClient, season: int, week: int) -> int:
    """
    Fetch schedule data and store opponent/home-away context for players.
    """
    LOG.info("Syncing player week meta for season %s week %s", season, week)
    schedule = client.get_schedule(season, week) or []

    team_context: dict[str, dict[str, object]] = {}
    for game in schedule:
        home = (game.get("HomeTeam") or game.get("HomeTeamAbbr") or "").upper()
        away = (game.get("AwayTeam") or game.get("AwayTeamAbbr") or "").upper()
        if not home or not away:
            continue

        team_context[home] = {"opp_team": away, "is_home": 1}
        team_context[away] = {"opp_team": home, "is_home": 0}

    if not team_context:
        LOG.info("No schedule data available for season %s week %s", season, week)
        return 0

    count = 0
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT player_id, team FROM players WHERE team IS NOT NULL"
        ).fetchall()

        for row in rows:
            team = (row["team"] or "").upper()
            ctx = team_context.get(team)
            if not ctx:
                continue

            upsert_player_week_meta(
                conn,
                player_id=row["player_id"],
                season=season,
                week=week,
                opp_team=ctx["opp_team"],
                is_home=ctx["is_home"],
            )
            count += 1

    LOG.info("Upserted %d player_week_meta rows", count)
    return count


def _ensure_player_week_meta_actual_points(conn) -> None:
    try:
        conn.execute("ALTER TABLE player_week_meta ADD COLUMN actual_points REAL;")
    except Exception:
        # Column already exists or table is missing (initialized elsewhere)
        pass


def sync_weekly_actuals(client: DataClient, season: int, week: int, league_id: str | None = None) -> int:
    """
    Fetch weekly fantasy stats and store FantasyPointsPPR as actual_points.
    """
    LOG.info("Syncing weekly actuals for season %s week %s", season, week)
    # Only load actuals for completed weeks (ScoresByWeekFinal returns finals only).
    finals = client.get_schedule(season, week) or []
    has_final = False
    for game in finals:
        status = str(game.get("Status") or "").lower()
        if status.startswith("final") or status in {"f", "fo", "f/ot"}:
            has_final = True
            break

    if not finals or not has_final:
        LOG.info("Skipping weekly actuals (week not final yet): season=%s week=%s", season, week)
        return 0

    try:
        rows = client.get_weekly_fantasy_stats(season, week) or []
    except RuntimeError as exc:
        LOG.warning("Skipping offensive actuals (stats endpoint failed): %s", exc)
        rows = []

    try:
        dst_fantasy_rows = client.get_weekly_defense_fantasy_by_game(season, week) or []
    except RuntimeError as exc:
        LOG.warning("Skipping DST fantasy points (by game endpoint failed): %s", exc)
        dst_fantasy_rows = []

    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (name or "").lower())

    def _build_player_index():
        with get_conn() as conn:
            data = conn.execute(
                "SELECT player_id, player_name, team, position FROM players"
            ).fetchall()

        index: dict[str, list[dict[str, str]]] = {}
        dst_index: dict[str, str] = {}
        for row in data:
            player_name = row["player_name"] or ""
            team = row["team"] or ""
            position = row["position"] or ""
            player_id = row["player_id"]

            key = _normalize_name(player_name)
            if key:
                index.setdefault(key, []).append(
                    {
                        "player_id": player_id,
                        "team": team,
                        "position": position,
                    }
                )

            if position.upper() == "DST" and team:
                dst_index[team.upper()] = player_id

        return index, dst_index

    def _resolve_player_id(
        name: str | None,
        team: str | None,
        position: str | None,
        index: dict[str, list[dict[str, str]]],
    ) -> str | None:
        if not name:
            return None

        key = _normalize_name(name)
        candidates = index.get(key, [])
        if not candidates:
            return None

        if team:
            team_upper = team.upper()
            filtered = [c for c in candidates if (c["team"] or "").upper() == team_upper]
            if filtered:
                candidates = filtered

        if position:
            pos_upper = position.upper()
            filtered = [c for c in candidates if (c["position"] or "").upper() == pos_upper]
            if filtered:
                candidates = filtered

        return candidates[0]["player_id"] if candidates else None

    count = 0
    player_index, dst_index = _build_player_index()

    with get_conn() as conn:
        _ensure_player_week_meta_actual_points(conn)
        league_id = league_id or settings.SLEEPER_LEAGUE_ID

        for row in rows:
            points = row.get("FantasyPointsPPR")
            if points is None:
                continue

            position = row.get("Position")
            team = row.get("Team") or row.get("TeamAbbr")
            name = row.get("Name") or row.get("PlayerName") or row.get("FullName")

            player_id = _resolve_player_id(name, team, position, player_index)
            if not player_id and team and (position or "").upper() == "DST":
                team_upper = team.upper()
                player_id = dst_index.get(team_upper)
                if not player_id:
                    player_id = f"DST-{team_upper}"
                    upsert_player(conn, player_id, f"{team_upper} DST", team_upper, "DST", "active")

            if not player_id:
                continue

            upsert_player_week_meta(
                conn,
                player_id=player_id,
                season=season,
                week=week,
                opp_team=None,
                is_home=None,
                actual_points=float(points),
            )
            count += 1

        for row in dst_fantasy_rows:
            team = row.get("Team") or row.get("TeamAbbr") or row.get("DefenseTeam")
            if not team:
                continue

            fantasy_points = row.get("FantasyPoints")
            if fantasy_points is None:
                continue

            team_upper = team.upper()
            upsert_dst_weekly_points(
                conn,
                season=season,
                week=week,
                dst_team=team_upper,
                projected_points=None,
                actual_points=float(fantasy_points),
                source="sportsdataio",
            )
            count += 1

    LOG.info("Upserted %d actual_points rows", count)
    return count


# ----------------- Simple DB inspector -----------------


def inspect_db(league_id: str | None = None, limit: int = 5) -> None:
    """
    Print simple summary counts and sample rows from the DB.

    Args:
        league_id: Optional league id to scope rosters/matchups/users.
        limit: Number of sample rows to print per table.
    """
    print("\n=== Database Summary ===")

    players_count = fetch_one("SELECT COUNT(*) AS c FROM players")
    print(f"players: {players_count['c'] if players_count else 0}")

    leagues_count = fetch_one("SELECT COUNT(*) AS c FROM leagues")
    print(f"leagues: {leagues_count['c'] if leagues_count else 0}")

    users_count = fetch_one("SELECT COUNT(*) AS c FROM users")
    print(f"users: {users_count['c'] if users_count else 0}")

    if league_id:
        roster_rows = fetch_all(
            """
            SELECT roster_id, owner_id, starters_json
            FROM rosters
            WHERE league_id = ?
            ORDER BY roster_id
            LIMIT ?
            """,
            (league_id, limit),
        )
        matchup_rows = fetch_all(
            """
            SELECT week, matchup_id, roster_id, points
            FROM matchups
            WHERE league_id = ?
            ORDER BY week, matchup_id, roster_id
            LIMIT ?
            """,
            (league_id, limit),
        )
        scoring_rows = fetch_all(
            """
            SELECT stat_key, weight
            FROM scoring_settings
            WHERE league_id = ?
            ORDER BY stat_key
            LIMIT ?
            """,
            (league_id, limit),
        )
    else:
        roster_rows = fetch_all(
            """
            SELECT league_id, roster_id, owner_id
            FROM rosters
            ORDER BY league_id, roster_id
            LIMIT ?
            """,
            (limit,),
        )
        matchup_rows = fetch_all(
            """
            SELECT league_id, season, week, roster_id, points
            FROM matchups
            ORDER BY league_id, season, week
            LIMIT ?
            """,
            (limit,),
        )
        scoring_rows = fetch_all(
            """
            SELECT league_id, stat_key, weight
            FROM scoring_settings
            ORDER BY league_id, stat_key
            LIMIT ?
            """,
            (limit,),
        )

    print(f"rosters (sample {limit}): {len(roster_rows)}")
    for r in roster_rows:
        print(" ", r)

    print(f"matchups (sample {limit}): {len(matchup_rows)}")
    for m in matchup_rows:
        print(" ", m)

    print(f"scoring_settings (sample {limit}): {len(scoring_rows)}")
    for s in scoring_rows:
        print(" ", s)

    print("=== End Summary ===\n")


# ----------------- CLI entrypoint -----------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Sleeper data into local DB",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("players", help="Sync all players")

    league_p = sub.add_parser("league", help="Sync a league (meta/users/rosters)")
    league_p.add_argument("league_id")

    match_p = sub.add_parser("matchups", help="Sync matchups for a league/week")
    match_p.add_argument("league_id")
    match_p.add_argument("week", type=int)

    meta_p = sub.add_parser("week-meta", help="Sync player week meta (opp/home)")
    meta_p.add_argument("season", type=int)
    meta_p.add_argument("week", type=int)

    adj_p = sub.add_parser("adjustments", help="Set projection adjustments for a league")
    adj_p.add_argument("league_id")
    adj_p.add_argument("--position", default="ALL")
    adj_p.add_argument("--multiplier", type=float, required=True)
    adj_p.add_argument("--bonus", type=float, default=0.0)

    actuals_p = sub.add_parser("week-actuals", help="Sync weekly fantasy actuals (PPR + DST)")
    actuals_p.add_argument("season", type=int)
    actuals_p.add_argument("week", type=int)
    actuals_p.add_argument("--league-id", dest="league_id", default=None)

    insp_p = sub.add_parser(
        "inspect",
        help="Inspect DB contents (counts + samples)",
    )
    insp_p.add_argument(
        "--league",
        dest="league_id",
        default=None,
        help="Optional league_id to scope results",
    )
    insp_p.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=5,
        help="Number of sample rows to show per table",
    )

    args = parser.parse_args()
    client = DataClient()

    if args.cmd == "players":
        initialize_db()
        sync_players(client)
    elif args.cmd == "league":
        initialize_db()
        sync_league(client, args.league_id)
    elif args.cmd == "matchups":
        initialize_db()
        sync_matchups(client, args.league_id, args.week)
    elif args.cmd == "week-meta":
        initialize_db()
        sync_player_week_meta(client, args.season, args.week)
    elif args.cmd == "adjustments":
        initialize_db()
        positions = [args.position] if args.position != "ALL" else ["QB", "RB", "WR", "TE", "K", "DST"]
        with get_conn() as conn:
            for pos in positions:
                upsert_projection_adjustment(conn, args.league_id, pos, args.multiplier, args.bonus)
    elif args.cmd == "week-actuals":
        initialize_db()
        sync_weekly_actuals(client, args.season, args.week, league_id=args.league_id)
    elif args.cmd == "inspect":
        # don't initialize DB here; inspect whatever exists
        inspect_db(args.league_id, args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
