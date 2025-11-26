"""
=============================================================
 File: main.py
 Author: Tai Sewell
 Description:
     Initializes the FastAPI application, configures CORS,
     and registers all routers (health, players, rosters, AI).
     Serves as the entry point for the backend server.
=============================================================
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health
from data.cache_manager import CacheManager
from data.data_client import DataClient
from backend.app.services.scoring_service import compute_weekly_projected_points

app = FastAPI(title="GridironGPT API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)