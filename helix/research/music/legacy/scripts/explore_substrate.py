import os
import json
from collections import defaultdict

LIB_ROOT = r'C:\Users\dissonance\Desktop\Helix\core\library\music'

def explore_substrate():
    artists_dir = os.path.join(LIB_ROOT, 'artist')
    albums_dir = os.path.join(LIB_ROOT, 'album')
    
    # 1. ARTIST STATS
    top_producers = []
    top_loved = []
    
    for f in os.listdir(artists_dir):
        if not f.endswith('.json'): continue
        with open(os.path.join(artists_dir, f), 'r', encoding='utf-8') as j:
            data = json.load(j)
            meta = data['metadata']
            top_producers.append((meta['canonical_name'], meta['track_count']))
            if meta['track_count'] > 50:
                top_loved.append((meta['canonical_name'], meta['loved_track_count'] / meta['track_count'], meta['track_count']))

    top_producers.sort(key=lambda x: x[1], reverse=True)
    top_loved.sort(key=lambda x: x[1], reverse=True)

    # 2. ALBUM STATS
    album_sizes = []
    for d in os.listdir(albums_dir):
        ap = os.path.join(albums_dir, d, "album.json")
        if os.path.exists(ap):
            with open(ap, 'r', encoding='utf-8') as j:
                data = json.load(j)
                album_sizes.append((data['name'], data['metadata']['track_count']))
    
    album_sizes.sort(key=lambda x: x[1], reverse=True)

    print("==================================================")
    print("HELIX SUBSTRATE - DEEP SIGNAL DISCOVERY")
    print("==================================================")
    print("\nTOP 10 PROLIFIC ARTISTS (Most Content):")
    for name, count in top_producers[:10]:
        print(f"  {name}: {count} tracks")

    print("\nTOP 10 'LOVED' ARTISTS (Highest Quality Density - Min 50 tracks):")
    for name, density, total in top_loved[:10]:
        print(f"  {name}: {density:.1%} Loved ({total} total)")

    print("\nTOP 10 MASSIVE ALBUMS (Soundtrack Scale):")
    for name, count in album_sizes[:10]:
        print(f"  {name}: {count} tracks")

if __name__ == "__main__":
    explore_substrate()
