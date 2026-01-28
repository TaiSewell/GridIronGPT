"""
=============================================================
 File: users.py
 Author: Tai Sewell
 Description:
     Endpoints for league users cached from Sleeper.
=============================================================
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.app.services import users_service as usvc
from backend.app.routers.deps import get_request_league_id


class User(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    team_name: Optional[str] = None
    metadata_json: Optional[str] = None


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[User])
def list_users(league_id: str = Depends(get_request_league_id)):
    try:
        return usvc.list_users_service(league_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/lookup", response_model=List[User])
def lookup_user(
    user_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    league_id: str = Depends(get_request_league_id),
):
    if bool(user_id) == bool(name):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of user_id or name.",
        )

    try:
        if user_id:
            user = usvc.get_user_by_id_service(user_id, league_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return [user]

        return usvc.search_users_by_name_service(name or "", league_id)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
