import json
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = Path(__file__).parent.parent / 'corpus' / 'wiki' / 'en_wiki_mirror_v1.json'

# Arc Detection Keywords
ARC_RULES = [
    ("sky", ["sky", "liberl", "cassius"]),
    ("crossbell", ["zero", "azure", "crossbell", "lloyd"]),
    ("erebonia", ["cold steel", "cs1", "cs2", "cs3", "cs4", "reverie", "erebonia", "rean"]),
    ("calvard", ["daybreak", "kuro", "calvard", "van", "kai"]),
    ("nayuta", ["nayuta", "boundless"]),
]

def map_arcs_bulk():
    if not MIRROR_PATH.exists():
        print("Mirror file not found.")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Executing Deep Arc Analysis (v17)...")
    
    mapped_count = 0
    for title, wikitext in mirror.items():
        if not wikitext: continue
        
        entity_id = f"char:{title.lower().replace(' ', '_').replace('-', '_')}"
        text = wikitext.lower()
        
        detected_arc = None
        
        # Heuristic 1: Scan for protagonist/region mentions in wikitext
        for arc, keywords in ARC_RULES:
            if any(k in text for k in keywords):
                detected_arc = arc
                break
        
        if detected_arc:
            # Update entity_registry with arc metadata in a structured way
            # We use the 'aliases' or a dedicated 'notes' field for now
            # Best practice: update the 'aliases' field to include the arc if not already there
            cursor.execute('''
                UPDATE entity_registry 
                SET aliases = COALESCE(aliases || ', ', '') || ? 
                WHERE entity_id = ? AND (aliases NOT LIKE ? OR aliases IS NULL)
            ''', (f"arc:{detected_arc}", entity_id, f"%arc:{detected_arc}%"))
            mapped_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Deep Arc Analysis complete. {mapped_count} entities tagged with arc metadata.")

if __name__ == "__main__":
    map_arcs_bulk()
