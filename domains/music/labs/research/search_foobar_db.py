import sqlite3
import os

db_path = r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\metadb.sqlite"

def search_db():
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Searching for Nagao/Maeda in foobar2000 filenames...")
        
        # Search for Nagao
        cursor.execute("SELECT name FROM metadb WHERE name LIKE '%Nagao%';")
        nagao_files = cursor.fetchall()
        
        # Search for Maeda
        cursor.execute("SELECT name FROM metadb WHERE name LIKE '%Maeda%';")
        maeda_files = cursor.fetchall()
        
        print(f"\n--- Masayuki Nagao hits ({len(nagao_files)}) ---")
        for f in nagao_files[:10]:
            print(f[0])
            
        print(f"\n--- Tatsuyuki Maeda hits ({len(maeda_files)}) ---")
        for f in maeda_files[:10]:
            print(f[0])

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_db()
