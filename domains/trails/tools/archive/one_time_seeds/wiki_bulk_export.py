import requests
import json
import time
from pathlib import Path

API_URL = "https://kiseki.fandom.com/api.php"
TITLES_PATH = Path(__file__).parent.parent / 'corpus' / 'wiki' / 'wiki_page_titles.json'
MIRROR_PATH = Path(__file__).parent.parent / 'corpus' / 'wiki' / 'en_wiki_mirror_v1.json'

def bulk_export():
    if not TITLES_PATH.exists():
        print("Discovery file not found. Run wiki_discovery.py first.")
        return

    with open(TITLES_PATH, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    # Flatten the list of titles to export
    all_titles = []
    for titles in categories.values():
        all_titles.extend(titles)

    print(f"Starting bulk export of {len(all_titles)} pages...")
    
    mirror = {}
    
    # Process in batches of 50 (API limit)
    for i in range(0, len(all_titles), 50):
        batch = all_titles[i:i+50]
        print(f" - Exporting batch {i//50 + 1}/{(len(all_titles)-1)//50 + 1}...")
        
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "titles": "|".join(batch),
            "format": "json"
        }
        
        try:
            response = requests.get(API_URL, params=params).json()
            pages = response.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                title = page_data.get('title')
                revisions = page_data.get('revisions')
                if revisions:
                    content = revisions[0].get('*')
                    mirror[title] = content
                    
            # Brief sleep to respect API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   [!] Error in batch: {e}")

    MIRROR_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
        json.dump(mirror, f, indent=4, ensure_ascii=False)
        
    print(f"\n[SUCCESS] Local Wiki Mirror created at {MIRROR_PATH}")
    print(f"Total pages archived: {len(mirror)}")

if __name__ == "__main__":
    bulk_export()
