#!/usr/bin/env python3
import sqlite3

DB = '/mnt/c/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

print("=== entity_registry entity_type breakdown ===")
c.execute("SELECT entity_type, COUNT(*) FROM entity_registry GROUP BY entity_type ORDER BY COUNT(*) DESC")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== media_registry all rows ===")
c.execute("SELECT media_id, english_title, media_type, internal_chronology, release_chronology, spoiler_band FROM media_registry ORDER BY release_chronology")
for row in c.fetchall():
    print(" ", row)

print("\n=== appearance_registry sample (5) ===")
c.execute("SELECT * FROM appearance_registry LIMIT 5")
cols = [d[0] for d in c.description]
print("Columns:", cols)
for row in c.fetchall():
    print(" ", row)

print("\n=== source_registry source_class breakdown ===")
c.execute("SELECT source_class, COUNT(*) FROM source_registry GROUP BY source_class ORDER BY COUNT(*) DESC")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
