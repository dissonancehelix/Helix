#!/usr/bin/env python3
"""
Extract typed relationship edges from chunk_registry text into relationships table.

Predicates extracted:
  member_of      — character mentioned in faction/org chunk
  trained_under  — "trained under X", "student of X", "taught by X"
  mentor_of      — inverse of trained_under
  family         — "X's father/mother/sister/brother/son/daughter"
  allied_with    — "allies with", "allied with"
  rivals         — "rival", "sworn enemy", "nemesis"
  wields         — "wields X", "uses X arts/sword/weapon"

Already in table from appearance_registry: appears_in
"""
import sqlite3, json, re
from collections import defaultdict

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------------------------------------------------------
# Build name→entity_id lookup (same as ingestion pipeline)
# -----------------------------------------------------------------------
c.execute("""
    SELECT entity_id, english_display_name, entity_type
    FROM entity_registry WHERE english_display_name IS NOT NULL
""")
name_to_eid = {}
eid_to_type = {}
for eid, name, etype in c.fetchall():
    if name and len(name) > 2:
        name_to_eid[name.lower()] = eid
        eid_to_type[eid] = etype

c.execute("SELECT entity_id, alias FROM aliases WHERE alias IS NOT NULL")
for eid, alias in c.fetchall():
    if alias and len(alias) > 2:
        name_to_eid.setdefault(alias.lower(), eid)

# Sort names by length (longer first to avoid partial matches)
sorted_names = sorted(name_to_eid.keys(), key=len, reverse=True)

def find_entity(text_fragment):
    """Find first entity name match in a text fragment."""
    text_lower = text_fragment.lower()
    for name in sorted_names:
        if len(name) < 4:
            continue
        if name in text_lower:
            return name_to_eid[name]
    return None

# -----------------------------------------------------------------------
# Relationship patterns
# -----------------------------------------------------------------------
FAMILY_PATTERNS = [
    (r"(\w[\w\s']{1,30}?)'s (?:father|dad)", 'child_of'),
    (r"(\w[\w\s']{1,30}?)'s (?:mother|mom)", 'child_of'),
    (r"(\w[\w\s']{1,30}?)'s (?:son)", 'parent_of'),
    (r"(\w[\w\s']{1,30}?)'s (?:daughter)", 'parent_of'),
    (r"(\w[\w\s']{1,30}?)'s (?:brother|sister|sibling)", 'sibling_of'),
    (r'father of (\w[\w\s\']{1,30})', 'parent_of'),
    (r'mother of (\w[\w\s\']{1,30})', 'parent_of'),
    (r'son of (\w[\w\s\']{1,30})', 'child_of'),
    (r'daughter of (\w[\w\s\']{1,30})', 'child_of'),
]

TRAINED_PATTERNS = [
    r'trained under (\w[\w\s\']{1,30})',
    r'student of (\w[\w\s\']{1,30})',
    r'taught by (\w[\w\s\']{1,30})',
    r'disciple of (\w[\w\s\']{1,30})',
    r'apprentice (?:to|of) (\w[\w\s\']{1,30})',
]

MENTOR_PATTERNS = [
    r'(?:trains?|trained|teaches?|taught) (\w[\w\s\']{1,30})',
    r'master (?:to|of) (\w[\w\s\']{1,30})',
    r'mentor(?:s|ed)? (\w[\w\s\']{1,30})',
]

RIVAL_PATTERNS = [
    r'rival(?:s|ry)? (?:of|with|to) (\w[\w\s\']{1,30})',
    r'sworn enemy of (\w[\w\s\']{1,30})',
    r'nemesis (?:of|to) (\w[\w\s\']{1,30})',
]

ALLIED_PATTERNS = [
    r'allied? with (\w[\w\s\']{1,30})',
    r'allies? with (\w[\w\s\']{1,30})',
    r'allied? alongside (\w[\w\s\']{1,30})',
]

# -----------------------------------------------------------------------
# Load all chunks and extract relationships
# -----------------------------------------------------------------------
c.execute("""
    SELECT chunk_id, linked_entity_ids, text_content, chunk_type
    FROM chunk_registry
    WHERE text_content IS NOT NULL AND language='en'
""")
chunks = c.fetchall()
print(f"Processing {len(chunks)} EN chunks...")

new_rels = []  # (subject_id, predicate, object_id, context_arc, spoiler_band)

def add_rel(subj, pred, obj, arc=None, band=0):
    if subj and obj and subj != obj:
        new_rels.append((subj, pred, obj, arc, band))

for chunk_id, ids_json, text, ctype in chunks:
    if not text:
        continue
    try:
        linked = json.loads(ids_json) if ids_json else []
    except:
        linked = []

    if not linked:
        continue

    subject_id = linked[0]  # primary entity this chunk is about
    subject_type = eid_to_type.get(subject_id, '')
    text_lower = text.lower()

    # -- member_of: character chunk mentions a faction by name
    if subject_type == 'character':
        for name in sorted_names:
            if len(name) < 4:
                continue
            target_eid = name_to_eid[name]
            if target_eid == subject_id:
                continue
            if eid_to_type.get(target_eid) == 'faction' and name in text_lower:
                add_rel(subject_id, 'member_of', target_eid)
                break  # one faction per chunk

    # -- trained_under
    for pat in TRAINED_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            obj = find_entity(m.group(1))
            if obj:
                add_rel(subject_id, 'trained_under', obj)

    # -- mentor_of
    for pat in MENTOR_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            obj = find_entity(m.group(1))
            if obj:
                add_rel(subject_id, 'mentor_of', obj)

    # -- rivals
    for pat in RIVAL_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            obj = find_entity(m.group(1))
            if obj:
                add_rel(subject_id, 'rivals', obj)

    # -- allied_with
    for pat in ALLIED_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            obj = find_entity(m.group(1))
            if obj:
                add_rel(subject_id, 'allied_with', obj)

    # -- family patterns
    for pat, pred in FAMILY_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            obj = find_entity(m.group(1))
            if obj:
                add_rel(subject_id, pred, obj)

print(f"Extracted {len(new_rels)} candidate relationships")

# Deduplicate
unique_rels = list({(s,p,o,a): (s,p,o,a,b) for s,p,o,a,b in new_rels}.values())
print(f"After dedup: {len(unique_rels)}")

# Count by predicate
from collections import Counter
pred_counts = Counter(r[1] for r in unique_rels)
print("\nBy predicate:")
for pred, count in pred_counts.most_common():
    print(f"  {pred}: {count}")

# Insert (skip existing appears_in rows)
inserted = 0
for subj, pred, obj, arc, band in unique_rels:
    try:
        c.execute("""
            INSERT OR IGNORE INTO relationships (subject_id, predicate, object_id, context_arc, spoiler_band)
            VALUES (?,?,?,?,?)
        """, (subj, pred, obj, arc, band))
        inserted += c.rowcount
    except Exception as e:
        pass

conn.commit()
print(f"\nInserted {inserted} new relationship rows")

c.execute("SELECT predicate, COUNT(*) FROM relationships GROUP BY predicate ORDER BY COUNT(*) DESC")
print("\nFinal relationships table:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")
c.execute("SELECT COUNT(*) FROM relationships")
print(f"  TOTAL: {c.fetchone()[0]}")

conn.close()
