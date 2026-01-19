"""
=============================================================
 File: league_context.py
 Author: Tai Sewell
 Description:
     Provides helpers to resolve and persist the active
     league id for runtime switching without restarts.
=============================================================
"""

from __future__ import annotations

from typing import Optional

from backend.app.config import settings
from backend.db import get_conn, get_meta, set_meta


def get_active_league_id() -> str:
    """
    Resolve the active league id from the meta table, falling back
    to the environment configuration if no override is set.
    """
    _ensure_meta_table()
    active_league_id = get_meta("active_league_id")
    resolved_league_id = active_league_id or settings.SLEEPER_LEAGUE_ID
    if not resolved_league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")
    return resolved_league_id


def set_active_league_id(league_id: str) -> None:
    """
    Persist the active league id for runtime switching.
    """
    cleaned_league_id = league_id.strip()
    if not cleaned_league_id:
        raise ValueError("league_id cannot be empty.")
    _ensure_meta_table()
    set_meta("active_league_id", cleaned_league_id)


def _ensure_meta_table() -> None:
    """
    Ensure the meta table exists for storing runtime settings.
    """
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key        TEXT PRIMARY KEY,
                value      TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
