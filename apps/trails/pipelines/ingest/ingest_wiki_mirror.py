import json
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'en_wiki_mirror_v1.json'

def parse_infobox_value(wikitext, key):
    # Regex to find |key = value in MediaWiki templates
    pattern = rf"\|{key}\s*=\s*(.*)"
    match = re.search(pattern, wikitext, re.IGNORECASE)
    if match:
        return match.group(1).split('<')[0].strip().replace('[[', '').replace(']]', '')
    return None

def ingest_wiki_mirror():
    if not MIRROR_PATH.exists():
        print("Mirror file not found.")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Ingesting {len(mirror)} pages from local mirror...")
    
    ingested_count = 0
    for title, wikitext in mirror.items():
        if not wikitext: continue
        
        # 1. Extract Metadata from Infobox
        ja_name = parse_infobox_value(wikitext, "kanji")
        debut_game = parse_infobox_value(wikitext, "first")
        
        entity_id = f"char:{title.lower().replace(' ', '_').replace('-', '_')}"
        
        # 2. Entity Registry
        cursor.execute('''
            INSERT OR IGNORE INTO entity_registry (
                entity_id, entity_type, english_display_name, japanese_name
            ) VALUES (?, ?, ?, ?)
        ''', (entity_id, "character", title, ja_name))
        
        # 3. Raw Bio Extraction (First Paragraph)
        # Regex to find the first paragraph after the infobox
        # (Simplified: find first text block that doesn't start with | or { or [)
        lines = wikitext.split('\n')
        bio_lines = []
        in_infobox = False
        for line in lines:
            line = line.strip()
            if line.startswith('{{'): in_infobox = True
            if line.endswith('}}'): 
                in_infobox = False
                continue
            if in_infobox: continue
            if line and not any(line.startswith(c) for c in ['|', '{', '[', '*', ':', '==']):
                bio_lines.append(line)
                if len(bio_lines) >= 2: break # Extract first 2 paragraphs
        
        raw_bio = " ".join(bio_lines).replace('[[', '').replace(']]', '')
        
        # 4. Chunk Registry
        if raw_bio:
            chunk_id = f"raw:{entity_id}"
            cursor.execute('''
                INSERT OR REPLACE INTO chunk_registry (
                    chunk_id, source_id, text_content, language, chunk_type, spoiler_band
                ) VALUES (?, 'wiki:en_mirror_v1', ?, 'en', 'bio', 20)
            ''', (chunk_id, raw_bio))
            
        # 5. Appearance Mapping (Initial Debut)
        if debut_game:
            # Simple debut linking
            media_id = debut_game.lower().replace(' ', '_').replace(':', '').replace('trails_in_the_sky_fc', 'sky_fc')
            # (Truncate to known media IDs if possible, or just use the string)
            if len(media_id) > 20: media_id = media_id[:20] 

            cursor.execute('''
                INSERT OR IGNORE INTO appearance_registry (
                    entity_id, media_id, appearance_type, debut_flag
                ) VALUES (?, ?, 'main', 1)
            ''', (entity_id, media_id))
            
        ingested_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {ingested_count} records into the Registry.")

if __name__ == "__main__":
    ingest_wiki_mirror()
