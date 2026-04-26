import json
import urllib.request
import urllib.parse
from pathlib import Path
import time

WIKI_API = 'https://kiseki.fandom.com/api.php'
MIRROR_PATH = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'en_wiki_lore_mirror_v1.json'

CATEGORIES = [
    'Category:Locations',
    'Category:Organizations',
    'Category:Terminology'
]

def get_category_members_recursive(start_category):
    all_members = set()
    categories_to_process = [start_category]
    processed_categories = set()
    
    while categories_to_process:
        current_category = categories_to_process.pop(0)
        if current_category in processed_categories:
            continue
            
        processed_categories.add(current_category)
        print(f"Scraping category: {current_category}")
        
        cmcontinue = ""
        while True:
            url = f"{WIKI_API}?action=query&list=categorymembers&cmtitle={urllib.parse.quote(current_category)}&cmlimit=500&format=json"
            if cmcontinue:
                url += f"&cmcontinue={urllib.parse.quote(cmcontinue)}"
                
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if 'query' in data and 'categorymembers' in data['query']:
                        for page in data['query']['categorymembers']:
                            if page['ns'] == 0:  # Normal page
                                all_members.add(page['title'])
                            elif page['ns'] == 14:  # Subcategory
                                categories_to_process.append(page['title'])
                                
                    if 'continue' in data and 'cmcontinue' in data['continue']:
                        cmcontinue = data['continue']['cmcontinue']
                    else:
                        break
                        
            except Exception as e:
                print(f"Error fetching members for {current_category}: {e}")
                break
                
            time.sleep(0.5) # Polite scraping
            
    return list(all_members)

def get_page_wikitext(title):
    url = f"{WIKI_API}?action=query&prop=revisions&titles={urllib.parse.quote(title)}&rvprop=content&rvslots=main&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_info in pages.items():
                if 'revisions' in page_info:
                    return page_info['revisions'][0].get('slots', {}).get('main', {}).get('*', '')
                elif 'revisions' in page_info: # older api compat
                     return page_info['revisions'][0].get('*', '')
    except Exception as e:
        print(f"Error fetching wikitext for {title}: {e}")
    return None

def main():
    print("Initiating Lore Crawler...")
    all_pages = set()
    
    for category in CATEGORIES:
        print(f"Fetching members for {category}...")
        members = get_category_members_recursive(category)
        all_pages.update(members)
        print(f" -> Found {len(members)} pages.")
        
    print(f"Total unique lore pages to fetch: {len(all_pages)}")
    
    mirror = {}
    
    # Check if mirror exists to avoid re-fetching everything if resuming
    if MIRROR_PATH.exists():
        with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
            mirror = json.load(f)
            print(f"Loaded {len(mirror)} existing pages from mirror.")

    count = 0
    for title in all_pages:
        if title in mirror:
            continue
            
        print(f"[{count+1}/{len(all_pages)}] Fetching: {title}")
        wikitext = get_page_wikitext(title)
        if wikitext:
            mirror[title] = wikitext
            
        count += 1
        
        # Save every 50 records to be safe
        if count % 50 == 0:
            with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
                json.dump(mirror, f, ensure_ascii=False, indent=2)
            time.sleep(1)
            
    # Final save
    # Ensure dir exists
    MIRROR_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
        json.dump(mirror, f, ensure_ascii=False, indent=2)
        
    print(f"Done! {len(mirror)} lore pages saved to {MIRROR_PATH.name}")

if __name__ == "__main__":
    main()
