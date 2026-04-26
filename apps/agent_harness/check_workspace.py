#!/usr/bin/env python3
"""Minimal Helix workspace boundary checker."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_ROOT_FILES = {"DISSONANCE.md", "README.md", "CLAUDE.md", ".gitignore", "pyproject.toml"}
ALLOWED_ROOT_DIRS = {"helix", "domains", "apps", "data", ".git", ".github", ".vscode"}
FORBIDDEN_DIRS = {"outputs", "work", "misc", "archive", "labs"}

def main() -> int:
    errors = []
    for p in ROOT.iterdir():
        if p.name.startswith(".") and p.name not in ALLOWED_ROOT_DIRS and p.name not in ALLOWED_ROOT_FILES:
            continue
        if p.is_file() and p.name not in ALLOWED_ROOT_FILES:
            errors.append(f"loose root file: {p.name}")
        if p.is_dir():
            if p.name in FORBIDDEN_DIRS:
                errors.append(f"forbidden root dir: {p.name}")
            elif p.name not in ALLOWED_ROOT_DIRS:
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
