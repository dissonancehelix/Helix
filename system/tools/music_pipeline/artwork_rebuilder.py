import os
import json
import shutil
from pathlib import Path
from PIL import Image

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
CODEX_ALBUMS = HELIX_ROOT / "codex/library/music/album"
AUDIT_REPORT = HELIX_ROOT / "model/domains/music/reports/album_art_audit_report.json"
POLICY_PATH = HELIX_ROOT / "model/domains/music/ingestion/artwork_source_policy.json"

def load_json(path):
    if not path.exists(): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def update_album_provenance(album_id: str, visual_data: dict):
    """Updates the album.json in codex with visual provenance."""
    album_path = CODEX_ALBUMS / album_id / "album.json"
    if not album_path.exists(): return
    
    data = load_json(album_path)
    data["visual"] = visual_data
    
    with open(album_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def consolidate_artwork(results: list):
    print("Helix Artwork Rebuilder v1.0")
    print(f"Processing {len(results)} audit records...")
    
    repaired_count = 0
    skipped_count = 0
    
    for res in results:
        album_id = res["album_id"]
        source_folder = res.get("source_folder")
        if not source_folder or source_folder == "None": continue
        
        src_path = Path(source_folder)
        if not src_path.exists(): continue
        
        current_status = res["status"]
        primary_file = res.get("primary_file") # Full path or name?
        # In my audit.py, primary_file was str(primary)
        
        visual_data = {
            "canonical_path": "cover.jpg", # Target
            "current_status": current_status,
            "resolution": res.get("resolution"),
            "is_square": res.get("is_square"),
            "branding_clean": not res.get("is_branded"),
            "source_type": "local_import" if res.get("has_cover") else "missing"
        }

        # 1. Action: Consolidate to cover.jpg
        # Only if we have a file and it's not already cover.jpg
        if primary_file:
            pfile = Path(primary_file)
            target = src_path / "cover.jpg"
            
            if pfile.exists() and pfile != target:
                print(f"  [FIX] {album_id}: Renaming {pfile.name} -> cover.jpg")
                try:
                    # If target exists and is different, we might have a conflict
                    # but audit.py already picked pfile as the "best".
                    if target.exists() and pfile.resolve() != target.resolve():
                        # Back up if different? Or just overwrite?
                        # Audit identified pfile as the one to use.
                        # For safety, move target to .trash
                        trash = src_path / ".trash"
                        trash.mkdir(exist_ok=True)
                        shutil.move(target, trash / f"old_{target.name}")
                    
                    shutil.move(pfile, target)
                    repaired_count += 1
                except Exception as e:
                    print(f"  [ERROR] {album_id}: Failed to target cover.jpg: {e}")
            elif pfile.exists() and pfile == target:
                # Already correct, but might need consolidation of others
                pass

        # 2. Update Codex Provenance
        update_album_provenance(album_id, visual_data)

    print(f"\nRebuild Finished. Repaired (renamed): {repaired_count}, Updated Codex for all.")

if __name__ == "__main__":
    audit_data = load_json(AUDIT_REPORT)
    if not audit_data:
        print("Error: No audit data found. Run audit first.")
    else:
        consolidate_artwork(audit_data)

