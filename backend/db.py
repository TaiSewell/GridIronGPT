"""
    Developer: Tai Sewell
    File: db.py
    Description: This file contains my db connection
    and the initilization of the db using schema.sql
"""
import sqlite3
from pathlib import Path

# DB Path Origin
DB_PATH = Path(__file__).resolve().parent / "GridIronGPT.db"

def get_connection():
    """
    Establishes and returns a connection to the SQLite database.

    This function creates a new connection to the database 
    specified by DB_PATH and enables foreign key constraints.

    Returns:
        sqlite3.Connection: A connection object to interact with the SQLite database.
    Note:
        The connection has foreign key constraints enabled through PRAGMA statement.
    """
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """
    Initialize the database by executing SQL schema file.

    This function reads the SQL schema from 'schema.sql' and executes it to create
    or reset the database structure. The schema file should contain valid SQLite 
    commands for creating tables and other database objects.

    Args:
        None
    Returns:
        None
    Raises:
        FileNotFoundError: If schema.sql file is not found
        sqlite3.Error: If there's an error executing the SQL commands
    """
    from pathlib import Path
    with open(Path(__file__).resolve().parent / "schema.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    with get_connection() as conn:
        conn.executescript(sql)
    print(f"[init_db] Initialized schema at: {DB_PATH.resolve()}")


