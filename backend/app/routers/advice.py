"""
=============================================================
 File: advice.py
 Author: Tai Sewell
 Description:
     AI endpoints that generate roster comparison summaries.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.ai.roster_compare import compare_rosters_service

router = APIRouter(prefix="/ai", tags=["ai"])


class CompareRostersRequest(BaseModel):
    user_a: str
    user_b: str
    week: int
    season: Optional[int] = None
    include_bench: bool = False


class CompareRostersResponse(BaseModel):
    summary: str
    data: Dict[str, Any]


@router.post("/compare-rosters", response_model=CompareRostersResponse)
def compare_rosters(request: CompareRostersRequest):
    try:
        return compare_rosters_service(
            user_a=request.user_a,
            user_b=request.user_b,
            week=request.week,
            season=request.season,
            include_bench=request.include_bench,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
