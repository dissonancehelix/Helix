import sqlite3

def list_tables():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    print("Tables in trails.db:")
    for t in tables:
        print(f"- {t}")
        # Show a few columns/data for each
        cur.execute(f"PRAGMA table_info({t})")
        cols = [f"{c[1]} ({c[2]})" for c in cur.fetchall()]
        print(f"  Columns: {', '.join(cols)}")
    conn.close()

if __name__ == "__main__":
    list_tables()
