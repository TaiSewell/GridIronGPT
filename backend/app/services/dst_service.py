"""
=============================================================
dst_service.py
Author: Tai Sewell

Business logic for DST projections and actuals.
=============================================================
"""

from typing import Optional

from backend.db import get_conn
import backend.queries.dst_queries as q_dst
import backend.queries.league_queries as q_league
from backend.cache_manager import CacheManager


def list_dst_weekly_points_service(
    week: int,
    league_id: str,
    season: Optional[int] = None,
    team: Optional[str] = None,
    limit: int = 32,
    offset: int = 0,
):
    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)
    cache.ensure_players_cached()

    if season is None:
        with get_conn() as conn:
            season = q_league.get_league_season(conn, league_id)
        if season is None:
            raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    cache.ensure_weekly_projections_cached(season, week)
    cache.ensure_weekly_actuals_cached(season, week)

    with get_conn() as conn:
        return q_dst.list_dst_weekly_points(
            conn=conn,
            season=season,
            week=week,
            team=team,
            limit=limit,
            offset=offset,
        )


def list_dst_season_actual_ranks_service(
    league_id: str,
    season: Optional[int] = None,
    limit: int = 32,
    offset: int = 0,
):
    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    if season is None:
        with get_conn() as conn:
            season = q_league.get_league_season(conn, league_id)
        if season is None:
            raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    with get_conn() as conn:
        return q_dst.list_dst_season_actual_ranks(
            conn=conn,
            season=season,
            limit=limit,
            offset=offset,
        )
