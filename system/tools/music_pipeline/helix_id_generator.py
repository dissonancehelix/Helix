import json
import hashlib
import os
import re
from pathlib import Path

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music/album"

_ART_RE   = re.compile(r"^(the |a |an )", re.I)
_PUNCT_RE = re.compile(r"[^\w]")
_SPACE_RE = re.compile(r"\s+")

def normalize_meta(s: str) -> str:
    """Strong normalization for stable ID generation."""
    if not s:
        return ""
    s = s.lower().strip()
    s = _ART_RE.sub("", s)
    s = _PUNCT_RE.sub("", s)  # Remove all punctuation/non-word chars
    s = _SPACE_RE.sub("", s).strip() # Remove all spaces
    return s

def generate_helix_id(track_data: dict) -> str:
    """
    Generates a stable 16-char hex ID based on core musical invariants.
    Formula: sha256(norm_artist + norm_album + norm_title + track_num + duration_ms)
    """
    metadata = track_data.get("metadata", {})
    hardware = track_data.get("hardware", {})
    
    artist = normalize_meta(metadata.get("artist", "unknown"))
    album  = normalize_meta(metadata.get("album", "unknown"))
    title  = normalize_meta(metadata.get("title", "unknown"))
    
    # Use track number and disc number for uniqueness in multi-disc sets
    track_num = str(metadata.get("track_number") or "0")
    disc_num  = str(metadata.get("disc_number") or "1")
    
    # Duration is a strong physical invariant in VGM/FLAC
    # Round to nearest second to handle small encoder variances if needed, 
    # but for Helix, exact duration_s is preferred if available.
    duration = str(int(hardware.get("duration_s") or 0)) 

    input_str = f"{artist}|{album}|{title}|{disc_num}|{track_num}|{duration}"
    hasher = hashlib.sha256(input_str.encode("utf-8"))
    return f"h_{hasher.hexdigest()[:16]}"

def run_id_generation(dry_run=True):
    print(f"{'DRY RUN: ' if dry_run else ''}Helix ID Generator v1.0")
    
    count = 0
    updated = 0
    
    for root, _, files in os.walk(str(LIB_ROOT)):
        for fname in files:
            if not fname.endswith(".json") or fname.startswith("."):
                continue
            
            fpath = Path(root) / fname
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    track = json.load(f)
            except Exception as e:
                print(f"Error reading {fpath}: {e}")
                continue
            
            if track.get("type") != "Track":
                continue
                
            count += 1
            
            # Generate the new stable ID
            new_id = generate_helix_id(track)
            
            # Check if it's already there and identical
            if track.get("helix_id") == new_id:
                continue
                
            updated += 1
            if not dry_run:
                track["helix_id"] = new_id
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(track, f, indent=2)
            
            if updated % 1000 == 0:
                print(f"  Processed {count}... {'Simulated' if dry_run else 'Updated'} {updated} tracks")

    print(f"Finished. Total Tracks: {count}, Updated: {updated}")

if __name__ == "__main__":
    import sys
    dry_run = "--commit" not in sys.argv
    run_id_generation(dry_run=dry_run)
