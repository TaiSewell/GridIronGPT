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

from backend.app.config import settings
from backend.cache_manager import CacheManager
from backend.db import get_conn
import backend.queries.league_queries as q_league
import backend.queries.player_queries as q_player


def build_fantasy_leaders_service(
    limit: int,
    season: Optional[int] = None,
    week: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a leaderboard of fantasy scorers based on actual points.
    """
    league_id = settings.SLEEPER_LEAGUE_ID
    if not league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")

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
        with get_conn() as conn:
            resolved_week = q_player.get_latest_week_with_actual_points(
                conn=conn,
                season=resolved_season,
            )

    if resolved_week:
        for current_week in range(1, resolved_week + 1):
            cache_manager.ensure_weekly_actuals_cached(resolved_season, current_week)

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
