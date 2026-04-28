import sqlite3

def check_counts():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    cur.execute("SELECT media_id, COUNT(*) FROM chunk_registry GROUP BY media_id")
    rows = cur.fetchall()
    print("Chunk Registry Counts by Media ID:")
    for row in rows:
        print(f"- {row[0]}: {row[1]}")
    conn.close()

if __name__ == "__main__":
    check_counts()
