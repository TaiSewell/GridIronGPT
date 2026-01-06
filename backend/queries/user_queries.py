"""
=============================================================
user_queries.py
Author: Tai Sewell

Database queries for user data.
=============================================================
"""

from typing import Any, Dict, List, Optional


def list_users(conn) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT user_id, display_name, avatar, team_name, metadata_json
        FROM users
        ORDER BY display_name ASC
        """
    ).fetchall()

    return [dict(r) for r in rows]


def get_user_by_id(conn, user_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT user_id, display_name, avatar, team_name, metadata_json
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    return dict(row) if row else None


def search_users_by_name(conn, name: str) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT user_id, display_name, avatar, team_name, metadata_json
        FROM users
        WHERE display_name LIKE ?
        ORDER BY display_name ASC
        """,
        (f"%{name}%",),
    ).fetchall()

    return [dict(r) for r in rows]
