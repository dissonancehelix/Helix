import requests
import json
from pathlib import Path

# MediaWiki API endpoint for Kiseki Wiki
API_URL = "https://kiseki.fandom.com/api.php"
CATEGORIES = ["Category:Characters", "Category:Lore", "Category:Media"]
OUPUT_PATH = Path(__file__).parent.parent / 'corpus' / 'wiki' / 'wiki_page_titles.json'

def fetch_category_members(category_name):
    print(f"Fetching members for {category_name}...")
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_name,
        "cmlimit": "max",
        "format": "json"
    }
    
    titles = []
    while True:
        response = requests.get(API_URL, params=params).json()
        if 'query' in response:
            members = response['query']['categorymembers']
            titles.extend([m['title'] for m in members if m['ns'] == 0]) # Main namespace only
            
        if 'continue' in response:
            params['cmcontinue'] = response['continue']['cmcontinue']
        else:
            break
            
    print(f"Found {len(titles)} pages in {category_name}.")
    return titles

def discover_wiki():
    all_titles = {}
    OUPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    for cat in CATEGORIES:
        all_titles[cat] = fetch_category_members(cat)
        
    with open(OUPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_titles, f, indent=4, ensure_ascii=False)
        
    print(f"Total discovered pages saved to {OUPUT_PATH}")

if __name__ == "__main__":
    discover_wiki()
