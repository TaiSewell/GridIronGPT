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
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Iterable, List, Dict, Optional, Mapping

DB_PATH = os.getenv("DB_PATH", "./data/gridiron.db")
SCHEMA_PATH = os.getenv("SCHEMA_PATH", "./backend/schema.sql")

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

    print(f"DEBUG: Connecting to database at: {os.path.abspath(DB_PATH)}")
    print(f"DEBUG: Does file exist? {os.path.exists(DB_PATH)}")
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

def initialize_db(schema_path: str | Path = SCHEMA_PATH) -> None:
    """
    Create tables if they do not exist by executing schema.sql.

    This should be called once at startup or before the first sync.

    Args:
        schema_path: Path to the SQL file that defines the schema.
    """
    with get_conn() as conn, open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
        conn.executescript(sql)
    print("Initializing DB at", os.getenv("DB_PATH"))

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
    
def fetch_one(query: str, params: Iterable[any] = ()) -> Optional[Dict[str, Any]]:
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
            return None

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
        return None

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

def upsert_league(conn, league_id, name, season, status, scoring_settings_json) -> None:
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
    conn.execute (
        """
        INSERT INTO leagues (league_id, name, season, status, scoring_settings_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(league_id) 
        DO UPDATE SET 
            name = excluded.name, 
            season = excluded.season,
            status = excluded.status,
            scoring_settings_json = excluded.scoring_settings_json,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (league_id, name, season, status, scoring_settings_json)
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
        """,
        (user_id, display_name, avatar, team_name, metadata_json)
    )

def upsert_roster(
    conn,
    league_id,
    roster_id,
    owner_id,
    starters_json,
    bench_json,
    wins,
    losses,
    ties,
    waiver_position,
    total_moves,
    fpts,
    fpts_against,
) -> None:
    """
    Insert or update a roster record in the database.

    Args:
        conn: Database connection object.
        league_id (int): The ID of the league the roster belongs to.
        roster_id (int): The unique identifier for the roster.
        owner_id (int): The ID of the owner/user who owns this roster.
        starters_json (str): JSON string containing the roster's starting players.
        bench_json (str): JSON string containing the roster's bench players.
    Returns:
        None
    """
    cur = conn.execute("SELECT 1 FROM leagues WHERE league_id = ?", (league_id,))
    if cur.fetchone() is None:
        raise RuntimeError(
            f"Cannot upsert roster: league '{league_id}' does not exist. "
            "Call upsert_league() (or sync_league) before inserting rosters."
        )

    conn.execute(
        """
        INSERT INTO rosters (
            league_id,
            roster_id,
            owner_id,
            starters_json,
            bench_json,
            wins,
            losses,
            ties,
            waiver_position,
            total_moves,
            fpts,
            fpts_against
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(league_id, roster_id)
        DO UPDATE SET
            owner_id = excluded.owner_id,
            starters_json = excluded.starters_json,
            bench_json = excluded.bench_json,
            wins = excluded.wins,
            losses = excluded.losses,
            ties = excluded.ties,
            waiver_position = excluded.waiver_position,
            total_moves = excluded.total_moves,
            fpts = excluded.fpts,
            fpts_against = excluded.fpts_against;
        """,
        (
            league_id,
            roster_id,
            owner_id,
            starters_json,
            bench_json,
            wins,
            losses,
            ties,
            waiver_position,
            total_moves,
            fpts,
            fpts_against,
        ),
    )
    
def upsert_player(conn, player_id, player_name, team, position, status) -> None:
        """
        Insert or update a player record in the database.

        Args:
            conn: Database connection object.
            player_id (int): Unique identifier for the player.
            player_name (str): Name of the player.
            team (str): Team abbreviation or identifier.
            position (str): Player's position (e.g., 'QB', 'RB', 'WR').
            status (str): Player's current status (e.g., 'active', 'injured', 'retired').

        Returns:
            None
        """
        conn.execute(
            """
            INSERT INTO players(player_id, player_name, team, position, status)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(player_id)
            DO UPDATE SET
            player_name = excluded.player_name,
            team = excluded.team,
            position = excluded.position,
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP;
            """,
            (player_id, player_name, team, position, status)
        )

def upsert_player_week_meta(conn, player_id, season, week, opp_team, is_home, actual_points=None) -> None:
    conn.execute(
        """
        INSERT INTO player_week_meta (
            player_id, season, week, opp_team, is_home, actual_points
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_id, season, week)
        DO UPDATE SET
            opp_team = COALESCE(excluded.opp_team, player_week_meta.opp_team),
            is_home = COALESCE(excluded.is_home, player_week_meta.is_home),
            actual_points = COALESCE(excluded.actual_points, player_week_meta.actual_points);
        """,
        (player_id, season, week, opp_team, is_home, actual_points),
    )

def upsert_matchup(conn, league_id, season, week, roster_id, matchup_id, players_json, points) -> None:
    """
    Insert or update a matchup record in the database.

    Args:
        conn: Database connection object.
        league_id (int): The ID of the league the matchup belongs to.
        season (int): Season/year for the matchup.
        week (int): The week number of the matchup.
        roster_id (int): The roster ID involved in this matchup.
        matchup_id (int): Unique identifier for the matchup.
        players_json (str): JSON string listing players for this roster in the matchup.
        points (float): Points scored by the roster in this matchup.

    Returns:
        None
    """
    conn.execute(
        """
        INSERT INTO matchups(league_id, season, week, roster_id, matchup_id, players_json, points)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(league_id, season, week, roster_id)
        DO UPDATE SET
            league_id = excluded.league_id,
            season = excluded.season,
            week = excluded.week,
            roster_id = excluded.roster_id,
            players_json = excluded.players_json,
            points = excluded.points,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (league_id, season, week, roster_id, matchup_id, players_json, points)
    )

def upsert_player_weekly_proj_stat(conn, season: int, week: int, player_id: str, stat_key: str, value: float, source: str = "sportsdataio") -> None:
    conn.execute(
        """
        INSERT INTO player_weekly_proj_stats (
            season, week, player_id, stat_key, value, source
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(season, week, player_id, stat_key, source)
        DO UPDATE SET
            value = excluded.value,
            generated_at = CURRENT_TIMESTAMP;
        """,
        (season, week, player_id, stat_key, value, source),
    )

def upsert_scoring_settings(conn, league_id, stat_key, weight) -> None:
        """
        Insert or update scoring settings for a league.

        Args:
            conn: Database connection object.
            league_id (int): The ID of the league.
            stat_key (str): The key for the scoring statistic.
            weight (float): The weight assigned to the scoring statistic.

        Returns:
            None
        """
        conn.execute(
            """
            INSERT INTO scoring_settings(league_id, stat_key, weight)
            VALUES(?, ?, ?)
            ON CONFLICT(league_id, stat_key)
            DO UPDATE SET
                weight = excluded.weight,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (league_id, stat_key, weight)
        )

def upsert_projection_adjustment(conn, league_id, position, multiplier, bonus) -> None:
    conn.execute(
        """
        INSERT INTO projection_adjustments(league_id, position, multiplier, bonus)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(league_id, position)
        DO UPDATE SET
            multiplier = excluded.multiplier,
            bonus = excluded.bonus;
        """,
        (league_id, position, multiplier, bonus),
    )


def upsert_dst_weekly_points(
    conn,
    season: int,
    week: int,
    dst_team: str,
    projected_points: float | None,
    actual_points: float | None,
    source: str = "sportsdataio",
) -> None:
    conn.execute(
        """
        INSERT INTO dst (
            season,
            week,
            dst_team,
            projected_points,
            actual_points,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(season, week, dst_team, source)
        DO UPDATE SET
            projected_points = COALESCE(excluded.projected_points, dst.projected_points),
            actual_points = COALESCE(excluded.actual_points, dst.actual_points),
            generated_at = CURRENT_TIMESTAMP;
        """,
        (
            season,
            week,
            dst_team,
            projected_points,
            actual_points,
            source,
        ),
    )
    

    
    
        
        

