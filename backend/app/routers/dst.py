"""
=============================================================
dst.py
Author: Tai Sewell

Endpoints for DST projections and actual points.
=============================================================
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.services import dst_service as dsvc


class DSTWeeklyPoints(BaseModel):
    player_id: str
    dst_team: str
    season: int
    week: int
    projected_points: Optional[float] = None
    actual_points: Optional[float] = None


class DSTSeasonRank(BaseModel):
    season: int
    dst_rank: int
    dst_team: str
    total_points: float


router = APIRouter(prefix="/dst", tags=["dst"])


@router.get("/weekly", response_model=List[DSTWeeklyPoints])
def list_dst_weekly(
    week: int = Query(..., ge=1, le=18),
    season: Optional[int] = None,
    team: Optional[str] = None,
    limit: int = Query(32, ge=1, le=64),
    offset: int = Query(0, ge=0),
):
    try:
        return dsvc.list_dst_weekly_points_service(
            week=week,
            season=season,
            team=team,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/season-ranks", response_model=List[DSTSeasonRank])
def list_dst_season_ranks(
    season: Optional[int] = None,
    limit: int = Query(32, ge=1, le=64),
    offset: int = Query(0, ge=0),
):
    try:
        return dsvc.list_dst_season_actual_ranks_service(
            season=season,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
