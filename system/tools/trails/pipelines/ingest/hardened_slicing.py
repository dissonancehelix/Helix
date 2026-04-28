import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
SUBSTRATE_PATH = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'ja_wiki_characters.html'

def hardened_slicing_v2():
    if not SUBSTRATE_PATH.exists():
        print("Substrate file not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Loading Substrate with BeautifulSoup (This may take a moment for 7.4MB)...")
    content = SUBSTRATE_PATH.read_text(encoding='utf-8')
    soup = BeautifulSoup(content, 'html.parser')

    # Strategy: Find all text segments that look like "Name（Romanization）"
    # Or find all <li> and <td> elements.
    
    print("Slicing text nodes...")
    resolved_count = 0
    
    # Pattern: [JA_NAME]（[EN_NAME]） or [JA_NAME] ( [EN_NAME] )
    pattern = re.compile(r'([^\s（(<>]+)[（\(]([A-Za-z\s\'\-.]{3,})[）\)]')

    for element in soup.find_all(['li', 'td', 'p']):
        text = element.get_text()
        matches = pattern.findall(text)
        
        for ja_name, en_name in matches:
            en_name = en_name.strip()
            entity_id = f"char:{en_name.lower().replace(' ', '_').replace('-', '_')}"
            
            # Entity Registry
            cursor.execute('''
                INSERT OR IGNORE INTO entity_registry (
                    entity_id, entity_type, english_display_name, japanese_name
                ) VALUES (?, ?, ?, ?)
            ''', (entity_id, "character", en_name, ja_name))
            
            # Appearance Registry (Initial Mapping)
            cursor.execute('''
                INSERT OR IGNORE INTO appearance_registry (
                    entity_id, media_id, appearance_type, debut_flag
                ) VALUES (?, 'sky_fc', 'support', 1)
            ''', (entity_id,))
            
            resolved_count += 1

    conn.commit()
    conn.close()
    print(f"Hardened Slicing V2 Complete: {resolved_count} records processed.")

if __name__ == "__main__":
    hardened_slicing_v2()
