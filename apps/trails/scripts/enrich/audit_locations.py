#!/usr/bin/env python3
"""Audit location coverage — find misfiled locations and ID prefix inconsistencies."""
import sqlite3, re

DB = '/mnt/c/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# Prefix inconsistency
c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE entity_id LIKE 'location:%' ORDER BY entity_id")
location_prefix = c.fetchall()
print(f"=== 'location:' prefix ({len(location_prefix)} rows — should be 'loc:') ===")
for row in location_prefix:
    print(f"  {row[0]}: {row[1]}")

# Concepts that are clearly geographic places
PLACE_PATTERNS = [
    # ID patterns
    r'^concept:(city_of_|crossbell_city|edith/|heimdallr/|armorica|bryonia|elmo_village|grancel|jenis)',
    # Name patterns
]
PLACE_KEYWORDS = [
    'city', 'town', 'village', 'district', 'province', 'region', 'kingdom',
    'republic', 'empire', 'state', 'principality', 'island', 'castle', 'academy',
    'station', 'harbor', 'port', 'street', 'highland', 'mountain', 'forest',
    'lake', 'bridge', 'road', 'trail', 'mine', 'ruins', 'shrine', 'temple',
    'church', 'hall', 'manor', 'fortress', 'fort', 'palace', 'plaza', 'square',
    'quarter', 'ward', 'alley', 'avenue', 'boulevard', 'market', 'gate',
    'tower', 'valley', 'coast', 'bay', 'cape', 'delta', 'canyon', 'plateau',
]

c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE entity_type='concept' ORDER BY entity_id")
all_concepts = c.fetchall()

location_concepts = []
for eid, name in all_concepts:
    name_lower = (name or '').lower()
    id_lower = eid.lower()
    # Skip "list of enemies" and other clearly non-place entries
    if 'list_of_enemies' in id_lower or 'list_of_' in id_lower:
        continue
    if any(kw in name_lower for kw in PLACE_KEYWORDS):
        location_concepts.append((eid, name))
    elif re.match(r'concept:(city_of|crossbell_city|edith|heimdallr|armorica|bryonia|elmo_|grancel|jenis|thors|lohengrin|hamel|eryn)', id_lower):
        location_concepts.append((eid, name))

print(f"\n=== concept entries that are likely locations ({len(location_concepts)}) ===")
for row in location_concepts[:100]:
    print(f"  {row[0]}: {row[1]}")
if len(location_concepts) > 100:
    print(f"  ... and {len(location_concepts)-100} more")

# Also check: concepts with entity_id starting with known place identifiers
c.execute("""
    SELECT entity_id, english_display_name FROM entity_registry
    WHERE entity_type='concept'
    AND (entity_id LIKE 'concept:crossbell%' OR entity_id LIKE 'concept:heimdallr%'
         OR entity_id LIKE 'concept:edith%' OR entity_id LIKE 'concept:city_of%'
         OR entity_id LIKE 'concept:grancel%')
    ORDER BY entity_id
""")
place_ids = c.fetchall()
print(f"\n=== concept with place-like IDs ({len(place_ids)}) ===")
for row in place_ids:
    print(f"  {row[0]}")

conn.close()
print(f"\nSummary:")
print(f"  Current location entities: 50 (loc: prefix) + 14 'location:' prefix = 64 but with duplication")
print(f"  Concepts that are likely places: {len(location_concepts)}")
print(f"  True location count if reclassified: ~{50 + len(location_concepts)}")
