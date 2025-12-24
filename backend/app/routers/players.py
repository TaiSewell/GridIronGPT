"""
=============================================================
 File: players.py
 Author: Tai Sewell
 Description:
     Exposes endpoints for accessing player data from the
     SQLite cache. Supports filters by team, position, and
     player name. Used by frontend search and AI layer.
=============================================================
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from backend.app.services import player_service as psvc

class Player(BaseModel):
    player_id: str
    player_name: str
    team: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search", response_model=List[Player])
def search_players(
    name: str = Query(..., min_length=1),
    limit: int = Query(25, ge=1, le=100),
):
    return psvc.search_player_by_name_service(name, limit)

@router.get("/{player_id}", response_model=Player)
def get_player(player_id: str):
    player = psvc.get_player_by_id_service(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.get("", response_model=List[Player])
def list_players(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return psvc.list_players_service(limit=limit, offset=offset)

@router.get("/search/projection")
def search_player_projections(
    name: str = Query(..., min_length=1),
    week: int = Query(..., ge=1, le=18),
    limit: int = Query(25, ge=1, le=100),
    season: Optional[int] = None,
    league_id: Optional[str] = None,
):
    try:
        return psvc.search_player_projections_service(
            name=name,
            week=week,
            limit=limit,
            season=season,
            league_id=league_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Helpful for MVP debugging (you can remove later)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}/projection")
def get_player_projection(
    player_id: str,
    week: int = Query(..., ge=1, le=18),
    season: Optional[int] = None,
    league_id: Optional[str] = None,
):
    data = psvc.get_player_with_weekly_projection_service(
        player_id=player_id,
        week=week,
        season=season,
        league_id=league_id,
    )
    if not data:
        raise HTTPException(status_code=404, detail="Player not found")
    return data