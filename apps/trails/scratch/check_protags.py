import sqlite3

def check_protags():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    names = ['Lloyd Bannings', 'Estelle Bright', 'Joshua Bright', 'Rean Schwarzer', 'Alisa Reinford', 'Jusis Albarea', 'Laura S. Arseid']
    
    print("--- Protag Verification ---")
    for name in names:
        cur.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE english_display_name = ?", (name,))
        row = cur.fetchone()
        if row:
            print(f"Found: {row}")
        else:
            # Check aliases
            cur.execute("SELECT entity_id FROM aliases WHERE alias = ?", (name,))
            row = cur.fetchone()
            if row:
                print(f"Found via alias: {name} -> {row[0]}")
            else:
                print(f"NOT FOUND: {name}")
                
    conn.close()

if __name__ == "__main__":
    check_protags()
