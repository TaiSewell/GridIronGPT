"""
=============================================================
player_service.py
Developer: Tai Sewell
------------------
Business logic for managing player data and operations.

Handles:
- Player information retrieval and updates
- Player statistics and performance data
- Player-related queries from the database
=============================================================
"""

from typing import Optional

from backend.db import get_conn
import backend.queries.player_queries as q_player
import backend.queries.league_queries as q_league
from backend.cache_manager import CacheManager
from backend.app.config import settings

cache = CacheManager(league_id=settings.SLEEPER_LEAGUE_ID)

def search_player_by_name_service(
    player_name: str,
    limit: Optional[int] = None,
):
    limit = limit or 25

    cache.ensure_players_cached()

    with get_conn() as conn:
        return q_player.search_players_by_name(conn, player_name, limit)


def get_player_by_id_service(player_id: str):
    """
    Fetch a single player by Sleeper player_id (TEXT).
    """
    cache.ensure_players_cached()

    with get_conn() as conn:
        return q_player.get_player_by_id(conn, player_id)


def search_player_projections_service(
    name: str,
    week: int,
    limit: int = 25,
    season: Optional[int] = None,
):
    league_id = settings.SLEEPER_LEAGUE_ID
    if not league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")

    # IMPORTANT: cache must be per-league (don't use a global CacheManager here)
    cache = CacheManager(league_id=league_id)

    # 1) Ensure scoring exists (view depends on scoring_settings via v_player_weekly_proj_points)
    cache.ensure_league_bundle_cached(week=None)

    # 2) Ensure players exist (view joins players)
    cache.ensure_players_cached()

    # 3) Resolve season from DB if not provided
    if season is None:
        with get_conn() as conn:
            season = q_league.get_league_season(conn, league_id)
        if season is None:
            raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    # 4) Ensure weekly projection stats exist
    cache.ensure_weekly_projections_cached(season, week)

    # 5) Ensure opponent/home-away context exists
    cache.ensure_player_week_meta_cached(season, week)

    # 6) Ensure weekly actuals exist (FantasyPointsPPR)
    cache.ensure_weekly_actuals_cached(season, week)

    # 7) Query the view
    with get_conn() as conn:
        return q_player.search_player_projections_by_name(
            conn=conn,
            league_id=league_id,
            season=season,
            week=week,
            name=name,
            limit=limit,
        )
    
def list_players_service(limit: int = 200, offset: int = 0):
    cache.ensure_players_cached()
    with get_conn() as conn:
        return q_player.get_players(conn, limit, offset)


def get_player_with_weekly_projection_service(
    player_id: str,
    week: int,
    season: Optional[int] = None,
):
    league_id = settings.SLEEPER_LEAGUE_ID
    if not league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")

    # IMPORTANT: cache must be per-league (don't use a global CacheManager here)
    cache = CacheManager(league_id=league_id)

    # 1) Ensure scoring exists (view depends on scoring_settings via v_player_weekly_proj_points)
    cache.ensure_league_bundle_cached(week=None)

    # 2) Ensure players exist (view joins players)
    cache.ensure_players_cached()

    # 3) Resolve season from DB if not provided
    if season is None:
        with get_conn() as conn:
            season = q_league.get_league_season(conn, league_id)
        if season is None:
            raise ValueError(f"League not found in DB (cannot resolve season): {league_id}")

    # 4) Ensure weekly projection stats exist
    cache.ensure_weekly_projections_cached(season, week)

    # 5) Ensure opponent/home-away context exists
    cache.ensure_player_week_meta_cached(season, week)

    # 6) Ensure weekly actuals exist (FantasyPointsPPR)
    cache.ensure_weekly_actuals_cached(season, week)

    # 7) Query the view
    with get_conn() as conn:
        return q_player.get_player_weekly_projection(
            conn=conn,
            league_id=league_id,
            season=season,
            week=week,
            player_id=player_id,
        )


def get_player_weekly_projections_by_ids_service(
    player_ids: list[str],
    week: int,
    season: Optional[int] = None,
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
        return q_player.get_player_weekly_projections_by_ids(
            conn=conn,
            league_id=league_id,
            season=season,
            week=week,
            player_ids=player_ids,
        )
