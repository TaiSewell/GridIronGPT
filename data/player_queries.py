"""
player_queries.py

Module for handling database queries related to player data.
Provides functionality to retrieve, filter, and manage player information
from the database including player statistics, profiles, and related metadata.
"""

from typing import Any, Dict, List, Optional

# Get a single player by ID
def get_player_by_id(conn, player_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.execute(
        """
        SELECT
            player_id,
            player_name,
            team,
            pos AS position,
            status,
            week,
            proj_points
        FROM players
        WHERE player_id = ?
        """,
        (player_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


# Search players by (partial) name
def search_players_by_name(conn, name: str) -> List[Dict[str, Any]]:
    cursor = conn.execute(
        """
        SELECT
            player_id,
            player_name,
            team,
            pos AS position,
            status,
            week,
            proj_points
        FROM players
        WHERE player_name LIKE ?
        ORDER BY player_name ASC
        """,
        (f"%{name}%",),
    )
    return [dict(r) for r in cursor.fetchall()]


# Get projections for a given week, optionally filtered by position
def get_player_projections_for_week(
    conn,
    week: int,
    position: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    sql = """
        SELECT
            player_id,
            player_name,
            team,
            pos AS position,
            status,
            week,
            proj_points
        FROM players
        WHERE week = ?
    """
    params: list[Any] = [week]

    if position is not None:
        sql += " AND pos = ?"
        params.append(position)

    sql += " ORDER BY proj_points DESC"

    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    cursor = conn.execute(sql, tuple(params))
    return [dict(r) for r in cursor.fetchall()]
