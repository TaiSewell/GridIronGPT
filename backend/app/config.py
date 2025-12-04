"""
=============================================================
 File: config.py
 Author: Tai Sewell
 Description:
     Centralized configuration management for the backend.
     Loads environment variables and defines global settings
     like database paths, allowed origins, and API keys.
=============================================================
"""

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    DB_PATH: str = "./data/gridiron.db"
    SLEEPER_BASE: str = "https://api.sleeper.app/v1"
    SLEEPER_LEAGUE_ID: str | None = None

    OPENAI_API_KEY: str | None = None

settings = Settings()

# simple DTO for health
class HealthInfo(BaseModel):
    status: str