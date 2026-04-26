"""
Atlas Ingestor -- Helix Formal System
Cross-compiles external trace datasets (Steam, Wikipedia) into Atlas-ready
entities and submits them through the Atlas Compiler transaction protocol.

Pipeline per source:
    load(raw_file) -> normalize(records) -> build_entities(records)
    -> compile_and_commit(entity) [via atlas_compiler]

Data sources:
    data/raw/games/steam_*.json       -- OwnershipRecord / playtime traces
    data/raw/wikipedia/<run>/         -- wikimedia_normalized_edits.jsonl

Output (all writes via atlas_compiler.compile_and_commit):
    codex/atlas/games/titles/<slug>.json
    codex/atlas/language/wikipedia/<slug>.json

CLOSED SYSTEM LAW:
    This module NEVER writes to atlas/ directly.
    All writes pass through atlas_compiler.compile_and_commit().
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists()),
    Path(__file__).resolve().parent.parent.parent,
)
sys.path.insert(0, str(ROOT))

RAW_DIR        = ROOT / "data" / "raw"
STEAM_RAW_DIR  = RAW_DIR / "games"
WIKI_RAW_DIR   = RAW_DIR / "wikipedia"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", s.lower().strip()).strip("_")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Steam ingestor
# ---------------------------------------------------------------------------

def _load_steam_files() -> list:
    if not STEAM_RAW_DIR.exists():
        return []
    return sorted(STEAM_RAW_DIR.glob("steam_*.json"))


def _iter_steam_entities(raw_path: Path) -> Iterator[dict]:
    """
    Yield one Atlas entity dict per owned game with >0 playtime.

    Entity id:   games.game:<title_slug>
    Entity type: Game
    """
    try:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception as e:
        print("  [steam] Failed to load {}: {}".format(raw_path.name, e))
        return

    owner  = data.get("vanity_name", "unknown")
    games  = data.get("games", [])
    source = _rel(raw_path)
    print("  [steam] {}: {} games for '{}'".format(raw_path.name, len(games), owner))

    for game in games:
        playtime = game.get("playtime_hours", 0.0)
        name     = game.get("name", "App {}".format(game.get("title_id", "?")))
        slug     = _slugify(name)
        appid    = str(game.get("title_id", ""))

        if playtime <= 0:
            continue

        last_ts  = game.get("last_played")
        last_iso = None
        if last_ts:
            try:
                last_iso = datetime.fromtimestamp(int(last_ts), tz=timezone.utc).isoformat()
            except Exception:
                pass

        yield {
            "id":          "games.game:{}".format(slug),
            "type":        "Game",
            "name":        name,
            "label":       name,
            "description": "Steam game owned by {}".format(owner),
            "substrate":   "games",
            "metadata": {
                "playtime_hours":        round(playtime, 2),
                "playtime_2weeks_hours": round(game.get("playtime_2weeks_hours", 0.0), 2),
                "last_played_iso":       last_iso,
                "achievements_earned":   game.get("achievements_earned", 0),
                "achievements_possible": game.get("achievements_possible", 0),
                "platform":              game.get("platform", "steam"),
                "steam_appid":           appid,
                "owner":                 owner,
                "source":                source,
                "ingestor":              "atlas_ingestor.steam",
                "ingested_at":           _now_iso(),
            },
        }


def ingest_steam(verbose: bool = True) -> dict:
    log   = print if verbose else (lambda *a, **k: None)
    stats = {"created": [], "skipped": [], "errors": []}

    files = _load_steam_files()
    if not files:
        log("  [steam] No raw Steam files found in data/raw/games/")
        return stats

    from core.compiler.atlas_compiler import compile_and_commit, CompilationError

    for raw_path in files:
        for entity in _iter_steam_entities(raw_path):
            try:
                out = compile_and_commit(entity)
                log("  [steam] WRITE: {}".format(_rel(out)))
                stats["created"].append(str(out))
            except CompilationError as e:
                log("  [steam] SKIP ({}): {}".format(entity.get("id"), e))
                stats["skipped"].append(entity.get("id", "?"))
            except Exception as e:
                log("  [steam] ERROR ({}): {}".format(entity.get("id"), e))
                stats["errors"].append(entity.get("id", "?"))

    return stats


# ---------------------------------------------------------------------------
# Wikipedia ingestor
# ---------------------------------------------------------------------------

def _load_wiki_runs() -> list:
    if not WIKI_RAW_DIR.exists():
        return []
    return sorted(
        p for p in WIKI_RAW_DIR.iterdir()
        if p.is_dir() and p.name.startswith("wiki_")
    )


def _iter_wiki_entities(run_dir: Path) -> Iterator[dict]:
    """
    Yield one Atlas entity per unique Wikipedia page edited by the operator.

    Reads wikimedia_normalized_edits.jsonl -- one JSON object per line.
    Groups by (project, page_id). Emits one entity per unique page with
    edit_count, first/last edit timestamps, and classification summary.

    Entity id:   language.wikipedia:<project>:<page_slug>
    Entity type: WikipediaPage
    """
    edits_file    = run_dir / "wikimedia_normalized_edits.jsonl"
    manifest_file = run_dir / "wikimedia_ingest_manifest.json"

    if not edits_file.exists():
        print("  [wiki] No edits file in {}".format(run_dir.name))
        return

    run_id = run_dir.name
    source = _rel(edits_file)

    manifest: dict = {}
    if manifest_file.exists():
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    pages: dict = {}
    try:
        with edits_file.open(encoding="utf-8") as fh:
            for raw_line in fh:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    edit = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue

                project = edit.get("project", "enwiki")
                page    = edit.get("page", {})
                page_id = page.get("page_id", 0)
                title   = page.get("title", "")
                ns      = page.get("namespace_id", 0)
                ts      = edit.get("timestamp", "")
                cls     = edit.get("classification", "unknown")

                key = (project, page_id)
                if key not in pages:
                    pages[key] = {
                        "project":         project,
                        "page_id":         page_id,
                        "title":           title,
                        "namespace_id":    ns,
                        "edit_count":      0,
                        "timestamps":      [],
                        "classifications": set(),
                    }
                pages[key]["edit_count"] += 1
                pages[key]["classifications"].add(cls)
                if ts:
                    pages[key]["timestamps"].append(ts)

    except Exception as e:
        print("  [wiki] Failed reading {}: {}".format(edits_file.name, e))
        return

    total_records = manifest.get("total_records", "?")
    print("  [wiki] {}: {} unique pages from {} edit records".format(
        run_dir.name, len(pages), total_records))

    for (project, page_id), rec in pages.items():
        title      = rec["title"]
        slug       = _slugify("{}_{}".format(project, title))
        timestamps = sorted(rec["timestamps"])

        yield {
            "id":          "language.wikipedia:{}:{}".format(project, slug),
            "type":        "WikipediaPage",
            "name":        title,
            "label":       title,
            "description": "Wikipedia page edited by operator ({})".format(project),
            "substrate":   "language",
            "metadata": {
                "project":          project,
                "page_id":          page_id,
                "namespace_id":     rec["namespace_id"],
                "edit_count":       rec["edit_count"],
                "first_edit_iso":   timestamps[0] if timestamps else None,
                "last_edit_iso":    timestamps[-1] if timestamps else None,
                "classifications":  sorted(rec["classifications"]),
                "run_id":           run_id,
                "source":           source,
                "ingestor":         "atlas_ingestor.wikipedia",
                "ingested_at":      _now_iso(),
            },
        }


def ingest_wikipedia(verbose: bool = True) -> dict:
    log   = print if verbose else (lambda *a, **k: None)
    stats = {"created": [], "skipped": [], "errors": []}

    runs = _load_wiki_runs()
    if not runs:
        log("  [wiki] No raw Wikipedia runs found in data/raw/wikipedia/")
        return stats

    from core.compiler.atlas_compiler import compile_and_commit, CompilationError

    for run_dir in runs:
        for entity in _iter_wiki_entities(run_dir):
            try:
                out = compile_and_commit(entity)
                log("  [wiki] WRITE: {}".format(_rel(out)))
                stats["created"].append(str(out))
            except CompilationError as e:
                log("  [wiki] SKIP ({}): {}".format(entity.get("id"), e))
                stats["skipped"].append(entity.get("id", "?"))
            except Exception as e:
                log("  [wiki] ERROR ({}): {}".format(entity.get("id"), e))
                stats["errors"].append(entity.get("id", "?"))

    return stats


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def ingest_all(verbose: bool = True) -> dict:
    """
    Run all ingestors. Safe to run repeatedly -- atlas_compiler skips
    already-committed entities unless --overwrite is passed to the compiler.
    """
    log = print if verbose else (lambda *a, **k: None)
    log("=== Atlas Ingestor -- cross-compiling external traces ===")
    log("Root: {}".format(ROOT))
    log("Raw:  {}".format(_rel(RAW_DIR)))

    total = {"created": [], "skipped": [], "errors": []}

    log("\n[1/2] Steam playtime traces ->  codex/atlas/games/titles/")
    for k, v in ingest_steam(verbose=verbose).items():
        total[k].extend(v)

    log("\n[2/2] Wikipedia edit traces ->  codex/atlas/language/wikipedia/")
    for k, v in ingest_wikipedia(verbose=verbose).items():
        total[k].extend(v)

    log("\n=== Ingestion complete ===")
    log("  Created:  {}".format(len(total["created"])))
    log("  Skipped:  {}".format(len(total["skipped"])))
    log("  Errors:   {}".format(len(total["errors"])))
    return total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Atlas Ingestor -- external trace cross-compiler")
    p.add_argument("--quiet",  action="store_true", help="Suppress output")
    p.add_argument("--source", choices=["steam", "wikipedia", "all"], default="all",
                   help="Which source to ingest (default: all)")
    args = p.parse_args()

    verbose = not args.quiet
    if args.source == "steam":
        ingest_steam(verbose=verbose)
    elif args.source == "wikipedia":
        ingest_wikipedia(verbose=verbose)
    else:
        ingest_all(verbose=verbose)
