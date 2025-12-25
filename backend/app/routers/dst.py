"""
dst.py

Endpoints for DST projections and actual points.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.services import dst_service as dsvc


class DSTProjection(BaseModel):
    player_id: str
    dst_team: str
    season: int
    week: int
    league_id: str
    projected_points: float


router = APIRouter(prefix="/dst", tags=["dst"])


@router.get("/projections", response_model=List[DSTProjection])
def list_dst_projections(
    week: int = Query(..., ge=1, le=18),
    season: Optional[int] = None,
    league_id: Optional[str] = None,
    team: Optional[str] = None,
    limit: int = Query(32, ge=1, le=64),
    offset: int = Query(0, ge=0),
):
    try:
        return dsvc.list_dst_weekly_projections_service(
            week=week,
            season=season,
            league_id=league_id,
            team=team,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Helpful for MVP debugging (you can remove later)
        raise HTTPException(status_code=500, detail=str(e))
