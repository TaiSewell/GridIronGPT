"""
Developer: Tai Sewell
File: test_db_init.py
"""
from data import db


print("\n**************************" \
"\n  db initilization Test" \
"\n**************************")
# Test db initialization & fetch_all()
db.initialize_db()
print("fetch_all() test:\n\n", db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'"))


print("\n**************************" \
"\n\tHelper Tests" \
"\n**************************")
# Test set_meta() & get_meta()
db.set_meta("123", "meta1")
print("set_meta() & get_meta() test results: ", db.get_meta("123"))

print("\nupserting_league() test results: \n")
# Tests upserting_league()
with db.get_conn() as conn:
    db.upsert_league(conn, "12345", "My League", 2025, "pre", '{"pass_yd":0.04,' \
    '"pass_td: 4}')
row1 = db.fetch_one("SELECT * FROM leagues WHERE league_id = ?", ("12345",))
print("First insert:", row1)

with db.get_conn() as conn:
    db.upsert_league(conn, "12345", "Updated League", 2025, "post", '{"pass_yd":0.05}')

row2 = db.fetch_one("SELECT * FROM leagues WHERE league_id = ?", ("12345",))
print("After update:", row2)

# -----------------------------------------
# Test fetch_one() when no rows are found
# -----------------------------------------

row_none = db.fetch_one(
    "SELECT key, value FROM meta WHERE key = ?",
    ("helper_test_does_not_exist",)
)
print("\nfetch_one no row:", row_none)


# --------------------------
# Test executemany()
# --------------------------

# Clean previous test rows
db.execute("DELETE FROM meta WHERE key LIKE 'helper_bulk_%'")

rows_to_insert = [
    ("helper_bulk_1", "one"),
    ("helper_bulk_2", "two"),
    ("helper_bulk_3", "three")
]

db.executemany(
    "INSERT INTO meta (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
    rows_to_insert
)

bulk_rows = db.fetch_all(
    "SELECT key, value FROM meta WHERE key LIKE 'helper_bulk_%' ORDER BY key"
)
print("executemany results:", bulk_rows)

# -----------------------------
# Test: upsert_user
# -----------------------------
with db.get_conn() as conn:
    # Clean
    conn.execute("DELETE FROM users WHERE user_id = 'u1'")

    # Insert
    db.upsert_user(conn, "u1", "Test User", "avatar1", "Team One", "{}")
    row1 = db.fetch_one("SELECT * FROM users WHERE user_id = 'u1'")
    print("user insert:", row1)

    # Update
    db.upsert_user(conn, "u1", "Updated User", "avatar2", "Team Two", '{"x":1}')
    row2 = db.fetch_one("SELECT * FROM users WHERE user_id = 'u1'")
    print("user update:", row2)


# -----------------------------
# Test: upsert_roster
# -----------------------------
with db.get_conn() as conn:
    conn.execute("DELETE FROM rosters WHERE league_id='L1' AND roster_id=1")

    # Insert
    db.upsert_roster(conn, "L1", 1, "u1", '["QB1"]', '["BN1"]')
    row1 = db.fetch_one(
        "SELECT * FROM rosters WHERE league_id='L1' AND roster_id=1"
    )
    print("roster insert:", row1)

    # Update
    db.upsert_roster(conn, "L1", 1, "u1", '["QB2"]', '["BN2"]')
    row2 = db.fetch_one(
        "SELECT * FROM rosters WHERE league_id='L1' AND roster_id=1"
    )
    print("roster update:", row2)


# -----------------------------
# Test: upsert_player
# -----------------------------
with db.get_conn() as conn:
    conn.execute("DELETE FROM players WHERE player_id='p1'")

    # Insert
    db.upsert_player(conn, "p1", "Player One", "NE", "QB", "active")
    row1 = db.fetch_one("SELECT * FROM players WHERE player_id='p1'")
    print("player insert:", row1)

    # Update
    db.upsert_player(conn, "p1", "Player One Updated", "BUF", "QB", "active")
    row2 = db.fetch_one("SELECT * FROM players WHERE player_id='p1'")
    print("player update:", row2)


# -----------------------------
# Test: upsert_matchup
# -----------------------------
with db.get_conn() as conn:
    conn.execute("DELETE FROM matchups")

    # Insert
    db.upsert_matchup(
        conn,
        matchup_id=1,
        league_id="L1",
        week=1,
        roster_id_1=1,
        roster_id_2=2,
        points_1=100.1,
        points_2=90.5,
    )
    row1 = db.fetch_one("SELECT * FROM matchups WHERE matchup_id=1")
    print("matchup insert:", row1)

    # Update
    db.upsert_matchup(
        conn,
        matchup_id=1,
        league_id="L1",
        week=1,
        roster_id_1=1,
        roster_id_2=2,
        points_1=110.0,
        points_2=92.0,
    )
    row2 = db.fetch_one("SELECT * FROM matchups WHERE matchup_id=1")
    print("matchup update:", row2)


# -----------------------------
# Test: upsert_player_week_meta
# -----------------------------
with db.get_conn() as conn:
    conn.execute("DELETE FROM player_week_meta WHERE player_id='p1' AND season=2025 AND week=1")

    # Insert
    db.upsert_player_week_meta(conn, "p1", 2025, 1, "JAX", 1)
    row1 = db.fetch_one(
        "SELECT * FROM player_week_meta WHERE player_id='p1' AND season=2025 AND week=1"
    )
    print("pwm insert:", row1)

    # Update
    db.upsert_player_week_meta(conn, "p1", 2025, 1, "KC", 0)
    row2 = db.fetch_one(
        "SELECT * FROM player_week_meta WHERE player_id='p1' AND season=2025 AND week=1"
    )
    print("pwm update:", row2)


# -----------------------------
# Test: upsert_scoring_settings
# -----------------------------
with db.get_conn() as conn:
    conn.execute("DELETE FROM scoring_settings WHERE league_id='L1' AND stat_key='pass_yd'")

    # Insert
    db.upsert_scoring_settings(conn, "L1", "pass_yd", 0.04)
    row1 = db.fetch_one(
        "SELECT * FROM scoring_settings WHERE league_id='L1' AND stat_key='pass_yd'"
    )
    print("ss insert:", row1)

    # Update
    db.upsert_scoring_settings(conn, "L1", "pass_yd", 0.05)
    row2 = db.fetch_one(
        "SELECT * FROM scoring_settings WHERE league_id='L1' AND stat_key='pass_yd'"
    )
    print("ss update:", row2)


# -----------------------------
# Test: upsert_dst_tier
# -----------------------------
with db.get_conn() as conn:
    conn.execute("DELETE FROM dst_tiers WHERE league_id='L1' AND metric='pa' AND min_incl=0")

    # Insert
    try:
        db.upsert_dst_tier(conn, "L1", "pa", 0, 6, -4)
        row1 = db.fetch_one(
            "SELECT * FROM dst_tiers WHERE league_id='L1' AND metric='pa' AND min_incl=0"
        )
        print("dst insert:", row1)
    except Exception as e:
        print("dst insert error:", e)