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
from data import player_queries as q
from data import cache_manager
from data.data_client import DataClient
from data import sync

data_client = DataClient()

def search_player_by_name_service(player_name: str):
    if cache_manager.is_expired("players"):
        players = data_client.fetch_players()
        sync.sync_players(players)
        cache_manager.update("players")

    with get_conn() as conn:
        return q.search_players_by_name(conn, player_name)


def get_player_by_id_service(player_id: int):
    if cache_manager.is_expired("players"):
        players = data_client.fetch_players()
        sync.sync_players(players)
        cache_manager.update("players")

    with get_conn() as conn:
        return q.get_player_by_id(conn, player_id)


def get_weekly_player_projections_service(week: int, position=None, limit=None):
    cache_key = f"projections_week_{week}"

    if cache_manager.is_expired(cache_key):
        projections = data_client.fetch_weekly_projections(week)
        sync.sync_weekly_projections(projections)
        cache_manager.update(cache_key)

    with get_conn() as conn:
        return q.get_player_projections_for_week(conn, week, position, limit)


