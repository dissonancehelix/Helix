#!/usr/bin/env python3
"""
Apply canonical name corrections from a reviewed TSV file.

After reviewing and editing a TSV produced by export_for_review.py,
run this script to apply the corrections to entity_registry.

Usage:
  # Dry-run: print proposed updates, make no changes
  python scripts/translation/apply_corrections.py translation/review_char_1.tsv --dry-run

  # Apply corrections
  python scripts/translation/apply_corrections.py translation/review_char_1.tsv --apply

The script reads the `entity_id` and `suggested_fix` columns.
Rows where `suggested_fix` is empty or identical to `current_name` are skipped.

Optionally also updates `japanese_name` if a `name_ja` value is present and
the entity currently has no japanese_name set.

Output:
  - Prints each UPDATE statement (or would-be update in dry-run)
  - Prints a summary count at the end
"""

import argparse
import csv
import sqlite3
import sys

TRAILS_DB = "C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db"

REQUIRED_COLUMNS = {"entity_id", "current_name", "suggested_fix"}


def load_tsv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            print(f"ERROR: TSV missing required columns: {missing}", file=sys.stderr)
            sys.exit(1)
        return list(reader)


def build_corrections(rows: list[dict]) -> list[tuple[str, str, str | None, str]]:
    """
    Returns list of (new_name_en, new_name_ja_or_None, entity_id, old_name) tuples.
    Skips rows with no meaningful change.
    """
    corrections = []
    seen = set()
    for row in rows:
        eid = row.get("entity_id", "").strip()
        current = row.get("current_name", "").strip()
        fix = row.get("suggested_fix", "").strip()
        name_ja = row.get("name_ja", "").strip() or None

        if not eid or not fix:
            continue
        if fix == current:
            continue
        if eid in seen:
            print(f"  WARN: Duplicate entity_id in TSV: {eid} — skipping second occurrence")
            continue
        seen.add(eid)
        corrections.append((fix, name_ja, eid, current))
    return corrections


def apply_corrections(conn: sqlite3.Connection, corrections: list[tuple], dry_run: bool) -> int:
    c = conn.cursor()
    applied = 0

    for new_name, name_ja, eid, old_name in corrections:
        # Verify entity exists
        c.execute("SELECT english_display_name, japanese_name FROM entity_registry WHERE entity_id = ?", (eid,))
        row = c.fetchone()
        if not row:
            print(f"  SKIP  {eid} — not found in entity_registry")
            continue

        db_current, db_ja = row

        # Build update
        updates = []
        params = []

        if new_name != db_current:
            updates.append("english_display_name = ?")
            params.append(new_name)

        # Update japanese_name only if provided and currently empty
        if name_ja and not db_ja:
            updates.append("japanese_name = ?")
            params.append(name_ja)

        if not updates:
            print(f"  SKIP  {eid} — no effective change (DB already has: {db_current!r})")
            continue

        params.append(eid)
        sql = f"UPDATE entity_registry SET {', '.join(updates)} WHERE entity_id = ?"

        if dry_run:
            parts = []
            if new_name != db_current:
                parts.append(f"name: {old_name!r} → {new_name!r}")
            if name_ja and not db_ja:
                parts.append(f"ja: {name_ja!r}")
            print(f"  WOULD UPDATE  {eid}  ({'; '.join(parts)})")
        else:
            c.execute(sql, params)
            parts = []
            if new_name != db_current:
                parts.append(f"name: {old_name!r} → {new_name!r}")
            if name_ja and not db_ja:
                parts.append(f"ja: {name_ja!r}")
            print(f"  UPDATED  {eid}  ({'; '.join(parts)})")

        applied += 1

    if not dry_run:
        conn.commit()

    return applied


def main():
    ap = argparse.ArgumentParser(description="Apply canonical name corrections from reviewed TSV")
    ap.add_argument("tsv_path", help="Path to the reviewed TSV file")
    ap.add_argument("--dry-run", action="store_true", help="Print proposed changes without applying")
    ap.add_argument("--apply", action="store_true", help="Actually apply changes (required to write)")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        print("Specify --dry-run to preview or --apply to write changes.", file=sys.stderr)
        sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "APPLYING"
    print(f"--- {mode} ---")
    print(f"Reading: {args.tsv_path}")

    rows = load_tsv(args.tsv_path)
    print(f"Loaded {len(rows)} rows from TSV.")

    corrections = build_corrections(rows)
    skipped = len(rows) - len(corrections)
    print(f"Corrections to apply: {len(corrections)}  (skipped unchanged: {skipped})\n")

    if not corrections:
        print("Nothing to do.")
        return

    conn = sqlite3.connect(TRAILS_DB)
    applied = apply_corrections(conn, corrections, dry_run=args.dry_run)
    conn.close()

    print(f"\n{'Would update' if args.dry_run else 'Updated'}: {applied} entities")

    if args.dry_run:
        print("\nRe-run with --apply to write changes.")


if __name__ == "__main__":
    main()
