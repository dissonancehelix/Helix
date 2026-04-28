import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def hash_id(prefix: str, content: str) -> str:
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hasher.hexdigest()[:10]}"

class NullScriptAdapter:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
    
    def ingest_mock_script(self):
        cursor = self.conn.cursor()
        
        # MOCK SCRIPT INPUT
        doc_id = "script:sky_fc:t0100"
        
        # 1. Source Document
        cursor.execute('''
            INSERT OR REPLACE INTO source_documents (doc_id, source_type, path, language)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, "official_script", "corpus/scripts/fc/t0100.txt", "en"))
        
        lines = [
            "Estelle: Hey, Joshua! Get over here!",
            "Joshua: I'm coming, I'm coming. No need to yell.",
            "Estelle: We've got our first Bracer request. We need to clear the Perzel Farm."
        ]
        
        # 2. Extract into Chunks
        # In a real script, we would window this to keep context together.
        chunk_text = "\n".join(lines)
        chunk_id = hash_id("chk", chunk_text)
        
        cursor.execute('''
            INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text_content, language, arc, game, chapter_band)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chunk_id, doc_id, chunk_text, "en", "sky", "sky_fc", "prologue"))
        
        self.conn.commit()
        print(f"Ingested mock script chunks for {doc_id}")

if __name__ == "__main__":
    adapter = NullScriptAdapter()
    adapter.ingest_mock_script()
