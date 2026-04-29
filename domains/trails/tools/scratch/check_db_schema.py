import sqlite3

def check_entities():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    
    print("--- Media Entities ---")
    # Using canonical_name instead of name
    cur.execute("SELECT entity_id, canonical_name, entity_type FROM entity_registry WHERE entity_type = 'media' OR canonical_name LIKE '%Drama CD%'")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- Chunk Registry Schema ---")
    cur.execute("PRAGMA table_info(chunk_registry)")
    for row in cur.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_entities()
