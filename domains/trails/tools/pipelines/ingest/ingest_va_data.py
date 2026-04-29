import json
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'en_wiki_mirror_v1.json'

def parse_infobox_value(wikitext, key):
    pattern = rf"\|{key}\s*=\s*(.*)"
    match = re.search(pattern, wikitext, re.IGNORECASE)
    if match:
        val = match.group(1).split('<')[0].split('[')[0].strip().replace('[[', '').replace(']]', '')
        return val if val and val.lower() != "none" else None
    return None

def ingest_va_data():
    if not MIRROR_PATH.exists():
        print("Mirror file not found.")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Executing Bulk Voice Actor Ingestion (v17)...")
    
    va_count = 0
    for char_name, wikitext in mirror.items():
        if not wikitext: continue
        
        char_id = f"char:{char_name.lower().replace(' ', '_').replace('-', '_')}"
        
        # Extract JP and EN voices
        jp_va = parse_infobox_value(wikitext, "jpvoice") or parse_infobox_value(wikitext, "seiyuu")
        en_va = parse_infobox_value(wikitext, "envoice")
        
        for va_name, lang in [(jp_va, "jp"), (en_va, "en")]:
            if not va_name: continue
            
            # 1. Ensure Staff Entity exists
            staff_id = f"staff:{va_name.lower().replace(' ', '_').replace('.', '').replace('-', '_')}"
            cursor.execute('''
                INSERT OR IGNORE INTO entity_registry (entity_id, entity_type, english_display_name)
                VALUES (?, 'staff', ?)
            ''', (staff_id, va_name))
            
            # 2. Add 'voiced_by' relationship
            cursor.execute('''
                INSERT OR IGNORE INTO relationship_registry (
                    subject_entity_id, relationship_type, object_id, source_id
                ) VALUES (?, ?, ?, 'wiki:en_mirror_v1')
            ''', (char_id, f"voiced_by_{lang}", staff_id))
            va_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {va_count} Voice Actor relationship nodes.")

if __name__ == "__main__":
    ingest_va_data()
