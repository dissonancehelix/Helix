import json
import os
import sys
from pathlib import Path

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music"
CATALOG_PATH = HELIX_ROOT / "domains/music/model/semantic/structural_tag_catalog.json"

def load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["taxonomy"]

def tag_track(track_data, catalog):
    metadata = track_data.get("metadata", {})
    hardware = track_data.get("hardware", {})
    attribution = track_data.get("attribution", {}).get("composition_credit", {})
    
    # Extract candidate signals
    artist = metadata.get("artist", "")
    album_artist = metadata.get("album_artist", "")
    genre = metadata.get("genre", "")
    platform = metadata.get("platform", "")
    chips = hardware.get("chips", [])
    
    tags = set(track_data.get("semantic", {}).get("structural_tags", []))
    
    for tag_name, criteria in catalog.items():
        # Match by Anchor Artist/Composer
        anchors = criteria.get("anchors", [])
        if any(a.lower() in artist.lower() or a.lower() in album_artist.lower() for a in anchors):
            tags.add(tag_name)
            continue
            
        # Match by Platform/Chip
        evidence = criteria.get("evidence", {})
        if platform and platform.lower() in [p.lower() for p in evidence.get("platforms", [])]:
            tags.add(tag_name)
            continue
            
        if any(c.lower() in [chip.lower() for chip in evidence.get("chips", [])] for c in chips):
            tags.add(tag_name)
            continue
            
        # Match by Genre
        if genre and genre.lower() in [g.lower() for g in evidence.get("genres", [])]:
            tags.add(tag_name)
            continue

    # Update record
    if "semantic" not in track_data:
        track_data["semantic"] = {}
    track_data["semantic"]["structural_tags"] = sorted(list(tags))
    return track_data

def run():
    print(f"Helix Structural Tagger v1.0")
    catalog = load_catalog()
    print(f"Loaded {len(catalog)} taxonomy definitions.")
    
    count = 0
    updated = 0
    
    for root, _, files in os.walk(LIB_ROOT):
        for fname in files:
            if not fname.endswith(".json") or fname.startswith("."):
                continue
            
            fpath = Path(root) / fname
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                original_tags = data.get("semantic", {}).get("structural_tags", [])
                new_data = tag_track(data, catalog)
                
                if new_data["semantic"]["structural_tags"] != original_tags:
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(new_data, f, indent=2, ensure_ascii=False)
                    updated += 1
                
                count += 1
                if count % 1000 == 0:
                    print(f"  Processed {count} tracks... ({updated} updated)")
                    
            except Exception as e:
                print(f"Error processing {fpath}: {e}")
                
    print(f"Finished. Total: {count}, Updated: {updated}")

if __name__ == "__main__":
    run()

