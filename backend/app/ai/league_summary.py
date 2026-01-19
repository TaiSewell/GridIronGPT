"""
=============================================================
 File: league_summary.py
 Author: Tai Sewell
Description:
     Builds an overall league summary using roster totals while
     deriving strengths/weaknesses from starter actual points.
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


def build_league_summary_service(
    season: Optional[int] = None,
    week: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a league-wide summary using roster season totals.
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
        with get_conn() as conn:
            resolved_week = q_player.get_latest_week_with_actual_points(
                conn=conn,
                season=resolved_season,
            )

    if resolved_week:
        for current_week in range(1, resolved_week + 1):
            cache_manager.ensure_matchups_cached(current_week)
            cache_manager.ensure_weekly_actuals_cached(resolved_season, current_week)

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

    summary_payload = _build_league_summary_payload(
        users=users,
        rosters=rosters,
        matchups=matchups,
        player_actuals=player_actuals,
        season=resolved_season,
        week=resolved_week or 0,
    )
    return summary_payload


def _build_league_summary_payload(
    users: List[Dict[str, Any]],
    rosters: List[Dict[str, Any]],
    matchups: List[Dict[str, Any]],
    player_actuals: List[Dict[str, Any]],
    season: int,
    week: int,
) -> Dict[str, Any]:
    """
    Build response payload with per-roster totals and strengths/weaknesses.
    """
    user_map = {
        user["user_id"]: {
            "display_name": user.get("display_name") or "",
            "team_name": user.get("team_name") or "",
        }
        for user in users
    }
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

    roster_summaries = []
    for roster in rosters:
        roster_id = roster.get("roster_id")
        owner_id = roster.get("owner_id")
        owner_info = user_map.get(owner_id, {})
        display_name = owner_info.get("display_name") or str(owner_id)
        team_name = owner_info.get("team_name") or ""
        wins = int(roster.get("wins") or 0)
        losses = int(roster.get("losses") or 0)
        ties = int(roster.get("ties") or 0)
        total_moves = int(roster.get("total_moves") or 0)
        waiver_position = roster.get("waiver_position")
        fpts = float(roster.get("fpts") or 0.0)
        fpts_against = float(roster.get("fpts_against") or 0.0)

        strength, weakness = _derive_strengths_and_weaknesses(
            roster_position_totals=roster_position_totals.get(roster_id, {}),
            league_position_averages=league_position_averages,
        )

        roster_summaries.append(
            {
                "roster_id": roster_id,
                "owner_id": owner_id,
                "display_name": display_name,
                "team_name": team_name,
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "total_moves": total_moves,
                "waiver_position": waiver_position,
                "fpts": round(fpts, 2),
                "fpts_against": round(fpts_against, 2),
                "position_totals": roster_position_totals.get(roster_id, {}),
                "strength": strength,
                "weakness": weakness,
            }
        )

    roster_summaries_sorted = sorted(
        roster_summaries,
        key=lambda entry: float(entry.get("fpts") or 0.0),
        reverse=True,
    )

    summary_text, details_text = _format_league_summary_text(
        roster_summaries=roster_summaries_sorted,
        week=week,
    )

    response = {
        "season": season,
        "week": week,
        "summary": summary_text,
        "details": details_text,
        "rosters": roster_summaries_sorted,
    }
    return response


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


def _format_league_summary_text(
    roster_summaries: List[Dict[str, Any]],
    week: int,
) -> Tuple[str, str]:
    """
    Build summary and details strings for display.
    """
    summary = "No league data available yet."
    details_lines: List[str] = []

    if roster_summaries:
        summary = "League Overview"
        for roster in roster_summaries:
            display_name = roster.get("display_name") or roster.get("owner_id")
            fpts = float(roster.get("fpts") or 0.0)
            fpts_against = float(roster.get("fpts_against") or 0.0)
            wins = roster.get("wins") or 0
            losses = roster.get("losses") or 0
            ties = roster.get("ties") or 0
            total_moves = roster.get("total_moves") or 0
            strength = roster.get("strength") or "Even"
            weakness = roster.get("weakness") or "Even"
            position_totals = roster.get("position_totals") or {}
            position_parts = [
                f"{position}: {float(total):.2f}"
                for position, total in sorted(position_totals.items())
            ]
            positions_line = ", ".join(position_parts) if position_parts else "None"

            details_lines.append(f"Roster Owner: {display_name}")
            details_lines.append(f"Record: {wins}-{losses}-{ties}")
            details_lines.append(f"Points Scored: {fpts:.2f}")
            details_lines.append(f"Points Allowed: {fpts_against:.2f}")
            details_lines.append(f"Roster Moves: {total_moves}")
            details_lines.append(f"Position Totals: {positions_line}")
            details_lines.append(f"Strength: {strength} | Weakness: {weakness}")
            details_lines.append("")

    details = "\n".join(details_lines).strip()
    return summary, details


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
