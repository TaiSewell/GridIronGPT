/*
=============================================================
 File: schema.sql
 Author: Tai Sewell
 Description:
   SQLite schema for GridironGPT (explainable projections).
   - Core: leagues, rosters, players, matchups, meta
   - Weekly context: player_week_meta (opp + home/away)
   - Projections (EAV): player_weekly_proj_stats
   - League scoring: scoring_settings (+ dst_tiers)
   - Views: player projections, DST projections, DST ranks
=============================================================
*/

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

/**************************
   Leagues (Sleeper)
**************************/
CREATE TABLE IF NOT EXISTS leagues (
  league_id TEXT PRIMARY KEY,                 -- Sleeper league_id
  name TEXT,
  season INTEGER NOT NULL,
  status TEXT NOT NULL,                       -- 'pre'|'in_season'|'post' (free-form ok)
  scoring_settings_json TEXT NOT NULL,        -- raw Sleeper scoring payload (cached)
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

/***************************
  Users In League (Sleeper)
***************************/
CREATE TABLE IF NOT EXISTS users (
  user_id      TEXT PRIMARY KEY,             -- Sleeper user_id
  display_name TEXT,
  avatar       TEXT,                         -- Sleeper avatar id/url
  team_name    TEXT,                         -- from metadata if present
  metadata_json TEXT,                        -- raw payload for anything else
  updated_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

/**************************
   Rosters per League
**************************/
CREATE TABLE IF NOT EXISTS rosters (
  league_id TEXT NOT NULL,
  roster_id INTEGER NOT NULL,
  owner_id TEXT,
  starters_json TEXT,
  bench_json TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (league_id, roster_id),
  FOREIGN KEY (league_id) REFERENCES leagues(league_id) ON DELETE CASCADE
);

/**************************
   Players
**************************/
CREATE TABLE IF NOT EXISTS players (
  player_id   TEXT PRIMARY KEY,               -- Sleeper player_id (or pseudo 'DST-BUF')
  player_name TEXT NOT NULL,
  team        TEXT,                           -- e.g., BUF
  position    TEXT,                           -- QB/RB/WR/TE/K/DST
  status      TEXT,
  updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(player_name);

/**********************************
   Player Week Meta (context only)
   
   * Each players league specific
   summarized fantasy context
**********************************/
CREATE TABLE IF NOT EXISTS player_week_meta (
  player_id TEXT NOT NULL,
  season    INTEGER NOT NULL,
  week      INTEGER NOT NULL CHECK (week BETWEEN 1 AND 18),
  opp_team  TEXT,                             -- e.g., JAX
  is_home   INTEGER,                          -- 1=home, 0=away, NULL=unknown
  PRIMARY KEY (player_id, season, week),
  FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pwm_season_week ON player_week_meta(season, week);

/**************************
   Matchups (optional cache)
**************************/
CREATE TABLE IF NOT EXISTS matchups (
  league_id TEXT NOT NULL,
  season    INTEGER NOT NULL,
  week      INTEGER NOT NULL,
  roster_id INTEGER NOT NULL,

  matchup_id   INTEGER,                       -- future use
  players_json TEXT,                          -- players used in that matchup
  points       REAL,                          -- points scored that week
  updated_at   TEXT DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (league_id, season, week, roster_id),
  FOREIGN KEY (league_id, roster_id)
    REFERENCES rosters(league_id, roster_id)
    ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_matchups_week ON matchups(season, week);

/********************************
  League Scoring (linear weights)
********************************/
CREATE TABLE IF NOT EXISTS scoring_settings (
  league_id TEXT NOT NULL,
  stat_key  TEXT NOT NULL,                    -- pass_yd, pass_td, rec, int, dst_sack, ...
  weight    REAL NOT NULL,                    -- 0.04, 4, 1, -2, ...
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (league_id, stat_key),
  FOREIGN KEY (league_id) REFERENCES leagues(league_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_scoring_league ON scoring_settings(league_id, stat_key);

/****************************************
  Player Weekly Projections (EAV model)

  * Each players raw stats for the week
****************************************/
CREATE TABLE IF NOT EXISTS player_weekly_proj_stats (
  season       INTEGER NOT NULL,
  week         INTEGER NOT NULL CHECK (week BETWEEN 1 AND 18),
  player_id    TEXT NOT NULL,
  stat_key     TEXT NOT NULL,                 -- pass_yd, pass_td, int, rush_yd, rec, dst_sack, dst_pa, ...
  value        REAL NOT NULL DEFAULT 0,
  source       TEXT NOT NULL DEFAULT 'sportsdataio',
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (season, week, player_id, stat_key, source),
  FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_proj_swp ON player_weekly_proj_stats(season, week, player_id);
CREATE INDEX IF NOT EXISTS idx_proj_swk ON player_weekly_proj_stats(season, week, stat_key);

/****************************************
  DST Tier Ranges (Sleeper-style buckets)
****************************************/
CREATE TABLE IF NOT EXISTS dst_tiers (
  league_id  TEXT NOT NULL,
  metric     TEXT NOT NULL CHECK (metric IN ('points_allowed','yards_allowed')),
  min_incl   INTEGER NOT NULL,                -- inclusive lower bound
  max_incl   INTEGER,                         -- inclusive upper (NULL=open-ended)
  points     REAL NOT NULL,                   -- tier bonus/penalty
  PRIMARY KEY (league_id, metric, min_incl, max_incl),
  FOREIGN KEY (league_id) REFERENCES leagues(league_id) ON DELETE CASCADE
);

/**************************************
  Projection Adjustments (by position)
**************************************/
CREATE TABLE IF NOT EXISTS projection_adjustments (
  league_id  TEXT NOT NULL,
  position   TEXT NOT NULL,  -- QB, RB, WR, TE, K, DST
  multiplier REAL NOT NULL DEFAULT 1.0,
  bonus      REAL NOT NULL DEFAULT 0.0,
  PRIMARY KEY (league_id, position),
  FOREIGN KEY (league_id) REFERENCES leagues(league_id) ON DELETE CASCADE
);

/******************************************
  Baseline Player Weekly Projections (FP)
******************************************/
CREATE VIEW IF NOT EXISTS v_player_weekly_proj_points AS
SELECT
  pws.season,
  pws.week,
  pws.player_id,
  ss.league_id,
  ROUND(SUM(pws.value * ss.weight), 2) AS baseline_points
FROM player_weekly_proj_stats AS pws
JOIN scoring_settings AS ss
  ON ss.stat_key = pws.stat_key
GROUP BY
  pws.season,
  pws.week,
  pws.player_id,
  ss.league_id;

/*********************************************
  Final Player Weekly Projections (Adjusted)
*********************************************/
CREATE VIEW IF NOT EXISTS v_player_weekly_final_proj AS
SELECT
  v.season,
  v.week,
  v.player_id,
  p.player_name,
  p.position,
  v.league_id,
  pwm.opp_team,
  pwm.is_home,
  v.baseline_points,
  COALESCE(adj.multiplier, 1.0) AS multiplier,
  COALESCE(adj.bonus, 0.0)      AS bonus,
  ROUND(
    v.baseline_points * COALESCE(adj.multiplier, 1.0)
    + COALESCE(adj.bonus, 0.0),
    2
  ) AS final_projection
FROM v_player_weekly_proj_points AS v
JOIN players AS p
  ON p.player_id = v.player_id
LEFT JOIN projection_adjustments AS adj
  ON adj.league_id = v.league_id
 AND adj.position  = p.position
LEFT JOIN player_week_meta AS pwm
  ON pwm.player_id = v.player_id
 AND pwm.season    = v.season
 AND pwm.week      = v.week;
/******************************************
  View: Projected DST Points (linear + tiers)
******************************************/
CREATE VIEW IF NOT EXISTS v_dst_weekly_proj_points AS
WITH base AS (
  SELECT
    pws.season,
    pws.week,
    pws.player_id,
    p.team AS dst_team,
    ss.league_id,
    SUM(pws.value * ss.weight) AS linear_points
  FROM player_weekly_proj_stats pws
  JOIN players p           ON p.player_id = pws.player_id AND p.position = 'DST'
  JOIN scoring_settings ss ON ss.stat_key = pws.stat_key
  GROUP BY pws.season, pws.week, pws.player_id, ss.league_id
),
pa AS (
  SELECT
    season, week, player_id,
    MAX(CASE WHEN stat_key = 'dst_pa' THEN value END) AS dst_pa,
    MAX(CASE WHEN stat_key = 'dst_ya' THEN value END) AS dst_ya
  FROM player_weekly_proj_stats
  GROUP BY season, week, player_id
)
SELECT
  b.season,
  b.week,
  b.player_id,
  b.dst_team,
  b.league_id,
  ROUND(
    b.linear_points
    + COALESCE((
        SELECT dt.points
        FROM dst_tiers dt
        WHERE dt.league_id = b.league_id
          AND dt.metric = 'points_allowed'
          AND pa.dst_pa IS NOT NULL
          AND pa.dst_pa >= dt.min_incl
          AND (dt.max_incl IS NULL OR pa.dst_pa <= dt.max_incl)
        LIMIT 1
      ), 0)
    + COALESCE((
        SELECT dt.points
        FROM dst_tiers dt
        WHERE dt.league_id = b.league_id
          AND dt.metric = 'yards_allowed'
          AND pa.dst_ya IS NOT NULL
          AND pa.dst_ya >= dt.min_incl
          AND (dt.max_incl IS NULL OR pa.dst_ya <= dt.max_incl)
        LIMIT 1
      ), 0)
  , 2) AS projected_points
FROM base b
LEFT JOIN pa
  ON pa.season = b.season AND pa.week = b.week AND pa.player_id = b.player_id;

/******************************************
  View: Weekly DST Ranks (per league)
******************************************/
CREATE VIEW IF NOT EXISTS v_dst_weekly_proj_rank AS
SELECT
  season,
  week,
  league_id,
  player_id,
  dst_team,
  projected_points,
  RANK() OVER (
    PARTITION BY season, week, league_id
    ORDER BY projected_points DESC
  ) AS dst_rank
FROM v_dst_weekly_proj_points;

/**************************
   Meta (key/value cache)
**************************/
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);