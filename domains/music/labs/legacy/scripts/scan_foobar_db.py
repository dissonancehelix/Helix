import sqlite3
import os

DB_PATH = r'C:\Users\dissonance\AppData\Roaming\foobar2000-v2\metadb.sqlite'
META_IDX = 'metadb_index_BE36C585_58CE_4465_9825_F2CA30CCEEED'
META_DATA = f'{META_IDX}_data'

def dump_foobar_stats():
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT i.filename, d.value 
        FROM {META_IDX} i 
        JOIN {META_DATA} d ON i.key = d.key 
        LIMIT 100
    """
    rows = conn.execute(query).fetchall()
    for filename, blob in rows:
        print(f"URL: {filename}")
        print(f"BLOB (hex): {blob.hex()}")
        print("-" * 20)
    conn.close()

if __name__ == "__main__":
    dump_foobar_stats()
