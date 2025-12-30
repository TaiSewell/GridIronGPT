"""
=============================================================
dst_service.py
Author: Tai Sewell

Business logic for DST projections and actuals.
=============================================================
"""

from typing import Optional

from data.db import get_conn
import data.queries.dst_queries as q_dst
import data.queries.league_queries as q_league
from data.cache_manager import CacheManager
from backend.app.config import settings


def list_dst_weekly_projections_service(
    week: int,
    season: Optional[int] = None,
    team: Optional[str] = None,
    limit: int = 32,
    offset: int = 0,
):
    league_id = settings.SLEEPER_LEAGUE_ID
    if not league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")

    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)
    cache.ensure_players_cached()

    if season is None:
        with get_conn() as conn:
            season = q_league.get_league_season(conn, league_id)
        if season is None:
            raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    cache.ensure_weekly_projections_cached(season, week)
    cache.ensure_player_week_meta_cached(season, week)
    cache.ensure_weekly_actuals_cached(season, week)

    with get_conn() as conn:
        return q_dst.list_dst_weekly_projections(
            conn=conn,
            league_id=league_id,
            season=season,
            week=week,
            team=team,
            limit=limit,
            offset=offset,
        )
