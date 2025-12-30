"""
=============================================================
rosters_service.py
Developer: Tai Sewell
------------------
Business logic for roster queries and orchestration.
=============================================================
"""

from __future__ import annotations

from typing import Optional

from backend.app.config import settings
from data.cache_manager import CacheManager
from data.db import get_conn
import data.queries.roster_queries as q_rosters
import data.queries.user_queries as q_users


def _get_league_id() -> str:
    league_id = settings.SLEEPER_LEAGUE_ID
    if not league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")
    return league_id


def list_rosters_service() -> list[dict]:
    league_id = _get_league_id()

    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    with get_conn() as conn:
        return q_rosters.list_rosters_by_league(conn, league_id)


def get_roster_by_owner_service(username: str) -> Optional[dict]:
    league_id = _get_league_id()

    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    with get_conn() as conn:
        matches = q_users.search_users_by_name(conn, username)
        if not matches:
            return None

        username_norm = username.strip().lower()
        exact = [u for u in matches if (u.get("display_name") or "").lower() == username_norm]

        if len(exact) == 1:
            owner_id = exact[0]["user_id"]
        elif len(matches) == 1:
            owner_id = matches[0]["user_id"]
        else:
            raise ValueError(f"Multiple users matched '{username}'. Use a more specific name.")

        return q_rosters.get_roster_by_owner(conn, league_id, owner_id)
