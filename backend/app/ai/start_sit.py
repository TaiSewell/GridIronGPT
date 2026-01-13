"""
=============================================================
 File: start_sit.py
 Author: Tai Sewell
 Description:
     Builds start/sit recommendations for a roster based on
     weekly projections.
=============================================================
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.app.services import player_service, rosters_service


def build_start_sit_recommendations_service(
    user_a: str,
    week: int,
    season: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build start/sit recommendations for a single roster.
    """
    roster = rosters_service.get_roster_by_owner_service(user_a)
    if not roster:
        raise ValueError(f"Roster not found for '{user_a}'.")

    roster_players = _extract_all_players(roster)
    projections = player_service.get_player_weekly_projections_by_ids_service(
        player_ids=roster_players,
        week=week,
        season=season,
    )
    projection_map = {p["player_id"]: p for p in projections}

    start_sit = _build_start_sit_recommendations(
        roster=roster,
        projection_map=projection_map,
    )
    recommendation_text = _format_start_sit_recommendation(start_sit)
    reasoning_text = _format_start_sit_reasoning(start_sit)

    response = {
        "week": week,
        "season": season,
        "recommendation": recommendation_text,
        "reasoning": reasoning_text,
        "start_sit": start_sit,
    }
    return response


def _extract_all_players(roster: Optional[Dict[str, Any]]) -> List[str]:
    """
    Extract all starter and bench player ids from a roster.
    """
    players: List[str] = []
    starters: List[Any] = []
    bench: List[Any] = []

    if roster is not None:
        starters = _safe_json_list(roster.get("starters_json"))
        bench = _safe_json_list(roster.get("bench_json"))

    for player_id in starters + bench:
        if player_id:
            players.append(str(player_id))

    return players


def _build_start_sit_recommendations(
    roster: Dict[str, Any],
    projection_map: Dict[str, Dict[str, Any]],
    max_swaps: int = 3,
    min_edge: float = 0.5,
) -> Dict[str, Any]:
    """
    Identify bench players projected to outscore starters at the same position.
    """
    starter_ids = _safe_json_list(roster.get("starters_json"))
    bench_ids = _safe_json_list(roster.get("bench_json"))

    starter_entries = _build_player_entries(starter_ids, projection_map)
    bench_entries = _build_player_entries(bench_ids, projection_map)

    starters_by_position: Dict[str, List[Dict[str, Any]]] = {}
    for entry in starter_entries:
        position = entry["position"] or "UNK"
        starters_by_position.setdefault(position, []).append(entry)

    for position, starters in starters_by_position.items():
        starters_by_position[position] = sorted(
            starters,
            key=lambda player: float(player.get("final_projection") or 0.0),
        )

    flex_positions = {"RB", "WR", "TE"}
    flex_starters = [
        starter
        for position in flex_positions
        for starter in starters_by_position.get(position, [])
    ]
    flex_starters_sorted = sorted(
        flex_starters,
        key=lambda player: float(player.get("final_projection") or 0.0),
    )

    swap_candidates: List[Dict[str, Any]] = []
    for bench_entry in bench_entries:
        bench_position = bench_entry["position"] or "UNK"
        bench_projection = float(bench_entry.get("final_projection") or 0.0)
        starter_pool = starters_by_position.get(bench_position, [])
        swap_target = starter_pool[0] if starter_pool else None
        slot_label = bench_position

        if swap_target is None and bench_position in flex_positions:
            swap_target = flex_starters_sorted[0] if flex_starters_sorted else None
            slot_label = "FLEX"

        if swap_target:
            starter_projection = float(swap_target.get("final_projection") or 0.0)
            diff = round(bench_projection - starter_projection, 2)
            if diff >= min_edge:
                swap_candidates.append(
                    {
                        "slot": slot_label,
                        "diff": diff,
                        "start": bench_entry,
                        "sit": swap_target,
                    }
                )

    swap_candidates_sorted = sorted(
        swap_candidates,
        key=lambda entry: float(entry.get("diff") or 0.0),
        reverse=True,
    )
    swap_candidates_sorted = swap_candidates_sorted[:max_swaps]

    start_list = [swap["start"] for swap in swap_candidates_sorted]
    sit_list = [swap["sit"] for swap in swap_candidates_sorted]

    result = {
        "roster_id": roster.get("roster_id"),
        "owner_id": roster.get("owner_id"),
        "start": start_list,
        "sit": sit_list,
        "swaps": swap_candidates_sorted,
    }
    return result


def _build_player_entries(
    player_ids: List[Any],
    projection_map: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build projection entries for a list of player ids.
    """
    entries: List[Dict[str, Any]] = []
    for player_id in player_ids:
        player_key = str(player_id)
        projection = projection_map.get(player_key)
        if not projection:
            continue
        entries.append(
            {
                "player_id": player_key,
                "player_name": projection.get("player_name"),
                "position": projection.get("position"),
                "final_projection": projection.get("final_projection"),
            }
        )
    return entries


def _safe_json_list(value: Optional[str]) -> List[Any]:
    """
    Return a list from JSON if possible; otherwise return empty list.
    """
    result: List[Any] = []
    parsed: List[Any] | Any = []

    if value:
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            parsed = []

    if isinstance(parsed, list):
        result = parsed

    return result


def _format_start_sit_recommendation(start_sit: Dict[str, Any]) -> str:
    """
    Build a short recommendation line from swaps.
    """
    swaps = start_sit.get("swaps") or []
    text = "Recommendation: keep your current starters."
    if swaps:
        swap = swaps[0]
        start_player = swap.get("start") or {}
        sit_player = swap.get("sit") or {}
        start_name = start_player.get("player_name") or start_player.get("player_id")
        sit_name = sit_player.get("player_name") or sit_player.get("player_id")
        diff = swap.get("diff")
        text = f"Recommendation: start {start_name} over {sit_name} (+{diff})."
    return text


def _format_start_sit_reasoning(start_sit: Dict[str, Any]) -> str:
    """
    Build a concise reasoning line for the recommendation.
    """
    swaps = start_sit.get("swaps") or []
    text = "Reasoning: projections do not show a clear upgrade from your bench."
    if swaps:
        swap = swaps[0]
        start_player = swap.get("start") or {}
        sit_player = swap.get("sit") or {}
        start_name = start_player.get("player_name") or start_player.get("player_id")
        sit_name = sit_player.get("player_name") or sit_player.get("player_id")
        position = start_player.get("position") or "UNK"
        start_proj = float(start_player.get("final_projection") or 0.0)
        sit_proj = float(sit_player.get("final_projection") or 0.0)
        diff = swap.get("diff")
        text = (
            f"Reasoning: {start_name} ({start_proj:.2f}) projects higher than "
            f"{sit_name} ({sit_proj:.2f}) at {position} by {diff} points."
        )
    return text
