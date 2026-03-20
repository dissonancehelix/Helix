"""
music_mir_analysis — Helix Music Lab
====================================
Performs audio-level MIR analysis (tempo, spectral brightness, energy).
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from domains.music.master_pipeline import MasterPipeline

def run(limit: int = 0, **kwargs):
    print("--- Running music_mir_analysis experiment ---")
    
    # Run stage 8 (mir)
    pipeline = MasterPipeline(stages=[8], limit=limit)
    pipeline.run()
    
    print("--- music_mir_analysis complete ---")

if __name__ == "__main__":
    run()
