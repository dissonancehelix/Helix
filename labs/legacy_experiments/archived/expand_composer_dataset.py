import sys
import os
from pathlib import Path

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from substrates.music.master_pipeline import MasterPipeline
from substrates.music.config import VGM_ROOT, LIBRARY_ROOT

TARGET_COMPOSERS = {
    "jun senoue", "tatsuyuki maeda", "sachio ogawa", 
    "masayuki nagao", "tomonori sawada"
}

def run_expansion():
    print("--- Helix Music Lab: Dataset Expansion ---")
    
    # 1. Broad Scan and Ingest (Stage 1-2)
    # We scan everything to find our target composers
    pipeline = MasterPipeline(stages=[1, 2])
    pipeline.run()
    
    # 2. Identify target tracks from DB
    from substrates.music.db.track_db import TrackDB
    from substrates.music.config import DB_PATH
    db = TrackDB(DB_PATH)
    all_tracks = db.get_tracks_by_tier(max_tier=1)
    targets = []
    target_composers = {
        "jun senoue", "tatsuyuki maeda", "sachio ogawa", 
        "masayuki nagao", "tomonori sawada"
    }
    
    target_games = {
        "j.league pro striker", "super thunder blade", 
        "phantasy star ii text adventures", "golden axe iii",
        "sonic 3d blast"
    }
    
    for t in all_tracks:
        artist = str(t.get("artist", "")).lower()
        album  = str(t.get("album", "")).lower()
        source = str(t.get("file_path", ""))
        
        is_target_composer = any(c in artist for c in target_composers)
        is_target_game = any(g in album for g in target_games)
        is_s3k = "sonic 3 & knuckles" in source.lower()
        
        if is_target_composer or is_target_game or is_s3k:
            targets.append(Path(t["file_path"]))

    print(f"Found {len(targets)} tracks for analysis (Target Composers + S3&K)")
    
    if not targets:
        print("No tracks found. Check library scan.")
        return

    # 3. Targeted Analysis (Stage 3-12)
    # Only run analysis on the relevant tracks
    analysis_pipeline = MasterPipeline(stages=list(range(3, 13)) + [15, 16, 17, 18])
    analysis_pipeline._files = targets
    analysis_pipeline.run()

if __name__ == "__main__":
    run_expansion()
