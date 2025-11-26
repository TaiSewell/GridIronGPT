"""
scoring_service.py
------------------
Business logic for computing projected fantasy points.

Combines:
- Raw weekly projection stats from SportsDataIO
- League scoring settings from the DB
- Positional multipliers/bonuses

and returns a list of player projections.

This module does NOT talk to external APIs or handle caching.
It only reads from SQLite via data/db.py and applies scoring rules.
"""

from __future__ import annotations
from typing import Any, Dict, List, Mapping, Optional
import logging
from data.db import get_conn 

LOG = logging.getLogger(__name__)

def fetch_scoring_weights(league_id: str) -> Dict[str, float]:
    """
    Load scoring settings for a league into a simple mapping:
        stat_key -> weight

    Example:
        "pass_yd" -> 0.04
        "pass_td" -> 4.0
        "rec_yd"  -> 0.1
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT stat_key, weight
            FROM scoring_settings
            WHERE league_id = ?
            """,
            (league_id,),
        ).fetchall()

    weights: Dict[str, float] = {}
    for row in rows:
        stat_key = row["stat_key"]
        weight = float(row["weight"])
        weights[stat_key] = weight

    LOG.info("Loaded %d scoring settings for league %s", len(weights), league_id)
    return weights


def fetch_player_positions() -> Dict[str, str]:
    """
    Load player positions into a mapping:
        player_id -> position (e.g., 'QB', 'RB', 'WR', 'TE')
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT player_id, position FROM players"
        ).fetchall()

    positions: Dict[str, str] = {}
    for row in rows:
        positions[row["player_id"]] = row["position"] or ""

    LOG.info("Loaded positions for %d players", len(positions))
    return positions


def fetch_weekly_projection_stats(season: int, week: int, source: Optional[str] = None) -> List[Mapping[str, Any]]:
    """
    Fetch raw projection stats from player_weekly_proj_stats for a given season/week.

    Each row is expected to have:
        - player_id
        - stat_key
        - value
        - season
        - week
        - source
    """
    query = """
        SELECT player_id, stat_key, value, season, week, source
        FROM player_weekly_proj_stats
        WHERE season = ? AND week = ?
    """
    params: tuple[Any, ...] = (season, week)

    if source is not None:
        query += " AND source = ?"
        params = (season, week, source)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    LOG.info(
        "Loaded %d raw projection stat rows for season=%s week=%s (source=%s)",
        len(rows),
        season,
        week,
        source or "ANY",
    )
    return rows


def compute_weekly_projected_points(
    league_id: str,
    season: int,
    week: int,
    *,
    position_multipliers: Optional[Dict[str, float]] = None,
    source: Optional[str] = "sportsdataio",
) -> List[Dict[str, Any]]:
    """
    Compute projected fantasy points for each player for a given season/week.

    Steps:
    1. Load league scoring settings (stat_key -> weight).
    2. Load player positions.
    3. Load raw projection stats for that season/week.
    4. Aggregate stats per player and apply scoring weights.
    5. Apply optional positional multipliers (e.g. TE premium).

    Args:
        league_id: Sleeper league ID for scoring settings.
        season:   Season (e.g., 2025).
        week:     Week number (e.g., 10).
        position_multipliers:
            Optional mapping like {"TE": 1.1, "RB": 1.05}.
            If None, defaults to no extra multiplier (1.0 for all).
        source:
            Optional stat source filter in player_weekly_proj_stats (e.g. "sportsdataio").

    Returns:
        List of dicts with:
            {
                "player_id": str,
                "position": str,
                "projected_points": float,
                "season": int,
                "week": int
            }
        Sorted by projected_points DESC.
    """
    position_multipliers = position_multipliers or {}

    weights = fetch_scoring_weights(league_id)
    positions = fetch_player_positions()
    raw_rows = fetch_weekly_projection_stats(season, week, source=source)

    # Aggregate to player_id -> {stat_key: value}
    stats_by_player: Dict[str, Dict[str, float]] = {}
    for row in raw_rows:
        pid = row["player_id"]
        stat_key = row["stat_key"]
        value = float(row["value"] or 0.0)

        if pid not in stats_by_player:
            stats_by_player[pid] = {}

        stats_by_player[pid][stat_key] = stats_by_player[pid].get(stat_key, 0.0) + value

    LOG.info(
        "Aggregated projection stats for %d players (season=%s, week=%s)",
        len(stats_by_player),
        season,
        week,
    )

    # 4) Apply scoring weights + positional multiplier
    results: List[Dict[str, Any]] = []

    for pid, stat_dict in stats_by_player.items():
        base_points = 0.0

        # Base fantasy points from league scoring weights
        for stat_key, val in stat_dict.items():
            weight = float(weights.get(stat_key, 0.0))
            base_points += val * weight

        # Positional multiplier (e.g., TE premium)
        pos = positions.get(pid, "")
        multiplier = float(position_multipliers.get(pos, 1.0))
        projected_points = base_points * multiplier

        results.append(
            {
                "player_id": pid,
                "position": pos,
                "projected_points": round(projected_points, 2),
                "season": season,
                "week": week,
            }
        )

    # Sort highest → lowest projected points
    results.sort(key=lambda r: r["projected_points"], reverse=True)

    LOG.info(
        "Computed weekly projected points for %d players (season=%s, week=%s)",
        len(results),
        season,
        week,
    )

    return results