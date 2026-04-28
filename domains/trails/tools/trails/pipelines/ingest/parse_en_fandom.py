import urllib.request
import urllib.parse
import json
import sqlite3
import hashlib
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def hash_id(prefix: str, content: str) -> str:
    hasher = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hasher.hexdigest()[:10]}"

def clean_wikitext(text: str) -> str:
    # Very basic wikitext cleanup
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text) # Remove [[Link|Text]]
    text = re.sub(r'{{(?:[^{}]*\|)?([^}]+)}}', r'\1', text) # Very naive template sweep
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL) # Remove refs
    text = re.sub(r'<[^>]+>', '', text) # Remove html tags
    text = re.sub(r"''+", "", text) # Remove bold/italics
    lines = text.split('\n')
    cleaned = [l.strip() for l in lines if l.strip() and not l.strip().startswith(('|', '{', '}', '==='))]
    return " ".join(cleaned)

class MediaWikiAPIAdapter:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)

    def fetch_and_ingest(self, titles: list, api_url: str, source_label: str):
        cursor = self.conn.cursor()
        
        for title in titles:
            print(f"Fetching {title} from {source_label}...")
            encoded_title = urllib.parse.quote(title)
            url = f"{api_url}&titles={encoded_title}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    pages = data['query']['pages']
                    page_id = list(pages.keys())[0]
                    
                    if page_id == "-1":
                        print(f"Page '{title}' not found on {source_label}.")
                        continue
                        
                    content = pages[page_id]['revisions'][0]['slots']['main']['*']
            except Exception as e:
                print(f"Failed to fetch '{title}' on {source_label}: {e}")
                continue

            # Ingest Document
            doc_id = f"wiki:{source_label}_{title.lower()}"
            cursor.execute('''
                INSERT OR REPLACE INTO source_documents (doc_id, source_type, path, language)
                VALUES (?, ?, ?, ?)
            ''', (doc_id, f"wiki_en_{source_label}", f"api:/{source_label}/{title}", "en"))
            
            # Split wikitext roughly by == Headers ==
            sections = re.split(r'==\s*([^=]+)\s*==', content)
            
            # sections[0] is the intro
            intro_text = clean_wikitext(sections[0])
            if len(intro_text) > 30:
                chunk_id = hash_id("chk", intro_text)
                cursor.execute('''
                    INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text_content, language)
                    VALUES (?, ?, ?, ?)
                ''', (chunk_id, doc_id, f"Intro:\n{intro_text}", "en"))
            
            chunks_inserted = 1
            # Next parts are header, text
            for i in range(1, len(sections)-1, 2):
                header = sections[i].strip()
                body = clean_wikitext(sections[i+1])
                
                # Ignore irrelevant sections
                if header.lower() in ['gallery', 'trivia', 'quotes', 'references', 'external links', 'navigation']:
                    continue
                    
                if len(body) > 30:
                    chunk_text = f"{header}:\n{body}"
                    chunk_id = hash_id("chk", chunk_text)
                    cursor.execute('''
                        INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text_content, language)
                        VALUES (?, ?, ?, ?)
                    ''', (chunk_id, doc_id, chunk_text, "en"))
                    chunks_inserted += 1
            
            self.conn.commit()
            print(f"Ingested {chunks_inserted} English chunks for {title}.")

if __name__ == "__main__":
    adapter = MediaWikiAPIAdapter()
    targets = [
        "Estelle_Bright",
        "Joshua_Bright",
        "Lloyd_Bannings",
        "Rean_Schwarzer",
        "Van_Arkride",
        "Ouroboros",
        "Bracer_Guild"
    ]
    
    apis = [
        ('kiseki_fandom', 'https://kiseki.fandom.com/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json'),
        ('falcom_fandom', 'https://nihon-falcom.fandom.com/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json'),
        ('miraheze', 'https://falcom.miraheze.org/w/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json')
    ]
    
    for t in targets:
        for label, url in apis:
            adapter.fetch_and_ingest([t], api_url=url, source_label=label)
