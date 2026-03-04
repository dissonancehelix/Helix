import os
import shutil
from pathlib import Path

WHITELIST = {
    ".git", ".gitignore", "HELIX.md", "OPERATOR.md",
    "00_core", "01_protocol", "02_runtime", "03_forge",
    "04_workspaces", "05_atlas", "06_artifacts", "docs", "helix.py",
    "setup_hardening.py", "run_eval.py", "__pycache__"
}

def enforce_root_quarantine(dry_run=False):
    root = Path("c:/Users/dissonance/Desktop/Helix")
    quarantine_dir = root / "06_artifacts" / "_quarantine"
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
