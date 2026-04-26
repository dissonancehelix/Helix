import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

def detect_collisions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- HELIX ALIAS COLLISION AUDIT v5 ---")

    # 1. Japanese Name Overlap
    # Multiple IDs sharing the same Japanese name
    cursor.execute('''
        SELECT japanese_name, COUNT(*) as counts, GROUP_CONCAT(entity_id) as ids
        FROM entity_registry
        WHERE japanese_name IS NOT NULL
        GROUP BY japanese_name
        HAVING counts > 1
    ''')
    ja_collisions = cursor.fetchall()

    # 2. English Display Name Overlap (Case Insensitive)
    cursor.execute('''
        SELECT LOWER(english_display_name) as lower_name, COUNT(*) as counts, GROUP_CONCAT(entity_id) as ids
        FROM entity_registry 
        GROUP BY lower_name 
        HAVING counts > 1
    ''')
    en_collisions = cursor.fetchall()

    # 3. Fuzzy Appearance Overlap (Same Debut + Same Role) 
    # (High likelihood of duplicate ingestion)
    cursor.execute('''
        SELECT media_id, appearance_type, COUNT(*) as counts, GROUP_CONCAT(entity_id) as ids
        FROM appearance_registry
        WHERE debut_flag = 1
        GROUP BY media_id, appearance_type
        HAVING counts > 50 -- Heuristic: If 50 people debut in the same role, it's likely a bulk error
    ''')
    role_explosions = cursor.fetchall()

    # Reporting
    print(f" - Japanese Identity Collisions: {len(ja_collisions)}")
    for row in ja_collisions:
        print(f"   [!] Conflict: '{row['japanese_name']}' shared by: {row['ids']}")

    print(f" - English Name Collisions: {len(en_collisions)}")
    for row in en_collisions:
        print(f"   [!] Conflict: '{row['lower_name']}' shared by: {row['ids']}")

    print(f" - Suspicious Role Clusters: {len(role_explosions)}")

    conn.close()
    if not any([ja_collisions, en_collisions, role_explosions]):
        print("\n[SUCCESS] No entity collisions detected. Registry is UNIQUE.")
    else:
        print("\n[ACTION REQUIRED] Potential duplicates found. Consider manual merge or mapping refinement.")

if __name__ == "__main__":
    detect_collisions()
