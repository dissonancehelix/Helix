import os
import json
from pathlib import Path
from datetime import datetime
import mutagen

ROOT = Path(r"c:\Users\dissonance\Desktop\Helix")
VGM_DIR = Path(r"C:\Users\dissonance\Music\VGM")
INDEX_PATH = ROOT / "runtime/cache/vgm_subset_index.json"

def get_tags(path):
    entry = {"path": str(path), "artist": "Unknown", "title": path.stem, "game": "Unknown"}
    try:
        m = mutagen.File(path)
        if m and m.tags:
            # Try to handle different tag formats (APEv2, ID3, Vorbis)
            artist = m.tags.get("artist") or m.tags.get("Artist") or m.tags.get("ARTIST")
            title = m.tags.get("title") or m.tags.get("Title") or m.tags.get("TITLE")
            album = m.tags.get("album") or m.tags.get("Album") or m.tags.get("ALBUM")
            
            if isinstance(artist, list): artist = artist[0]
            if isinstance(title, list): title = title[0]
            if isinstance(album, list): album = album[0]
            
            if artist: entry["artist"] = str(artist)
            if title: entry["title"] = str(title)
            if album: entry["game"] = str(album)
    except:
        pass
    return entry

def index_vgm():
    print(f"Indexing high-priority VGM subset at {VGM_DIR}...")
    results = []
    
    # We'll also check for .tag files as they are priority sidecars in the spec
    for root, dirs, files in os.walk(VGM_DIR):
        for file in files:
            path = Path(root) / file
            if path.suffix.lower() in {'.vgm', '.vgz', '.spc', '.nsf', '.mid', '.vgz.tag'}:
                # If it's a .tag file, we parse it as if it were the song metadata
                results.append(get_tags(path))

    with open(INDEX_PATH, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"Sub-indexed {len(results)} VGM files.")
    
    nagao = [r for r in results if "nagao" in str(r.get("artist", "")).lower()]
    maeda = [r for r in results if "maeda" in str(r.get("artist", "")).lower()]
    
    print(f"Detected {len(nagao)} Masayuki Nagao entries.")
    print(f"Detected {len(maeda)} Tatsuyuki Maeda entries.")
    
    # Showcase some specific works
    print("\n--- Nagao Highlights ---")
    for n in list({r['game'] for r in nagao}):
        print(f"  Game: {n}")
        
    print("\n--- Maeda Highlights ---")
    for m in list({r['game'] for r in maeda}):
        print(f"  Game: {m}")

if __name__ == "__main__":
    index_vgm()
