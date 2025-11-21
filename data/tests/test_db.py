"""
Pytest-style tests for sync functionality.

These tests exercise `data.sync` using a temporary SQLite file and a
fake `DataClient` implementation. They reload the `data.db` and
`data.sync` modules after setting `DB_PATH` so the modules use the
temporary database.
"""
import os
import importlib
import json

class FakeDataClient:
    """
    Fake implementation of DataClient for tests.

    Matches the public interface of sleeper_client.DataClient
    but returns static, in-memory data instead of hitting real APIs.
    """

    # -----------------------------
    # Sleeper-like fake data
    # -----------------------------
    def get_league(self, league_id: str):
        return {
            "league_id": league_id,
            "name": "Test Gridiron League",
            "season": "2025",
            "status": "in_season",
            "total_rosters": 2,
        }

    def get_users(self, league_id: str):
        return [
            {
                "user_id": "user_1",
                "display_name": "Tai",
                "avatar": None,
                "metadata": {},
            },
            {
                "user_id": "user_2",
                "display_name": "Opponent",
                "avatar": None,
                "metadata": {},
            },
        ]

    def get_rosters(self, league_id: str):
        # Minimal shape similar to Sleeper rosters
        return [
            {
                "roster_id": 1,
                "league_id": league_id,
                "owner_id": "user_1",
                "players": ["player_josh_allen", "player_jamarr_chase"],
            },
            {
                "roster_id": 2,
                "league_id": league_id,
                "owner_id": "user_2",
                "players": ["player_justin_jefferson"],
            },
        ]

    def get_matchups(self, league_id: str, week: int):
        # Very simplified matchup structure – tweak to whatever sync_matchups expects
        return [
            {
                "matchup_id": 1,
                "roster_id": 1,
                "points": 120.5,
                "players": ["player_josh_allen", "player_jamarr_chase"],
                "week": week,
            },
            {
                "matchup_id": 1,
                "roster_id": 2,
                "points": 110.3,
                "players": ["player_justin_jefferson"],
                "week": week,
            },
        ]

    def get_all_players(self):
        # Dict keyed by player_id, similar to Sleeper /players/nfl
        return {
            "player_josh_allen": {
                "player_id": "player_josh_allen",
                "first_name": "Josh",
                "last_name": "Allen",
                "full_name": "Josh Allen",
                "position": "QB",
                "team": "BUF",
            },
            "player_jamarr_chase": {
                "player_id": "player_jamarr_chase",
                "first_name": "Ja'Marr",
                "last_name": "Chase",
                "full_name": "Ja'Marr Chase",
                "position": "WR",
                "team": "CIN",
            },
            "player_justin_jefferson": {
                "player_id": "player_justin_jefferson",
                "first_name": "Justin",
                "last_name": "Jefferson",
                "full_name": "Justin Jefferson",
                "position": "WR",
                "team": "MIN",
            },
        }

    # -----------------------------
    # SportsDataIO-like fake data
    # -----------------------------
    def get_weekly_offensive_projections(self, year: int, week: int):
        # Returns a list of projection rows (SportsDataIO style)
        return [
            {
                "Season": year,
                "Week": week,
                "PlayerID": 1,
                "Name": "Josh Allen",
                "Team": "BUF",
                "Opponent": "MIA",
                "FantasyPoints": 25.3,
                "Position": "QB",
            },
            {
                "Season": year,
                "Week": week,
                "PlayerID": 2,
                "Name": "Ja'Marr Chase",
                "Team": "CIN",
                "Opponent": "BAL",
                "FantasyPoints": 18.7,
                "Position": "WR",
            },
        ]

    def get_weekly_defensive_projections(self, year: int, week: int):
        # List of DST projections
        return [
            {
                "Season": year,
                "Week": week,
                "Team": "BUF",
                "Opponent": "MIA",
                "FantasyPoints": 7.5,
                "FantasyDefenseID": 101,
            },
            {
                "Season": year,
                "Week": week,
                "Team": "CIN",
                "Opponent": "BAL",
                "FantasyPoints": 6.2,
                "FantasyDefenseID": 102,
            },
        ]

    def get_schedule(self, year: int, week: int):
        # List of games for that week
        return [
            {
                "Season": year,
                "Week": week,
                "GameKey": f"{year}{week:02d}BUF-MIA",
                "HomeTeam": "BUF",
                "AwayTeam": "MIA",
                "Date": "2025-10-01T17:00:00",
            },
            {
                "Season": year,
                "Week": week,
                "GameKey": f"{year}{week:02d}CIN-BAL",
                "HomeTeam": "CIN",
                "AwayTeam": "BAL",
                "Date": "2025-10-01T20:25:00",
            },
        ]

def _reload_modules_with_temp_db(monkeypatch, db_path):
    """
    Helper to reload data.db and data.sync & make sure to use a temp db
    """
    # Point DB_PATH to the temporary test database
    monkeypatch.setenv("DB_PATH", str(db_path))

    # Import the modules fresh
    import data.db as db_mod
    import data.sync as sync_mod
    import importlib

    importlib.reload(db_mod)
    importlib.reload(sync_mod)

    return db_mod, sync_mod
    
def test_sync_players_uses_temp_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_gridiron.db"
    db, sync = _reload_modules_with_temp_db(monkeypatch, test_db_path)
    db.initialize_db()

    client = FakeDataClient()
    count = sync.sync_players(client)

    assert count > 0
    rows = db.fetch_all("SELECT player_id FROM players")
    assert len(rows) == count