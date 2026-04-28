import sqlite3

def dump_media():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    cur.execute("SELECT media_id, english_title, media_type FROM media_registry")
    rows = cur.fetchall()
    print(f"Total media entries: {len(rows)}")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    dump_media()
