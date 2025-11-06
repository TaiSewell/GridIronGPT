"""
    Developer: Tai Sewell
    File: load_csv.py
    Description: This file is used to load the data
    from the playersdata.csv file and then populate
    the database with the data.
"""
from db import get_connection, init_db, DB_PATH
import os
import csv
from pathlib import Path

# ---- Paths ----
# backend/ (this file) -> ../data/playersdata.csv
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "playersdata.csv"

def ensure_db_initialized():
    if not DB_PATH.exists():
        print("Database not found. Initializing schema...")
        init_db()

def load_csv_to_db(csv_path: Path):
    ensure_db_initialized()
    print(f"[loader] Using DB:  {DB_PATH.resolve()}")
    print(f"[loader] Using CSV: {csv_path.resolve()}")

    conn = get_connection()
    cur = conn.cursor()

    # (Optional) create unique index if you want to prevent duplicates
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_player_week ON players(player_name, week);
    """)

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        inserted = skipped = 0
        for line_num, row in enumerate(reader, start=2):
            if not row or len(row) != 9:
                skipped += 1
                continue

            # Trim & parse; use None for blanks to avoid CHECK failures
            row = [c.strip() for c in row]
            values = (
                row[0],              # player_name
                row[1],              # team
                row[2],              # pos
                int(row[3]) if row[3] else None,          # week (must be 1..18)
                float(row[4]) if row[4] else None,        # proj_points
                int(row[5]) if row[5] else None,          # opp_def_rank (1..32)
                int(row[6]) if row[6] else None,          # ros_value (1..404)
                float(row[7]) if row[7] else None,        # rostered_pct (0..100)
                row[8] if row[8] else None                # status
            )

            try:
                cur.execute(
                    """
                    INSERT INTO players
                    (player_name, team, pos, week, proj_points, opp_def_rank, ros_value, rostered_pct, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(player_name, week) DO UPDATE SET
                      team         = excluded.team,
                      pos          = excluded.pos,
                      proj_points  = excluded.proj_points,
                      opp_def_rank = excluded.opp_def_rank,
                      ros_value    = excluded.ros_value,
                      rostered_pct = excluded.rostered_pct,
                      status       = excluded.status
                    """,
                    values
                )
                inserted += 1
            except Exception as e:
                print(f"[loader] Line {line_num} error: {e} -> {row}")
                skipped += 1

    conn.commit()
    conn.close()
    print(f"[loader] Done. Inserted/Upserted: {inserted}, Skipped: {skipped}")

if __name__ == "__main__":
    load_csv_to_db(CSV_PATH)