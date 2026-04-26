import json
import sqlite3
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup
import re

DB_PATH = Path('retrieval/index/trails.db')
BOOKS_JSON_PATH = Path('corpus/github/kiseki-books-main/src/lib/bookmaker/kiseki-books-full.json')

def hash_id(prefix: str, content: str) -> str:
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}:{hasher.hexdigest()[:12]}"

def clean_html(html: str) -> str:
    if not html: return ""
    soup = BeautifulSoup(html, 'html.parser')
    # Remove figure captions and other fluff if needed
    return soup.get_text(separator='\n').strip()

def ingest_books():
    if not BOOKS_JSON_PATH.exists():
        print("Books JSON not found.")
        return

    with open(BOOKS_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    chunk_count = 0
    for game_category in data:
        game_title = game_category.get('title', 'Unknown Media')
        print(f"Processing books for: {game_title}")
        
        for series in game_category.get('series', []):
            series_title = series.get('title', 'Unknown Series')
            
            for book in series.get('books', []):
                chapter_title = book.get('title', 'Unknown Chapter')
                content_en = book.get('text_en', '')
                
                if not content_en: continue
                
                clean_content = clean_html(content_en)
                if len(clean_content) < 50: continue
                
                # Create a lore chunk
                chunk_id = hash_id("lore", f"{series_title} {chapter_title} {game_title}")
                source_id = f"lore_book:{series.get('slug', 'generic')}"
                
                cursor.execute('''
                    INSERT OR IGNORE INTO chunk_registry (
                        chunk_id, source_id, text_content, language, chunk_type, spoiler_band
                    ) VALUES (?, ?, ?, 'en', 'lore_book', 10)
                ''', (chunk_id, source_id, f"[{series_title}: {chapter_title}]\n{clean_content}"))
                chunk_count += 1
                
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {chunk_count} book chunks into the substrate.")

if __name__ == "__main__":
    ingest_books()
