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
import urllib.request
import json

SLEEPER_BASE = os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1")

def _get_json(path: str) -> t.Any:
    url = f"{SLEEPER_BASE.rstrip('/')}/{path.lstrip('/')}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))

# phase 1 will fill real methods; this is just a smoke test
def ping_league(league_id: str) -> dict:
    try:
        data = _get_json(f"league/{league_id}")
        return {"ok": True, "name": data.get("name"), "season": data.get("season")}
    except Exception as e:
        return {"ok": False, "error": str(e)}