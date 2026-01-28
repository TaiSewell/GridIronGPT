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

from backend.cache_manager import CacheManager
from backend.db import get_conn
import backend.queries.roster_queries as q_rosters
import backend.queries.user_queries as q_users

def list_rosters_service(league_id: str) -> list[dict]:
    cache = CacheManager(league_id=league_id)
    cache.ensure_league_bundle_cached(week=None)

    with get_conn() as conn:
        return q_rosters.list_rosters_by_league(conn, league_id)


def get_roster_by_owner_service(username: str, league_id: str) -> Optional[dict]:
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
