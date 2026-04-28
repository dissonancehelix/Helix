import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

def verify_integrity():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- HELIX INTEGRITY AUDIT v5 ---")
    
    # 1. Broken Foreign Keys (Manual Check)
    cursor.execute('''
        SELECT a.appearance_id, a.entity_id 
        FROM appearance_registry a 
        LEFT JOIN entity_registry e ON a.entity_id = e.entity_id
        WHERE e.entity_id IS NULL
    ''')
    orphaned_entities = cursor.fetchall()
    
    cursor.execute('''
        SELECT a.appearance_id, a.media_id 
        FROM appearance_registry a 
        LEFT JOIN media_registry m ON a.media_id = m.media_id
        WHERE m.media_id IS NULL
    ''')
    orphaned_media = cursor.fetchall()

    # 2. Conflicting Debut Flags
    cursor.execute('''
        SELECT entity_id, COUNT(*) as counts 
        FROM appearance_registry 
        WHERE debut_flag = 1 
        GROUP BY entity_id 
        HAVING counts > 1
    ''')
    conflicting_debuts = cursor.fetchall()

    # 3. Duplicate Appearance Rows
    cursor.execute('''
        SELECT entity_id, media_id, COUNT(*) as counts 
        FROM appearance_registry 
        GROUP BY entity_id, media_id 
        HAVING counts > 1
    ''')
    duplicate_appearances = cursor.fetchall()

    # Summary Output
    print(f" - Orphaned Entities in Appearances: {len(orphaned_entities)}")
    if orphaned_entities:
        print(f"   [!] Sample: {orphaned_entities[0]}")
        
    print(f" - Orphaned Media in Appearances: {len(orphaned_media)}")
    if orphaned_media:
        print(f"   [!] Sample: {orphaned_media[0]}")

    print(f" - Entities with Multi-Debut Flags: {len(conflicting_debuts)}")
    if conflicting_debuts:
        print(f"   [!] Sample: {conflicting_debuts[0]}")

    print(f" - Duplicate Appearance Pairs: {len(duplicate_appearances)}")
    if duplicate_appearances:
        print(f"   [!] Sample: {duplicate_appearances[0]}")

    conn.close()
    if not any([orphaned_entities, orphaned_media, conflicting_debuts, duplicate_appearances]):
        print("\n[SUCCESS] Relational integrity is HARDENED.")
    else:
        print("\n[WARNING] Integrity issues detected. Review audit logs.")

if __name__ == "__main__":
    verify_integrity()
