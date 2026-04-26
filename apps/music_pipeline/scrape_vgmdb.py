import urllib.request
import urllib.parse

def scrape_vgmdb(query):
    query_encoded = urllib.parse.quote(query)
    url = f"https://vgmdb.net/search?q={query_encoded}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            print(html[:2000]) # Print first 2000 chars to see structure
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
     scrape_vgmdb('Akumajo Dracula')
