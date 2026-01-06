"""
=============================================================
 File: health.py
 Author: Tai Sewell
 Description:
     Provides the /health endpoint for verifying backend
     status and connectivity. Confirms the API is online
     and environment variables are loaded correctly.
=============================================================
"""

from fastapi import APIRouter
from backend.app.config import settings, HealthInfo

router = APIRouter(tags=["health"])

@router.get("/")
def root():
    return {"Welcome": "To GridIronGPT"}

@router.get("/health", response_model=HealthInfo)
def health():
    return HealthInfo(status="ok", backend_port=settings.BACKEND_PORT)
