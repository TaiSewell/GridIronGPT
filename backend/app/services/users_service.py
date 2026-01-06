"""
=============================================================
users_service.py
Developer: Tai Sewell
------------------
Business logic for user queries and orchestration.
=============================================================
"""

from __future__ import annotations

from typing import List, Optional
import json

from backend.app.config import settings
from backend.cache_manager import CacheManager
from backend.db import get_conn
import backend.queries.user_queries as q_users


def _get_league_id() -> str:
    league_id = settings.SLEEPER_LEAGUE_ID
    if not league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")
    return league_id


def list_users_service() -> List[dict]:
    league_id = _get_league_id()
    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    with get_conn() as conn:
        users = q_users.list_users(conn)

    return [_hydrate_team_name(u) for u in users]


def get_user_by_id_service(user_id: str) -> Optional[dict]:
    league_id = _get_league_id()
    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    with get_conn() as conn:
        user = q_users.get_user_by_id(conn, user_id)

    return _hydrate_team_name(user) if user else None


def search_users_by_name_service(name: str) -> List[dict]:
    league_id = _get_league_id()
    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    with get_conn() as conn:
        users = q_users.search_users_by_name(conn, name)

    return [_hydrate_team_name(u) for u in users]


def _hydrate_team_name(user: dict) -> dict:
    if not user:
        return user

    if user.get("team_name"):
        return user

    metadata_json = user.get("metadata_json")
    if not metadata_json:
        return user

    try:
        metadata = json.loads(metadata_json)
    except (TypeError, ValueError):
        return user

    if isinstance(metadata, dict):
        team_name = metadata.get("team_name")
        if team_name:
            user["team_name"] = team_name

    return user
