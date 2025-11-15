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


class DataClient:
    def __init__(self, sleeper_base_url = os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1"), sportsdata_base_url = os.getenv("SPORTS_DATA_BASE", "https://api.sportsdata.io/v3/nfl/projections/json")):
        self.sleeper_base_url = sleeper_base_url
        self.sportsdata_base_url = sportsdata_base_url

    def sleeper_get_json(self, path: str) -> t.Any:
        """
        Build the full URL, send a GET request using httpx,
        and return the parsed JSON.
        """
        url = f"{self.sleeper_base_url.rstrip('/')}/{path.lstrip('/')}"
        
        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()  # raises HTTPError if 4xx or 5xx
            return response.json()       # no need to decode manually
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc
    
    def sportsdata_get_json(self, path: str) -> t.Any:

        url = f"({self.sportsdata_base_url.rstrip('/')}/{path.lstrip('/')})"

        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
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
    
    def get_players(self):
        try:
            data = self.get_json(f"players/nfl")
            return {
                "ok": True,
                "player_id": data.get("player_id"),
                "player_name": data.get("player_name"),
                "team": data.get("team"),
                "position": data.get("pos"),
                "status": data.get("status")
            }
        except Exception as e:
            return {
                "Retrieved": False,
                "Error": str(e)
            }
    
    def get_weekly_player_stats(self, year: int, week: int):
        try:
            season = f"{year}REG"
            key = os.getenv("SPORTS_DATA_KEY")
            headers = {
                "Ocp-Apim-Subscription-Key": key
            }

            data = self.sportsdata_get_json(
                f"/IdpPlayerGameProjectionStatsByWeek/{season}/{week}",
                headers=headers
            )

            return {
                "Retrieved": True,
                "player_id": data.get("player_id"),
                "season": data.get("season"),
                "week": data.get("week"),

            }

        except Exception as e:
            return {

            }