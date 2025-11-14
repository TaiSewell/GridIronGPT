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

import os
import typing as t
import httpx
import json

#SLEEPER_BASE = os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1")

class SleeperClient:
    def __init__(self, base_url = os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1")):
        self.base_url = base_url

    def get_json(self, path: str) -> t.Any:
        """
        Build the full URL, send a GET request using httpx,
        and return the parsed JSON.
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        
        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()  # raises HTTPError if 4xx or 5xx
            return response.json()       # no need to decode manually
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc


    def get_league(self, league_id: str) -> dict:
        """
        Try to fetch league metadata. If successful, return league
        name + season + status. If failed, return an error message.
        """
        try:
            data = self.get_json(f"/league/{league_id}")
            return {
                "ok": True,
                "name": data.get("name"),
                "season": data.get("season"),
                "status": data.get("status"),
                "scoring_settings": data.get("scoring_settings")
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def get_rosters(self, league_id):
        try:
            data = self.get_json(f"/league/{league_id}/rosters")
            return {
                "ok": True,
                "league_id": data.get("league_id"),
                "roster_id": data.get("roster_id"),
                "owner_id": data.get("owner_id"),
                "starters_json": data.get("starters_json"),
                "bench_json": data.get("bench_json")
            }
        except Exception as err:
            return {
                "Retrieved": False,
                "Error": str(err)
            }

        