import json
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = Path(__file__).parent.parent / 'corpus' / 'wiki' / 'en_wiki_mirror_v1.json'

# Faction Detection Rules
FACTION_RULES = [
    ("faction:bracer_guild", ["Bracer Guild", "Bracer"]),
    ("faction:ouroboros", ["Ouroboros", "The Society"]),
    ("faction:septian_church", ["Septian Church", "Gralsritter", "Church"]),
    ("faction:erebonian_army", ["Imperial Army", "RMP", "Thors Military Academy"]),
    ("faction:calvard_intel", ["CID", "Rocksmith Agency"]),
    ("faction:arkride_solutions", ["Arkride Solution Office", "Spriggan"]),
]

def map_factions_bulk():
    if not MIRROR_PATH.exists():
        print("Mirror file not found.")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Executing Bulk Faction Analysis (v18)...")
    
    # 1. Ensure Faction Entities exist
    for faction_id, keywords in FACTION_RULES:
        display_name = faction_id.split(':')[-1].replace('_', ' ').title()
        cursor.execute('''
            INSERT OR IGNORE INTO entity_registry (entity_id, entity_type, english_display_name)
            VALUES (?, 'faction', ?)
        ''', (faction_id, display_name))

    link_count = 0
    for title, wikitext in mirror.items():
        if not wikitext: continue
        
        char_id = f"char:{title.lower().replace(' ', '_').replace('-', '_')}"
        text = wikitext # Keep case sensitive for cleaner matching
        
        # Check for faction mentions
        for faction_id, keywords in FACTION_RULES:
            if any(k in text for k in keywords):
                cursor.execute('''
                    INSERT OR IGNORE INTO relationship_registry (
                        subject_entity_id, relationship_type, object_id, source_id
                    ) VALUES (?, 'member_of', ?, 'wiki:en_mirror_v1')
                ''', (char_id, faction_id))
                
                if cursor.rowcount > 0:
                    link_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Faction analysis complete. {link_count} organizational links established.")

if __name__ == "__main__":
    map_factions_bulk()
