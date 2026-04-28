import sqlite3
import os
import sys
import time
import re
import json

# Paths
sys.path.append(r'c:\Users\dissonance\Desktop\Helix\core\bin')
sys.path.append(r'c:\Users\dissonance\Desktop\Helix\core\compiler')

from lib_ingest import IngestionManager

DB_PATH = r'C:\Users\dissonance\AppData\Roaming\foobar2000-v2\metadb.sqlite'
STATS_PATH = r'C:\Users\dissonance\Downloads\playcount.json'
LIB_ROOT = r'C:\Users\dissonance\Desktop\Helix\core\library\music'
# THE STORED LIBRARY ROOT (Filter for purity)
MUSIC_ROOT_FILTER = r'C:\Users\dissonance\Music'.lower().replace('\\', '/')

class SQLiteIngestRunner:
    def __init__(self, lib_root):
        self.manager = IngestionManager(lib_root)

    def execute(self, limit=None):
        print("==================================================")
        print(f"HELIX SUBSTRATE PURITY RUN (V27)")
        print("==================================================")
        
        # 1. LOAD JSON STATS
        print(f"Loading stats from {STATS_PATH}...")
        json_stats = {}
        try:
            with open(STATS_PATH, 'r', encoding='utf-8') as f:
                raw_stats = json.load(f)
                for item in raw_stats:
                    key = item['id'].split('|')[0].lower().replace('\\', '/')
                    json_stats[key] = {
                        "loved": bool(item.get('2003_loved', 0)),
                        "pc": item.get('2003_playcount', 0)
                    }
            print(f"  Loaded {len(json_stats)} stats records.")
        except Exception as e:
            print(f"  Warning: Could not load JSON stats: {e}")

        conn = sqlite3.connect(DB_PATH)
        count = 0
        start_time = time.time()
        
        cur = conn.execute("SELECT name, info FROM metadb")
        for name, info in cur:
            # 1. PATH DISCOVERY & PURITY FILTER
            if not name.startswith(('0+file://', '0+C:', '0+D:')): continue
            raw_path = name.replace('0+file://', '').replace('0+', '')
            norm_path = raw_path.lower().replace('\\', '/')
            
            # THE PURITY FILTER: Only ingest files from the official Music folder
            if MUSIC_ROOT_FILTER not in norm_path:
                continue

            folder_path = os.path.dirname(raw_path)
            
            try:
                parts = info.decode('utf-8', 'ignore').split('\x00')
                parts = [p for p in parts if len(p) > 0]
                m = {}
                for i in range(len(parts)-1):
                    k = parts[i].lower()
                    if k in ['album', 'artist', 'title', 'tracknumber']:
                        m[k] = parts[i+1]
            except: continue
            
            st = json_stats.get(norm_path, {"loved": False, "pc": 0})
            
            def is_junk_identity(n):
                if not n: return True
                n = str(n).strip()
                if len(n) <= 2: return True
                if re.match(r'^(CD|Disc|Disk|Vol|Volume|Part|Side|Disque|Disct|D|V)[\s\-_]*[\d\w]*$', n, re.I): return True
                if n.lower() in ['music', 'vgm', 'soundtrack', 'ost', 'soundtracks', 'games', 'game', 'gaming', '#']: return True
                return False

            def normalize_album(name):
                if not name: return "Unknown Album"
                res = name
                res = re.sub(r'^\s*\d{4}[\s\-_]+', '', res)
                res = re.sub(r'^[\s\-_]*(CD|Disc|Disk|Vol|Volume|Part|Side)[\s\-_]*\d*[\s\-:_]+', '', res, flags=re.IGNORECASE)
                res = re.sub(r'^[\s\-_]*\d+[\-:_]+', '', res)
                res = re.sub(r'\s*[\[\(](Disc|CD|Side|Vol|Volume|Part)\.?\s*[\d\w]*\s*[\]\)]', '', res, flags=re.IGNORECASE)
                res = re.sub(r'\s+(CD\d+|Vol\.\d+|Disc\s+\d+|Disk\s+\d+)\s*$', '', res, flags=re.IGNORECASE)
                res = re.sub(r'\s+(Original|Game|Digital|Complete)?\s*(Soundtrack|OST|Game Soundtrack|BGM|Score|Arranged|Arrange|Collection|Selection|Version|Anthology|Themes|Best Selection)\s*$', '', res, flags=re.IGNORECASE)
                res = re.sub(r'\s*[\[\(][^\]\)]+[\]\)]\s*$', '', res)
                return res.strip()

            album_tag = m.get('album')
            found_raw = None
            if not is_junk_identity(album_tag):
                found_raw = album_tag
            else:
                curr = folder_path
                for _ in range(5):
                    cand = os.path.basename(curr)
                    if cand and not is_junk_identity(cand):
                        found_raw = cand
                        break
                    prev = curr
                    curr = os.path.dirname(curr)
                    if len(curr) < 10 or curr == prev: break
            
            if not found_raw:
                path_parts = folder_path.replace('\\', '/').split('/')
                safe_parts = [p for p in path_parts if not is_junk_identity(p)]
                found_raw = f"Orphan {safe_parts[-1]}" if safe_parts else "Collection Artifact"

            def clean_name(t):
                if not t: return t
                if t == t.lower() and len(t) > 3: return t.title()
                return t

            title = m.get('title') or os.path.basename(raw_path).rsplit('.', 1)[0]
            album_clean = normalize_album(found_raw)
            artist = m.get('artist') or "Unknown Artist"
            
            record = {
                "title": clean_name(title),
                "album": clean_name(album_clean),
                "artist": clean_name(artist),
                "track_number": m.get('tracknumber', 0),
                "format": raw_path.split('.')[-1].lower() if '.' in raw_path else 'vgm',
                "loved": st['loved'],
                "parent_slug": os.path.basename(folder_path).lower().replace(' ', '_'),
                "sources": {"title": "foobar_db", "artist": "foobar_db", "loved": "json_stats"}
            }
            
            try:
                self.manager.ingest_record(record)
                count += 1
                if count % 20000 == 0:
                    print(f"  Ingesting... {count} tracks ({count/(time.time()-start_time):.1f} t/s)")
                if limit and count >= limit: break
            except: pass
                
        self.manager.finalize()
        print(f"PURITY COMPLETE. {count} tracks processed from official Music library.")
        conn.close()

if __name__ == "__main__":
    runner = SQLiteIngestRunner(LIB_ROOT)
    runner.execute()
