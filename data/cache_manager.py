"""
=============================================================
 File: cache_manager.py
 Author: Tai Sewell
 Description:
     Handles cache validation and time-to-live (TTL) logic
     for locally stored Sleeper API data. Determines when
     player, roster, or matchup data should be refreshed.
=============================================================
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from data.db import get_conn
import data.sync as sync
from data.data_client import DataClient

class CacheManager:
    """
    High-level cache controller.

    Usage:
        cache = CacheManager(league_id="1234567890")
        cache.ensure_league_bundle_cached(week=10)
        cache.ensure_players_cached()
    """
    DEFAULT_TTL_SECONDS = 60        # 5 minutes for dynamic stuff (matchups, rosters)
    PLAYER_TTL_SECONDS = 24 * 3600  # 24 hours for mostly-static player metadata

    def __init__(self, league_id: str, client: DataClient | None = None, default_ttl_seconds: int = DEFAULT_TTL_SECONDS, player_ttl_seconds: int = PLAYER_TTL_SECONDS) -> None:
        self.league_id = league_id
        self.client = client or DataClient()
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.players_ttl = timedelta(seconds=player_ttl_seconds)
        self._ensure_meta_table()

    # ---------- Public API ----------
    def build_key(self, kind: str, week: int | None = None) -> str:
        """
        Build a unique cache key for the meta table.

        Examples:
        _build_key("league_bundle", None)          -> "league_bundle:league:<league_id>"
        _build_key("league_bundle", 10)            -> "league_bundle:league:<league_id>:week:10"
        _build_key("matchups", 8)                  -> "matchups:league:<league_id>:week:8"
        _build_key("players", None)                -> "players:all"
        """
        if kind == "players" and week is None:
            return "players:all"

        if week is not None:
            return f"{kind}:league:{self.league_id}:week:{week}"

        return f"{kind}:league:{self.league_id}"

    def ensure_league_bundle_cached(self, week: Optional[int] = None, force_refresh: bool = False) -> None:
        """
        Ensure that league + users + rosters (+ optionally matchups) for a given week
        are fresh in the SQLite cache.
        """
        cache_key = self._build_key("league_bundle", week)

        if not force_refresh and not self._is_stale(cache_key, self.default_ttl):
            return None

        sync.sync_league(self.client, self.league_id)

        if week is not None:
            sync.sync_matchups(self.client, self.league_id, week)

        self._touch(cache_key)

    def ensure_players_cached(self, force_refresh: bool = False) -> None:
        """
        Ensure that the global player list is cached and up to date.
        Players change slowly, so we give them a longer TTL.
        """
        cache_key = "players:all"

        if not force_refresh and not self._is_stale(cache_key, self.players_ttl):
            return

        sync.sync_players(self.client)

        self._touch(cache_key)

    def ensure_matchups_cached(self, week: int, force_refresh: bool = False) -> None:
        """
        Make sure matchups for a specific week are cached.
        """
        cache_key = self._build_key("matchups", week)

        if not force_refresh and not self._is_stale(cache_key, self.default_ttl):
            return

        sync.sync_matchups(self.client, self.league_id, week)

        self._touch(cache_key)

    def ensure_weekly_projections_cached(
        self,
        season: int,
        week: int,
        force_refresh: bool = False,
    ) -> None:
        """
        Ensure SportsDataIO weekly projections are cached for a given season+week.
        """
        cache_key = f"weekly_projections:season:{season}:week:{week}"

        if not force_refresh and not self._is_stale(cache_key, self.default_ttl):
            return

        sync.sync_weekly_projections(self.client, season, week)

        self._touch(cache_key)

    # ───────── Meta / cache helpers using `meta` table ─────────

    def ensure_meta_table(self) -> None:
        """
        Make sure the meta table exists.

        This table is used as a simple key/value store with a timestamp
        so we can track when each cache segment was last refreshed.
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

    def get_last_synced(self, cache_key: str) -> Optional[datetime]:
        """
        Look up the last time this cache_key was updated in the meta table.
        Returns a datetime or None if there's no record.
        """
        with get_conn() as conn:
            row = conn.execute(
                "SELECT updated_at FROM meta WHERE key = ?",
                (cache_key,),
            ).fetchone()

        if not row or not row[0]:
            return None

        ts = row[0]

        # SQLite's CURRENT_TIMESTAMP is "YYYY-MM-DD HH:MM:SS"
        # datetime.fromisoformat can handle the space separator.
        try:
                # Parse naive datetime
            dt = datetime.fromisoformat(ts)
            # Make it timezone-aware in UTC
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    def is_stale(self, cache_key: str, ttl: timedelta) -> bool:
        last = self._get_last_synced(cache_key)
        if last is None:
            return True
        
        now = datetime.now(timezone.utc)
        return (now - last) > ttl

    def touch(self, cache_key: str, value: str | None = None) -> None:
        """
        Update the meta row for this cache_key to 'now'.

        `value` is optional and can be used later to store extra JSON, counts, etc.
        For now, we mostly care about updated_at.
        """
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO meta (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key)
                DO UPDATE SET
                    value = COALESCE(excluded.value, meta.value),
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (cache_key, value),
            )
            conn.commit()