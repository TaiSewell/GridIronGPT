"""
=============================================================
roster_queries.py
Author: Tai Sewell

Database queries for roster data.
=============================================================
"""

from typing import Any, Dict, List, Optional


def list_rosters_by_league(conn, league_id: str) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT league_id, roster_id, owner_id, starters_json, bench_json
        FROM rosters
        WHERE league_id = ?
        ORDER BY roster_id ASC
        """,
        (league_id,),
    ).fetchall()

    return [dict(r) for r in rows]


def get_roster_by_owner(conn, league_id: str, owner_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT league_id, roster_id, owner_id, starters_json, bench_json
        FROM rosters
        WHERE league_id = ? AND owner_id = ?
        """,
        (league_id, owner_id),
    ).fetchone()

    return dict(row) if row else None
