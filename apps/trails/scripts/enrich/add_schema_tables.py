#!/usr/bin/env python3
"""
Add LLM-comprehension schema tables to trails.db:

  entity_summary     — 2-4 sentence synthesis + completeness score per entity
  relationships      — directed graph edges between entities (traversable)
  entity_appearances — arc/game coverage flags per entity
  chunk_mentions     — cross-entity provenance (which chunks mention which entities)

Also seeds entity_appearances from the existing appearance_registry table,
and seeds relationships with 'appears_in' edges from appearance_registry.
"""
import sqlite3, json, re
from collections import defaultdict

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------------------------------------------------------
# 1. entity_summary
# -----------------------------------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS entity_summary (
    entity_id    TEXT PRIMARY KEY REFERENCES entity_registry(entity_id),
    summary      TEXT,
    completeness INTEGER DEFAULT 0,
    updated_at   TEXT
)
""")
print("Created: entity_summary")

# Seed with stub rows for all entities (empty summary, completeness derived from chunk count)
c.execute("SELECT entity_id FROM entity_registry")
all_eids = [r[0] for r in c.fetchall()]

# Compute completeness: 0-100 based on chunk count (>= 5 chunks = 100)
c.execute("""
    SELECT linked_entity_ids FROM chunk_registry WHERE linked_entity_ids IS NOT NULL
""")
eid_chunk_count = defaultdict(int)
for (ids_json,) in c.fetchall():
    try:
        for eid in json.loads(ids_json):
            eid_chunk_count[eid] += 1
    except:
        pass

stub_rows = []
for eid in all_eids:
    n = eid_chunk_count.get(eid, 0)
    completeness = min(100, n * 20)  # 5+ chunks = 100
    stub_rows.append((eid, None, completeness))

c.executemany(
    "INSERT OR IGNORE INTO entity_summary (entity_id, summary, completeness) VALUES (?,?,?)",
    stub_rows
)
print(f"  Seeded {len(stub_rows)} entity_summary rows")

# -----------------------------------------------------------------------
# 2. relationships
# -----------------------------------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS relationships (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  TEXT NOT NULL,
    predicate   TEXT NOT NULL,
    object_id   TEXT NOT NULL,
    context_arc TEXT,
    spoiler_band INTEGER DEFAULT 0,
    UNIQUE (subject_id, predicate, object_id, context_arc)
)
""")
c.execute("CREATE INDEX IF NOT EXISTS idx_rel_subject ON relationships(subject_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_rel_object  ON relationships(object_id)")
print("Created: relationships")

# Seed from appearance_registry: entity appears_in game
c.execute("PRAGMA table_info(appearance_registry)")
cols = [r[1] for r in c.fetchall()]
print(f"  appearance_registry columns: {cols}")

# Check what appearance_registry looks like
c.execute("SELECT * FROM appearance_registry LIMIT 3")
sample = c.fetchall()
print(f"  sample rows: {sample}")

c.execute("SELECT COUNT(*) FROM appearance_registry")
appear_total = c.fetchone()[0]
print(f"  appearance_registry rows: {appear_total}")

if appear_total > 0:
    # Determine column names for entity and game references
    # Common patterns: entity_id + game_id, or subject + object
    entity_col = next((col for col in cols if 'entity' in col.lower()), cols[0] if cols else None)
    game_col   = next((col for col in cols if 'game' in col.lower() or 'media' in col.lower() or 'arc' in col.lower()),
                       cols[1] if len(cols) > 1 else None)

    if entity_col and game_col:
        c.execute(f"SELECT {entity_col}, {game_col} FROM appearance_registry")
        appear_rows = c.fetchall()
        rel_rows = [(eid, 'appears_in', gid, None, 0) for eid, gid in appear_rows if eid and gid]
        c.executemany(
            "INSERT OR IGNORE INTO relationships (subject_id, predicate, object_id, context_arc, spoiler_band) VALUES (?,?,?,?,?)",
            rel_rows
        )
        print(f"  Seeded {len(rel_rows)} 'appears_in' relationships from appearance_registry")

# -----------------------------------------------------------------------
# 3. entity_appearances (arc/game coverage flags)
# -----------------------------------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS entity_appearances (
    entity_id TEXT NOT NULL,
    game_id   TEXT NOT NULL,
    role_type TEXT DEFAULT 'supporting',
    PRIMARY KEY (entity_id, game_id)
)
""")
c.execute("CREATE INDEX IF NOT EXISTS idx_eapp_entity ON entity_appearances(entity_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_eapp_game   ON entity_appearances(game_id)")
print("Created: entity_appearances")

# Seed from appearance_registry if we found the columns
if appear_total > 0 and entity_col and game_col:
    c.execute(f"SELECT DISTINCT {entity_col}, {game_col} FROM appearance_registry")
    eapp_rows = [(eid, gid, 'supporting') for eid, gid in c.fetchall() if eid and gid]
    c.executemany(
        "INSERT OR IGNORE INTO entity_appearances (entity_id, game_id, role_type) VALUES (?,?,?)",
        eapp_rows
    )
    print(f"  Seeded {len(eapp_rows)} entity_appearances rows")

# -----------------------------------------------------------------------
# 4. chunk_mentions (cross-entity provenance via name matching)
# -----------------------------------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS chunk_mentions (
    chunk_id          TEXT NOT NULL,
    mentioned_entity_id TEXT NOT NULL,
    PRIMARY KEY (chunk_id, mentioned_entity_id)
)
""")
c.execute("CREATE INDEX IF NOT EXISTS idx_cment_chunk  ON chunk_mentions(chunk_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_cment_entity ON chunk_mentions(mentioned_entity_id)")
print("Created: chunk_mentions")

# Build name→entity_id lookup from entity_registry + aliases
c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE english_display_name IS NOT NULL")
name_to_eids = defaultdict(list)
for eid, name in c.fetchall():
    if name and len(name) > 3:  # skip very short names (too many false positives)
        name_to_eids[name.lower()].append(eid)

# Also load aliases
try:
    c.execute("SELECT entity_id, alias FROM aliases WHERE alias IS NOT NULL")
    for eid, alias in c.fetchall():
        if alias and len(alias) > 3:
            name_to_eids[alias.lower()].append(eid)
    print(f"  Loaded aliases for mention matching")
except Exception as e:
    print(f"  No aliases table: {e}")

print(f"  Name lookup: {len(name_to_eids)} distinct names")

# Build set of entity names sorted by length (longer first to avoid partial matches)
sorted_names = sorted(name_to_eids.keys(), key=len, reverse=True)

# Scan chunks for entity mentions
c.execute("SELECT chunk_id, linked_entity_ids, text_content FROM chunk_registry WHERE text_content IS NOT NULL")
chunks = c.fetchall()

mention_rows = []
BATCH_SIZE = 1000

for chunk_id, ids_json, text in chunks:
    if not text or len(text) < 10:
        continue
    text_lower = text.lower()

    # Get the entities already linked to this chunk (don't add as "mentions" — they're the subject)
    try:
        linked = set(json.loads(ids_json)) if ids_json else set()
    except:
        linked = set()

    # Find names mentioned in the text
    found = set()
    for name in sorted_names:
        if name in text_lower:
            for eid in name_to_eids[name]:
                if eid not in linked:
                    found.add(eid)
            if len(found) > 50:  # cap mentions per chunk
                break

    for eid in found:
        mention_rows.append((chunk_id, eid))

    if len(mention_rows) >= BATCH_SIZE:
        c.executemany(
            "INSERT OR IGNORE INTO chunk_mentions (chunk_id, mentioned_entity_id) VALUES (?,?)",
            mention_rows
        )
        mention_rows.clear()

if mention_rows:
    c.executemany(
        "INSERT OR IGNORE INTO chunk_mentions (chunk_id, mentioned_entity_id) VALUES (?,?)",
        mention_rows
    )

print(f"  Populated chunk_mentions from {len(chunks)} chunks")

conn.commit()

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
print(f"\n=== Schema tables summary ===")
for tbl in ('entity_summary', 'relationships', 'entity_appearances', 'chunk_mentions'):
    c.execute(f"SELECT COUNT(*) FROM {tbl}")
    print(f"  {tbl}: {c.fetchone()[0]} rows")

# Verify completeness distribution
c.execute("SELECT completeness, COUNT(*) FROM entity_summary GROUP BY completeness ORDER BY completeness")
print(f"\nCompleteness distribution:")
for comp, cnt in c.fetchall():
    print(f"  {comp:3d}: {cnt} entities")

conn.close()
print("\nDone.")
