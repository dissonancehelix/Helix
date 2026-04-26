import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
WIKI_FILE = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'ja_wiki_characters.html'

class JaWikiParser:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def parse_and_ingest(self):
        if not WIKI_FILE.exists():
            print(f"Substrate file {WIKI_FILE} not found.")
            return

        print(f"Loading Substrate (7.4MB)...")
        with open(WIKI_FILE, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Wikipedia list items often contain the character name in bold (<b>)
        # and then the description follows.
        list_items = soup.find_all('li')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        source_id = "wiki:ja_wikipedia_chars"
        count = 0
        mapped_count = 0
        
        for item in list_items:
            # Most character entries start with <b>[Name]</b>
            bold_el = item.find('b', recursive=False)
            if not bold_el:
                # Fallback: check if the first child is a bold element or link
                first_child = next(item.children, None)
                if first_child and first_child.name == 'b':
                    bold_el = first_child

            if not bold_el: continue
            
            name_ja = bold_el.get_text(strip=True)
            if len(name_ja) < 2 or len(name_ja) > 30 or any(c in name_ja for c in '〔〕()'):
                continue

            full_text = item.get_text(strip=True)
            # Remove wikipedia references [1], [注 1] etc.
            full_text = re.sub(r'\[.*?\]', '', full_text)
            
            # The description logic: text after the name
            if len(full_text) < 50: continue

            chunk_id = f"chk_ja_wiki_v2_{count}"
            
            # Ingest as high-trust encyclopedic substrate
            cursor.execute('''
                INSERT OR REPLACE INTO chunks (chunk_id, source_id, text_content, original_text, language, trust_tier, quality_tone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (chunk_id, source_id, full_text, full_text, 'ja', 1, 'encyclopedic'))
            
            # Attempt to map to the English Backbone
            # We look for the Japanese identity in the aliases table
            cursor.execute('''
                UPDATE entities SET japanese_name = ?, creation_status = 'verified'
                WHERE (entity_id IN (SELECT entity_id FROM aliases WHERE alias = ?))
                AND (japanese_name IS NULL OR japanese_name = ?)
            ''', (name_ja, name_ja, name_ja))
            
            if cursor.rowcount > 0:
                mapped_count += 1

            count += 1
            if count % 100 == 0:
                print(f"Processed {count} entries...")

        conn.commit()
        conn.close()
        print(f"Ingestion Finished: {count} encyclopedic records found. {mapped_count} successfully mapped to Backbone.")

if __name__ == "__main__":
    # Ensure schema has quality_tone column
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('ALTER TABLE chunks ADD COLUMN quality_tone TEXT')
    except:
        pass
    conn.close()

    parser = JaWikiParser()
    parser.parse_and_ingest()
