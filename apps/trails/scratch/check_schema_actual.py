import sqlite3

def check_schema():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    
    print("--- entity_registry Schema ---")
    cur.execute("PRAGMA table_info(entity_registry)")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- chunk_registry Schema ---")
    cur.execute("PRAGMA table_info(chunk_registry)")
    for row in cur.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_schema()
