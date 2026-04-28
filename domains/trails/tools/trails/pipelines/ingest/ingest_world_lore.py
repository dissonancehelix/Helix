import json
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'en_wiki_lore_mirror_v1.json'

def parse_infobox_value(wikitext, key):
    # Regex to find |key = value in MediaWiki templates
    pattern = rf"\|{key}\s*=\s*(.*)"
    match = re.search(pattern, wikitext, re.IGNORECASE)
    if match:
        return match.group(1).split('<')[0].strip().replace('[[', '').replace(']]', '')
    return None

def extract_entity_type(wikitext):
    if '{{Infobox location' in wikitext or '{{Infobox Location' in wikitext:
        return 'location'
    elif '{{Infobox organization' in wikitext or '{{Infobox Organization' in wikitext:
        return 'faction'
    elif '{{Infobox event' in wikitext or '{{Infobox Event' in wikitext:
        return 'event'
    elif '{{Infobox weapon' in wikitext or '{{Infobox item' in wikitext:
        return 'item'
    elif '{{Infobox Lore' in wikitext or '{{Infobox Term' in wikitext or '{{Infobox concept' in wikitext:
        return 'concept'
    return 'concept' # default fallback for other terms

def ingest_world_lore():
    if not MIRROR_PATH.exists():
        print(f"Mirror file not found at {MIRROR_PATH}. Please run the crawler first.")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Ingesting {len(mirror)} Lore pages into Database...")
    
    ingested_count = 0
    for title, wikitext in mirror.items():
        if not wikitext: continue
        
        # 1. Determine entity type
        entity_type = extract_entity_type(wikitext)
        
        # 2. Extract Metadata from Infobox
        ja_name = parse_infobox_value(wikitext, "kanji")
        debut_game = parse_infobox_value(wikitext, "first")
        
        entity_id = f"lore:{title.lower().replace(' ', '_').replace('-', '_')}"
        
        # 3. Entity Registry
        cursor.execute('''
            INSERT OR IGNORE INTO entity_registry (
                entity_id, entity_type, english_display_name, japanese_name
            ) VALUES (?, ?, ?, ?)
        ''', (entity_id, entity_type, title, ja_name))
        
        # 4. Raw Bios Extraction (First 2 Paragraphs)
        lines = wikitext.split('\n')
        bio_lines = []
        in_infobox = False
        for line in lines:
            line = line.strip()
            # Handle standard infoboxes, quotations, etc
            if line.startswith('{{'): in_infobox = True
            
            # Simple check for infobox ending based on closing brackets.
            # (Note: robust wikitext parsing is complex, this is a heuristic).
            if line.startswith('}}'): 
                in_infobox = False
                continue
                
            if in_infobox: 
                # basic handle for nesting if it closes on same line
                if line.endswith('}}') and not line.startswith('{{'):
                    in_infobox = False
                continue
                
            if line and not any(line.startswith(c) for c in ['|', '{', '[', '*', ':', '==', ';']):
                bio_lines.append(line)
                if len(bio_lines) >= 2: break # Extract first 2 paragraphs
        
        raw_bio = " ".join(bio_lines)
        # Strip simple links
        raw_bio = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', raw_bio)
        # Strip some common templates that slipped through
        raw_bio = re.sub(r'\{\{[^}]+\}\}', '', raw_bio)

        
        # 5. Chunk Registry
        if raw_bio:
            chunk_id = f"raw:{entity_id}"
            cursor.execute('''
                INSERT OR REPLACE INTO chunk_registry (
                    chunk_id, source_id, text_content, language, chunk_type, spoiler_band
                ) VALUES (?, 'wiki:en_lore_mirror_v1', ?, 'en', 'bio', 20)
            ''', (chunk_id, raw_bio))
            
        # 6. Appearance Mapping (Initial Debut)
        if debut_game:
            media_id = debut_game.lower().replace(' ', '_').replace(':', '').replace('trails_in_the_sky_fc', 'sky_fc')
            if len(media_id) > 20: media_id = media_id[:20] 

            cursor.execute('''
                INSERT OR IGNORE INTO appearance_registry (
                    entity_id, media_id, appearance_type, debut_flag
                ) VALUES (?, ?, 'main', 1)
            ''', (entity_id, media_id))
            
        ingested_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {ingested_count} World Lore records into the Registry.")

if __name__ == "__main__":
    ingest_world_lore()
