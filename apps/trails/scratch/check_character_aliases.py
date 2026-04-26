import sqlite3

def check_aliases():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    names = ['Tita', 'Estelle', 'Joshua', 'Lloyd', 'Randy', 'Tio', 'Elie', 'Rean']
    print(f"{'Name':<10} | {'Found ID':<20}")
    print("-" * 35)
    for name in names:
        cur.execute("SELECT entity_id FROM aliases WHERE alias = ?", (name,))
        row = cur.fetchone()
        if row:
            print(f"{name:<10} | {row[0]:<20}")
        else:
            # check english_display_name
            cur.execute("SELECT entity_id FROM entity_registry WHERE english_display_name LIKE ?", (f'{name}%',))
            row = cur.fetchone()
            if row:
                print(f"{name:<10} | {row[0]:<20} (via display name)")
            else:
                print(f"{name:<10} | NOT FOUND")
    conn.close()

if __name__ == "__main__":
    check_aliases()
