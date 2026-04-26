#!/usr/bin/env python3
"""
Purge wiki subsection artifacts from entity_registry (v2 — entity_id discriminator).

After the v1 over-deletion + recovery pass, artifact entity_ids had their slashes
stripped during ingestion normalization. Patterns are detectable by entity_id:

  Pattern A — fused suffix: entity_id ends with a wiki section keyword.
    concept:agate_crosnergallery   concept:agate_crosnerstory   concept:agate_crosnergameplay

  Pattern B — bonding aggregate (not the base concept:bonding entity).
    concept:bondingtrails_from_zero   concept:bondingtrails_of_cold_steel

  Pattern C — list_of aggregate pages.
    concept:list_of_enemies_sky_fc   concept:list_of_achievements_azure

Chunk handling before deletion:
  - Gallery / portraits / bonding / list_of chunks → DELETE (image markup / index pages)
  - Story / gameplay chunks → RE-ATTRIBUTE to parent character entity

Parent lookup: strip fused suffix → try char:X, fallback concept:X.

Dry-run by default. Pass --apply to commit.
"""
import sqlite3, sys, json
from collections import Counter, defaultdict

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
APPLY = '--apply' in sys.argv

# Section suffixes — fused onto character name in entity_id
DELETE_SUFFIXES   = ('gallery', 'portraits')      # image/visual pages — delete chunks
REATTR_SUFFIXES   = ('story', 'gameplay', 'strategy', 'navigation', 'trivia', 'quotes')  # prose — re-attribute

ALL_SUFFIXES = DELETE_SUFFIXES + REATTR_SUFFIXES

conn = sqlite3.connect(DB)
c = conn.cursor()

# Load all entity_ids for fast lookup
c.execute("SELECT entity_id FROM entity_registry")
existing_ids = set(r[0] for r in c.fetchall())

c.execute("SELECT entity_id, entity_type, english_display_name FROM entity_registry ORDER BY entity_id")
all_entities = c.fetchall()

artifacts_delete_chunks = []   # (eid, etype, name, reason) — chunks deleted
artifacts_reattr_chunks = []   # (eid, etype, name, suffix) — chunks re-attributed to parent

for eid, etype, name in all_entities:
    # Pattern A — fused delete suffix
    matched = next((s for s in DELETE_SUFFIXES if eid.endswith(s) and len(eid) > len('concept:') + len(s)), None)
    if matched:
        artifacts_delete_chunks.append((eid, etype, name, f'fused:{matched}'))
        continue

    # Pattern A — fused re-attribute suffix
    matched = next((s for s in REATTR_SUFFIXES if eid.endswith(s) and len(eid) > len('concept:') + len(s)), None)
    if matched:
        artifacts_reattr_chunks.append((eid, etype, name, matched))
        continue

    # Pattern B — bonding aggregate
    if eid.startswith('concept:bonding') and eid != 'concept:bonding':
        artifacts_delete_chunks.append((eid, etype, name, 'bonding_aggregate'))
        continue

    # Pattern C — list_of aggregate
    if eid.startswith('concept:list_of'):
        artifacts_delete_chunks.append((eid, etype, name, 'list_of_aggregate'))
        continue

all_artifacts = artifacts_delete_chunks + [(e,t,n,s) for e,t,n,s in artifacts_reattr_chunks]
artifact_ids  = [eid for eid,_,_,_ in all_artifacts]

print(f"Total artifacts: {len(all_artifacts)}")
print(f"  Delete-chunks: {len(artifacts_delete_chunks)}")
print(f"  Re-attr-chunks: {len(artifacts_reattr_chunks)}")

reasons = Counter(r for _,_,_,r in all_artifacts)
print(f"\nBy reason:")
for r, n in reasons.most_common():
    print(f"  {r}: {n}")

# -----------------------------------------------------------------------
# Build parent lookup map for re-attribution
# -----------------------------------------------------------------------
def find_parent(artifact_eid, suffix):
    """Strip fused suffix, try char: then concept: prefix."""
    base = artifact_eid[len('concept:'):][:-len(suffix)]  # strip 'concept:' prefix and suffix
    base = base.rstrip('_')
    for prefix in ('char:', 'concept:', 'faction:', 'loc:'):
        candidate = prefix + base
        if candidate in existing_ids:
            return candidate
    return None

parent_map = {}  # artifact_eid → parent_eid
unresolved = []
for eid, etype, name, suffix in artifacts_reattr_chunks:
    parent = find_parent(eid, suffix)
    if parent:
        parent_map[eid] = parent
    else:
        unresolved.append(eid)

print(f"\nRe-attribution parent lookup:")
print(f"  Resolved:   {len(parent_map)}")
print(f"  Unresolved: {len(unresolved)}")
if unresolved:
    print(f"  Sample unresolved (first 10):")
    for eid in unresolved[:10]:
        print(f"    {eid}")

# -----------------------------------------------------------------------
# Chunk analysis
# -----------------------------------------------------------------------
# Count chunks for delete-type artifacts
delete_artifact_ids = [eid for eid,_,_,_ in artifacts_delete_chunks]
c.execute(f"SELECT COUNT(*) FROM chunk_registry WHERE chunk_id IN (SELECT chunk_id FROM chunk_registry WHERE {' OR '.join(['linked_entity_ids LIKE ?' for _ in delete_artifact_ids[:20]])})",
          [f'%{eid}%' for eid in delete_artifact_ids[:20]])

# Simpler: just count directly
chunk_del_count = 0
for eid in delete_artifact_ids:
    c.execute("SELECT COUNT(*) FROM chunk_registry WHERE linked_entity_ids LIKE ?", (f'%{eid}%',))
    chunk_del_count += c.fetchone()[0]

chunk_reattr_count = 0
for eid in parent_map:
    c.execute("SELECT COUNT(*) FROM chunk_registry WHERE linked_entity_ids LIKE ?", (f'%{eid}%',))
    chunk_reattr_count += c.fetchone()[0]

print(f"\nChunk impact:")
print(f"  Chunks to DELETE:       {chunk_del_count}")
print(f"  Chunks to RE-ATTRIBUTE: {chunk_reattr_count}")

# Sample re-attribution
print(f"\nSample re-attributions (first 10):")
sample_shown = 0
for eid, parent in list(parent_map.items())[:10]:
    print(f"  {eid} → {parent}")
    sample_shown += 1

# Cross-registry counts
def count_in(table, column, ids):
    total = 0
    for i in range(0, len(ids), 500):
        batch = ids[i:i+500]
        c.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IN ({','.join('?'*len(batch))})", batch)
        total += c.fetchone()[0]
    return total

appear_count   = count_in('appearance_registry', 'entity_id', artifact_ids)
lifecycle_count= count_in('lifecycle_registry', 'object_id', artifact_ids)
alias_count    = count_in('aliases', 'entity_id', artifact_ids)

print(f"\nCross-registry rows to delete:")
print(f"  appearance_registry: {appear_count}")
print(f"  lifecycle_registry:  {lifecycle_count}")
print(f"  aliases:             {alias_count}")
print(f"\nEntity count after: {len(existing_ids) - len(all_artifacts)}")

print(f"\n{'--- DRY RUN ---' if not APPLY else '--- APPLYING ---'}")

if APPLY:
    print("\nStep 1: Delete chunks for delete-type artifacts...")
    del_chunk_count = 0
    for i, eid in enumerate(delete_artifact_ids):
        c.execute("DELETE FROM chunk_registry WHERE linked_entity_ids LIKE ?", (f'%{eid}%',))
        del_chunk_count += c.rowcount
    print(f"  Deleted {del_chunk_count} chunks")

    print("\nStep 2: Re-attribute story/gameplay chunks to parent entities...")
    reattr_count = 0
    for artifact_eid, parent_eid in parent_map.items():
        # Get all chunks linked to this artifact
        c.execute("SELECT chunk_id, linked_entity_ids FROM chunk_registry WHERE linked_entity_ids LIKE ?",
                  (f'%{artifact_eid}%',))
        rows = c.fetchall()
        for chunk_id, ids_json in rows:
            try:
                ids = json.loads(ids_json) if ids_json else []
            except:
                ids = [ids_json] if ids_json else []

            # Replace artifact_eid with parent_eid
            new_ids = [parent_eid if eid == artifact_eid else eid for eid in ids]
            # Deduplicate while preserving order
            seen = set()
            deduped = [x for x in new_ids if not (x in seen or seen.add(x))]

            c.execute("UPDATE chunk_registry SET linked_entity_ids=? WHERE chunk_id=?",
                      (json.dumps(deduped), chunk_id))
            reattr_count += 1

        # Delete chunks where artifact was the ONLY linked entity (nothing to re-attribute to)
        # (covered above — parent_eid now in the list, so chunk is kept)

    print(f"  Re-attributed {reattr_count} chunk records")

    print("\nStep 3: Delete unresolved artifact chunks (no parent found)...")
    unresolved_del = 0
    for eid in unresolved:
        c.execute("DELETE FROM chunk_registry WHERE linked_entity_ids LIKE ?", (f'%{eid}%',))
        unresolved_del += c.rowcount
    print(f"  Deleted {unresolved_del} chunks (no parent)")

    print("\nStep 4: Delete artifact entities from all registries...")
    def batch_delete(table, column, ids):
        deleted = 0
        for i in range(0, len(ids), 500):
            batch = ids[i:i+500]
            c.execute(f"DELETE FROM {table} WHERE {column} IN ({','.join('?'*len(batch))})", batch)
            deleted += c.rowcount
        return deleted

    d1 = batch_delete('entity_registry',    'entity_id', artifact_ids)
    d2 = batch_delete('appearance_registry','entity_id', artifact_ids)
    d3 = batch_delete('lifecycle_registry', 'object_id', artifact_ids)
    d4 = batch_delete('aliases',            'entity_id', artifact_ids)

    conn.commit()

    print(f"\nDeleted from registries:")
    print(f"  entity_registry:     {d1}")
    print(f"  appearance_registry: {d2}")
    print(f"  lifecycle_registry:  {d3}")
    print(f"  aliases:             {d4}")

    print(f"\nFinal entity_type breakdown:")
    c.execute("SELECT entity_type, COUNT(*) FROM entity_registry GROUP BY entity_type ORDER BY COUNT(*) DESC")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")
    c.execute("SELECT COUNT(*) FROM entity_registry")
    print(f"  TOTAL: {c.fetchone()[0]}")

    print(f"\nChunk_registry total:")
    c.execute("SELECT COUNT(*) FROM chunk_registry")
    print(f"  {c.fetchone()[0]}")

conn.close()
