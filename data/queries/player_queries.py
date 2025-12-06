"""
player_queries.py

Module for handling database queries related to player data.
Provides functionality to retrieve, filter, and manage player information
from the database including player statistics, profiles, and related metadata.
"""

from typing import Any, Dict, List, Optional

def get_players(conn, limit: int) -> Optional[Dict[str, Any]]:
    cursor = conn.execute(
        """
        SELECT * FROM players 
        """
    )

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
def get_player_with_weekly_projection(
    conn,
    player_id: str,
    season: int,
    week: int,
    league_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Return a single player's info + weekly projection for a given league/season/week.
    """
    row = conn.execute(
        """
        SELECT
          p.player_id,
          p.player_name,
          p.team,
          p.position,
          v.season,
          v.week,
          v.league_id,
          v.opp_team,
          v.is_home,
          v.baseline_points,
          v.multiplier,
          v.bonus,
          v.final_projection
        FROM players AS p
        LEFT JOIN v_player_weekly_final_proj AS v
          ON v.player_id = p.player_id
         AND v.season    = ?
         AND v.week      = ?
         AND v.league_id = ?
        WHERE p.player_id = ?;
        """,
        (season, week, league_id, player_id),
    ).fetchone()

    if row is None:
        return None
    
    return dict(row)
