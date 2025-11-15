"""
=============================================================
 File: sync.py
 Author: Tai Sewell
 Description:
     Synchronizes data from the Sleeper API into the local
     SQLite database. Runs full and incremental updates
     based on TTL rules and user-triggered refresh requests.
=============================================================
"""
from data_client import DataClient