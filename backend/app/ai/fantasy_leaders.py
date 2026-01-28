"""
=============================================================
 File: fantasy_leaders.py
 Author: Tai Sewell
 Description:
     Builds a fantasy points leaderboard from weekly actuals.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.cache_manager import CacheManager
from backend.db import get_conn
import backend.queries.league_queries as q_league
import backend.queries.player_queries as q_player

def _resolve_latest_completed_week(client, season: int) -> Optional[int]:
    latest_week: Optional[int] = None
    for week in range(1, 19):
        schedule = client.get_schedule(season, week) or []
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


def build_fantasy_leaders_service(
    limit: int,
    league_id: str,
    season: Optional[int] = None,
    week: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a leaderboard of fantasy scorers based on actual points.
    """
    cache_manager = CacheManager(league_id=league_id)
    cache_manager.ensure_players_cached()

    resolved_season = season
    if resolved_season is None:
        with get_conn() as conn:
            resolved_season = q_league.get_league_season(conn, league_id)

    if resolved_season is None:
        raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    resolved_week = week
    if resolved_week is None:
        resolved_week = _resolve_latest_completed_week(cache_manager.client, resolved_season)

    if resolved_week:
        for current_week in range(1, resolved_week + 1):
            cache_manager.ensure_weekly_actuals_cached(resolved_season, current_week)
        with get_conn() as conn:
            latest_with_points = q_player.get_latest_week_with_actual_points(
                conn=conn,
                season=resolved_season,
            )
        if latest_with_points:
            resolved_week = latest_with_points

    leaders: List[Dict[str, Any]] = []
    if resolved_week:
        with get_conn() as conn:
            leaders = q_player.get_top_players_by_actual_points(
                conn=conn,
                season=resolved_season,
                week=resolved_week,
                limit=limit,
            )

    response = _format_fantasy_leaders_response(
        leaders=leaders,
        season=resolved_season,
        week=resolved_week or 0,
        limit=limit,
    )
    return response


def _format_fantasy_leaders_response(
    leaders: List[Dict[str, Any]],
    season: int,
    week: int,
    limit: int,
) -> Dict[str, Any]:
    """
    Format fantasy leaders into a ranked response payload.
    """
    ranked_leaders: List[Dict[str, Any]] = []
    lines: List[str] = []
    summary = "No fantasy scoring data available yet."

    if leaders:
        for index, leader in enumerate(leaders, start=1):
            player_name = leader.get("player_name") or leader.get("player_id")
            position = leader.get("position") or "UNK"
            team = leader.get("team") or "FA"
            total_points = float(leader.get("total_points") or 0.0)
            ranked_leaders.append(
                {
                    "rank": index,
                    "player_id": leader.get("player_id"),
                    "player_name": player_name,
                    "position": position,
                    "team": team,
                    "total_points": total_points,
                }
            )
            lines.append(
                f"{index}. {player_name} ({position}-{team}) - {total_points:.2f} pts"
            )

        summary = f"Top {len(ranked_leaders)} fantasy scorers through week {week}."

    details = "\n".join(lines)
    response = {
        "season": season,
        "week": week,
        "limit": limit,
        "summary": summary,
        "details": details,
        "leaders": ranked_leaders,
    }
    return response
