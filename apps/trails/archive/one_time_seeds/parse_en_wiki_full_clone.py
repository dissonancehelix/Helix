import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

WIKI_API = 'https://kiseki.fandom.com/api.php'
MIRROR_PATH = Path(__file__).parent.parent.parent / 'corpus' / 'wiki' / 'en_wiki_full_mirror.json'

def fetch_wiki_pages():
    print("Initiating Full Wiki Clone...")
    
    mirror = {}
    if MIRROR_PATH.exists():
        with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
            mirror = json.load(f)
            print(f"Resuming: Loaded {len(mirror)} existing pages.")
            
    gapcontinue = ""
    pages_processed = 0
    
    while True:
        url = f"{WIKI_API}?action=query&generator=allpages&gaplimit=50&prop=revisions&rvprop=content&rvslots=main&format=json"
        if gapcontinue:
            url += f"&gapcontinue={urllib.parse.quote(gapcontinue)}"
            
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if 'query' in data and 'pages' in data['query']:
                    for page_id, page_info in data['query']['pages'].items():
                        title = page_info.get('title')
                        if title in mirror:
                            continue
                            
                        wikitext = ""
                        if 'revisions' in page_info:
                            rev = page_info['revisions'][0]
                            if 'slots' in rev and 'main' in rev['slots']:
                                wikitext = rev['slots']['main'].get('*', '')
                            else:
                                wikitext = rev.get('*', '')
                                
                        if wikitext:
                            mirror[title] = wikitext
                            pages_processed += 1
                            
                    print(f"Cloned batch... Currently at {len(mirror)} pages stored.")
                    
                    # Save every batch
                    with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
                        json.dump(mirror, f, ensure_ascii=False, indent=2)
                        
                if 'continue' in data and 'gapcontinue' in data['continue']:
                    gapcontinue = data['continue']['gapcontinue']
                else:
                    print("Reached end of wiki pages.")
                    break
                    
        except Exception as e:
            print(f"Error fetching batch: {e}")
            break
            
        time.sleep(1) # Polite scraping

    # Final cleanup save
    MIRROR_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MIRROR_PATH, 'w', encoding='utf-8') as f:
        json.dump(mirror, f, ensure_ascii=False, indent=2)
        
    print(f"[SUCCESS] Operation Complete. {len(mirror)} total unadulterated pages cloned to {MIRROR_PATH.name}.")

if __name__ == "__main__":
    fetch_wiki_pages()
