"""
=============================================================
 File: roster_insights.py
 Author: Tai Sewell
 Description:
     Builds roster-level insights for a single owner, including
     position totals, strengths/weaknesses, and roster listings.
=============================================================
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.league_context import get_active_league_id
from backend.cache_manager import CacheManager
from backend.db import get_conn
import backend.queries.league_queries as q_league
import backend.queries.player_queries as q_player
import backend.queries.roster_queries as q_rosters
import backend.queries.user_queries as q_users


def build_roster_insights_service(
    user_a: str,
    season: Optional[int] = None,
    week: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build roster insights for a single roster owner.
    """
    league_id = get_active_league_id()

    cache_manager = CacheManager(league_id=league_id)
    cache_manager.ensure_league_bundle_cached(week=None)

    resolved_season = season
    if resolved_season is None:
        with get_conn() as conn:
            resolved_season = q_league.get_league_season(conn, league_id)

    if resolved_season is None:
        raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    resolved_week = week
    if resolved_week is None:
        resolved_week = _resolve_latest_completed_week(cache_manager, resolved_season)

    if resolved_week:
        for current_week in range(1, resolved_week + 1):
            cache_manager.ensure_matchups_cached(current_week)
            cache_manager.ensure_weekly_actuals_cached(resolved_season, current_week)
        with get_conn() as conn:
            latest_with_points = q_player.get_latest_week_with_actual_points(
                conn=conn,
                season=resolved_season,
            )
        if latest_with_points:
            resolved_week = latest_with_points

    with get_conn() as conn:
        users = q_users.list_users(conn)
        rosters = q_rosters.list_rosters_by_league(conn, league_id)
        matchups = []
        player_actuals = []

        if resolved_week:
            matchups = q_rosters.get_matchups_for_league_season(
                conn=conn,
                league_id=league_id,
                season=resolved_season,
                week=resolved_week,
            )
            player_actuals = q_player.get_player_week_actuals(
                conn=conn,
                season=resolved_season,
                week=resolved_week,
            )

        target_roster, target_user = _resolve_roster_for_user(
            user_a=user_a,
            users=users,
            rosters=rosters,
        )

        roster_players = _build_roster_player_lists(
            conn=conn,
            roster=target_roster,
        )

    summary_payload = _build_roster_insights_payload(
        target_roster=target_roster,
        target_user=target_user,
        rosters=rosters,
        matchups=matchups,
        player_actuals=player_actuals,
        roster_players=roster_players,
        season=resolved_season,
        week=resolved_week or 0,
    )
    return summary_payload


def _resolve_latest_completed_week(cache_manager: CacheManager, season: int) -> Optional[int]:
    latest_week: Optional[int] = None
    for week in range(1, 19):
        schedule = cache_manager.client.get_schedule(season, week) or []
        has_final = False
        for game in schedule:
            status = str(game.get("Status") or "").lower()
            if status.startswith("final") or status in {"f", "fo", "f/ot"}:
                has_final = True
                break

        if has_final:
            latest_week = week
        elif latest_week is not None:
            break

    return latest_week


def _resolve_roster_for_user(
    user_a: str,
    users: List[Dict[str, Any]],
    rosters: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Resolve a roster and user record by display name or team name.
    """
    matches = _find_users_by_name(user_a, users)
    if not matches:
        raise ValueError(f"Roster not found for '{user_a}'.")

    user_a_norm = user_a.strip().lower()
    exact = [
        user
        for user in matches
        if (user.get("display_name") or "").strip().lower() == user_a_norm
        or (user.get("team_name") or "").strip().lower() == user_a_norm
    ]

    if len(exact) == 1:
        owner_id = exact[0]["user_id"]
        resolved_user = exact[0]
    elif len(matches) == 1:
        owner_id = matches[0]["user_id"]
        resolved_user = matches[0]
    else:
        raise ValueError(f"Multiple users matched '{user_a}'. Use a more specific name.")

    target_roster = next(
        (roster for roster in rosters if roster.get("owner_id") == owner_id),
        None,
    )

    if not target_roster:
        raise ValueError(f"Roster not found for '{user_a}'.")

    return target_roster, resolved_user


def _find_users_by_name(
    username: str,
    users: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Filter users by display name or team name.
    """
    normalized = username.strip().lower()
    matches = [
        user
        for user in users
        if normalized in (user.get("display_name") or "").lower()
        or normalized in (user.get("team_name") or "").lower()
    ]
    return matches


def _build_roster_player_lists(
    conn,
    roster: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build starter and bench player lists with metadata.
    """
    starter_ids = _safe_json_list(roster.get("starters_json"))
    bench_ids = _safe_json_list(roster.get("bench_json"))
    all_ids = [player_id for player_id in starter_ids + bench_ids if player_id]

    players_by_id = {}
    if all_ids:
        players = q_player.get_players_by_ids(conn, all_ids)
        players_by_id = {player["player_id"]: player for player in players}

    starters = [_format_player(players_by_id.get(pid), pid) for pid in starter_ids]
    bench = [_format_player(players_by_id.get(pid), pid) for pid in bench_ids]

    return {
        "starters": starters,
        "bench": bench,
    }


def _format_player(player: Optional[Dict[str, Any]], player_id: Any) -> Dict[str, Any]:
    """
    Normalize a player entry for responses.
    """
    normalized = {
        "player_id": player_id,
        "player_name": player.get("player_name") if player else str(player_id),
        "position": player.get("position") if player else "UNK",
        "team": player.get("team") if player else "FA",
        "status": player.get("status") if player else "",
    }
    return normalized


def _build_roster_insights_payload(
    target_roster: Dict[str, Any],
    target_user: Dict[str, Any],
    rosters: List[Dict[str, Any]],
    matchups: List[Dict[str, Any]],
    player_actuals: List[Dict[str, Any]],
    roster_players: Dict[str, List[Dict[str, Any]]],
    season: int,
    week: int,
) -> Dict[str, Any]:
    """
    Build response payload for roster insights.
    """
    roster_ids = [roster["roster_id"] for roster in rosters]
    actual_points_map = {}
    position_map = {}
    for row in player_actuals:
        player_id = row.get("player_id")
        actual_week = row.get("week")
        actual_points = float(row.get("actual_points") or 0.0)
        actual_points_map[(player_id, actual_week)] = actual_points
        if player_id and player_id not in position_map:
            position_map[player_id] = row.get("position")

    roster_position_totals = {roster_id: {} for roster_id in roster_ids}
    for matchup in matchups:
        roster_id = matchup.get("roster_id")
        matchup_week = matchup.get("week")
        players = _safe_json_list(matchup.get("players_json"))
        if roster_id is None or matchup_week is None:
            continue

        position_totals = roster_position_totals.setdefault(roster_id, {})
        for player_id in players:
            points = actual_points_map.get((player_id, matchup_week), 0.0)
            position = position_map.get(player_id)
            if position:
                position_totals[position] = float(position_totals.get(position, 0.0)) + points

    league_position_averages = _compute_league_position_averages(
        roster_position_totals=roster_position_totals,
        roster_count=len(roster_ids),
    )

    roster_id = target_roster.get("roster_id")
    display_name = target_user.get("display_name") or str(target_user.get("user_id"))
    team_name = target_user.get("team_name") or ""
    wins = int(target_roster.get("wins") or 0)
    losses = int(target_roster.get("losses") or 0)
    ties = int(target_roster.get("ties") or 0)
    total_moves = int(target_roster.get("total_moves") or 0)
    fpts = float(target_roster.get("fpts") or 0.0)
    fpts_against = float(target_roster.get("fpts_against") or 0.0)
    position_totals = roster_position_totals.get(roster_id, {})

    strength, weakness = _derive_strengths_and_weaknesses(
        roster_position_totals=position_totals,
        league_position_averages=league_position_averages,
    )

    summary, details = _format_roster_insights_text(
        display_name=display_name,
        week=week,
        wins=wins,
        losses=losses,
        ties=ties,
        fpts=fpts,
        fpts_against=fpts_against,
        total_moves=total_moves,
        position_totals=position_totals,
        strength=strength,
        weakness=weakness,
        roster_players=roster_players,
    )

    response = {
        "season": season,
        "week": week,
        "summary": summary,
        "details": details,
        "roster": {
            "roster_id": roster_id,
            "owner_id": target_roster.get("owner_id"),
            "display_name": display_name,
            "team_name": team_name,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "total_moves": total_moves,
            "fpts": round(fpts, 2),
            "fpts_against": round(fpts_against, 2),
            "strength": strength,
            "weakness": weakness,
            "position_totals": position_totals,
        },
        "players": roster_players,
    }
    return response


def _format_roster_insights_text(
    display_name: str,
    week: int,
    wins: int,
    losses: int,
    ties: int,
    fpts: float,
    fpts_against: float,
    total_moves: int,
    position_totals: Dict[str, float],
    strength: str,
    weakness: str,
    roster_players: Dict[str, List[Dict[str, Any]]],
) -> Tuple[str, str]:
    """
    Build summary and details strings for roster insights.
    """
    summary = f"Roster insights for {display_name} through week {week}."
    position_parts = [
        f"{position}: {float(total):.2f}"
        for position, total in sorted(position_totals.items())
    ]
    positions_line = ", ".join(position_parts) if position_parts else "None"

    starter_names = [
        player.get("player_name") or player.get("player_id")
        for player in roster_players.get("starters", [])
    ]
    bench_names = [
        player.get("player_name") or player.get("player_id")
        for player in roster_players.get("bench", [])
    ]
    starters_line = ", ".join(starter_names) if starter_names else "None"
    bench_line = ", ".join(bench_names) if bench_names else "None"

    details_lines = [
        f"Record: {wins}-{losses}-{ties}",
        f"Points Scored: {fpts:.2f}",
        f"Points Allowed: {fpts_against:.2f}",
        f"Roster Moves: {total_moves}",
        f"Position Totals: {positions_line}",
        f"Strength: {strength} | Weakness: {weakness}",
        f"Starters: {starters_line}",
        f"Bench: {bench_line}",
    ]

    details = "\n".join(details_lines)
    return summary, details


def _derive_strengths_and_weaknesses(
    roster_position_totals: Dict[str, float],
    league_position_averages: Dict[str, float],
) -> Tuple[str, str]:
    """
    Compare roster position totals to league averages.
    """
    strength = "Even"
    weakness = "Even"
    deltas = {}

    for position, league_average in league_position_averages.items():
        roster_total = float(roster_position_totals.get(position, 0.0))
        deltas[position] = round(roster_total - float(league_average), 2)

    if deltas:
        strength = max(deltas, key=deltas.get)
        weakness = min(deltas, key=deltas.get)
    return strength, weakness


def _compute_league_position_averages(
    roster_position_totals: Dict[int, Dict[str, float]],
    roster_count: int,
) -> Dict[str, float]:
    """
    Compute per-position league averages across rosters.
    """
    league_totals: Dict[str, float] = {}
    for position_totals in roster_position_totals.values():
        for position, total in position_totals.items():
            league_totals[position] = float(league_totals.get(position, 0.0)) + float(total)

    league_averages: Dict[str, float] = {}
    divisor = float(roster_count) if roster_count else 1.0
    for position, total in league_totals.items():
        league_averages[position] = round(float(total) / divisor, 2)

    return league_averages


def _safe_json_list(value: Optional[str]) -> List[Any]:
    """
    Return a list from JSON if possible; otherwise return empty list.
    """
    result: List[Any] = []
    parsed: List[Any] | Any = []

    if value:
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            parsed = []

    if isinstance(parsed, list):
        result = parsed

    return result
