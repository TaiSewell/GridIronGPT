"""
=============================================================
 File: prompt_builder.py
 Author: Tai Sewell
 Description:
     Builds prompt messages for AI comparisons.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_roster_compare_messages(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    system = (
        "You are a fantasy football analyst. "
        "Summarize roster comparisons clearly, focusing on projected points and positional edges. "
        "Be concise and avoid listing every player unless necessary. "
        "Respond in JSON with keys: summary, reasoning, recommendation."
    )

    user = (
        "Compare the two rosters for this week using the data below. "
        "Return JSON only. "
        "summary: 1-2 sentences with overall edge. "
        "reasoning: 1-2 sentences citing 2-3 positional projection edges. "
        "recommendation: 1 sentence with a lineup suggestion based on projection gaps. "
        "If projections are close, say so.\n\n"
        f"{payload}"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
