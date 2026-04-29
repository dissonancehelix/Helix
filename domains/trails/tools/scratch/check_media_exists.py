import sqlite3

def check_media():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM media_registry WHERE media_id = 'drama_advanced'")
    row = cur.fetchone()
    print(f"Media Info for drama_advanced: {row}")
    conn.close()

if __name__ == "__main__":
    check_media()
