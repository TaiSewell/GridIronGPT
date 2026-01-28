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
from backend.db import get_conn


def resolve_league_id(league_id: Optional[str]) -> str:
    """
    Resolve a league id with environment fallback when missing.
    """
    cleaned_league_id = (league_id or "").strip()
    resolved_league_id = cleaned_league_id or settings.SLEEPER_LEAGUE_ID
    if not resolved_league_id:
        raise ValueError("SLEEPER_LEAGUE_ID is required in the environment.")
    return resolved_league_id


def get_active_league_id() -> str:
    """
    Resolve the default league id from the environment configuration.
    """
    resolved_league_id = resolve_league_id(None)
    return resolved_league_id


def set_active_league_id(league_id: str) -> None:
    """
    Persist the active league id for runtime switching.
    """
    cleaned_league_id = league_id.strip()
    if not cleaned_league_id:
        raise ValueError("league_id cannot be empty.")
    _ensure_meta_table()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO meta (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            ("active_league_id", cleaned_league_id),
        )
        conn.commit()


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
