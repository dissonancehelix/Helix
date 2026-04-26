import os
import sys

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

def execute_run(limit=1000):
    print(f"Starting Production Ingestion Run (Limit: {limit})...")
    
    adapter = MusicSourceAdapter(MUSIC_ROOT, FOOBAR_DB)
    manager = IngestionManager(LIB_ROOT)
    
    count = 0
    # Collect IDs for referential integrity check?
    # No, manager handles it.
    
    gen = adapter.scan_tracks(limit=limit)
    if not gen:
        print("No tracks found in source root.")
        return

    for record in gen:
        try:
            manager.ingest_record(record)
            count += 1
            if count % 100 == 0:
                print(f"  Ingested {count} tracks...")
        except Exception as e:
            # We don't stop the whole run for one bad track
            print(f"  ERROR ingesting record: {record.get('title', 'Unknown')} - {e}")
            
    manager.finalize()
    print(f"Run complete. {count} tracks successfully ingested to {LIB_ROOT}.")

if __name__ == "__main__":
    execute_run(limit=1000)
