import sqlite3
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup
import re

DB_PATH = Path('retrieval/index/trails.db')
WIKI_PATH = Path('corpus/raw/英雄傳說 軌跡系列 - Wikipedia.html')

def hash_id(prefix: str, content: str) -> str:
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}:{hasher.hexdigest()[:12]}"

def clean_text(text: str) -> str:
    text = re.sub(r'\[\d+\]', '', text) # Remove wiki reference numbers
    return " ".join(text.split())

def parse_zh_wikipedia():
    if not WIKI_PATH.exists():
        print("Chinese Wiki file not found.")
        return

    with open(WIKI_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    source_id = "wiki:zh_kiseki"
    
    # 1. Source Registry
    cursor.execute('''
        INSERT OR REPLACE INTO source_registry (
            source_id, title, source_class, language, local_path, trust_tier
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (source_id, "Trails Chinese Wikipedia", "wikipedia_zh", "zh", str(WIKI_PATH), 2))
    
    # 2. Extract Media Table (Release Order)
    # The Chinese Wiki has a 媒体列表 (Media List) section.
    content_div = soup.find(id='mw-content-text')
    
    # We'll specifically look for the "Media" tables which usually have release counts and arc info
    media_count = 0
    for table in content_div.find_all('table', class_='wikitable'):
        headers = [th.get_text().strip() for th in table.find_all('th')]
        if '作品名稱' in str(headers) or '標題' in str(headers):
            print(f"Found media table. Parsing...")
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    zh_title = cols[0].get_text().strip()
                    # Release date is often present
                    cursor.execute('''
                        INSERT OR IGNORE INTO media_registry (
                            media_id, english_title, japanese_title, media_type
                        ) VALUES (?, ?, ?, 'game')
                    ''', (hash_id("media", zh_title), zh_title, zh_title))
                    media_count += 1
            
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {media_count} media references from Chinese Wiki.")

if __name__ == "__main__":
    parse_zh_wikipedia()
