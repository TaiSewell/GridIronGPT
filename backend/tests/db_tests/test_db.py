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

# Initialize db
import data.db as db
db.initialize_db()

def test_integration_sync_real_db_env():
    """
    Integration test that hits the real Sleeper API and writes to the DB
    defined in your .env file.

    Uses:
    - DB_PATH from .env (default: ./data/gridiron.db)
    - SLEEPER_LEAGUE_ID from .env (optional)
    """
    import pytest
    from dotenv import load_dotenv
    import data.db as real_db
    import data.sync as real_sync
    from data.data_client import DataClient
    import os

    # Load variables from .env file
    load_dotenv()

    db_path = os.getenv("DB_PATH", "./data/gridiron.db")
    league_id = os.getenv("SLEEPER_LEAGUE_ID")  # optional

    # Require explicit opt-in so CI doesn’t hit APIs
    if os.getenv("ENABLE_INTEGRATION") not in ("1", "true", "yes"):
        pytest.skip("Enable integration test by setting ENABLE_INTEGRATION=1 in environment.")

    # Make sure DB_PATH is respected
    os.environ["DB_PATH"] = db_path

    # Ensure DB schema is created
    real_db.initialize_db()

    client = DataClient()

    # --------- PLAYERS SYNC (always runs) ---------
    count = real_sync.sync_players(client)
    assert count > 0, "Expected real Sleeper player payload"

    rows = real_db.fetch_all("SELECT player_id FROM players LIMIT 1")
    assert len(rows) > 0, "Players table should contain real Sleeper data"

    # --------- LEAGUE SYNC (optional if league ID exists) ---------
    if league_id:
        real_sync.sync_league(client, league_id)

        league = real_db.fetch_one(
            "SELECT * FROM leagues WHERE league_id = ?", (league_id,)
        )
        assert league is not None, "League did not save to DB"

        users = real_db.fetch_all(
            "SELECT user_id FROM users WHERE user_id IS NOT NULL LIMIT 1"
        )
        assert len(users) > 0, "Users failed to save to DB"

        rosters = real_db.fetch_all(
            "SELECT roster_id FROM rosters WHERE league_id = ? LIMIT 1",
            (league_id,),
        )
        assert len(rosters) > 0, "Rosters failed to save to DB"
