"""
=============================================================
 File: roster_compare.py
 Author: Tai Sewell
 Description:
     Orchestrates roster comparison data retrieval and
     generates a natural language summary when possible.
=============================================================
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.app.ai.client import run_chat_completion
from backend.app.ai.prompt_builder import build_roster_compare_messages
from backend.app.ai.response_formatter import format_roster_compare_response
from backend.app.services import player_service, rosters_service


def compare_rosters_service(
    user_a: str,
    user_b: str,
    week: int,
    season: Optional[int] = None,
    include_bench: bool = False,
) -> Dict[str, Any]:
    roster_a = rosters_service.get_roster_by_owner_service(user_a)
    roster_b = rosters_service.get_roster_by_owner_service(user_b)

    if not roster_a or not roster_b:
        missing = user_a if not roster_a else user_b
        raise ValueError(f"Roster not found for '{missing}'.")

    roster_a_players = _extract_roster_players(roster_a, include_bench)
    roster_b_players = _extract_roster_players(roster_b, include_bench)

    player_ids = list({*roster_a_players, *roster_b_players})
    projections = player_service.get_player_weekly_projections_by_ids_service(
        player_ids=player_ids,
        week=week,
        season=season,
    )
    projection_map = {p["player_id"]: p for p in projections}

    roster_a_data = _build_roster_projection(
        name=user_a,
        roster=roster_a,
        player_ids=roster_a_players,
        projection_map=projection_map,
    )
    roster_b_data = _build_roster_projection(
        name=user_b,
        roster=roster_b,
        player_ids=roster_b_players,
        projection_map=projection_map,
    )

    comparison = _summarize_comparison(roster_a_data, roster_b_data)
    payload = {
        "week": week,
        "season": season,
        "include_bench": include_bench,
        "roster_a": roster_a_data,
        "roster_b": roster_b_data,
        "comparison": comparison,
    }

    summary = None
    try:
        messages = build_roster_compare_messages(payload)
        summary = run_chat_completion(messages)
    except Exception:
        summary = comparison["summary"]

    return format_roster_compare_response(summary, payload)


def _extract_roster_players(roster: Dict[str, Any], include_bench: bool) -> List[str]:
    starters = _safe_json_list(roster.get("starters_json"))
    bench = _safe_json_list(roster.get("bench_json"))

    players = starters + (bench if include_bench else [])
    cleaned = [str(pid) for pid in players if pid]
    return cleaned


def _safe_json_list(value: Optional[str]) -> List[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


def _build_roster_projection(
    name: str,
    roster: Dict[str, Any],
    player_ids: List[str],
    projection_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    players = []
    total_projection = 0.0

    for pid in player_ids:
        projection = projection_map.get(pid)
        entry = {
            "player_id": pid,
            "player_name": projection.get("player_name") if projection else None,
            "position": projection.get("position") if projection else None,
            "final_projection": projection.get("final_projection") if projection else None,
            "actual_points": projection.get("actual_points") if projection else None,
        }
        players.append(entry)

        points = projection.get("final_projection") if projection else None
        if isinstance(points, (int, float)):
            total_projection += float(points)

    return {
        "name": name,
        "roster_id": roster.get("roster_id"),
        "owner_id": roster.get("owner_id"),
        "players": players,
        "total_projection": round(total_projection, 2),
    }


def _summarize_comparison(
    roster_a: Dict[str, Any],
    roster_b: Dict[str, Any],
) -> Dict[str, Any]:
    total_a = roster_a["total_projection"]
    total_b = roster_b["total_projection"]
    diff = round(total_a - total_b, 2)

    position_advantage = _position_breakdown(roster_a, roster_b)
    leader = roster_a["name"] if diff > 0 else roster_b["name"] if diff < 0 else "Even"

    summary = (
        f"{leader} projects higher by {abs(diff)} points."
        if leader != "Even"
        else "Both rosters project evenly."
    )

    return {
        "leader": leader,
        "point_diff": diff,
        "position_advantage": position_advantage,
        "summary": summary,
    }


def _position_breakdown(
    roster_a: Dict[str, Any],
    roster_b: Dict[str, Any],
) -> List[Dict[str, Any]]:
    def by_pos(roster: Dict[str, Any]) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for player in roster["players"]:
            pos = player.get("position") or "UNK"
            points = player.get("final_projection")
            if isinstance(points, (int, float)):
                totals[pos] = totals.get(pos, 0.0) + float(points)
        return totals

    a_totals = by_pos(roster_a)
    b_totals = by_pos(roster_b)
    positions = sorted(set(a_totals) | set(b_totals))

    breakdown = []
    for pos in positions:
        a_val = round(a_totals.get(pos, 0.0), 2)
        b_val = round(b_totals.get(pos, 0.0), 2)
        breakdown.append(
            {
                "position": pos,
                "roster_a": a_val,
                "roster_b": b_val,
                "diff": round(a_val - b_val, 2),
            }
        )

    return breakdown
