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
import logging
import os
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routers import advice, health, players, rosters, dst, users

logger = logging.getLogger(__name__)

app = FastAPI(title="GridironGPT API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(advice.router)
app.include_router(players.router)
app.include_router(dst.router)
app.include_router(rosters.router)
app.include_router(users.router)

