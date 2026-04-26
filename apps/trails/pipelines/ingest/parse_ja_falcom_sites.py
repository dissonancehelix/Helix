import asyncio
import aiohttp
import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

class FalcomJAScraper:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.sem = asyncio.Semaphore(5) # Limit concurrency to be polite

    async def fetch_page(self, session, url):
        async with self.sem:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        return None

    def parse_bio(self, html, mode="kuro"):
        soup = BeautifulSoup(html, 'html.parser')
        
        name_ja = ""
        name_en_label = ""
        quote_ja = ""
        bio_ja = ""

        if mode == "kuro":
            main = soup.select_one('main#individual') or soup
            name_el = main.select_one('h1')
            name_ja = name_el.get_text(strip=True) if name_el else ""
            
            name_en_el = main.select_one('.large-name')
            name_en_label = name_en_el.get_text(strip=True) if name_en_el else ""
            
            quote_els = main.select('.serif .wrap') or main.select('.serif p')
            quote_ja = " / ".join([q.get_text(strip=True) for q in quote_els])
            
            bio_el = main.select_one('.desc')
            if bio_el:
                bio_ja = "\n\n".join([p.get_text(strip=True) for p in bio_el.find_all('p')])
        
        else: # Kai Mode
            main = soup.select_one('main.character') or soup
            name_el = main.select_one('h1.name')
            name_ja = name_el.get_text(strip=True) if name_el else ""
            
            name_en_el = main.select_one('div.spell')
            name_en_label = name_en_el.get_text(strip=True) if name_en_el else ""
            
            quote_els = main.select('.serif p') or main.select('.serif')
            quote_ja = " / ".join([q.get_text(strip=True) for q in quote_els if q.get_text(strip=True)])
            
            bio_el = main.select_one('.character-single-description')
            if bio_el:
                bio_ja = "\n\n".join([p.get_text(strip=True) for p in bio_el.find_all('p')])

        return name_ja, name_en_label, quote_ja, bio_ja

    async def ingest_character(self, session, slug, game_id, source_id, spoiler_tier):
        game_path = "kuro" if game_id == "Daybreak" else "kai"
        url = f"https://www.falcom.co.jp/{game_path}/character/{slug}.html"
        
        html = await self.fetch_page(session, url)
        if not html:
            return

        mode = "kuro" if game_id == "Daybreak" else "kai"
        name_ja, name_en_label, quote_ja, bio_ja = self.parse_bio(html, mode)
        if not bio_ja:
            print(f"Skipping {slug} ({game_id}) - No bio content found at {url}")
            return

        chunk_id = f"chk_falcom_ja_{game_path}_{slug}"
        text = f"Official Japanese Bio - {name_ja} ({name_en_label})\nQuote: {quote_ja}\n\n{bio_ja}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ingest as Substrate (Original Text)
        cursor.execute('''
            INSERT OR REPLACE INTO chunks (chunk_id, source_id, text_content, original_text, language, game, trust_tier, spoiler_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chunk_id, source_id, text, text, 'ja', game_id, 0, spoiler_tier))
        
        # Update Entity Table Japanese Name and Aliases if we find a match
        # Match by official EN name from site if possible
        if name_en_label:
            cursor.execute('''
                UPDATE entities SET japanese_name = ? 
                WHERE (display_name COLLATE NOCASE = ? OR entity_id LIKE ?) AND japanese_name IS NULL
            ''', (name_ja, name_en_label, f"%{slug}%"))
            
            # Add Japanese alias
            cursor.execute('''
                INSERT OR IGNORE INTO aliases (entity_id, alias, is_official, language)
                SELECT entity_id, ?, 1, 'ja' FROM entities WHERE display_name COLLATE NOCASE = ?
            ''', (name_ja, name_en_label))

        conn.commit()
        conn.close()
        print(f"Ingested JA Bio: {name_ja} ({game_id}) - Mapped via: {name_en_label or slug}")

    async def run(self):
        # Configuration
        targets = [
            # Daybreak I/II (Safe-ish)
            {"game": "Daybreak", "source": "official:falcom_kuro_bios", "spoiler": 20, "slugs": ["van", "agnes", "ferie", "aaron", "risette", "quatre", "judith", "bergard"]},
            # Beyond the Horizon (LOCKED)
            {"game": "Beyond the Horizon", "source": "official:falcom_kai_bios", "spoiler": 100, "slugs": ["van", "agnes", "ferie", "aaron", "risette", "quatre", "judith", "bergard", "reane", "kevin", "rufus"]}
        ]

        async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
            tasks = []
            for t in targets:
                for slug in t["slugs"]:
                    tasks.append(self.ingest_character(session, slug, t["game"], t["source"], t["spoiler"]))
            
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    scraper = FalcomJAScraper()
    asyncio.run(scraper.run())
