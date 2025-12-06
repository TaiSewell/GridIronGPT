"""
player_service.py
Developer: Tai Sewell
------------------
Business logic for managing player data and operations.

Handles:
- Player information retrieval and updates
- Player statistics and performance data
- Player-related queries from the database

This module does NOT talk to external APIs or handle caching.
It only reads from SQLite via data/db.py and applies business rules.
"""

from data.db import get_conn
import data.queries as q
from data.cache_manager import CacheManager
from data.data_client import DataClient
from data import sync
from typing import Optional
from app.config import settings

data_client = DataClient()
cache = CacheManager(league_id=settings.SLEEPER_LEAGUE_ID)

def search_player_by_name_service(
    player_name: str,
    limit: Optional[int] = None,
):
    """
    Search players by (partial) name.

    - Ensures the players cache is fresh.
    - Delegates to `q.search_players_by_name`.
    """
    cache.ensure_players_cached()

    with get_conn() as conn:
        return q.search_players_by_name(conn, player_name, limit=limit)


def get_player_by_id_service(player_id: int):
    """
    Fetch a single player row by internal player_id.
    """
    cache.ensure_players_cached()

    with get_conn() as conn:
        return q.get_player_by_id(conn, player_id)


def get_player_with_weekly_projection_service(
    player_id: str,
    week: int,
    season: int | None = None,
    league_id: str | None = None,
):
    # If no league_id passed, use your global default
    league_id = league_id or settings.SLEEPER_LEAGUE_ID, default=None
    season = season or q.get_league_season_service(league_id)

    cache.ensure_players_cached()
    cache.ensure_weekly_projections_cached(season, week)

    with get_conn() as conn:
        return q.get_player_with_weekly_projection(
            conn,
            player_id,
            season,
            week,
            league_id,
        )