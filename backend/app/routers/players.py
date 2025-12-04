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
from fastapi import APIRouter
from pydantic import BaseModel

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
    return {
        "player_info": Player
    }