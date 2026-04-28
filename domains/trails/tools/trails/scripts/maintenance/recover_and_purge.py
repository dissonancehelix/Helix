#!/usr/bin/env python3
"""
Combined recovery + purge script.

State: entity_registry is missing 2,765 entities that are still referenced
in chunk_registry. These fall into two categories:

  ARTIFACTS (do not restore, re-attribute or delete their chunks):
    - Fused suffix: concept:*gallery, *gameplay, *story, *portraits
    - Bonding aggregates: concept:bonding*  (not concept:bonding)
    - List-of aggregates: concept:list_of*

  LEGITIMATE (restore to entity_registry):
    - All quest: entities
    - All item: entities
    - concept: entities that don't match artifact patterns

For artifact story/gameplay chunks → re-attribute to parent character entity.
For artifact gallery/portraits/list_of/bonding chunks → delete from chunk_registry.

Dry-run by default. Pass --apply to commit.
"""
import sqlite3, sys, json, re
from collections import Counter

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
APPLY = '--apply' in sys.argv

DELETE_SUFFIXES = ('gallery', 'portraits')
REATTR_SUFFIXES = ('story', 'gameplay', 'strategy', 'navigation', 'trivia', 'quotes')
ALL_SUFFIXES    = DELETE_SUFFIXES + REATTR_SUFFIXES

conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------------------------------------------------------
# Find all missing entity_ids
# -----------------------------------------------------------------------
c.execute('SELECT DISTINCT linked_entity_ids FROM chunk_registry WHERE linked_entity_ids IS NOT NULL')
referenced = set()
for (ids_json,) in c.fetchall():
    try:
        for eid in json.loads(ids_json):
            referenced.add(eid)
    except: pass

c.execute('SELECT entity_id FROM entity_registry')
existing_ids = set(r[0] for r in c.fetchall())
missing = sorted(referenced - existing_ids)

# -----------------------------------------------------------------------
# Classify each missing entity_id
# -----------------------------------------------------------------------
to_restore   = []   # (eid, type, display_name)
artifacts_reattr  = []   # (eid, suffix)  — story/gameplay, re-attribute chunks
artifacts_delete  = []   # eid             — gallery/list_of, delete chunks

def is_artifact(eid):
    """Returns (is_artifact, reason, suffix_if_reattr)"""
    # Fused delete suffix
    for s in DELETE_SUFFIXES:
        if eid.endswith(s) and len(eid) > len('concept:') + len(s):
            return True, 'delete', None
    # Fused re-attribute suffix
    for s in REATTR_SUFFIXES:
        if eid.endswith(s) and len(eid) > len('concept:') + len(s):
            return True, 'reattr', s
    # Bonding aggregate
    if eid.startswith('concept:bonding') and eid != 'concept:bonding':
        return True, 'delete', None
    # List-of aggregate
    if eid.startswith('concept:list_of'):
        return True, 'delete', None
    return False, None, None

def infer_type(eid):
    prefix = eid.split(':')[0]
    return {'quest':'quest','item':'item','concept':'concept','char':'character',
            'faction':'faction','loc':'location','staff':'staff',
            'media':'main_game','lore':'concept'}.get(prefix, 'concept')

def make_display_name(eid):
    """Reconstruct display name from entity_id slug."""
    slug = eid.split(':', 1)[-1]
    # Title-case words, preserve known abbreviations
    return slug.replace('_', ' ').title()

for eid in missing:
    art, reason, suffix = is_artifact(eid)
    if art:
        if reason == 'reattr':
            artifacts_reattr.append((eid, suffix))
        else:
            artifacts_delete.append(eid)
    else:
        etype = infer_type(eid)
        name  = make_display_name(eid)
        to_restore.append((eid, etype, name))

print(f"Missing entity_ids: {len(missing)}")
print(f"  To restore:           {len(to_restore)}")
print(f"  Artifacts (re-attr):  {len(artifacts_reattr)}")
print(f"  Artifacts (delete):   {len(artifacts_delete)}")

by_type = Counter(t for _,t,_ in to_restore)
print(f"\nRestore by type: {dict(by_type)}")

# -----------------------------------------------------------------------
# Build parent map for re-attribution
# -----------------------------------------------------------------------
def find_parent(artifact_eid, suffix):
    base = artifact_eid[len('concept:'):][:-len(suffix)].rstrip('_')
    for prefix in ('char:', 'concept:', 'faction:', 'loc:'):
        candidate = prefix + base
        if candidate in existing_ids:
            return candidate
    return None

parent_map = {}
unresolved_reattr = []
for eid, suffix in artifacts_reattr:
    parent = find_parent(eid, suffix)
    if parent:
        parent_map[eid] = parent
    else:
        unresolved_reattr.append(eid)

print(f"\nRe-attribution parent lookup:")
print(f"  Resolved:   {len(parent_map)}")
print(f"  Unresolved (will drop chunks): {len(unresolved_reattr)}")
if unresolved_reattr[:5]:
    print(f"  Sample unresolved: {unresolved_reattr[:5]}")

# Sample restore list
print(f"\nSample entities to restore (first 10):")
for eid, etype, name in to_restore[:10]:
    print(f"  [{etype}] {eid}: {name}")

# -----------------------------------------------------------------------
# Chunk impact summary
# -----------------------------------------------------------------------
print(f"\n{'--- DRY RUN ---' if not APPLY else '--- APPLYING ---'}")

if APPLY:
    print("\n[1/4] Restoring legitimate entities to entity_registry...")
    c.executemany(
        'INSERT OR IGNORE INTO entity_registry (entity_id, entity_type, english_display_name) VALUES (?,?,?)',
        to_restore
    )
    print(f"  Inserted: {c.rowcount} (may differ — INSERT OR IGNORE)")
    conn.commit()

    # Re-fetch existing_ids after restore
    c.execute('SELECT entity_id FROM entity_registry')
    existing_ids = set(r[0] for r in c.fetchall())

    print(f"\n[2/4] Re-attributing story/gameplay chunks to parent entities...")
    reattr_chunk_count = 0
    for artifact_eid, parent_eid in parent_map.items():
        c.execute("SELECT chunk_id, linked_entity_ids FROM chunk_registry WHERE linked_entity_ids LIKE ?",
                  (f'%{artifact_eid}%',))
        rows = c.fetchall()
        for chunk_id, ids_json in rows:
            try:
                ids = json.loads(ids_json) if ids_json else []
            except:
                ids = [ids_json] if ids_json else []
            new_ids = [parent_eid if eid == artifact_eid else eid for eid in ids]
            seen = set(); deduped = [x for x in new_ids if not (x in seen or seen.add(x))]
            c.execute("UPDATE chunk_registry SET linked_entity_ids=? WHERE chunk_id=?",
                      (json.dumps(deduped), chunk_id))
            reattr_chunk_count += 1
    print(f"  Re-attributed {reattr_chunk_count} chunk records")

    print(f"\n[3/4] Deleting chunks for gallery/portraits/list_of/bonding/unresolved artifacts...")
    del_chunk_count = 0
    for eid in artifacts_delete + unresolved_reattr:
        c.execute("DELETE FROM chunk_registry WHERE linked_entity_ids LIKE ?", (f'%{eid}%',))
        del_chunk_count += c.rowcount
    print(f"  Deleted {del_chunk_count} chunks")

    print(f"\n[4/4] Removing any remaining artifact entities from entity_registry...")
    all_artifact_ids = [eid for eid, _ in artifacts_reattr] + artifacts_delete
    # Also sweep entity_registry for any still-present fused-suffix / list_of entities
    c.execute("SELECT entity_id FROM entity_registry")
    remaining_artifacts = []
    for (eid,) in c.fetchall():
        art, _, _ = is_artifact(eid)
        if art:
            remaining_artifacts.append(eid)

    if remaining_artifacts:
        for i in range(0, len(remaining_artifacts), 500):
            batch = remaining_artifacts[i:i+500]
            c.execute(f"DELETE FROM entity_registry WHERE entity_id IN ({','.join('?'*len(batch))})", batch)
        print(f"  Removed {len(remaining_artifacts)} artifact entities still in registry")
    else:
        print(f"  No artifact entities remain in registry")

    conn.commit()

    print(f"\nFinal entity_type breakdown:")
    c.execute("SELECT entity_type, COUNT(*) FROM entity_registry GROUP BY entity_type ORDER BY COUNT(*) DESC")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")
    c.execute("SELECT COUNT(*) FROM entity_registry")
    print(f"  TOTAL: {c.fetchone()[0]}")

    print(f"\nchunk_registry total:")
    c.execute("SELECT COUNT(*) FROM chunk_registry")
    print(f"  {c.fetchone()[0]}")

conn.close()
