import json
import os
import re
from pathlib import Path
from collections import defaultdict

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music/album"
DATASETS = HELIX_ROOT / "domains/music/data/music/metadata"
PC2003_PATH = DATASETS / "2003_playcount.json"
RECOVERY_MAP_PATH = HELIX_ROOT / "codex/library/music/.recovery_map.json"

_ART_RE   = re.compile(r"^(the |a |an )", re.I)
_PUNCT_RE = re.compile(r"[^\w]")
_SPACE_RE = re.compile(r"\s+")

def normalize_meta(s: str) -> str:
    if not s: return ""
    s = s.lower().strip()
    s = _ART_RE.sub("", s)
    s = _PUNCT_RE.sub("", s)
    s = _SPACE_RE.sub("", s).strip()
    return s

def run_recovery(verbose=True):
    print("Helix Recovery Engine v1.0")
    
    # 1. Build the Current Library Index
    # We need: 
    #   path -> helix_id
    #   (album_dir, duration, norm_title) -> helix_id
    
    path_to_hid = {}
    fuzzy_index = defaultdict(list) # (album_dir, duration, norm_title) -> [helix_id]
    
    print("Building library index...")
    count = 0
    for root, _, files in os.walk(str(LIB_ROOT)):
        album_dir = Path(root).name
        for fname in files:
            if not fname.endswith(".json") or fname.startswith("."): continue
            
            fpath = Path(root) / fname
            with open(fpath, "r", encoding="utf-8") as f:
                track = json.load(f)
            
            if track.get("type") != "Track": continue
            
            hid = track.get("helix_id")
            if not hid: continue
            
            count += 1
            source_path = track.get("metadata", {}).get("source", "").replace("\\", "/").lower()
            if source_path:
                path_to_hid[source_path] = hid
            
            # Fuzzy keys
            duration = int(track.get("hardware", {}).get("duration_s") or 0)
            title = normalize_meta(track.get("metadata", {}).get("title", ""))
            
            # Key: (album_folder_name, duration, normalized_title)
            fuzzy_index[(album_dir, duration, title)].append(hid)
            
            if count % 10000 == 0:
                print(f"  Indexed {count} tracks...")

    # 2. Load Playcount 2003
    if not PC2003_PATH.exists():
        print(f"Error: Playcount 2003 not found at {PC2003_PATH}")
        return

    print(f"Loading Playcount 2003 from {PC2003_PATH}...")
    with open(PC2003_PATH, "r", encoding="utf-8") as f:
        pc_data = json.load(f)
    
    recovery_map = {}
    matched_exact = 0
    matched_fuzzy = 0
    missed = 0
    
    print("Mapping historical entries...")
    for entry in pc_data:
        raw_id = entry.get("id", "")
        # Playcount 2003 ID is "path|subsong"
        old_path = raw_id.split("|")[0].replace("\\", "/").lower()
        
        # Strategy A: Exact Path Match
        if old_path in path_to_hid:
            recovery_map[raw_id] = path_to_hid[old_path]
            matched_exact += 1
            continue
            
        # Strategy B: Neighborhood Match
        # old_path example: "c:/users/dissonance/music/vgm/#/1080° snowboarding/01 - vacant lives.mp3"
        # We need the album folder part
        parts = old_path.split("/")
        if len(parts) < 2:
            missed += 1
            continue
            
        old_album_dir = parts[-2]
        # We don't have duration in the 2003_playcount.json directly? 
        # Wait, the signal_sources.py says it has 2003_playcount, 2003_loved, etc.
        # Let's check 2003_playcount.json schema again.
        
        # If we don't have duration in the export, we can use title + album_dir
        # But wait, 1080 - Vacant Lives might have changed to 01 - Vacant Lives.
        # We'll use normalized title.
        
        # To get the title from the old path, we'll try to guess it from the filename
        # or just skip if we don't have a better signal.
        # Actually, let's assume we might have the duration if we cross-reference 
        # but for now let's just use AlbumDir + NormTitle.
        
        # Guess title from filename: "01 - vacant lives.mp3" -> "vacant lives"
        filename = parts[-1]
        raw_title = filename.rsplit(".", 1)[0]
        # Strip leading numbers: "01 - "
        raw_title = re.sub(r"^\d+\s*-\s*", "", raw_title)
        old_norm_title = normalize_meta(raw_title)
        
        # Optimization: We'll try to find a match in the same album folder with the same title
        # ignoring duration for now if we don't have it in the source.
        
        # Search fuzzy_index for (old_album_dir, ANY_DURATION, old_norm_title)
        found = False
        # Potentially slow if fuzzy_index is big, but let's see.
        # Better: build a separate index for (album_dir, title)
        
        # (For now, just exact path matched {matched_exact})
        missed += 1

    print(f"Results: Exact={matched_exact}, Fuzzy={matched_fuzzy}, Missed={missed}")
    
    # Save the recovery map
    with open(RECOVERY_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(recovery_map, f, indent=2)
    print(f"Saved recovery map to {RECOVERY_MAP_PATH}")

if __name__ == "__main__":
    run_recovery()
