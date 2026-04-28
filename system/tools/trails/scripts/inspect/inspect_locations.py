#!/usr/bin/env python3
import sqlite3

DB = '/mnt/c/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

print("=== entity_type='location' (all 50) ===")
c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE entity_type='location' ORDER BY entity_id")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== concept entries that look like places ===")
c.execute("""
    SELECT entity_id, english_display_name
    FROM entity_registry
    WHERE entity_type='concept'
    AND (
        entity_id LIKE 'loc:%' OR entity_id LIKE 'place:%' OR entity_id LIKE 'city:%'
        OR entity_id LIKE 'region:%' OR entity_id LIKE 'country:%' OR entity_id LIKE 'town:%'
        OR english_display_name LIKE '%City%' OR english_display_name LIKE '%Town%'
        OR english_display_name LIKE '%Kingdom%' OR english_display_name LIKE '%Republic%'
        OR english_display_name LIKE '%Empire%' OR english_display_name LIKE '%Province%'
        OR english_display_name LIKE '%District%' OR english_display_name LIKE '%Academy%'
        OR english_display_name LIKE '%Castle%' OR english_display_name LIKE '%Church%'
        OR english_display_name LIKE '%Station%' OR english_display_name LIKE '%Harbor%'
        OR english_display_name LIKE '%Village%' OR english_display_name LIKE '%Island%'
    )
    ORDER BY entity_id
    LIMIT 60
""")
rows = c.fetchall()
print(f"  ({len(rows)} shown)")
for row in rows:
    print(f"  {row[0]}: {row[1]}")

print("\n=== chunk_registry linked entities that look like locations ===")
c.execute("""
    SELECT DISTINCT linked_entity_ids FROM chunk_registry
    WHERE linked_entity_ids LIKE '%loc:%'
    LIMIT 5
""")
for row in c.fetchall():
    print(" ", row[0][:200])

conn.close()
