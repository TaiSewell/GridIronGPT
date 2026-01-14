"""
=============================================================
 File: sleeper_client.py
 Author: Tai Sewell
 Description:
     Handles all API requests to the Sleeper API. Fetches
     league, roster, matchup, and player data which are
     cached locally in SQLite for performance and reliability.
=============================================================
"""
from dotenv import load_dotenv
load_dotenv()
import os
import typing as t
import httpx
import json


class DataClient:
    """
    Minimal raw fetcher for external APIs.
    - Sleeper: public, no auth.
    - SportsDataIO: requires Ocp-Apim-Subscription-Key.
    """

    def __init__(self, sleeper_base_url: str | None = None, sportsdata_base_url: str | None = None, sportsdata_key: str | None = None, timeout: float = 10.0) -> None:
        self.sleeper_base_url = (sleeper_base_url or os.getenv("SLEEPER_BASE") or "https://api.sleeper.app/v1").rstrip("/")
        self.sportsdata_base_url = (sportsdata_base_url or os.getenv("SPORTS_DATA_BASE") or "https://api.sportsdata.io/v3/nfl").rstrip("/")
        self.sportsdata_key = sportsdata_key or os.getenv("SPORTS_DATA_KEY") or ""
        self._client = httpx.Client(timeout=timeout)

    # -----------------------------
    # Low-level HTTP helpers
    # -----------------------------
    def _get(self, url: str, headers=None, params=None):
        try:
            r = httpx.get(url, headers=headers, params=params, timeout=20.0)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"GET {url} failed: {exc}") from exc

    def sleeper_get_json(self, path: str, params: dict[str, t.Any] | None = None) -> json:
        """
        Raw GET to Sleeper. `path` may be '/league/123' or 'league/123'.
        """
        url = f"{self.sleeper_base_url}/{path.lstrip('/')}"
        return self._get(url, params=params)

    def sportsdata_get_json(self, path: str, params: dict[str, t.Any] | None = None) -> json:
        if not self.sportsdata_key:
            raise RuntimeError("SPORTS_DATA_KEY is missing/empty. Check .env loading.")

        if path.startswith(("http://", "https://")):
            url = path
        else:
            url = f"{self.sportsdata_base_url}/{path.lstrip('/')}"

        # Always add key as query param
        params = dict(params or {})
        params["key"] = self.sportsdata_key

        # Also send header (docs-supported)
        headers = {"Ocp-Apim-Subscription-Key": self.sportsdata_key}

        return self._get(url, headers=headers, params=params)
    # -----------------------------
    # Sleeper Endpoints (raw)
    # -----------------------------
    def get_league(self, league_id: str) -> json:
        return self.sleeper_get_json(f"/league/{league_id}")
    
    def get_users(self, league_id: str) -> json:
        return self.sleeper_get_json(f"/league/{league_id}/users")
    
    def get_rosters(self, league_id: str) -> json:
        return self.sleeper_get_json(f"/league/{league_id}/rosters")
    
    def get_matchups(self, league_id: str, week: int) -> json:
        return self.sleeper_get_json(f"/league/{league_id}/matchups/{week}")
    
    def get_all_players(self) -> json:
        return self.sleeper_get_json("/players/nfl")
    
    # -----------------------------
    # SportsDataIO endpoints (raw)
    # -----------------------------
    @staticmethod
    def season_key(year: int) -> str:
        return f"{year}REG"
    
    def get_weekly_offensive_projections(self, year: int, week: int) -> json:
        season_key = self.season_key(year)
        path = f"projections/json/PlayerGameProjectionStatsByWeek/{season_key}/{week}"
        return self.sportsdata_get_json(path)
    
    def get_schedule(self, year: int, week: int) -> json:
        season_key = self.season_key(year)
        path = f"scores/json/ScoresByWeekFinal/{season_key}/{week}"
        return self.sportsdata_get_json(path)

    def get_weekly_fantasy_stats(self, year: int, week: int) -> json:
        season_key = self.season_key(year)
        path = f"stats/json/FantasyGameStatsByWeek/{season_key}/{week}"
        return self.sportsdata_get_json(path)
    
    def get_weekly_defensive_projections(self, year: int, week: int) -> json:
        season_key = self.season_key(year)
        path = f"projections/json/FantasyDefenseProjectionsByGame/{season_key}/{week}"
        return self.sportsdata_get_json(path)

    def get_weekly_defense_fantasy_by_game(self, year: int, week: int) -> json:
        season_key = self.season_key(year)
        path = f"stats/json/FantasyDefenseByGame/{season_key}/{week}"
        return self.sportsdata_get_json(path)
