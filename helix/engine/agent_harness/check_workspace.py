#!/usr/bin/env python3
"""Minimal Helix workspace boundary checker."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ROOT_FILES = {"DISSONANCE.md", "README.md"}
REQUIRED_ROOT_DIRS = {"helix", "domains", "apps", "data"}

ALLOWED_ROOT_FILES = REQUIRED_ROOT_FILES | {"CLAUDE.md", ".gitignore", ".gitattributes", "pyproject.toml"}
ALLOWED_ROOT_DIRS = REQUIRED_ROOT_DIRS | {".git", ".github"}

def main() -> int:
    errors = []
    
    # Check for required shape
    for f in REQUIRED_ROOT_FILES:
        if not (ROOT / f).is_file():
            errors.append(f"missing required root file: {f}")
            
    for d in REQUIRED_ROOT_DIRS:
        if not (ROOT / d).is_dir():
            errors.append(f"missing required root dir: {d}")

    # Check for extraneous clutter
    for p in ROOT.iterdir():
        if p.name.startswith(".") and p.name not in ALLOWED_ROOT_DIRS and p.name not in ALLOWED_ROOT_FILES:
            continue  # Ignore other hidden files like .vscode since gitignore handles them
            
        if p.is_file() and p.name not in ALLOWED_ROOT_FILES:
            errors.append(f"loose root file: {p.name}")
            
        if p.is_dir() and p.name not in ALLOWED_ROOT_DIRS and not p.name.startswith("."):
            errors.append(f"uncontracted root dir: {p.name}")

    data_like = {".zip", ".csv", ".tsv", ".html", ".vmf"}
    engine = ROOT / "helix"
    if engine.exists():
        for p in engine.rglob("*"):
            if p.is_file() and p.suffix.lower() in data_like and not any(x in p.parts for x in ["fixtures", "memory", "schemas", "models"]):
                errors.append(f"possible raw data inside helix/: {p.relative_to(ROOT)}")
                
    if errors:
        print("Helix boundary check failed:")
        for e in errors:
            print(f"- {e}")
        return 1
        
    print("Helix boundary check passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
