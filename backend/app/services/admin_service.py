"""
=============================================================
 File: admin_service.py
 Author: Tai Sewell
 Description:
     Admin workflows for switching the active league and
     triggering a full cache refresh.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.cache_manager import CacheManager
from backend.db import get_conn
import backend.queries.league_queries as q_league


def switch_active_league_service(league_id: str) -> Dict[str, Any]:
    """
    Sync league data for the requested league id.
    """
    cleaned_league_id = league_id.strip()
    if not cleaned_league_id:
        raise ValueError("league_id cannot be empty.")

    cache_manager = CacheManager(league_id=cleaned_league_id)
    cache_manager.ensure_players_cached(force_refresh=True)
    cache_manager.ensure_league_bundle_cached(week=None, force_refresh=True)

    league_season: Optional[int] = None
    with get_conn() as conn:
        league_season = q_league.get_league_season(conn, cleaned_league_id)

    response = {
        "league_id": cleaned_league_id,
        "season": league_season,
        "status": "synced",
    }
    return response
