#!/usr/bin/env python3
"""
Migrate location data in entity_registry:
1. Fix 'location:' prefix → 'loc:' (normalize ID scheme)
2. Reclassify concept → location for actual geographic places

Dry-run by default; pass --apply to commit changes.
"""
import sqlite3, sys, re

DB = '/mnt/c/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
APPLY = '--apply' in sys.argv

conn = sqlite3.connect(DB)
c = conn.cursor()

# ---------------------------------------------------------------------------
# 1. Fix location: → loc: prefix
# ---------------------------------------------------------------------------
# Check for conflicts (loc:X already exists when we rename location:X)
c.execute("SELECT entity_id FROM entity_registry WHERE entity_id LIKE 'location:%'")
location_prefix = [r[0] for r in c.fetchall()]

prefix_renames = []
prefix_conflicts = []
for old_id in location_prefix:
    new_id = 'loc:' + old_id[len('location:'):]
    c.execute("SELECT 1 FROM entity_registry WHERE entity_id=?", (new_id,))
    if c.fetchone():
        prefix_conflicts.append((old_id, new_id))
    else:
        prefix_renames.append((old_id, new_id))

print(f"Prefix renames (location: → loc:): {len(prefix_renames)}")
for old, new in prefix_renames:
    print(f"  {old} → {new}")

if prefix_conflicts:
    print(f"\nPrefix conflicts (both exist — will keep loc: version, delete location: duplicate): {len(prefix_conflicts)}")
    for old, new in prefix_conflicts:
        print(f"  DROP {old} (duplicate of {new})")

# ---------------------------------------------------------------------------
# 2. Reclassify concept → location
# ---------------------------------------------------------------------------

# Exclusion patterns — clearly NOT geographic places
EXCLUDE_SUFFIXES = [
    '/gallery', '/story', '/gameplay', '/portraits', '/strategy',
    '/bonding', '/navigation', '/trivia', '/quotes', '/other',
    'gallery', 'gameplay', 'portraits', 'strategy', 'bonding'
]
EXCLUDE_KEYWORDS = ['npc', 'standoff', 'tragedy', 'incident', 'operation ',
                    'list of enemies', 'list of ', 'bonding/', 'cryptid survey',
                    'tourist information', 'times_azure', 'times_zero',
                    'back alley doctor', 'festival', 'an invitation to',
                    'guild job', 'side quest', 'sub quest']
EXCLUDE_ID_PATTERNS = [
    r'.*/gallery$', r'.*/story$', r'.*/gameplay$', r'.*/portraits$',
    r'.*_npc_.*', r'concept:bonding.*',
    r'concept:list_of_.*', r'concept:cryptid_.*',
    r'concept:crossbell_times.*', r'concept:crossbell_province_tourist.*',
]

# Inclusion patterns — clearly geographic
INCLUDE_ID_PATTERNS = [
    r'concept:city_of_.*',
    r'concept:crossbell_city.*',
    r'concept:edith.*',
    r'concept:heimdallr.*',
    r'concept:grancel.*',
    r'concept:armorica_village',
    r'concept:bryonia_island',
    r'concept:elmo_village',
    r'concept:hamel$',
    r'concept:hamel_road',
    r'concept:eryn$',
    r'concept:capel$',
    r'concept:felicity$',
]
INCLUDE_NAME_PATTERNS = [
    r'\b(village|island|bay|coast|harbor|port|road|gate|fort(ress)?|castle|tower|shrine|cathedral|station|academy|highway|trail|canyon|valley|mine|ruins|palace|plaza|square|district|quarter|street|avenue|alley|underground|passage|waterway|airport|racecourse|park|circuit|marketplace|market)\b',
    r'\bcity of\b',
]

c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE entity_type='concept' ORDER BY entity_id")
all_concepts = c.fetchall()

to_reclassify = []
for eid, name in all_concepts:
    name_lower = (name or '').lower()
    id_lower = eid.lower()

    # Hard exclusions
    if any(re.search(p, id_lower) for p in EXCLUDE_ID_PATTERNS):
        continue
    if any(kw in name_lower for kw in EXCLUDE_KEYWORDS):
        continue
    if any(name_lower.endswith(s) for s in EXCLUDE_SUFFIXES):
        continue

    # Include by ID pattern
    if any(re.match(p, id_lower) for p in INCLUDE_ID_PATTERNS):
        to_reclassify.append((eid, name, 'id_pattern'))
        continue

    # Include by name pattern
    if any(re.search(p, name_lower) for p in INCLUDE_NAME_PATTERNS):
        to_reclassify.append((eid, name, 'name_pattern'))

print(f"\nConcepts → location reclassification: {len(to_reclassify)}")
for eid, name, reason in sorted(to_reclassify):
    print(f"  [{reason}] {eid}: {name}")

print(f"\n{'--- DRY RUN ---' if not APPLY else '--- APPLYING ---'}")
print(f"  Prefix renames: {len(prefix_renames)}")
print(f"  Prefix drops (conflicts): {len(prefix_conflicts)}")
print(f"  Concept→location reclassifications: {len(to_reclassify)}")
print(f"  New total locations: {50 + len(prefix_renames) + len(to_reclassify)}")

if APPLY:
    # Rename location: → loc:
    for old_id, new_id in prefix_renames:
        c.execute("UPDATE entity_registry SET entity_id=? WHERE entity_id=?", (new_id, old_id))
        # Update appearance_registry, aliases, etc.
        for tbl, col in [('appearance_registry','entity_id'), ('aliases','entity_id'),
                         ('lifecycle_registry','object_id'), ('chunk_registry','linked_entity_ids')]:
            try:
                if col == 'linked_entity_ids':
                    c.execute(f"UPDATE {tbl} SET {col}=REPLACE({col},?,?) WHERE {col} LIKE ?",
                              (old_id, new_id, f'%{old_id}%'))
                else:
                    c.execute(f"UPDATE {tbl} SET {col}=? WHERE {col}=?", (new_id, old_id))
            except Exception:
                pass

    # Remove duplicate location: entries that already have a loc: equivalent
    for old_id, new_id in prefix_conflicts:
        c.execute("DELETE FROM entity_registry WHERE entity_id=?", (old_id,))

    # Reclassify concept → location
    ids = [row[0] for row in to_reclassify]
    c.executemany("UPDATE entity_registry SET entity_type='location' WHERE entity_id=?",
                  [(eid,) for eid in ids])

    conn.commit()
    print("\nApplied. New counts:")
    c.execute("SELECT entity_type, COUNT(*) FROM entity_registry GROUP BY entity_type ORDER BY COUNT(*) DESC")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")

conn.close()
