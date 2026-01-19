"""
=============================================================
 File: admin.py
 Author: Tai Sewell
 Description:
     Admin endpoints for managing runtime configuration,
     including active league switching.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.admin_service import switch_active_league_service

router = APIRouter(prefix="/admin", tags=["admin"])


class SwitchLeagueRequest(BaseModel):
    league_id: str


class SwitchLeagueResponse(BaseModel):
    league_id: str
    season: Optional[int]
    status: str


@router.post("/league", response_model=SwitchLeagueResponse)
def switch_league(request: SwitchLeagueRequest):
    try:
        return switch_active_league_service(request.league_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
