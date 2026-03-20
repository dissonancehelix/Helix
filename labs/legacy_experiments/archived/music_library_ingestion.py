import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from domains.music.experiments.music_ingestion import run as ingestion_run

def run(**kwargs):
    print("--- INGEST music_library ---")
    ingestion_run(**kwargs)
    return {"status": "ok", "message": "Music library ingested"}

if __name__ == "__main__":
    run()
