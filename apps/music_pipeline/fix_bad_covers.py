"""
fix_bad_covers.py
Finds all ~28MB placeholder images and deletes them.
The main crawler (category_a_cleanup.py) will re-process them on the next run,
and the updated placeholder hash detection will prevent them being re-saved.
"""
import sys, hashlib
from pathlib import Path

VGM_ROOT = Path("C:/Users/dissonance/Music/VGM")

BAD_SIZE_MIN = 28 * 1024 * 1024
BAD_SIZE_MAX = 30 * 1024 * 1024
BAD_HASHES = {
    "856faeec5bfabac93bf8657a98e6db5c",
    "10ae74119286b34978e3f02307610217",
}

deleted = 0
flagged = []

for cat_path in sorted(VGM_ROOT.iterdir()):
    if not cat_path.is_dir():
        continue
    for folder in sorted(cat_path.iterdir()):
        if not folder.is_dir():
            continue
        cover = folder / "cover.jpg"
        if not cover.exists():
            continue

        size = cover.stat().st_size

        # Quick size gate first (avoid hashing every file)
        if not BAD_SIZE_MIN <= size <= BAD_SIZE_MAX:
            continue

        # Confirm via hash
        with open(cover, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()

        if h in BAD_HASHES:
            cover.unlink()
            print(f"[DELETED] {cat_path.name}/{folder.name}")
            deleted += 1
            flagged.append(folder.name)

print(f"\nDeleted {deleted} bad placeholder images.")
print("Re-run category_a_cleanup.py to fill in replacements from VGMdb/MobyGames/SNESmusic.")
