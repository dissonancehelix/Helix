import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

def cleanse_integrity():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- HELIX DATA CLEANSE v5 ---")

    # 1. Deduplicate Appearance Registry
    # This keeps only one entry for each (entity_id, media_id) pair
    cursor.execute('''
        DELETE FROM appearance_registry 
        WHERE rowid NOT IN (
            SELECT MIN(rowid) 
            FROM appearance_registry 
            GROUP BY entity_id, media_id
        )
    ''')
    print(f" - Deduplicated appearances: {cursor.rowcount} rows removed.")

    # 2. Enforce Single Debut Flag
    # This ensures an entity only has 'debut_flag=1' on their earliest media entry
    # Based on release_chronology
    cursor.execute('''
        UPDATE appearance_registry 
        SET debut_flag = 0 
        WHERE appearance_id NOT IN (
            SELECT a.appearance_id
            FROM appearance_registry a
            JOIN media_registry m ON a.media_id = m.media_id
            WHERE a.debut_flag = 1
            GROUP BY a.entity_id
            HAVING m.release_chronology = MIN(m.release_chronology)
        ) AND debut_flag = 1
    ''')
    print(f" - Fixed debut multi-flags: {cursor.rowcount} entities corrected.")

    conn.commit()
    conn.close()
    print("[SUCCESS] Substrate integrity is now HARDENED.")

if __name__ == "__main__":
    cleanse_integrity()
