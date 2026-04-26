import sqlite3

def find_media():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    
    queries = [
        "SELECT media_id, english_title, media_type FROM media_registry WHERE english_title LIKE '%Drama CD%'",
        "SELECT media_id, english_title, media_type FROM media_registry WHERE english_title LIKE '%Advanced%'",
        "SELECT media_id, english_title, media_type FROM media_registry WHERE english_title LIKE '%Future%'",
        "SELECT media_id, english_title, media_type FROM media_registry WHERE english_title LIKE '%Cold Steel II%'",
        "SELECT media_id, english_title, media_type FROM media_registry WHERE media_type = 'media'"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        cur.execute(q)
        for row in cur.fetchall():
            print(row)
            
    conn.close()

if __name__ == "__main__":
    find_media()
