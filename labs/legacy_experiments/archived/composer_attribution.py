"""
composer_attribution — Helix Music Lab
======================================
Performs probabilistic composer attribution for tracks in the library.
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from domains.music.master_pipeline import MasterPipeline

def run(limit: int = 0, soundtrack: str = None, **kwargs):
    print(f"--- Running composer_attribution experiment ---")
    if soundtrack: print(f"  Filtering for soundtrack: {soundtrack}")
    
    # Run stage 12 (attributions)
    pipeline = MasterPipeline(stages=[12], limit=limit)
    pipeline.run()
    
    print("--- composer_attribution complete ---")

if __name__ == "__main__":
    run()
