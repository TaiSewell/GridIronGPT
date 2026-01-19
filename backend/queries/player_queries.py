"""
=============================================================
player_queries.py
Author: Tai Sewell

Module for handling database queries related to player data.
Provides functionality to retrieve, filter, and manage player information
from the database including player statistics, profiles, and related metadata.
=============================================================
"""

from typing import Any, Dict, List, Optional

def get_players(conn, limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            player_id,
            player_name,
            team,
            position,
            status
        FROM players
        ORDER BY player_name
        LIMIT ? OFFSET ?;
        """,
        (limit, offset),
    ).fetchall()

    return [dict(row) for row in rows]

# Get a single player by ID
def get_player_by_id(conn, player_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.execute(
        """
        SELECT
            player_id,
            player_name,
            team,
            position,
            status
        FROM players
        WHERE player_id = ?
        """,
        (player_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None

# Search players by (partial) name
def search_players_by_name(conn, name: str, limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            player_id,
            player_name,
            team,
            position,
            status
        FROM players
        WHERE player_name LIKE ?
        ORDER BY player_name ASC
        LIMIT ? OFFSET ?
        """,
        (f"%{name}%", limit, offset),
    ).fetchall()

    return [dict(r) for r in rows]


# Get projections for a given week, optionally filtered by position
def search_player_projections_by_name(
    conn,
    league_id: str,
    season: int,
    week: int,
    name: str,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            v.player_id,
            v.player_name,
            v.position,
            v.season,
            v.week,
            v.opp_team,
            v.is_home,
            pwm.actual_points,
            v.final_projection
        FROM v_player_weekly_final_proj AS v
        LEFT JOIN player_week_meta AS pwm
          ON pwm.player_id = v.player_id
         AND pwm.season = v.season
         AND pwm.week = v.week
        WHERE v.league_id = ?
          AND v.season = ?
          AND v.week = ?
          AND v.player_name LIKE ?
        ORDER BY v.final_projection DESC, v.player_name ASC
        LIMIT ?;
        """,
        (league_id, season, week, f"%{name}%", limit),
    ).fetchall()

    return [dict(r) for r in rows]


def get_player_weekly_projection(
    conn,
    league_id: str,
    season: int,
    week: int,
    player_id: str,
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT
            v.player_id,
            v.player_name,
            v.position,
            v.season,
            v.week,
            v.opp_team,
            v.is_home,
            pwm.actual_points,
            v.final_projection
        FROM v_player_weekly_final_proj AS v
        LEFT JOIN player_week_meta AS pwm
          ON pwm.player_id = v.player_id
         AND pwm.season = v.season
         AND pwm.week = v.week
        WHERE v.league_id = ?
          AND v.season = ?
          AND v.week = ?
          AND v.player_id = ?
        """,
        (league_id, season, week, player_id),
    ).fetchone()

    return dict(row) if row else None


def get_player_weekly_projections_by_ids(
    conn,
    league_id: str,
    season: int,
    week: int,
    player_ids: List[str],
) -> List[Dict[str, Any]]:
    if not player_ids:
        return []

    placeholders = ",".join("?" for _ in player_ids)
    rows = conn.execute(
        f"""
        SELECT
            v.player_id,
            v.player_name,
            v.position,
            v.season,
            v.week,
            v.opp_team,
            v.is_home,
            pwm.actual_points,
            v.final_projection
        FROM v_player_weekly_final_proj AS v
        LEFT JOIN player_week_meta AS pwm
          ON pwm.player_id = v.player_id
         AND pwm.season = v.season
         AND pwm.week = v.week
        WHERE v.league_id = ?
          AND v.season = ?
          AND v.week = ?
          AND v.player_id IN ({placeholders})
        ORDER BY v.final_projection DESC, v.player_name ASC
        """,
        (league_id, season, week, *player_ids),
    ).fetchall()

    return [dict(r) for r in rows]


def get_latest_week_with_actual_points(
    conn,
    season: int,
) -> Optional[int]:
    row = conn.execute(
        """
        SELECT MAX(week) AS max_week
        FROM player_week_meta
        WHERE season = ?
          AND actual_points IS NOT NULL
        """,
        (season,),
    ).fetchone()

    latest_week: Optional[int] = None
    if row and row["max_week"] is not None:
        latest_week = int(row["max_week"])

    return latest_week


def get_top_players_by_actual_points(
    conn,
    season: int,
    week: int,
    limit: int,
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            p.player_id,
            p.player_name,
            p.team,
            p.position,
            ROUND(SUM(pwm.actual_points), 2) AS total_points
        FROM player_week_meta AS pwm
        JOIN players AS p
          ON p.player_id = pwm.player_id
        WHERE pwm.season = ?
          AND pwm.week <= ?
          AND pwm.actual_points IS NOT NULL
        GROUP BY
            p.player_id,
            p.player_name,
            p.team,
            p.position
        ORDER BY total_points DESC, p.player_name ASC
        LIMIT ?;
        """,
        (season, week, limit),
    ).fetchall()

    results = [dict(row) for row in rows]
    return results


def get_player_week_actuals(
    conn,
    season: int,
    week: int,
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            pwm.player_id,
            pwm.week,
            pwm.actual_points,
            p.position
        FROM player_week_meta AS pwm
        JOIN players AS p
          ON p.player_id = pwm.player_id
        WHERE pwm.season = ?
          AND pwm.week <= ?
          AND pwm.actual_points IS NOT NULL
        """,
        (season, week),
    ).fetchall()

    results = [dict(row) for row in rows]
    return results


def get_players_by_ids(
    conn,
    player_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Fetch player metadata for a list of player ids.
    """
    results: List[Dict[str, Any]] = []
    if player_ids:
        placeholders = ",".join("?" for _ in player_ids)
        rows = conn.execute(
            f"""
            SELECT
                player_id,
                player_name,
                team,
                position,
                status
            FROM players
            WHERE player_id IN ({placeholders})
            """,
            tuple(player_ids),
        ).fetchall()

        results = [dict(row) for row in rows]
    return results
