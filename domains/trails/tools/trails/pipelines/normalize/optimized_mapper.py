import sqlite3
import re
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')
WIKI_FILE = Path('corpus/wiki/ja_wiki_characters.html')

def optimized_map():
    if not WIKI_FILE.exists():
        print("Substrate file not found.")
        return

    print("Loading Substrate once (7.4MB)...")
    content = WIKI_FILE.read_text(encoding='utf-8')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Load English Backbone
    cursor.execute("SELECT entity_id, display_name FROM entities WHERE japanese_name IS NULL")
    entities = cursor.fetchall()
    print(f"Entities to map: {len(entities)}")
    
    # 2. Bulk Search Pattern
    # Matches: [JA_NAME] ( [EN_NAME] )
    # Wikipedia patterns: エステル・ブライト（Estelle Bright）、ヨシュア・ブライト (Joshua Bright)
    pattern = re.compile(r'([^\s（(<>]+)[（\(]([A-Za-z\s\'\-]+)[）\)]')
    
    matches = pattern.findall(content)
    print(f"Found {len(matches)} potential JA/EN name pairs in substrate.")
    
    # Create a quick lookup for English names to JA names found
    ja_lookup = {en_name.strip().lower(): ja_name.strip() for ja_name, en_name in matches}
    
    mapped_count = 0
    for entity_id, display_name in entities:
        en_key = display_name.lower()
        if en_key in ja_lookup:
            ja_name = ja_lookup[en_key]
            
            # Clean if it captured some HTML or noise
            ja_name = re.sub(r'<.*?>', '', ja_name)
            
            cursor.execute('''
                UPDATE entities SET japanese_name = ?, creation_status = 'verified'
                WHERE entity_id = ?
            ''', (ja_name, entity_id))
            
            cursor.execute('''
                INSERT OR IGNORE INTO aliases (entity_id, alias, is_official, language)
                VALUES (?, ?, 1, 'ja')
            ''', (entity_id, ja_name))
            
            mapped_count += 1

    conn.commit()
    conn.close()
    print(f"Finished Optimized Mapping: {mapped_count} Japanese names resolved.")

if __name__ == "__main__":
    optimized_map()
