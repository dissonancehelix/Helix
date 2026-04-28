#!/usr/bin/env python3
"""
Normalize english_display_name for all entities.

Problems:
1. Recovered entities have slugified names: "Daydreamsa Day In The Lives Of The Sss"
2. Some entities have garbled concatenated names from lost-slash reconstruction

Strategy: extract canonical name from chunk text (wiki bold '''Name''' pattern).
Chunk text reliably opens with the canonical English title in bold markup.

Also: flag entities with suspected non-canonical names for review.

Dry-run by default. Pass --apply to commit.
"""
import sqlite3, sys, re, json
from collections import Counter

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
APPLY = '--apply' in sys.argv

BOLD_RE = re.compile(r"'''(.+?)'''")

conn = sqlite3.connect(DB)
c = conn.cursor()

def extract_canonical_name(text):
    """Extract first '''...''' bold from wiki text."""
    if not text:
        return None
    m = BOLD_RE.search(text[:500])
    if not m:
        return None
    name = m.group(1).strip()
    # Skip if it looks like a wiki category / template artifact
    if name.startswith('[[') or name.startswith('{{') or len(name) > 120:
        return None
    # Skip JP-only names (all non-ASCII)
    ascii_ratio = sum(1 for ch in name if ord(ch) < 128) / max(len(name), 1)
    if ascii_ratio < 0.5:
        return None
    return name

def looks_reconstructed(name, eid):
    """Detect names that were reconstructed from entity_id slugs."""
    if not name:
        return True
    slug = eid.split(':', 1)[-1].replace('_', ' ').title()
    # Exact match with slug means it was reconstructed
    if name == slug:
        return True
    # Obvious garbled patterns: no spaces between what should be separate words
    # e.g. "Daydreamsa Day" (Daydreams + a Day)
    if re.search(r'[a-z][A-Z]', name):
        return True
    return False

# Load all entities
c.execute("SELECT entity_id, entity_type, english_display_name FROM entity_registry ORDER BY entity_id")
all_entities = c.fetchall()

# For each entity, try to find a canonical name from chunks
updates = []   # (new_name, entity_id)
no_chunk = []
bad_extract = []
already_good = []

for eid, etype, current_name in all_entities:
    if not looks_reconstructed(current_name, eid):
        already_good.append(eid)
        continue

    # Find best chunk: prefer 'lead' type, then any
    c2 = conn.cursor()
    c2.execute("""
        SELECT text_content, chunk_type FROM chunk_registry
        WHERE linked_entity_ids LIKE ?
        ORDER BY CASE chunk_type WHEN 'lead' THEN 0 WHEN 'raw' THEN 1 ELSE 2 END
        LIMIT 5
    """, (f'%{eid}%',))
    rows = c2.fetchall()

    if not rows:
        no_chunk.append((eid, current_name))
        continue

    canonical = None
    for text, ctype in rows:
        canonical = extract_canonical_name(text)
        if canonical:
            break

    if canonical and canonical != current_name:
        # Don't apply if current name has a parenthetical disambiguation and the
        # extracted name doesn't — the disambig is intentional.
        has_disambig = re.search(r'\([\w\s]+\)$', current_name)
        extracted_has_disambig = re.search(r'\([\w\s]+\)$', canonical)
        if has_disambig and not extracted_has_disambig:
            bad_extract.append((eid, current_name, f'[kept disambig] → {canonical}'))
            continue
        # Don't apply if the extracted name is strictly shorter (losing info)
        # unless the current name is clearly a slug reconstruction
        clearly_reconstructed = (current_name == eid.split(':',1)[-1].replace('_',' ').title())
        if len(canonical) < len(current_name) - 5 and not clearly_reconstructed:
            bad_extract.append((eid, current_name, f'[shorter, skipped] → {canonical}'))
            continue
        updates.append((canonical, eid))
    else:
        bad_extract.append((eid, current_name, rows[0][0][:80] if rows else ''))

print(f"Total entities: {len(all_entities)}")
print(f"  Already canonical:  {len(already_good)}")
print(f"  Names to update:    {len(updates)}")
print(f"  No chunks found:    {len(no_chunk)}")
print(f"  Could not extract:  {len(bad_extract)}")

# By entity type
update_types = Counter()
for _, eid in updates:
    c.execute("SELECT entity_type FROM entity_registry WHERE entity_id=?", (eid,))
    r = c.fetchone()
    if r:
        update_types[r[0]] += 1
print(f"\nUpdates by entity_type: {dict(update_types)}")

print(f"\nSample updates (first 20):")
for new_name, eid in updates[:20]:
    c.execute("SELECT english_display_name FROM entity_registry WHERE entity_id=?", (eid,))
    old = c.fetchone()[0]
    print(f"  {eid}")
    print(f"    '{old}' → '{new_name}'")

if bad_extract[:10]:
    print(f"\nSample failures (first 10):")
    for eid, name, chunk_preview in bad_extract[:10]:
        print(f"  {eid}: {name}")
        print(f"    chunk: {chunk_preview}")

print(f"\n{'--- DRY RUN ---' if not APPLY else '--- APPLYING ---'}")
print(f"Will update {len(updates)} display names")

if APPLY:
    c.executemany("UPDATE entity_registry SET english_display_name=? WHERE entity_id=?", updates)
    conn.commit()
    print(f"Updated {c.rowcount} rows")

    # Verify spot-check
    print(f"\nSpot-check (10 quest names after update):")
    c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE entity_type='quest' LIMIT 10")
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}")

conn.close()
