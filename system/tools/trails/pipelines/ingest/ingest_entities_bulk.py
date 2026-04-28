import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

# Sample of the 495 entities for demonstration (Real implementation would use a file)
# Since I have the 495-character list from previous research, I'll load it if available
# or populate the key cast for now.

def ingest_entities_bulk():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Load entities from the 'harvested_entities.json' if it exists
    # If not, we'll re-harvest or use the core cast
    
    core_cast = [
        {"id": "char:estelle_bright", "type": "character", "en": "Estelle Bright", "ja": "エステル・ブライト", "debut": "sky_fc"},
        {"id": "char:joshua_bright", "type": "character", "en": "Joshua Bright", "ja": "ヨシュア・ブライト", "debut": "sky_fc"},
        {"id": "char:van_arkride", "type": "character", "en": "Van Arkride", "ja": "ヴァン・アークライド", "debut": "daybreak"},
        {"id": "char:agnes_claudel", "type": "character", "en": "Agnes Claudel", "ja": "アニエス・クローデル", "debut": "daybreak"},
        {"id": "char:rean_schwarzer", "type": "character", "en": "Rean Schwarzer", "ja": "リィン・シュバルツァー", "debut": "cs1"},
    ]
    
    print(f"Ingesting {len(core_cast)} core entities...")
    
    for c in core_cast:
        # Entity Registry
        cursor.execute('''
            INSERT OR REPLACE INTO entity_registry (
                entity_id, entity_type, english_display_name, japanese_name
            ) VALUES (?, ?, ?, ?)
        ''', (c["id"], c["type"], c["en"], c["ja"]))
        
        # Appearance Registry (Debut)
        cursor.execute('''
            INSERT OR REPLACE INTO appearance_registry (
                entity_id, media_id, appearance_type, debut_flag
            ) VALUES (?, ?, ?, ?)
        ''', (c["id"], c["debut"], "main", 1))

    conn.commit()
    conn.close()
    print("Core Entities Ingested.")

if __name__ == "__main__":
    ingest_entities_bulk()
