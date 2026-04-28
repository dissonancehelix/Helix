import urllib.request
import urllib.parse
import sqlite3
import hashlib
import re
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def hash_id(prefix: str, content: str) -> str:
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hasher.hexdigest()[:10]}"

def clean_html(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

class SteamGuideAdapter:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)

    def fetch_and_ingest(self, target_url: str):
        cursor = self.conn.cursor()
        print(f"Fetching Steam Guide: {target_url}")
        
        req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try getting the title of the guide
                guide_title_tag = soup.find('div', class_='workshopItemTitle')
                guide_title = guide_title_tag.get_text(strip=True) if guide_title_tag else "Steam Guide"
                doc_id = f"steam:{hash_id('', target_url)}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO source_documents (doc_id, source_type, path, language)
                    VALUES (?, ?, ?, ?)
                ''', (doc_id, "steam_guide_en", target_url, "en"))

                sections = soup.find_all('div', class_='subSection')
                chunks_inserted = 0
                
                for sec in sections:
                    title_tag = sec.find(class_='subSectionTitle')
                    desc_tag = sec.find(class_='subSectionDesc')
                    
                    if not title_tag or not desc_tag:
                        continue
                        
                    header = clean_html(title_tag.get_text())
                    body = clean_html(desc_tag.get_text())
                    
                    if len(body) > 30:
                        chunk_text = f"{header}:\n{body}"
                        chunk_id = hash_id("chk", chunk_text)
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text_content, language)
                            VALUES (?, ?, ?, ?)
                        ''', (chunk_id, doc_id, chunk_text, "en"))
                        
                        chunks_inserted += cursor.rowcount
                
                self.conn.commit()
                print(f"Ingested {chunks_inserted} semantic chunks from Steam Guide '{guide_title}'.")
                
        except Exception as e:
            print(f"Failed to process steam guide {target_url}: {e}")

if __name__ == "__main__":
    adapter = SteamGuideAdapter()
    url = "https://steamcommunity.com/sharedfiles/filedetails/?id=3292491556"
    adapter.fetch_and_ingest(url)
