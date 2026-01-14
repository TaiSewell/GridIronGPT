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
        SELECT
            league_id,
            roster_id,
            owner_id,
            starters_json,
            bench_json,
            wins,
            losses,
            ties,
            waiver_position,
            total_moves,
            fpts,
            fpts_against
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
        SELECT
            league_id,
            roster_id,
            owner_id,
            starters_json,
            bench_json,
            wins,
            losses,
            ties,
            waiver_position,
            total_moves,
            fpts,
            fpts_against
        FROM rosters
        WHERE league_id = ? AND owner_id = ?
        """,
        (league_id, owner_id),
    ).fetchone()

    return dict(row) if row else None


def get_matchups_for_league_season(
    conn,
    league_id: str,
    season: int,
    week: int,
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            roster_id,
            week,
            players_json,
            points
        FROM matchups
        WHERE league_id = ?
          AND season = ?
          AND week <= ?
        ORDER BY roster_id ASC, week ASC
        """,
        (league_id, season, week),
    ).fetchall()

    results = [dict(row) for row in rows]
    return results
