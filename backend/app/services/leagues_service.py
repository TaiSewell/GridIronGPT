"""
=============================================================
leagues_service.py
Author: Tai Sewell

Business logic for providing league information.
=============================================================
"""

from data.db import get_conn
import data.queries as q

def get_league_season_service(league_id: str) -> int:
    with get_conn() as conn:
        season = q.get_league_season(conn, league_id)
        if season is None:
            raise ValueError(f"League {league_id} not found.")
        return season