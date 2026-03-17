import sqlite3
import os

db_path = r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\metadb.sqlite"

def search_all_indices():
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'metadb_index_%_data';")
        data_tables = [t[0] for t in cursor.fetchall()]
        
        for table in data_tables:
            # We search the BLOB values.
            # SQLite can use LIKE on BLOBs, but we'll try to just cast it or use hex/instr.
            # foobar v2 stores strings in the BLOBs, usually UTF-8.
            try:
                # Searching for Nagao
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE CAST(value AS TEXT) LIKE '%Nagao%';")
                nagao_count = cursor.fetchone()[0]
                
                # Searching for Maeda
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE CAST(value AS TEXT) LIKE '%Maeda%';")
                maeda_count = cursor.fetchone()[0]
                
                if nagao_count > 0 or maeda_count > 0:
                    index_table = table.replace("_data", "")
                    print(f"Found matches in {index_table}: Nagao={nagao_count}, Maeda={maeda_count}")
                    
                    # Let's get a few examples
                    cursor.execute(f"""
                        SELECT i.filename, CAST(d.value AS TEXT)
                        FROM {index_table} i
                        JOIN {table} d ON i.key = d.key
                        WHERE CAST(d.value AS TEXT) LIKE '%Nagao%' OR CAST(d.value AS TEXT) LIKE '%Maeda%'
                        LIMIT 5
                    """)
                    for row in cursor.fetchall():
                        print(f"  File: {row[0]}\n  Tag: {row[1][:100]}...")
            except Exception as e:
                # print(f"Error searching {table}: {e}")
                pass

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_all_indices()
