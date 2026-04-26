#!/usr/bin/env python3
"""
Export entity display names for canonical translation review.

Flags entities whose english_display_name may not match the official
XSEED/NISA localization, and outputs them as a TSV for review in
Claude Code chatspace.

Usage:
  # Dry-run: print to stdout
  python scripts/translation/export_for_review.py --type character --batch 1 --dry-run

  # Write TSV to translation/ folder
  python scripts/translation/export_for_review.py --type character --batch 1

  # Other entity types
  python scripts/translation/export_for_review.py --type location --batch 1
  python scripts/translation/export_for_review.py --type faction --batch 1
  python scripts/translation/export_for_review.py --type quest --batch 1 --arc sky
  python scripts/translation/export_for_review.py --type item --batch 1
  python scripts/translation/export_for_review.py --type concept --batch 1

Batch size: 80 rows per file, to keep review sessions manageable.

Output columns (TSV):
  entity_id | entity_type | current_name | name_ja | chunk_preview | flag_reason | suggested_fix

After review:
  Edit the suggested_fix column, then run:
  python scripts/translation/apply_corrections.py translation/review_char_1.tsv
"""

import argparse
import csv
import io
import os
import re
import sqlite3
import sys

TRAILS_DB = "C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db"
TRANSLATION_DIR = "C:/Users/dissonance/Desktop/Trails/translation"
BATCH_SIZE = 80

# Arc name fragments in entity_id for filtering quests by arc
ARC_SLUG_MAP = {
    "sky":       ("sky", "liberl", "fc_", "sc_", "the3rd", "3rd_"),
    "crossbell": ("crossbell", "zero_", "ao_", "azure_"),
    "cs":        ("cs1_", "cs2_", "cs3_", "cs4_", "cold_steel"),
    "daybreak":  ("daybreak", "kuro_", "db1_", "db2_"),
    "reverie":   ("reverie", "hajimari"),
}

# Patterns that suggest a name is NOT canonical
KATAKANA_RE  = re.compile(r'[\u30A0-\u30FF]')
HIRAGANA_RE  = re.compile(r'[\u3040-\u309F]')
KANJI_RE     = re.compile(r'[\u4E00-\u9FFF]')
BOLD_RE      = re.compile(r"'''(.+?)'''")

ENTITY_TYPE_MAP = {
    "character": "character",
    "char":      "character",
    "location":  "location",
    "loc":       "location",
    "faction":   "faction",
    "quest":     "quest",
    "item":      "item",
    "concept":   "concept",
    "staff":     "staff",
}

TYPE_PREFIXES = {
    "character": "char:",
    "location":  "loc:",
    "faction":   "faction:",
    "quest":     "quest:",
    "item":      "item:",
    "concept":   "concept:",
    "staff":     "staff:",
}


# ---------------------------------------------------------------------------
# Flag detection
# ---------------------------------------------------------------------------

def has_japanese(text: str) -> bool:
    return bool(KATAKANA_RE.search(text) or HIRAGANA_RE.search(text) or KANJI_RE.search(text))


def looks_slug_reconstructed(name: str, entity_id: str) -> bool:
    """
    True if the name looks like it was reconstructed from the slug rather
    than set from a real source. Heuristics:
    - Matches title-cased slug tokens exactly (no punctuation, apostrophes, etc.)
    - Very short (single word) and all-caps or all-lowercase
    """
    prefix = entity_id.split(":")[0] + ":"
    slug = entity_id[len(prefix):]
    # Reconstruct what a slug-derived name would look like
    reconstructed = slug.replace("_", " ").title()
    if name == reconstructed:
        # Could be legitimate (e.g. "Estelle Bright") or reconstructed
        # Only flag if it also has NO chunks confirming the name
        return True  # Soft flag — caller checks chunk text
    return False


def extract_bold_name(chunk_text: str) -> str | None:
    """Extract canonical name from wiki-style '''Name''' bold markup."""
    m = BOLD_RE.search(chunk_text[:800])
    if not m:
        return None
    name = m.group(1).strip()
    if has_japanese(name):
        return None
    if len(name) > 60 or len(name) < 2:
        return None
    return name


def get_chunk_preview(chunk_text: str, max_len: int = 120) -> str:
    """First non-empty line of chunk, truncated."""
    if not chunk_text:
        return ""
    lines = [l.strip() for l in chunk_text.splitlines() if l.strip()]
    preview = lines[0] if lines else chunk_text[:max_len]
    return preview[:max_len] + ("…" if len(preview) > max_len else "")


# ---------------------------------------------------------------------------
# Main flagging logic
# ---------------------------------------------------------------------------

def collect_flagged(conn, entity_type: str, arc: str | None, offset: int, limit: int) -> list[dict]:
    c = conn.cursor()
    prefix = TYPE_PREFIXES.get(entity_type, "")

    # Build arc filter for quests
    arc_clause = ""
    if entity_type == "quest" and arc and arc in ARC_SLUG_MAP:
        tokens = ARC_SLUG_MAP[arc]
        arc_clause = " AND (" + " OR ".join(
            f"entity_id LIKE '{prefix}{t}%'" for t in tokens
        ) + ")"

    c.execute(f"""
        SELECT entity_id, english_display_name, japanese_name
        FROM entity_registry
        WHERE entity_type = ?
        {arc_clause}
        ORDER BY entity_id
        LIMIT ? OFFSET ?
    """, (entity_type, limit * 5, offset * limit))   # Fetch 5× to filter down to flagged ones
    candidates = c.fetchall()

    # Gather chunks for each entity in one query to avoid N+1
    if not candidates:
        return []

    eids = [row[0] for row in candidates]
    placeholders = ",".join("?" * len(eids))
    c.execute(f"""
        SELECT linked_entity_ids, text_content, chunk_type
        FROM chunk_registry
        WHERE linked_entity_ids IN ({placeholders})
          AND chunk_type IN ('background', 'lead')
          AND language = 'en'
        ORDER BY chunk_type DESC
    """, eids)
    chunk_map: dict[str, list[tuple[str, str]]] = {}
    for eid, text, ctype in c.fetchall():
        chunk_map.setdefault(eid, []).append((text, ctype))

    flagged = []
    for entity_id, name_en, name_ja in candidates:
        if not name_en:
            flagged.append({
                "entity_id": entity_id,
                "entity_type": entity_type,
                "current_name": name_en or "",
                "name_ja": name_ja or "",
                "chunk_preview": "",
                "flag_reason": "missing_en_name",
                "suggested_fix": "",
            })
            continue

        flag_reason = None
        suggested_fix = name_en  # Default: no change

        # Flag 1: Japanese characters in display name
        if has_japanese(name_en):
            flag_reason = "japanese_in_name"
            # Try to get EN name from chunk
            chunks = chunk_map.get(entity_id, [])
            for text, _ in chunks:
                extracted = extract_bold_name(text)
                if extracted and not has_japanese(extracted):
                    suggested_fix = extracted
                    break

        # Flag 2: Looks reconstructed AND no bold name in chunks confirms it
        if not flag_reason and looks_slug_reconstructed(name_en, entity_id):
            chunks = chunk_map.get(entity_id, [])
            bold_name = None
            for text, _ in chunks:
                bold_name = extract_bold_name(text)
                if bold_name:
                    break
            if bold_name and bold_name != name_en:
                flag_reason = "name_differs_from_chunk"
                suggested_fix = bold_name
            elif not chunks:
                flag_reason = "no_chunks_reconstructed"
            # else: slug matches bold name, no issue — skip

        if flag_reason:
            chunks = chunk_map.get(entity_id, [])
            preview = ""
            for text, _ in chunks:
                preview = get_chunk_preview(text)
                if preview:
                    break
            flagged.append({
                "entity_id": entity_id,
                "entity_type": entity_type,
                "current_name": name_en,
                "name_ja": name_ja or "",
                "chunk_preview": preview,
                "flag_reason": flag_reason,
                "suggested_fix": suggested_fix,
            })

        if len(flagged) >= limit:
            break

    return flagged[:limit]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

COLUMNS = ["entity_id", "entity_type", "current_name", "name_ja", "chunk_preview", "flag_reason", "suggested_fix"]


def write_tsv(rows: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Written {len(rows)} rows → {path}")


def print_tsv(rows: list[dict]):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, delimiter="\t", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    print(buf.getvalue())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Export entity names for canonical translation review")
    ap.add_argument("--type", required=True, help="Entity type: character|location|faction|quest|item|concept|staff")
    ap.add_argument("--batch", type=int, default=1, help="Batch number (1-based)")
    ap.add_argument("--arc", default=None, help="Arc filter for quests: sky|crossbell|cs|daybreak|reverie")
    ap.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing file")
    ap.add_argument("--all", action="store_true", help="Export all flagged entities (no batch limit)")
    args = ap.parse_args()

    entity_type = ENTITY_TYPE_MAP.get(args.type.lower())
    if not entity_type:
        print(f"Unknown entity type: {args.type}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(TRAILS_DB)

    limit = 999999 if args.all else BATCH_SIZE
    offset = (args.batch - 1) if not args.all else 0

    print(f"Scanning {entity_type} entities (batch {args.batch}, offset {offset * BATCH_SIZE})…")
    rows = collect_flagged(conn, entity_type, args.arc, offset, limit)
    conn.close()

    if not rows:
        print("No flagged entities found in this batch.")
        return

    print(f"Found {len(rows)} flagged entities.")

    if args.dry_run:
        print_tsv(rows)
        return

    # Determine output filename
    arc_tag = f"_{args.arc}" if args.arc else ""
    type_short = {"character": "char", "location": "loc", "faction": "fac",
                  "quest": "quest", "item": "item", "concept": "concept", "staff": "staff"}.get(entity_type, entity_type)
    filename = f"review_{type_short}{arc_tag}_{args.batch}.tsv"
    path = os.path.join(TRANSLATION_DIR, filename)
    write_tsv(rows, path)


if __name__ == "__main__":
    main()
