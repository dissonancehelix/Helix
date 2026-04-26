import urllib.request
import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

class NISAmericaAdapter:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)

    def fetch_and_parse_char(self, slug: str, game_title: str):
        url = f"https://thelegendofheroes.com/daybreak/characters/{slug}"
        print(f"Fetching Official Bio for {slug}: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')
                
                name_el = soup.find('h1', class_='character-name_accent')
                name = name_el.get_text(strip=True) if name_el else slug.capitalize()
                
                quote_el = soup.find('h3', class_='character-phrase')
                quote = quote_el.get_text(strip=True) if quote_el else ""
                
                info_container = soup.find('div', class_='character-info')
                bios = []
                if info_container:
                    bios = [p.get_text(strip=True) for p in info_container.find_all('p', recursive=False)]
                
                full_bio = f"Official Quote: {quote}\n\n" + "\n\n".join(bios)
                
                if len(full_bio) > 20:
                    cursor = self.conn.cursor()
                    doc_id = f"official:nisa_daybreak_{slug}"
                    cursor.execute('''
                        INSERT OR REPLACE INTO source_documents (doc_id, source_type, path, language, trust_tier)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (doc_id, "official_site_en", url, "en", 0))

                    chunk_id = f"chk_nisa_day_{slug}"
                    cursor.execute('''
                        INSERT OR REPLACE INTO chunks (chunk_id, doc_id, text_content, language, game, trust_tier)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (chunk_id, doc_id, f"Official Bio - {name}\n\n{full_bio}", "en", game_title, 0))
                    
                    self.conn.commit()
                    return True
        except Exception as e:
            print(f"Failed to fetch {slug}: {e}")
            return False

    def harvest_all(self):
        # Initial character slugs for Daybreak coverage
        slugs = ["van", "agnes", "ferie", "aaron", "risette", "quatre", "judith", "bergard"]
        count = 0
        for s in slugs:
            if self.fetch_and_parse_char(s, "Trails through Daybreak"):
                count += 1
        print(f"Successfully ingested {count} official character records.")

if __name__ == "__main__":
    adapter = NISAmericaAdapter()
    adapter.harvest_all()
