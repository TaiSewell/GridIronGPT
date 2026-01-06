"""
=============================================================
dst_queries.py
Author: Tai Sewell

Description: Queries for DST projections and actuals.
=============================================================
"""

from typing import Any, Dict, List, Optional


def list_dst_weekly_projections(
    conn,
    league_id: str,
    season: int,
    week: int,
    team: Optional[str] = None,
    limit: int = 32,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    params = [league_id, season, week]
    team_filter = ""
    if team:
        team_filter = " AND p.team = ?"
        params.append(team.upper())

    params.extend([league_id, limit, offset])

    rows = conn.execute(
        f"""
        WITH dst_base AS (
            SELECT
                pws.player_id,
                p.team AS dst_team,
                pws.season,
                pws.week,
                ROUND(
                    pws.value * COALESCE(adj.multiplier, 1.0)
                    + COALESCE(adj.bonus, 0.0),
                    2
                ) AS projected_points
            FROM player_weekly_proj_stats AS pws
            JOIN players AS p
              ON p.player_id = pws.player_id AND p.position = 'DST'
            LEFT JOIN projection_adjustments AS adj
              ON adj.league_id = ?
             AND adj.position = 'DST'
            WHERE pws.season = ?
              AND pws.week = ?
              AND pws.stat_key = 'dst_fp'
              {team_filter}
        )
        SELECT
            d.player_id,
            d.dst_team,
            d.season,
            d.week,
            ? AS league_id,
            d.projected_points
        FROM dst_base AS d
        ORDER BY d.projected_points DESC, d.dst_team ASC
        LIMIT ? OFFSET ?;
        """,
        tuple(params),
    ).fetchall()

    return [dict(r) for r in rows]
