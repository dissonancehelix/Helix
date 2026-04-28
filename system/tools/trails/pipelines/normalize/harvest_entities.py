import urllib.request
import json
import urllib.parse
import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def clean_name(name):
    return re.sub(r'\(.*?\)', '', name).strip()

class EntityHarvester:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)

    def get_category_members(self, wiki, category):
        members = []
        cmcontinue = ''
        while True:
            url = f'https://{wiki}.fandom.com/api.php?action=query&list=categorymembers&cmtitle={urllib.parse.quote(category)}&cmlimit=500&format=json&cmcontinue={cmcontinue}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    members.extend([m['title'] for m in data['query']['categorymembers']])
                    if 'continue' in data:
                        cmcontinue = data['continue']['cmcontinue']
                    else:
                        break
            except:
                break
        return members

    def harvest_all_characters(self):
        print("Harvesting character names from Kiseki Fandom...")
        source_id = "wiki:kiseki_fandom"
        
        # 1. Start with the main category
        all_chars = set(self.get_category_members('kiseki', 'Category:Characters'))
        
        # 2. Add subcategories for better coverage
        subcats = ['Category:Liberl_Characters', 'Category:Crossbell_Characters', 'Category:Erebonia_Characters', 'Category:Calvard_Characters', 'Category:Ouroboros_Members']
        for cat in subcats:
            print(f"Harvesting {cat}...")
            all_chars.update(self.get_category_members('kiseki', cat))

        print(f"Total unique names collected: {len(all_chars)}")
        
        cursor = self.conn.cursor()
        inserted_count = 0
        
        for name in all_chars:
            if name.startswith('Category:'): continue
            
            clean = clean_name(name)
            entity_id = f"char:{clean.lower().replace(' ', '_')}"
            
            # Tier 2 for Fandom Wiki
            cursor.execute('''
                INSERT OR IGNORE INTO entities (entity_id, type, display_name, trust_tier, creation_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (entity_id, "character", clean, 2, 'draft'))
            
            cursor.execute('''
                INSERT OR IGNORE INTO aliases (entity_id, alias, is_official, language)
                VALUES (?, ?, ?, ?)
            ''', (entity_id, clean, 0, 'en'))
            
            inserted_count += cursor.rowcount
            
        self.conn.commit()
        print(f"Successfully integrated {inserted_count} character entities into the backbone.")

if __name__ == "__main__":
    harvester = EntityHarvester()
    harvester.harvest_all_characters()
