"""
dedup_library.py — One record per unique source file, no more.

Problems this fixes:
  1. Blank source paths (29,035 phantom records from ingest runs that
     didn't record the file path).  These cannot be matched to a real
     file — deleted.
  2. Duplicate source paths (the same file ingested N times under
     different album slugs or across repeat ingest runs).  Keep the
     most "complete" record (highest score on filled-in fields), delete
     the rest.

Dry run by default.  Pass --execute to actually delete.

Usage:
    python core/bin/maintenance/dedup_library.py            # dry run
    python core/bin/maintenance/dedup_library.py --execute  # live
    python core/bin/maintenance/dedup_library.py --execute --verify-disk
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Completeness scoring
# ---------------------------------------------------------------------------

_PENDING = {"pending", "unavailable", None}


def _score(record: dict) -> int:
    """
    Score a record by how many fields have real (non-pending) values.
    Higher = more complete = preferred when deduplicating.
    """
    score = 0

    meta = record.get("metadata", {})
    for key, val in meta.items():
        if key.startswith("_"):
            continue
        if isinstance(val, str) and val.lower() in ("", "none", "null", "pending", "unavailable"):
            continue
        if val is None:
            continue
        if isinstance(val, list) and len(val) == 0:
            continue
        if isinstance(val, dict) and not any(v for v in val.values() if v):
            continue
        score += 1

    hw = record.get("hardware", {})
    if hw.get("chips"):
        score += 5
    if hw.get("duration_s"):
        score += 2
    if hw.get("has_loop") is not None:
        score += 1

    analysis = record.get("analysis", {})
    if analysis.get("analysis_tier"):
        score += 10
    if analysis.get("dcp_complete"):
        score += 5
    if analysis.get("symbolic_complete"):
        score += 3
    if analysis.get("perceptual_complete"):
        score += 3
    if analysis.get("confidence", 0):
        score += int(analysis["confidence"] * 10)

    dcp = record.get("dcp", {})
    if dcp.get("_status") not in _PENDING:
        score += 8

    return score


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(library_root: Path, execute: bool, verify_disk: bool) -> None:
    track_files = [f for f in library_root.rglob("*.json") if f.name != "album.json"]
    print(f"Scanning {len(track_files):,} track records ...", flush=True)

    # Load all records
    records: list[tuple[Path, dict]] = []
    parse_errors: list[Path] = []
    for f in track_files:
        try:
            obj = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            records.append((f, obj))
        except Exception:
            parse_errors.append(f)

    if parse_errors:
        print(f"  {len(parse_errors):,} parse errors (skipped, not touched)")

    # Group by source path
    by_source: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    blank_source: list[Path] = []

    for fpath, obj in records:
        src = obj.get("metadata", {}).get("source", "")
        if not src or not src.strip():
            blank_source.append(fpath)
        else:
            by_source[src].append((fpath, obj))

    # Identify duplicates and missing disk files
    to_delete: list[tuple[Path, str]] = []   # (path, reason)
    to_keep:   list[Path]              = []

    # Blank source → delete
    for f in blank_source:
        to_delete.append((f, "blank_source"))

    # Duplicates → keep best, delete rest
    for src, group in by_source.items():
        if len(group) == 1:
            kept_path = group[0][0]
            # Optional disk verification
            if verify_disk and not Path(src).exists():
                to_delete.append((kept_path, "source_missing_from_disk"))
            else:
                to_keep.append(kept_path)
        else:
            # Score each and pick the winner
            scored = sorted(group, key=lambda x: _score(x[1]), reverse=True)
            winner_path, _ = scored[0]

            if verify_disk and not Path(src).exists():
                # Source file gone — delete all
                for fpath, _ in group:
                    to_delete.append((fpath, "source_missing_from_disk"))
            else:
                to_keep.append(winner_path)
                for fpath, _ in scored[1:]:
                    to_delete.append((fpath, f"duplicate_of:{winner_path.name}"))

    # ---------------------------------------------------------------------------
    # Report
    # ---------------------------------------------------------------------------
    blank_count  = sum(1 for _, r in to_delete if r == "blank_source")
    dupe_count   = sum(1 for _, r in to_delete if r.startswith("duplicate_of"))
    disk_count   = sum(1 for _, r in to_delete if r == "source_missing_from_disk")

    print()
    print(f"Total records scanned:     {len(records):,}")
    print(f"Unique source paths:       {len(by_source):,}")
    print(f"Records to keep:           {len(to_keep):,}")
    print()
    print(f"Records to delete:         {len(to_delete):,}")
    print(f"  blank source path:       {blank_count:,}")
    print(f"  duplicate (keeping best):{dupe_count:,}")
    if verify_disk:
        print(f"  source missing on disk:  {disk_count:,}")
    print()

    if not execute:
        print("DRY RUN — no files changed.  Pass --execute to apply.")
        print()
        # Show a sample of what would be deleted
        sample = [(p, r) for p, r in to_delete if r.startswith("duplicate_of")][:10]
        if sample:
            print("Sample duplicates that would be removed:")
            for p, reason in sample:
                print(f"  {p.relative_to(library_root)}  ({reason})")
        return

    # ---------------------------------------------------------------------------
    # Execute
    # ---------------------------------------------------------------------------
    deleted = 0
    errors  = 0
    for fpath, reason in to_delete:
        try:
            fpath.unlink()
            deleted += 1
        except Exception as e:
            print(f"  ERROR deleting {fpath}: {e}", file=sys.stderr)
            errors += 1

    # Clean up now-empty album directories (but leave album.json directories)
    for album_dir in sorted(library_root.iterdir()):
        if not album_dir.is_dir():
            continue
        remaining = list(album_dir.iterdir())
        # Only album.json left → leave it (it's metadata for the album entity)
        # Completely empty → remove
        if len(remaining) == 0:
            album_dir.rmdir()

    print(f"Deleted {deleted:,} records ({errors} errors).")
    print(f"Library now contains {len(to_keep):,} unique track records.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true",
                        help="Actually delete.  Default is dry run.")
    parser.add_argument("--verify-disk", action="store_true",
                        help="Also delete records whose source file no longer exists on disk.")
    parser.add_argument("--library", default=None,
                        help="Path to library root (default: auto-detect from Helix repo root).")
    args = parser.parse_args()

    if args.library:
        library_root = Path(args.library)
    else:
        # Walk up from this file to find Helix repo root
        here = Path(__file__).resolve()
        root = here
        for _ in range(8):
            if (root / "codex").exists():
                break
            root = root.parent
        library_root = root / "codex" / "library" / "music" / "album"

    if not library_root.exists():
        print(f"ERROR: Library not found at {library_root}", file=sys.stderr)
        sys.exit(1)

    run(library_root, execute=args.execute, verify_disk=args.verify_disk)


if __name__ == "__main__":
    main()
