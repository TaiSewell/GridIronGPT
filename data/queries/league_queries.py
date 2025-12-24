def get_league_season(conn, league_id: str) -> int | None:
    """
    Return the current season for a league.
    """
    row = conn.execute(
        "SELECT season FROM leagues WHERE league_id = ?",
        (league_id,),
    ).fetchone()

    return row[0] if row else None