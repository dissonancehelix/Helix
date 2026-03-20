"""
music_ingestion — Helix Music Lab
=================================
Ingests metadata from foobar2000 metadb.sqlite and scans library files.
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from domains.music.ingestion.metadata_processor import MetadataProcessor
from domains.music.config import LIBRARY_ROOT
from domains.music.master_pipeline import MasterPipeline

def run(limit: int = 0, **kwargs):
    print("--- Running music_ingestion experiment ---")
    
    # 1. Full metadata ingestion pipeline (including metadb.sqlite)
    processor = MetadataProcessor(LIBRARY_ROOT)
    processor.run_pipeline()
    
    # 2. Sync with Master Pipeline stages 1-2 to ensure DB is primed
    pipeline = MasterPipeline(stages=[1, 2], limit=limit)
    pipeline.run()
    
    print("--- music_ingestion complete ---")

if __name__ == "__main__":
    run()
