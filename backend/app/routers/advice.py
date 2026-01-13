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
from backend.app.ai.start_sit import build_start_sit_recommendations_service

router = APIRouter(prefix="/ai", tags=["ai"])


class CompareRostersRequest(BaseModel):
    user_a: str
    user_b: str
    week: int
    season: Optional[int] = None
    include_bench: bool = False


class CompareRostersResponse(BaseModel):
    summary: str
    reasoning: str
    recommendation: str
    data: Dict[str, Any]


class StartSitRequest(BaseModel):
    user_a: str
    week: int
    season: Optional[int] = None


class StartSitResponse(BaseModel):
    week: int
    season: Optional[int]
    recommendation: str
    reasoning: str
    start_sit: Dict[str, Any]


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


@router.post("/start-sit", response_model=StartSitResponse)
def start_sit(request: StartSitRequest):
    try:
        return build_start_sit_recommendations_service(
            user_a=request.user_a,
            week=request.week,
            season=request.season,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
