#!/usr/bin/env python3
"""Helix workspace boundary checker. Phase-aware."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ROOT_FILES = {"DISSONANCE.md", "README.md", "AGENTS.md"}
REQUIRED_ROOT_DIRS = {"model", "data", "system", "labs", "reports", "quarantine"}

ALLOWED_ROOT_FILES = REQUIRED_ROOT_FILES | {"CLAUDE.md", ".gitignore", ".gitattributes", "pyproject.toml"}

# data/ is canonical evidence lake, kept at root.
# scratch/ is legacy temporary — warn-only, decision deferred.
LEGACY_TEMP_DIRS = {"scratch"}
ALLOWED_ROOT_DIRS = REQUIRED_ROOT_DIRS | {".git", ".github", ".vscode"} | LEGACY_TEMP_DIRS

# Files that are ignorable at the root (transitional artifacts, prompt files, etc).
TRANSITIONAL_ROOT_FILES = {"CLAUDE_WORKSPACE_REFACTOR_PROMPT.md"}

DATA_LIKE_SUFFIXES = {".zip", ".csv", ".tsv", ".html", ".vmf"}
ENGINE_DATA_ALLOW_PARTS = {"fixtures", "schemas", "models"}

MAP_YAMLS = ["patterns.yaml", "gates.yaml", "examples.yaml", "probes.yaml", "anomalies.yaml", "links.yaml", "sources.yaml"]

PHASE3_EXPECTED = [
    "system/tools/README.md",
    "system/tools/TOOL_INDEX.yaml",
    "system/tools/workstation_bridge/README.md",
    "system/tools/workstation_bridge/workstation_snapshot.py",
    "system/engine/schemas/source.schema.json",
    "system/engine/schemas/workstation_snapshot.schema.json",
    "reports/analyses/workstation",
]


def check_required(errors: list[str]) -> None:
    for f in REQUIRED_ROOT_FILES:
        if not (ROOT / f).is_file():
            errors.append(f"missing required root file: {f}")
    for d in REQUIRED_ROOT_DIRS:
        if not (ROOT / d).is_dir():
            errors.append(f"missing required root dir: {d}")


def check_root_clutter(errors: list[str], warnings: list[str]) -> None:
    for p in ROOT.iterdir():
        name = p.name
        if name.startswith("."):
            continue
        if p.is_file():
            if name in ALLOWED_ROOT_FILES or name in TRANSITIONAL_ROOT_FILES:
                if name in TRANSITIONAL_ROOT_FILES:
                    warnings.append(f"transitional root file present: {name}")
                continue
            errors.append(f"loose root file: {name}")
        elif p.is_dir():
            if name in LEGACY_TEMP_DIRS:
                warnings.append(f"legacy temporary root dir present: {name}/ (Phase 2 decision pending)")
                continue
            if name not in ALLOWED_ROOT_DIRS:
                errors.append(f"uncontracted root dir: {name}")


def check_engine_no_raw_data(errors: list[str]) -> None:
    engine_dir = ROOT / "system" / "engine"
    if not engine_dir.exists():
        return
    for p in engine_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in DATA_LIKE_SUFFIXES:
            if not any(part in ENGINE_DATA_ALLOW_PARTS for part in p.parts):
                errors.append(f"possible raw data inside system/engine/: {p.relative_to(ROOT)}")


def check_no_standing_raw_folder(errors: list[str]) -> None:
    if (ROOT / "data" / "raw").exists():
        errors.append("standing data/raw/ folder present; archive source dumps under data/archives/ and promote extracted records into Helix-shaped data")


def check_map_yamls(errors: list[str]) -> None:
    map_dir = ROOT / "model" / "map"
    if not map_dir.is_dir():
        return
    try:
        import yaml  # type: ignore
    except ImportError:
        errors.append("model/map/*.yaml parse skipped: PyYAML not installed")
        return
    for fname in MAP_YAMLS:
        fpath = map_dir / fname
        if not fpath.is_file():
            errors.append(f"missing map file: model/map/{fname}")
            continue
        try:
            data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"model/map/{fname} failed to parse: {exc}")
            continue
        if not isinstance(data, dict) or "items" not in data or "version" not in data or "status" not in data:
            errors.append(f"model/map/{fname} does not match {{version, status, items}} shape")


def check_no_duplicate_ontology(errors: list[str]) -> None:
    candidates = list(ROOT.glob("DISSONANCE*.md"))
    actives = [p for p in candidates if p.name == "DISSONANCE.md"]
    extras = [p for p in candidates if p.name != "DISSONANCE.md"]
    if len(actives) != 1:
        errors.append(f"expected exactly one root DISSONANCE.md, found {len(actives)}")
    for p in extras:
        errors.append(f"duplicate ontology file at root: {p.name} (move to reports/regenerations/)")


PHASE2_EXPECTED_READMES = [
    "system/tools/music_bridge/README.md",
    "model/domains/music/foobar/README.md",
]


def check_phase2_music_bridge(warnings: list[str]) -> None:
    for rel in PHASE2_EXPECTED_READMES:
        if not (ROOT / rel).is_file():
            warnings.append(f"Phase 2 music-bridge scaffold missing: {rel}")


def check_phase3_workstation(warnings: list[str]) -> None:
    for rel in PHASE3_EXPECTED:
        p = ROOT / rel
        if rel.endswith("/") or "." not in Path(rel).name:
            ok = p.is_dir()
        else:
            ok = p.is_file()
        if not ok:
            warnings.append(f"Phase 3 workstation scaffold missing: {rel}")


def check_domains_have_readmes(errors: list[str]) -> None:
    domains_dir = ROOT / "model" / "domains"
    if not domains_dir.is_dir():
        return
    skip = {"__pycache__"}
    for sub in domains_dir.iterdir():
        if not sub.is_dir() or sub.name.startswith(".") or sub.name in skip:
            continue
        if not (sub / "README.md").is_file() and not (sub / "README.template.md").is_file():
            errors.append(f"domain missing README: model/domains/{sub.name}/")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    check_required(errors)
    check_root_clutter(errors, warnings)
    check_engine_no_raw_data(errors)
    check_no_standing_raw_folder(errors)
    check_map_yamls(errors)
    check_no_duplicate_ontology(errors)
    check_domains_have_readmes(errors)
    check_phase2_music_bridge(warnings)
    check_phase3_workstation(warnings)

    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)

    if errors:
        print("Helix boundary check failed:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"Helix boundary check passed ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

