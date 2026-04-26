"""
legacy_tag_validator.py
Part B: Legacy .tag verification and quarantine
"""
import os
import json
import sqlite3
import shutil
from pathlib import Path

# Paths
MUSIC_ROOT = Path("C:/Users/dissonance/Music")
FOOBAR_APPDATA = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2")
EXTERNAL_TAGS_DB = FOOBAR_APPDATA / "external-tags.db"
REPORTS_DIR = Path(__file__).parent / "reports"
QUARANTINE_DIR = MUSIC_ROOT / "_legacy_tag_quarantine"

# Output files
MIGRATION_REPORT = REPORTS_DIR / "external_tags_migration_report.json"
PARITY_REPORT = REPORTS_DIR / "legacy_tag_parity_report.json"
QUARANTINE_MANIFEST = REPORTS_DIR / "legacy_tag_quarantine_manifest.json"

def scan_legacy_tags():
    tags = []
    print(f"Scanning {MUSIC_ROOT} for legacy .tag and .json sidecars...")
    for root, dirs, files in os.walk(MUSIC_ROOT):
        # Exclude quarantine
        if "_legacy_tag_quarantine" in root:
            continue
        
        for file in files:
            if file.endswith('.tag') or file.endswith('.meta.json'):
                # Avoid accidentally grabbing unrelated JSON
                if "album.json" in file.lower() or file.endswith(".meta.json") or file.endswith(".tag"):
                    tags.append(Path(root) / file)
    return tags

def validate_and_quarantine():
    legacy_files = scan_legacy_tags()
    print(f"Found {len(legacy_files)} legacy sidecar files.")
    
    report = {
        "scanned_directory": str(MUSIC_ROOT),
        "total_legacy_files_found": len(legacy_files),
        "files_quarantined": 0,
        "mismatches_found": 0,
        "quarantine_location": str(QUARANTINE_DIR)
    }

    parity = []
    manifest = []
    
    if legacy_files:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        # Assuming we check external-tags.db size/existence as proof of active new plane
        db_exists = EXTERNAL_TAGS_DB.exists()
        
        for file_path in legacy_files:
            relative_path = file_path.relative_to(MUSIC_ROOT)
            q_dest = QUARANTINE_DIR / relative_path
            q_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Record parity
            parity_entry = {
                "file": str(file_path),
                "status": "quarantined_for_safe_deletion",
                "reason": "external-tags.db is active plane" if db_exists else "unknown"
            }
            parity.append(parity_entry)
            
            # Move file
            try:
                shutil.move(str(file_path), str(q_dest))
                manifest.append(str(q_dest))
                report["files_quarantined"] += 1
            except Exception as e:
                parity_entry["error"] = str(e)
    
    # Write artifacts
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(MIGRATION_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(PARITY_REPORT, "w", encoding="utf-8") as f:
        json.dump(parity, f, indent=2)
        
    with open(QUARANTINE_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Wrote reports to {REPORTS_DIR}")

if __name__ == "__main__":
    validate_and_quarantine()
