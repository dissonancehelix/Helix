import json
import sqlite3
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')
REGIONS_JSON_PATH = Path('corpus/github/zemurian-atlas-main/src/data/regions.json')

def ingest_geography():
    if not REGIONS_JSON_PATH.exists():
        print("Regions JSON not found.")
        return

    with open(REGIONS_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We'll map these to the entity_registry under 'faction' or 'location' type.
    # Currently schema.md says entity_registry is for "Character, Staff, and Faction".
    # I'll check if a 'location' registry exists or if I should use entity_registry.
    # Looking at schema.md, there's no location_registry listed in table 1. 
    # But it mentions "sub-regional hierarchies" in the implementation plan.
    # I'll assume I should use entity_registry with type='location'.

    location_count = 0
    for region in data:
        rid = f"location:{region.get('id', '')}"
        name = region.get('name', '')
        desc = region.get('description', '')
        history = region.get('history', '')
        
        capital = region.get('capital', '')
        gov = region.get('government', '')
        
        full_notes = f"Capital: {capital}\nGovernment: {gov}\n\n{desc}\n\nHistory: {history}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO entity_registry (
                entity_id, english_display_name, entity_type, notes
            ) VALUES (?, ?, 'location', ?)
        ''', (rid, name, full_notes))
        location_count += 1
                
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {location_count} major geographic regions into the substrate.")

if __name__ == "__main__":
    ingest_geography()
