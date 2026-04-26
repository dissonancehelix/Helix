import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

def clean_wikitext(text):
    if not text: return ""
    
    # 1. Strip Templates {{...}} - Handle nested braces by iterating
    while '{{' in text:
        text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    
    # 2. Resolve Links [[Link|Text]] -> Text, [[Link]] -> Link
    text = re.sub(r'\[\[[^|\]]+\|([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    
    # 3. Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 4. Strip leftover MediaWiki artifacts (References, files)
    text = re.sub(r'\[http[^\]\s]+(\s[^\]]+)?\]', '', text) # [url text]
    
    # 5. Normalize whitespace and remove common wiki "Main" references
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('Main article: ', '')
    
    return text.strip()

def run_cleaning_pass():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Executing Bulk Wikitext Cleaning Pass (v16)...")
    
    # Fetch all raw bio chunks
    cursor.execute('''
        SELECT chunk_id, text_content 
        FROM chunk_registry 
        WHERE source_id = 'wiki:en_mirror_v1' AND chunk_type = 'bio'
    ''')
    rows = cursor.fetchall()
    
    cleaned_count = 0
    for row in rows:
        raw_id = row[0]
        raw_text = row[1]
        
        cleaned_text = clean_wikitext(raw_text)
        
        if cleaned_text:
            # Upsert into chunk_registry as 'clean' chunks
            clean_id = raw_id.replace('raw:', 'clean:')
            cursor.execute('''
                INSERT OR REPLACE INTO chunk_registry (
                    chunk_id, source_id, text_content, language, chunk_type, spoiler_band
                ) VALUES (?, 'system:cleaner_v16', ?, 'en', 'clean_bio', 20)
            ''', (clean_id, cleaned_text))
            cleaned_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Cleaned {cleaned_count} biographies. Brackets and templates removed.")

if __name__ == "__main__":
    run_cleaning_pass()
