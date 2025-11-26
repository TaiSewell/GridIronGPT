from data.cache_manager import CacheManager
from data.data_client import DataClient

# Put your actual league ID here
LEAGUE_ID = "1266923357840871424"

def main():
    cm = CacheManager(league_id=LEAGUE_ID, client=DataClient())

    print("\n=== FIRST RUN (should trigger syncs) ===")
    cm.ensure_players_cached()
    cm.ensure_league_bundle_cached(week=10)
    cm.ensure_matchups_cached(week=10)

    print("\n=== SECOND RUN (should use cache, no sync logs) ===")
    cm.ensure_players_cached()
    cm.ensure_league_bundle_cached(week=10)
    cm.ensure_matchups_cached(week=10)

if __name__ == "__main__":
    main()