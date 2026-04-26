import csv
import sqlite3
import re
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')
RAW_DIR = Path('corpus/raw')

def ingest_csv_media():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    csv_files = {
        "Companion Books": "List of Trails Media - Companion Books.csv",
        "Drama CDs": "List of Trails Media - Drama CDs.csv",
        "Light Novels": "List of Trails Media - Light Novels.csv"
    }

    media_count = 0
    for category, filename in csv_files.items():
        file_path = RAW_DIR / filename
        if not file_path.exists():
            print(f"Skipping {category}: {filename} not found.")
            continue
            
        print(f"Processing category: {category}")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Find the header row (sometimes there's junk at the top)
            headers = next(reader)
            
            for row in reader:
                if not row or not row[0]: continue
                title = row[0].strip()
                if title.lower() in ['title', 'index']: continue
                
                # Simple ID generation
                mid = title.lower().replace(' ', '_').replace(':', '').replace('!', '').replace("'", "")
                mid = re.sub(r'[^a-zA-Z0-9_]', '', mid)[:50]
                
                # Determine type
                mtype = category.lower().replace(' ', '_')
                
                # Get notes if available
                notes = row[1] if len(row) > 1 else ""
                
                cursor.execute('''
                    INSERT OR IGNORE INTO media_registry (
                        media_id, media_type, english_title, canonical_notes, is_main_series
                    ) VALUES (?, ?, ?, ?, 0)
                ''', (mid, mtype, title, notes))
                media_count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {media_count} media entries from CSV library.")

if __name__ == "__main__":
    ingest_csv_media()
