"""
=============================================================
 File: deps.py
 Author: Tai Sewell
 Description:
     Shared router dependencies for resolving the active
     league id from request headers with env fallback.
=============================================================
"""

from __future__ import annotations

from typing import Optional

from fastapi import Header

from backend.app.services.league_context import resolve_league_id


def get_request_league_id(
    x_league_id: Optional[str] = Header(None, alias="X-League-Id"),
) -> str:
    """
    Resolve the league id from request headers or environment.
    """
    resolved_league_id = resolve_league_id(x_league_id)
    return resolved_league_id
