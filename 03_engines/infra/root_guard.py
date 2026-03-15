import os
import shutil
from pathlib import Path

WHITELIST = {
    ".git", ".gitignore", ".agents",
    "HELIX.md", "OPERATOR.md", "REBUILD_CHECKPOINT.md", "operator.json",
    "helix.py",
    "00_kernel", "01_basis", "02_governance", "03_engines",
    "04_labs", "05_applications", "06_atlas", "07_artifacts",
    "docs", "__pycache__"
}

def enforce_root_quarantine(dry_run=False):
    root = Path("c:/Users/dissonance/Desktop/Helix")
    quarantine_dir = root / "07_artifacts" / "_quarantine"
    moved = []
    for item in root.iterdir():
        if item.name not in WHITELIST and item.name != "_quarantine":
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            if not dry_run:
                try:
                    shutil.move(str(item), str(quarantine_dir / item.name))
                except Exception:
                    pass
            moved.append(item.name)
    return moved
