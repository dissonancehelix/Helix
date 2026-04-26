"""
music_chip_analysis — Helix Music Lab
=====================================
Extracts chip-level synthesis features (registers, operators, DAC).
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from substrates.music.master_pipeline import MasterPipeline

def run(limit: int = 0, **kwargs):
    print("--- Running music_chip_analysis experiment ---")
    
    # Run stages 3 (tier_a_parse) and 4 (chip_features)
    pipeline = MasterPipeline(stages=[3, 4], limit=limit)
    pipeline.run()
    
    print("--- music_chip_analysis complete ---")

if __name__ == "__main__":
    run()
