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
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import player_service as psvc
from typing import Optional, List

class Player(BaseModel):
    player_id: int
    player_name: str
    team: str
    position: str
    status: str

router = APIRouter(tags=["players"])

# Retrieve certain player
@router.get("/players/{player_id}", response_model=Player)
def getPlayer(player_id: int):
    player = psvc.get_player_by_id_service(player_id)
    if not player:
        raise HTTPException(status_code=404, detail= "Player Not Found")
    return player

@router.get("")
def list_players(week: Optional[int] = None, position: Optional[str] = None, name: Optional[str] = None, limit: Optional[int] = 50):
    if name:
        return psvc.search_player_by_name_service(name, limit)
    if week is not None:
        return psvc.get_weekly_player_projections_service(week, position, limit)
    return []
