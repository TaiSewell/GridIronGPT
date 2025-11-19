"""
=============================================================
 File: db.py
 Author: Tai Sewell
 Description:
     Manages SQLite database connections and query execution.
     Provides helper functions for inserts, selects, and
     context-managed connections for other modules.
=============================================================
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterable, List, Mapping, Optional

DB_PATH = os.getenv("DB_PATH", "./data/gridiron.db")

@contextmanager
def get_conn():
    """
    Context manager that yields a SQLite connection with
    sane defaults (row_factory, WAL, foreign keys ON).

    Usage:
        with get_conn() as conn:
            conn.execute("SELECT 1")
    """
    # Make sure the folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    # Make rows behave like dictionaries
    conn.row_factory = sqlite3.Row

    # Set important PRAGMAs for reliability/perf
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def initialize_db(schema_path: str = "./data/schema.sql") -> None:
    """
    Create tables if they do not exist by executing schema.sql.

    This should be called once at startup or before the first sync.

    Args:
        schema_path: Path to the SQL file that defines the schema.
    """
    with get_conn() as conn, open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
        conn.executescript(sql)

def fetch_all(query: str, params: Iterable[Any] = ()) -> List[Mapping[str, Any]]:
    """
    Run a SELECT query and return all rows as a list of dict-like objects.

    Args:
        query: SQL SELECT statement with placeholders (?)
        params: Values to bind to the placeholders

    Returns:
        List of rows, where each row behaves like a dict:
        row["column_name"]
    """
    with get_conn() as conn:
        cur = conn.execute(query, tuple(params))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    
def fetch_one(query: str, params: Iterable[any] = ()) -> List[Mapping[str, Any]]:
    """
    Run a SELECT query and return a single row (or None).

    Useful when you expect at most one result, e.g. by primary key.

    Args:
        query: SQL SELECT statement with placeholders (?)
        params: Values to bind to the placeholders

    Returns:
        A single row as a dict, or None if no rows match.
    """
    with get_conn() as conn:
        cur = conn.execute(query, tuple(params))
        row = cur.fetchone()
        if row is not None:
            return dict(row)
        else:
            None

def execute(query: str, params: Iterable[any] = ()) -> None:
    """
    Run a single non-SELECT statement (INSERT, UPDATE, DELETE).

    Args:
        query: SQL statement with placeholders (?)
        params: Values to bind to the placeholders
    """
    with get_conn() as conn:
        conn.execute(query, tuple(params))
    
def executemany(query: str, rows: Iterable[Iterable[Any]]) -> None:
    """
    Run the same non-SELECT statement for multiple rows.

    Useful for bulk insert/update operations during sync.

    Args:
        query: SQL statement with placeholders (?)
        rows: Iterable of tuples/lists with values to bind.
    """
    with get_conn() as conn:
        conn.executemany(query, list(rows))   

def get_meta(key: str) -> Optional[str]:
    """
    Fetch a single value from the meta table by key.

    Used for things like:
        - active_league_id
        - players_last_sync
        - rosters_last_sync

    Returns:
        The stored value as a string, or None if not set.
    """
    row = fetch_one("SELECT value FROM meta WHERE key = ?", (key,))
    if row is not None:
        return row["value"]
    else:
        None

def set_meta(key: str, value: str) -> None:
    """
    Insert or update a meta key/value pair.

    The updated_at column is automatically set to CURRENT_TIMESTAMP
    by the schema (if defined that way).

    Args:
        key: Name of the meta entry (e.g., 'active_league_id')
        value: Value to store (converted to TEXT in SQLite)
    """
    execute(
        """
        INSERT OR REPLACE INTO meta (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
        (key, value),
    )

def upsert_league(conn, league_id, name, season, status, scoring_setting_json) -> None:
    """
    Upsert the league information

    It will insert row if league_id does not exist,
    if the league_id exists it will update existing row.

    Args:
        conn = db connection 
        league_id = sleeper league id
        name = sleeper league name
        season = year
        status = Pre, Regular or post season
        scoring_setting_json = Scoring settings this league uses
    """
    execute (
        """
        INSERT INTO leagues (league_id, name, season, status, scoring_settings_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(league_id) 
        DO UPDATE SET 
            name = excluded.name, 
            season = excluded.season,
            status = excluded.status
            scoring_settings_json = excluded.scoring_settings_json,
            updated_at = CURRENT_TIMESTAMP;
        """
    )

def upsert_user(conn, user_id, display_name, avatar, team_name, metadata_json) -> None:
    """
    Upsert user into users table

    It will insert new user row if the user_id does not exist,
    otherwise it will update the existin user_id with the new information.

    Args:
        conn = db connection
        user_id = sleeper user id
        display_name = user display name
        avatar = user avatar
        team_name = users team name
        metadata_json = users metadata
    """
    conn.execute (
        """
        INSERT INTO users (user_id, display_name, avatar, team_name, metadata_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            display_name = excluded.display_name,
            avatar = excluded.avatar,
            team_name = excluded.team_name,
            metadata_json = excluded.metadata_json,
            updated_at = CURRENT_TIMESTAMP;
        """
    )
