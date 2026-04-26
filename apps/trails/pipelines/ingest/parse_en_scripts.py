import urllib.request
import urllib.parse
import json
import sqlite3
import hashlib
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def hash_id(prefix: str, content: str) -> str:
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hasher.hexdigest()[:10]}"

class ScriptAPIAdapter:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.base_url = 'https://trailsinthedatabase.com/api/script/search/?p={}&q={}'
        
        # Reference mapping from DB's /api/game/
        self.game_map = {
            1: ('sky', 'sky_fc'),
            2: ('sky', 'sky_sc'),
            3: ('sky', 'sky_3rd'),
            4: ('crossbell', 'zero'),
            5: ('crossbell', 'azure'),
            6: ('cold_steel', 'cs1'),
            7: ('cold_steel', 'cs2'),
            8: ('cold_steel', 'cs3'),
            9: ('cold_steel', 'cs4'),
            10: ('daybreak', 'daybreak'),
            11: ('reverie', 'reverie')
        }

    def clean_html(self, text: str) -> str:
        # e.g., "There are enough.<br/>It'd be tough.\x0f"
        text = str(text).replace('<br/>', '\n')
        text = text.replace('\x0f', '') # Control characters
        return text.strip()

    def fetch_and_ingest(self, character: str, max_pages: int = 2):
        cursor = self.conn.cursor()
        
        print(f"Fetching script lines for '{character}'...")
        encoded = urllib.parse.quote(character)
        
        doc_id = f"script:search_{character.lower().replace(' ', '_')}"
        cursor.execute('''
            INSERT OR REPLACE INTO source_documents (doc_id, source_type, path, language)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, "official_script_en", f"api:/{character}", "en"))
        
        chunks_inserted = 0
        for p in range(1, max_pages + 1):
            url = self.base_url.format(p, encoded)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if not data:
                        break # No more pages
                        
                    for row in data:
                        eng_text = self.clean_html(row.get('engHtmlText', row.get('engSearchText', '')))
                        speaker = row.get('engChrName', 'Unknown')
                        game_id = row.get('gameId')
                        
                        if not eng_text:
                            continue
                            
                        arc_tag, game_tag = self.game_map.get(game_id, ('unknown', f'game_{game_id}'))
                        
                        # Formulate a mini-dialogue chunk
                        chunk_text = f"{speaker}: {eng_text}"
                        chunk_id = hash_id("chk", chunk_text)
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text_content, language, arc, game)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (chunk_id, doc_id, chunk_text, "en", arc_tag, game_tag))
                        
                        chunks_inserted += cursor.rowcount
            except Exception as e:
                print(f"Failed to fetch page {p} for '{character}': {e}")
                break
                
            time.sleep(1) # Protect against API rate limits
            
        self.conn.commit()
        print(f"Ingested {chunks_inserted} dialogue chunks for {character}.")

if __name__ == "__main__":
    adapter = ScriptAPIAdapter()
    targets = [
        "Estelle",
        "Joshua",
        "Rean",
        "Lloyd",
        "Van",
        "Renne",
        "Ouroboros"
    ]
    for t in targets:
        # Fetching 5 pages of dialogue per targeted concept (up to 500 lines each)
        adapter.fetch_and_ingest(t, max_pages=5)
