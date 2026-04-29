import os
import json
import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'
MIRROR_DIR = ROOT / 'corpus' / 'tvtropes'

SOURCE_ID = 'tvtropes:en_manual_clone_v1'
SOURCE_TITLE = 'TV Tropes — Trails Series (Manual SingleFile Clone)'
SOURCE_URL = 'https://tvtropes.org/pmwiki/pmwiki.php/Characters/TrailsSeries'

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s[:80]

def parse_tvtropes():
    if not MIRROR_DIR.exists():
        print(f"Directory not found: {MIRROR_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Register Source
    cursor.execute('''
        INSERT OR REPLACE INTO source_registry (
            source_id, title, source_class, language, origin_url, trust_tier
        ) VALUES (?, ?, 'fan_wiki', 'en', ?, 3)
    ''', (SOURCE_ID, SOURCE_TITLE, SOURCE_URL))

    # 2. Load characters for matching
    cursor.execute('SELECT entity_id, english_display_name FROM entity_registry WHERE entity_type = "character"')
    char_rows = cursor.fetchall()
    
    name_to_id = {}
    for eid, display_name in char_rows:
        name_to_id[display_name.lower()] = eid
        parts = display_name.split(' ')
        if len(parts) > 1 and len(parts[0]) > 3:
            # Only add shorthand if it doesn't collide or is a known unique first name
            fn = parts[0].lower()
            if fn not in name_to_id:
                name_to_id[fn] = eid

    # Pre-compile the massive regex
    sorted_names = sorted(name_to_id.keys(), key=len, reverse=True)
    # Be careful with regex size; if too big, split or use dict
    pattern_str = rf"^({'|'.join(re.escape(n) for n in sorted_names)})(?:\s*[:\-–—\.]|\s|$)"
    name_regex = re.compile(pattern_str, re.IGNORECASE)

    print(f"Prepared optimized regex for {len(name_to_id)} names.")

    total_chunks_inserted = 0
    matched_chars = set()

    # 3. Iterate through all HTML files
    html_files = list(MIRROR_DIR.glob('*.html'))
    print(f"Parsing {len(html_files)} HTML files...")

    for html_file in html_files:
        print(f" -> Processing: {html_file.name}")
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Remove boilerplate
        for trash in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            trash.decompose()

        # Iterate through elements
        for elem in soup.find_all(['li', 'p', 'h1', 'h2', 'h3']):
            content = elem.get_text().strip()
            if not content:
                continue

            m = name_regex.match(content)
            if m:
                matched_name = m.group(1).lower()
                matched_id = name_to_id.get(matched_name)
                
                if matched_id:
                    chunk_text = ""
                    if elem.name in ['h1', 'h2', 'h3']:
                        parts = []
                        for sibling in elem.find_next_siblings():
                            if sibling.name in ['h1', 'h2', 'h3']:
                                break
                            parts.append(sibling.get_text())
                        chunk_text = "\n".join(parts)
                    else:
                        chunk_text = content
                    
                    if len(chunk_text) > 40:
                        clean_chunk = clean_text(chunk_text)
                        chunk_id = f"tropes:{matched_id}:{slugify(html_file.stem[:15])}"
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO chunk_registry (
                                chunk_id, source_id, linked_entity_ids, text_content, language, chunk_type, spoiler_band
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (chunk_id, SOURCE_ID, json.dumps([matched_id]), clean_chunk, 'en', 'character_tropes', 50))
                        
                        total_chunks_inserted += 1
                        matched_chars.add(matched_id)

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] TV Tropes ingestion complete.")
    print(f" -> Unique Characters Matched: {len(matched_chars)}")
    print(f" -> Trope Chunks Ingested: {total_chunks_inserted}")

if __name__ == '__main__':
    parse_tvtropes()
