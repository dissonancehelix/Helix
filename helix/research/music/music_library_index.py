import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import mutagen
from mutagen.easyid3 import EasyID3
try:
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
except ImportError:
    pass

ROOT = Path(r"c:\Users\dissonance\Desktop\Helix")
MUSIC_DIR = Path(r"C:\Users\dissonance\Music")
INDEX_PATH = ROOT / "runtime/cache/music_library_index.json"

TARGET_EXTENSIONS = {'.vgm', '.vgz', '.flac', '.mp3', '.ogg', '.wav', '.mid'}

def get_file_hash(path):
    """Simple hash for change detection."""
    return hashlib.md5(str(path).encode()).hexdigest()

def extract_tags(path):
    ext = path.suffix.lower()
    tags = {
        "title": path.stem,
        "artist": "Unknown",
        "album": "Unknown",
        "year": "Unknown",
        "format": ext[1:]
    }
    
    try:
        if ext == ".mp3":
            audio = EasyID3(path)
            tags["title"] = audio.get("title", [path.stem])[0]
            tags["artist"] = audio.get("artist", ["Unknown"])[0]
            tags["album"] = audio.get("album", ["Unknown"])[0]
            tags["year"] = audio.get("date", ["Unknown"])[0]
        elif ext == ".flac":
            audio = FLAC(path)
            tags["title"] = audio.get("title", [path.stem])[0]
            tags["artist"] = audio.get("artist", ["Unknown"])[0]
            tags["album"] = audio.get("album", ["Unknown"])[0]
            tags["year"] = audio.get("date", ["Unknown"])[0]
        # For VGM/VGZ, we might need a custom parser or check sidecar files if mutagen doesn't handle them natively well.
        # But foobar2000 uses APEv2 for VGM often.
        else:
            m = mutagen.File(path)
            if m and m.tags:
                tags["title"] = m.tags.get("title", [path.stem])[0]
                tags["artist"] = m.tags.get("artist", ["Unknown"])[0]
                tags["album"] = m.tags.get("album", ["Unknown"])[0]
    except Exception:
        pass
    
    return tags

def run_index():
    print(f"Indexing library at {MUSIC_DIR}...")
    index = {"timestamp": datetime.now().isoformat(), "tracks": []}
    
    nagao_maeda_hits = []

    for root, dirs, files in os.walk(MUSIC_DIR):
        for file in files:
            path = Path(root) / file
            if path.suffix.lower() in TARGET_EXTENSIONS:
                try:
                    tags = extract_tags(path)
                    track_entry = {
                        "path": str(path),
                        "hash": get_file_hash(path),
                        "tags": tags,
                        "size": path.stat().st_size
                    }
                    index["tracks"].append(track_entry)
                    
                    # Search for Target Composers
                    artist_lower = tags["artist"].lower()
                    if "nagao" in artist_lower or "maeda" in artist_lower:
                        nagao_maeda_hits.append(track_entry)
                except Exception as e:
                    print(f"Error processing {file}: {e}")

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=4)
        
    print(f"Indexed {len(index['tracks'])} tracks.")
    print(f"Found {len(nagao_maeda_hits)} potential Nagao/Maeda tracks.")
    
    # Save a specific report for these composers
    report_path = ROOT / "artifacts/reports/nagao_maeda_index.json"
    with open(report_path, "w") as f:
        json.dump(nagao_maeda_hits, f, indent=4)

if __name__ == "__main__":
    run_index()
