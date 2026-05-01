#!/usr/bin/env python3
"""Helix workspace boundary checker for the domain-capsule architecture."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ROOT_FILES = {"DISSONANCE.md", "README.md", "AGENTS.md"}
REQUIRED_ROOT_DIRS = {"core", "domains", "labs"}
LOCAL_ONLY_ROOT_DIRS = {"archive", "inbox"}
ACTIVE_DOMAINS = {
    "self",
    "music",
    "games",
    "eft",
    "trails",
    "wiki",
    "software",
    "language",
    "attraction",
    "food",
    "aesthetics",
    "body_sensory",
    "sports",
    "worldview",
}
DOMAIN_FILES = {
    "self": "SELF.md",
    "music": "MUSIC.md",
    "games": "GAMES.md",
    "eft": "EFT.md",
    "trails": "TRAILS.md",
    "wiki": "WIKI.md",
    "software": "SOFTWARE.md",
    "language": "LANGUAGE.md",
    "attraction": "ATTRACTION.md",
    "food": "FOOD.md",
    "aesthetics": "AESTHETICS.md",
    "body_sensory": "BODY_SENSORY.md",
    "sports": "SPORTS.md",
    "worldview": "WORLDVIEW.md",
}
NO_TOOL_DOMAINS = {
    "attraction",
    "food",
    "aesthetics",
    "body_sensory",
    "sports",
    "worldview",
    "eft",
}

ALLOWED_ROOT_FILES = REQUIRED_ROOT_FILES | {".gitignore", ".gitattributes", "pyproject.toml"}
ALLOWED_ROOT_DIRS = REQUIRED_ROOT_DIRS | LOCAL_ONLY_ROOT_DIRS | {".git", ".github", ".vscode", ".claude"}
FORBIDDEN_OLD_ROOTS = {"model", "data", "system", "reports"}

MAP_YAMLS = [
    "patterns.yaml",
    "gates.yaml",
    "examples.yaml",
    "probes.yaml",
    "anomalies.yaml",
    "links.yaml",
    "sources.yaml",
]

BASE_CAPSULE_DIRS = [
    "model",
    "data",
]

OPTIONAL_DOMAIN_DIRS = {"labs", "reports", "tools"}

HEAVY_SUFFIXES = {
    ".zip",
    ".parquet",
    ".csv",
    ".tsv",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".jsonl",
    ".mp3",
    ".flac",
    ".wav",
    ".spc",
    ".vgz",
    ".vgm",
    ".exe",
    ".dll",
}

TRACKED_HEAVY_LIMIT = 10 * 1024 * 1024

ALLOWED_COMPACT_LEDGER_PATHS = {
    "labs/domain_synthesis/data/gpt_export/domain_index.csv",
    "labs/domain_synthesis/data/gpt_export/artifact_ledger.csv",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_required(errors: list[str]) -> None:
    for f in REQUIRED_ROOT_FILES:
        if not (ROOT / f).is_file():
            errors.append(f"missing required root file: {f}")
    for d in REQUIRED_ROOT_DIRS:
        if not (ROOT / d).is_dir():
            errors.append(f"missing required root dir: {d}/")


def check_root_shape(errors: list[str]) -> None:
    for p in ROOT.iterdir():
        name = p.name
        if p.is_file() and name not in ALLOWED_ROOT_FILES:
            errors.append(f"loose root file: {name}")
        elif p.is_dir():
            if name in FORBIDDEN_OLD_ROOTS:
                errors.append(f"old active root still present: {name}/")
            elif name not in ALLOWED_ROOT_DIRS and not name.startswith("."):
                errors.append(f"uncontracted root dir: {name}/")


def check_map_yamls(errors: list[str]) -> None:
    map_dir = ROOT / "core" / "map"
    if not map_dir.is_dir():
        errors.append("missing core/map/")
        return
    try:
        import yaml  # type: ignore
    except ImportError:
        errors.append("core/map/*.yaml parse skipped: PyYAML not installed")
        return

    for fname in MAP_YAMLS:
        fpath = map_dir / fname
        if not fpath.is_file():
            errors.append(f"missing map file: core/map/{fname}")
            continue
        try:
            data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"core/map/{fname} failed to parse: {exc}")
            continue
        if not isinstance(data, dict) or "items" not in data or "version" not in data or "status" not in data:
            errors.append(f"core/map/{fname} does not match {{version, status, items}} shape")


def check_domain_capsules(errors: list[str]) -> None:
    domains_dir = ROOT / "domains"
    if not domains_dir.is_dir():
        return
    actual = {p.name for p in domains_dir.iterdir() if p.is_dir() and not p.name.startswith(".")}
    missing = sorted(ACTIVE_DOMAINS - actual)
    extra = sorted(actual - ACTIVE_DOMAINS)
    for name in missing:
        errors.append(f"missing active domain capsule: domains/{name}/")
    for name in extra:
        if name != "__pycache__":
            errors.append(f"unregistered domain capsule: domains/{name}/")

    for domain in sorted(ACTIVE_DOMAINS):
        base = domains_dir / domain
        if not base.is_dir():
            continue
        domain_file = DOMAIN_FILES[domain]
        if (base / "README.md").exists():
            errors.append(f"domain root README retired; use {domain_file}: domains/{domain}/")
        for file_name in (domain_file, "manifest.yaml"):
            if not (base / file_name).is_file():
                errors.append(f"domain missing {file_name}: domains/{domain}/")
        named_files = [p.name for p in base.glob("*.md") if p.name == domain_file]
        if len(named_files) != 1:
            errors.append(f"domain must have exactly one named domain file: domains/{domain}/{domain_file}")
        required_dirs = list(BASE_CAPSULE_DIRS)
        for folder in required_dirs:
            if not (base / folder).is_dir():
                errors.append(f"domain missing {folder}/: domains/{domain}/")
        if domain in NO_TOOL_DOMAINS and (base / "tools").exists():
            errors.append(f"domain has no runnable workflow yet; remove tools/: domains/{domain}/tools/")
        for child in base.iterdir():
            allowed_dirs = set(required_dirs) | OPTIONAL_DOMAIN_DIRS
            if child.is_dir() and child.name not in allowed_dirs:
                errors.append(f"unexpected domain-root folder: domains/{domain}/{child.name}/")
        for forbidden in ("domains", "core", "vendor"):
            if (base / forbidden).exists():
                errors.append(f"forbidden domain-root folder: domains/{domain}/{forbidden}/")
        for old_data_room in ("normalized", "derived", "staging", "output"):
            if (base / "data" / old_data_room).exists():
                errors.append(f"old data lifecycle room still present: domains/{domain}/data/{old_data_room}/")
        local_labs = base / "labs"
        if local_labs.is_dir() and not any(local_labs.iterdir()) and not (local_labs / "README.md").exists():
            errors.append(f"empty optional domain lab has no purpose note: domains/{domain}/labs/")


def check_cross_domain_labs(errors: list[str]) -> None:
    if not (ROOT / "labs" / "appearance_ownership_continuity").is_dir():
        errors.append("missing cross-domain lab: labs/appearance_ownership_continuity/")
    if (ROOT / "labs" / "research").exists():
        errors.append("old research lab root still present")
    if (ROOT / "labs" / "labs").exists():
        errors.append("nested lab folder repeats itself: labs/labs/")
    if (ROOT / "reports" / "reports").exists():
        errors.append("nested report folder repeats itself: reports/reports/")
    if (ROOT / "archive" / "legacy").exists():
        errors.append("archive/legacy/ has been retired; archive is grouped by evidence type")
    if (ROOT / "archive" / "quarantine").exists():
        errors.append("archive/quarantine/ duplicates root inbox sorting")
    if (ROOT / "quarantine").exists():
        errors.append("root quarantine/ has been retired; use inbox/ for drops")


def check_committed_cache(errors: list[str]) -> None:
    for path in tracked_files():
        parts = Path(path).parts
        if "__pycache__" in parts:
            errors.append(f"committed Python cache: {path}")


def check_no_duplicate_ontology(errors: list[str]) -> None:
    candidates = list(ROOT.glob("DISSONANCE*.md"))
    if len([p for p in candidates if p.name == "DISSONANCE.md"]) != 1:
        errors.append("expected exactly one root DISSONANCE.md")
    for p in candidates:
        if p.name != "DISSONANCE.md":
            errors.append(f"duplicate ontology file at root: {p.name}")


def tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def is_allowed_compact_ledger(path: str) -> bool:
    if path in ALLOWED_COMPACT_LEDGER_PATHS:
        return True
    return path.startswith("domains/") and path.endswith("/data/gpt_evidence_index.jsonl")


def check_tracked_bloat(errors: list[str], warnings: list[str]) -> None:
    for path in tracked_files():
        p = ROOT / path
        if not p.exists() or not p.is_file():
            continue
        if path.startswith("archive/") or path.startswith("inbox/"):
            errors.append(f"local-only folder tracked in git: {path}")
        if "/vendor/" in path and p.name not in {"README.md", "manifest.yaml"}:
            errors.append(f"vendor mirror tracked in git: {path}")
        if "/toolkits/" in path and p.name not in {"README.md", "manifest.yaml"}:
            errors.append(f"toolkit/source mirror tracked in git: {path}")
        if p.suffix.lower() in HEAVY_SUFFIXES and not is_allowed_compact_ledger(path):
            errors.append(f"heavy data/binary file tracked in git: {path}")
        elif p.stat().st_size > TRACKED_HEAVY_LIMIT:
            warnings.append(f"large tracked file over 5 MiB: {path}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    check_required(errors)
    check_root_shape(errors)
    check_map_yamls(errors)
    check_domain_capsules(errors)
    check_cross_domain_labs(errors)
    check_no_duplicate_ontology(errors)
    check_committed_cache(errors)
    check_tracked_bloat(errors, warnings)

    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)

    if errors:
        print("Helix workspace check failed:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"Helix workspace check passed ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
