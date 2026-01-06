"""
=============================================================
 File: response_formatter.py
 Author: Tai Sewell
 Description:
     Normalizes AI responses into a consistent payload.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict


def format_roster_compare_response(summary: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": summary,
        "data": payload,
    }
