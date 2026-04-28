import sqlite3

DB_PATH = 'retrieval/index/trails.db'

def check_lore_coverage():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    targets = ['Advanced Chapter', 'Road to the Future', 'Ring of Judgment', 'Returning Home', 'Alster']
    
    print(f"{'Target':<25} | {'Chunk Count':<12} | {'Avg Length':<12}")
    print("-" * 55)
    
    for t in targets:
        cursor.execute("SELECT COUNT(*), AVG(LENGTH(text_content)) FROM chunk_registry WHERE text_content LIKE ?", (f'%{t}%',))
        count, avg_len = cursor.fetchone()
        avg_len = round(avg_len) if avg_len else 0
        print(f"{t:<25} | {count:<12} | {avg_len:<12}")
    
    conn.close()

if __name__ == "__main__":
    check_lore_coverage()
