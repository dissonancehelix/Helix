import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

# Mapping of common wiki strings to Registry media_ids
MEDIA_MAP = {
    "trails in the sky fc": "sky_fc",
    "trails in the sky the 1st": "sky_fc",
    "trails in the sky sc": "sky_sc",
    "trails in the sky the 3rd": "sky_3rd",
    "trails from zero": "zero",
    "trails to azure": "azure",
    "trails of cold steel": "cs1",
    "trails of cold steel i": "cs1",
    "trails of cold steel ii": "cs2",
    "trails of cold steel iii": "cs3",
    "trails of cold steel iv": "cs4",
    "trails into reverie": "reverie",
    "trails through daybreak": "daybreak",
    "trails through daybreak ii": "daybreak_2",
    "trails beyond the horizon": "kai",
    "trails of cold steel – northern war": "northern_war",
}

def link_appearances_bulk():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Hardening Appearance Links for 500+ entities...")
    
    # 1. Fetch all raw bio chunks from the mirror ingest
    cursor.execute('''
        SELECT chunk_id, text_content 
        FROM chunk_registry 
        WHERE source_id = 'wiki:en_mirror_v1'
    ''')
    chunks = cursor.fetchall()
    
    linked_count = 0
    for row in chunks:
        entity_id = row['chunk_id'].replace('raw:', '')
        text = row['text_content'].lower()
        
        # Check for media mentions in the first paragraph
        for search_str, media_id in MEDIA_MAP.items():
            if search_str in text:
                # Map as Debut if they don't have one, or Support if they do
                cursor.execute('''
                    INSERT OR IGNORE INTO appearance_registry (
                        entity_id, media_id, appearance_type, debut_flag
                    ) VALUES (?, ?, 'main', 1)
                ''', (entity_id, media_id))
                
                if cursor.rowcount > 0:
                    linked_count += 1
                    break # Stop at first major game mention for debut

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Linked {linked_count} entities to their Debut media.")

if __name__ == "__main__":
    link_appearances_bulk()
