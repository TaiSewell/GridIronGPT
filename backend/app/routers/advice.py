"""
=============================================================
 File: advice.py
 Author: Tai Sewell
 Description:
     AI endpoints that generate roster comparison summaries.
=============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.ai.roster_compare import compare_rosters_service
from backend.app.ai.start_sit import build_start_sit_recommendations_service
from backend.app.ai.fantasy_leaders import build_fantasy_leaders_service
from backend.app.ai.league_summary import build_league_summary_service
from backend.app.ai.roster_insights import build_roster_insights_service

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


class FantasyLeadersRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    season: Optional[int] = None
    week: Optional[int] = Field(default=None, ge=1, le=18)


class FantasyLeadersResponse(BaseModel):
    season: int
    week: int
    limit: int
    summary: str
    details: str
    leaders: List[Dict[str, Any]]


class LeagueSummaryRequest(BaseModel):
    season: Optional[int] = None
    week: Optional[int] = Field(default=None, ge=1, le=18)


class LeagueSummaryResponse(BaseModel):
    season: int
    week: int
    summary: str
    details: str
    rosters: List[Dict[str, Any]]


class RosterInsightsRequest(BaseModel):
    user_a: str
    season: Optional[int] = None
    week: Optional[int] = None


class RosterInsightsResponse(BaseModel):
    season: int
    week: int
    summary: str
    details: str
    roster: Dict[str, Any]
    players: Dict[str, Any]


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


@router.post("/fantasy-leaders", response_model=FantasyLeadersResponse)
def fantasy_leaders(request: FantasyLeadersRequest):
    try:
        return build_fantasy_leaders_service(
            limit=request.limit,
            season=request.season,
            week=request.week,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/league-summary", response_model=LeagueSummaryResponse)
def league_summary(request: LeagueSummaryRequest):
    try:
        return build_league_summary_service(
            season=request.season,
            week=request.week,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/roster-insights", response_model=RosterInsightsResponse)
def roster_insights(request: RosterInsightsRequest):
    try:
        return build_roster_insights_service(
            user_a=request.user_a,
            season=request.season,
            week=request.week,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
