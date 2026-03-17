"""
s3k_analysis — Helix Music Lab
==============================
Initial test dataset experiment focusing on Sonic the Hedgehog 3 & Knuckles.
Generates style vectors, motif networks, and similarity graphs for the S3&K soundtrack.
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from substrates.music.master_pipeline import MasterPipeline
from substrates.music.config import S3K_PATH, ARTIFACTS
import json

def run(**kwargs):
    print("--- Running s3k_analysis Initial Test Dataset experiment ---")
    
    if not S3K_PATH.exists():
        print(f"Warning: S3&K path {S3K_PATH} not found. Skipping execution.")
        return

    # 1. Run analysis pipeline for S3&K tracks (Stages 1-12, 15)
    # Skipping 13 (Taste) and 14 (Recommend).
    pipeline = MasterPipeline(stages=list(range(1, 13)) + [15])
    # Override files to only S3K
    pipeline._stage_scan = lambda: None # Skip default scan
    pipeline._files = list(S3K_PATH.rglob("*.vgm")) + list(S3K_PATH.rglob("*.vgz"))
    
    print(f"Analyzing {len(pipeline._files)} tracks from S3&K...")
    pipeline.run()
    
    # 2. Extract S3K-specific summary artifacts
    # (Simplified for this experiment trigger)
    summary = {
        "soundtrack": "Sonic the Hedgehog 3 & Knuckles",
        "tracks_analyzed": len(pipeline._files),
        "composer_attribution_summary": "See attribution_results.json",
        "patch_usage_analysis": "Completed (Stage 4)",
        "motif_network": "Generated (Stage 7)"
    }
    
    output_path = ARTIFACTS / "music_lab" / "s3k_analysis_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"S3&K Analysis complete. Report: {output_path}")
    print("--- s3k_analysis test complete ---")

if __name__ == "__main__":
    run()
