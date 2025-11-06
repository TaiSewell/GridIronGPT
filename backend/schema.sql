/*
   Developer: Tai Sewell
   File: Schema.sql
   Description: This file contains the schema that
   is implemented as the structure for the data that is loaded
   from playersdata.csv
*/

/*
    Create Players Table
*/
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    pos TEXT NOT NULL,
    week INTEGER NOT NULL,
    proj_points REAL,
    opp_def_rank INTEGER,
    ros_value INTEGER,
    rostered_pct REAL,
    status TEXT,
    CHECK (week BETWEEN 1 AND 18),
    CHECK (opp_def_rank BETWEEN 1 AND 32),
    CHECK (rostered_pct BETWEEN 0.0 AND 100.0),
    CHECK (ros_value BETWEEN 1 AND 404),
    CHECK (status IN ('ACTIVE', 'QUESTIONABLE', 'OUT', 'BYE'))
);


/*
    Create Indexes
    -- idx_playername: Quicker Lookup for a specific player
    -- idx_player_week: Quicker lookup for a specific player during a specific week
*/
CREATE INDEX IF NOT EXISTS idx_playername ON players(player_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_player_week ON players(player_name, week);




