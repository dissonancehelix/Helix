import sqlite3

DB_PATH = 'retrieval/index/trails.db'

def check_lore_coverage():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # (Label, Media ID Filter)
    targets = [
        ('Advanced Chapter', 'drama_advanced'),
        ('Road to the Future', 'drama_future'),
        ('Alister’s Snowlight', 'ss_snowlight')
    ]
    
    print(f"{'Target Media':<30} | {'Chunk Count':<12} | {'Avg Length':<12}")
    print("-" * 60)
    
    for label, media_id in targets:
        cursor.execute("SELECT COUNT(*), AVG(LENGTH(text_content)) FROM chunk_registry WHERE media_id = ?", (media_id,))
        count, avg_len = cursor.fetchone()
        avg_len = round(avg_len) if avg_len else 0
        print(f"{label:<30} | {count:<12} | {avg_len:<12}")
        
    print("\n--- Sample Chunks (First 3 for drama_advanced) ---")
    cursor.execute("SELECT linked_entity_ids, text_content FROM chunk_registry WHERE media_id = 'drama_advanced' LIMIT 3")
    for row in cursor.fetchall():
        print(f"Entity: {row[0]} | Text: {row[1][:100]}...")

    conn.close()

if __name__ == "__main__":
    check_lore_coverage()
