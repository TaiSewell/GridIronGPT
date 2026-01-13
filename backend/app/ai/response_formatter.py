"""
=============================================================
 File: response_formatter.py
 Author: Tai Sewell
 Description:
     Normalizes AI responses into a consistent payload.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def format_roster_compare_response(
    summary: str,
    reasoning: Optional[str],
    recommendation: Optional[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    response = {
        "summary": summary,
        "reasoning": reasoning,
        "recommendation": recommendation,
        "data": payload,
    }
    return response
