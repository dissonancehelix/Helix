import json
import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def hash_id(prefix: str, content: str) -> str:
    """Generate a stable chunk ID"""
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hasher.hexdigest()[:10]}"

class NullWikiAdapter:
    """
    A foundational adapter for transforming structured wiki data into 
    the local DB schema. Mocks pulling JSON extracts.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
    
    def ingest_mock_character(self):
        cursor = self.conn.cursor()
        
        # MOCK WIKI INPUT
        wiki_payload = {
            "title": "Estelle Bright",
            "japanese": "エステル・ブライト",
            "aliases": ["Sun", "Cassius's Daughter"],
            "affiliations": ["Bracer Guild"],
            "bio": "Estelle Bright is the main protagonist of the Trails in the Sky arc. Originally from Rolent, she becomes a senior Bracer.",
            "games": ["fc", "sc", "the_3rd", "zero", "ao", "cs4", "reverie"]
        }
        
        entity_id = "char:estelle_bright"
        
        # 1. Normalize and Insert Entity
        cursor.execute('''
            INSERT OR REPLACE INTO entities (entity_id, type, display_name, japanese_name, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (entity_id, "character", wiki_payload["title"], wiki_payload["japanese"], "Protagonist of Sky Arc"))
        
        # 2. Insert Aliases
        cursor.execute("DELETE FROM aliases WHERE entity_id = ?", (entity_id,))
        for alias in wiki_payload["aliases"]:
            cursor.execute('''
                INSERT INTO aliases (entity_id, alias) VALUES (?, ?)
            ''', (entity_id, alias))
            
        # 3. Create Source Document Entry
        doc_id = "wiki:estelle_bright"
        cursor.execute('''
            INSERT OR REPLACE INTO source_documents (doc_id, source_type, path, language)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, "fan_wiki", "corpus/wiki/estelle_bright.json", "en"))
        
        # 4. Extract text to chunk and insert to DB (Retrieval Layer)
        chunk_id = hash_id("chk", wiki_payload["bio"])
        cursor.execute('''
            INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text_content, language, arc, game)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chunk_id, doc_id, wiki_payload["bio"], "en", "sky", "sky_fc"))
        
        self.conn.commit()
        print(f"Ingested mock wiki data for {entity_id}")

if __name__ == "__main__":
    adapter = NullWikiAdapter()
    adapter.ingest_mock_character()
