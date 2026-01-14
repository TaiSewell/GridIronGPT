"""
=============================================================
dst_queries.py
Author: Tai Sewell

Description: Queries for DST projections and actuals.
=============================================================
"""

from typing import Any, Dict, List, Optional


def list_dst_weekly_points(
    conn,
    season: int,
    week: int,
    team: Optional[str] = None,
    limit: int = 32,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    params = [season, week]
    team_filter = ""
    if team:
        team_filter = " AND dst_team = ?"
        params.append(team.upper())

    params.extend([limit, offset])

    rows = conn.execute(
        f"""
        SELECT
            dst_team,
            season,
            week,
            projected_points,
            actual_points
        FROM dst
        WHERE season = ?
          AND week = ?
          {team_filter}
        ORDER BY projected_points DESC, dst_team ASC
        LIMIT ? OFFSET ?;
        """,
        tuple(params),
    ).fetchall()

    results = []
    for row in rows:
        result = dict(row)
        result["player_id"] = f"DST-{result.get('dst_team')}"
        results.append(result)

    return results


def list_dst_season_actual_ranks(
    conn,
    season: int,
    limit: int = 32,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            season,
            dst_rank,
            dst_team,
            total_points
        FROM v_dst_season_actual_rank
        WHERE season = ?
        ORDER BY dst_rank ASC
        LIMIT ? OFFSET ?;
        """,
        (season, limit, offset),
    ).fetchall()

    results = [dict(row) for row in rows]
    return results
