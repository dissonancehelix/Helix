import os
import sys
import time

# Paths
sys.path.append(r'c:\Users\dissonance\Desktop\Helix\core\bin')
sys.path.append(r'c:\Users\dissonance\Desktop\Helix\core\compiler')
sys.path.append(r'c:\Users\dissonance\Desktop\Helix\core\adapters')

from lib_ingest import IngestionManager
from music_source_adapter import MusicSourceAdapter

# Production Source Config
MUSIC_ROOT = r"C:\Users\dissonance\Music"
FOOBAR_DB = r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\metadb.sqlite"
LIB_ROOT = r"C:\Users\dissonance\Desktop\Helix\core\library\music"

def execute_full_run():
    print("==================================================")
    print("HELIX MUSIC LIBRARY - FULL PRODUCTION INGESTION")
    print("==================================================")
    print(f"Source: {MUSIC_ROOT}")
    print(f"Substrate: {LIB_ROOT}")
    print("--------------------------------------------------")
    
    start_time = time.time()
    adapter = MusicSourceAdapter(MUSIC_ROOT, FOOBAR_DB)
    manager = IngestionManager(LIB_ROOT)
    
    count = 0
    # No limit = full run (~122k tracks)
    for record in adapter.scan_tracks(limit=150000): # High limit acting as None
        try:
            manager.ingest_record(record)
            count += 1
            if count % 1000 == 0:
                elapsed = time.time() - start_time
                rate = count / elapsed
                print(f"  Ingested {count} tracks... ({rate:.1f} t/s)")
        except Exception as e:
            print(f"  ERROR record: {record.get('title', 'Unknown')} - {e}")
            
    manager.finalize()
    duration = time.time() - start_time
    print("--------------------------------------------------")
    print(f"RUN COMPLETE. {count} tracks successfully ingested.")
    print(f"Total time: {duration/60:.1f} minutes.")
    print("==================================================")

if __name__ == "__main__":
    execute_full_run()
