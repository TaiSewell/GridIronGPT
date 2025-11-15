/*
=============================================================
 File: schema.sql
 Author: Tai Sewell
 Description:
     Defines the SQLite database schema for the project.
     Includes tables for players, rosters, matchups, and
     metadata used for caching and validation.
=============================================================
*/

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

/**************************
    Create Leagues Table
**************************/
CREATE TABLE IF NOT EXISTS leagues (
    league_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    season INTEGER NOT NULL,
    status TEXT NOT NULL,
    scoring_settings_json TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

/**************************
    Create Rosters Table
**************************/
CREATE TABLE IF NOT EXISTS rosters (
    league_id TEXT NOT NULL,
    roster_id INTEGER NOT NULL
    owner_id TEXT,
    starters_json TEXT,
    bench_json TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (league_id, roster_id),
    FOREIGN KEY (league_id) REFERENCES leagues(league_id) ON DELETE CASCADE
);

/**************************
    Create Players Table
**************************/
CREATE TABLE IF NOT EXISTS players (
  player_id TEXT PRIMARY KEY,
  player_name TEXT NOT NULL,
  team TEXT,
  position TEXT,
  status TEXT
);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(player_name);

/**********************************
   Create Player_week_stats Table
**********************************/
CREATE TABLE IF NOT EXISTS player_week_stats (
  player_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,
  proj_points REAL,
  opp_def_rank INTEGER,
  ros_value INTEGER,
  rostered_pct REAL,
  PRIMARY KEY (player_id, season, week),
  FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
  CHECK (week BETWEEN 1 AND 18),
  CHECK (opp_def_rank IS NULL OR (opp_def_rank BETWEEN 1 AND 32)),
  CHECK (rostered_pct IS NULL OR (rostered_pct BETWEEN 0 AND 100))
);
CREATE INDEX IF NOT EXISTS idx_pws_season_week ON player_week_stats(season, week);

/**************************
   Create Matchups Table
**************************/
CREATE TABLE IF NOT EXISTS matchups (
    league_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    roster_id INTEGER NOT NULL,

    matchup_id INTEGER,              -- storing matchup_id for future improvements
    players_json TEXT,               -- players used in that matchup
    points REAL,                     -- points scored that week
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (league_id, season, week, roster_id),

    FOREIGN KEY (league_id, roster_id)
        REFERENCES rosters(league_id, roster_id)
        ON DELETE CASCADE
);

/**************************
     Create Meta Table
**************************/
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);