"""
=============================================================
 File: rosters.py
 Author: Tai Sewell
 Description:
     Endpoints for roster data stored in the SQLite cache.
=============================================================
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.services import rosters_service as rsvc


class RosterUpsertItem(BaseModel):
    league_id: str
    roster_id: int
    owner_id: Optional[str] = None
    starters_json: Optional[str] = None
    bench_json: Optional[str] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    ties: Optional[int] = None
    waiver_position: Optional[int] = None
    total_moves: Optional[int] = None
    fpts: Optional[float] = None
    fpts_against: Optional[float] = None


class RosterUpsertRequest(BaseModel):
    rosters: List[RosterUpsertItem]


class RosterUpsertResponse(BaseModel):
    upserted: int


class Roster(BaseModel):
    league_id: str
    roster_id: int
    owner_id: Optional[str] = None
    starters_json: Optional[str] = None
    bench_json: Optional[str] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    ties: Optional[int] = None
    waiver_position: Optional[int] = None
    total_moves: Optional[int] = None
    fpts: Optional[float] = None
    fpts_against: Optional[float] = None


router = APIRouter(prefix="/rosters", tags=["rosters"])

@router.get("/league", response_model=List[Roster])
def list_rosters():
    try:
        return rsvc.list_rosters_service()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/owner", response_model=Roster)
def get_roster_by_owner(username: str = Query(..., min_length=1)):
    try:
        roster = rsvc.get_roster_by_owner_service(username=username)
        if not roster:
            raise HTTPException(status_code=404, detail="Roster not found")
        return roster
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
