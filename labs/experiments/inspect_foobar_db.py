import sqlite3
import os

db_path = r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\metadb.sqlite"

def inspect_db():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("--- Tables ---")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(table[0])
            
        # Common foobar2000 v2 tables: 'metadb', 'metadb_index', etc.
        # Let's try to find tracks by Nagao or Maeda if a likely table exists.
        # Note: v2 often stores tags in a specialized way.
        
        print("\n--- Peeking at likely metadata tables ---")
        for table in [t[0] for t in tables]:
            try:
                cursor.execute(f"PRAGMA table_info({table});")
                cols = cursor.fetchall()
                print(f"\nTable: {table}")
                for col in cols:
                    print(f"  {col[1]} ({col[2]})")
            except:
                pass

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
