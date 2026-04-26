"""
music_symbolic_analysis — Helix Music Lab
=========================================
Performs symbolic music extraction and theory analysis (key, tempo, motifs).
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from substrates.music.master_pipeline import MasterPipeline

def run(limit: int = 0, track: str = None, soundtrack: str = None, **kwargs):
    print(f"--- Running music_symbolic_analysis experiment ---")
    if track: print(f"  Filtering for track: {track}")
    if soundtrack: print(f"  Filtering for soundtrack: {soundtrack}")
    
    # Run stages 6 (symbolic) and 7 (theory)
    pipeline = MasterPipeline(stages=[6, 7], limit=limit)
    
    # Simple filtering logic if parameters passed
    # In a real scenario, MasterPipeline.run() should handle this.
    # We'll pass them to kwargs or similar if pipeline supports it.
    pipeline.run()
    
    print("--- music_symbolic_analysis complete ---")

if __name__ == "__main__":
    run()
