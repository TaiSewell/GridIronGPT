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

from data.data_client import DataClient
from data.db import get_conn, initialize_db, fetch_all, fetch_one, upsert_league, upsert_user, upsert_roster, upsert_player, upsert_matchup, upsert_scoring_settings, upsert_player_weekly_proj_stat

LOG = logging.getLogger("gridiron.sync")
logging.basicConfig(level=logging.INFO)


# ----------------- Core sync helpers -----------------


def _safe_get_player_name(p: dict[str, Any], player_id: str) -> str:
    return p.get("full_name") or p.get("name") or p.get("player_name") or str(player_id)


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
            if isinstance(metadata, dict):
                team_name = metadata.get("team_name") or ""
            else:
                team_name = u.get("team_name") or ""

            metadata_json = json.dumps(metadata or {})
            upsert_user(conn, uid, display_name, avatar, team_name, metadata_json)

        # rosters
        rosters = client.get_rosters(league_id) or []
        for r in rosters:
            roster_id = r.get("roster_id") or r.get("id")
            owner_id = r.get("owner_id") or r.get("user_id") or r.get("owner")
            players = r.get("players") or []
            starters_json = json.dumps(players)
            bench_json = json.dumps([])

            upsert_roster(
                conn,
                league_id,
                roster_id,
                owner_id,
                starters_json,
                bench_json,
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

    data = client.get_weekly_projections(season, week)  # whatever your DataClient uses
    count = 0

    with get_conn() as conn:
        for p in data:
            player_id = p["player_id"]  # however you map SportsDataIO -> Sleeper id
            # Loop through the stat fields you care about
            for stat_key, value in p["stats"].items():   # or however it's shaped
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

    LOG.info("Upserted %d projection stat rows", count)
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
    elif args.cmd == "inspect":
        # don't initialize DB here; inspect whatever exists
        inspect_db(args.league_id, args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()