import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
sys.path.insert(0, str(HELIX_ROOT))

from model.domains.music.atlas_integration.track_db import TrackDB

LIB_ROOT = HELIX_ROOT / "codex/library/music"

def run_sync(force: bool = False):
    print(f"=== Helix Music: Incremental Semantic Sync{' (Full Re-sync)' if force else ''} ===")
    db = TrackDB()
    
    count = 0
    synced_tags = 0
    synced_meta = 0
    tag_instances = 0
    skipped = 0
    
    print(f"Scanning {LIB_ROOT}...")
    
    for root, _, files in os.walk(LIB_ROOT):
        # We focus on the 'album' and 'artist' directories for primary records
        root_str = str(root)
        if "album" not in root_str and "artist" not in root_str:
            continue
            
        for fname in files:
            if not fname.endswith(".json") or fname.startswith("."):
                continue
            
            fpath = Path(root) / fname
            try:
                # 0. Incremental Check
                mtime_ts = os.path.getmtime(fpath)
                # ISO8601 for comparison
                mtime_iso = datetime.fromtimestamp(mtime_ts, tz=timezone.utc).isoformat()
                
                # Check if we already have this file synced and it hasn't changed
                # We use the helix_id as a hint, but we need the internal DB record for extraction_ts
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                track_id = data.get("id")
                if not track_id:
                    continue
                    
                meta = data.get("metadata", {})
                file_path = meta.get("source")
                if not file_path:
                    continue
                
                # Look up existing record to check staleness
                if not force:
                    existing = db.get_track_by_helix_id(track_id)
                    if existing and existing.get("ingested_ts"):
                        if existing["ingested_ts"] >= mtime_iso:
                            skipped += 1
                            count += 1
                            if count % 1000 == 0:
                                print(f"  Processed {count} files... ({synced_meta} meta updated, {skipped} skipped)")
                            continue

                # 1. Sync Identity and Metadata
                rec = {
                    "id":           data.get("id"),
                    "file_path":    file_path,
                    "title":        meta.get("title"),
                    "artist":       meta.get("artist"),
                    "album":        meta.get("album"),
                    "platform":     meta.get("platform"),
                    "genre":        meta.get("genre"),
                    "loved":        meta.get("library_state", {}).get("loved", False),
                    "duration":     data.get("hardware", {}).get("duration_s", 0)
                }
                db.insert_track(rec)
                synced_meta += 1
                
                # 2. Sync Structural Tags
                tags = data.get("semantic", {}).get("structural_tags", [])
                if tags:
                    from model.domains.music.atlas_integration.track_db import _track_id
                    internal_id = _track_id(file_path)
                    db.upsert_semantic_tags(internal_id, tags)
                    synced_tags += 1
                    tag_instances += len(tags)
                
                count += 1
                if count % 1000 == 0:
                    print(f"  Processed {count} files... ({synced_meta} meta updated, {skipped} skipped)")
                    
            except Exception as e:
                pass

    print(f"Sync complete. Meta updated: {synced_meta} | Skipped: {skipped} | Tracks with tags: {synced_tags}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force re-sync even if unchanged")
    args = parser.parse_args()
    run_sync(force=args.force)

