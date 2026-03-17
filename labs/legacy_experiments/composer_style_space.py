"""
composer_style_space — Helix Music Lab
======================================
Constructs the style-space embedding and clusters composers/soundtracks.
"""

import sys
from pathlib import Path
# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from substrates.music.master_pipeline import MasterPipeline
from substrates.music.similarity.composer_similarity import ComposerProfiler
from substrates.music.config import DB_PATH, FEATURE_VECTOR_VERSION, ARTIFACTS
from substrates.music.db.track_db import TrackDB
import json

def run(limit: int = 0, **kwargs):
    print("--- Running composer_style_space experiment ---")
    
    # 1. Run fingerprinting and style space mapping
    pipeline = MasterPipeline(stages=[11, 18], limit=limit)
    pipeline.run()
    
    # 2. Perform advanced style space analysis (UMAP/PCA could be added here)
    # For now, we aggregate the composer vectors as requested in Part 5
    db = TrackDB(DB_PATH)
    ids, mat = db.load_all_vectors(FEATURE_VECTOR_VERSION)
    
    # Group by composer
    composer_vectors = {}
    for i, tid in enumerate(ids):
        track = db.get_track(tid)
        composer = track.get("artist") or "Unknown"
        if composer not in composer_vectors:
            composer_vectors[composer] = []
        composer_vectors[composer].append(mat[i].tolist())
    
    # Compute mean vectors
    mean_vectors = {}
    for composer, vectors in composer_vectors.items():
        import numpy as np
        mean_vectors[composer] = np.mean(vectors, axis=0).tolist()
    
    # Store results in artifacts
    output_path = ARTIFACTS / "music_lab" / "composer_vectors.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(mean_vectors, f, indent=2)
    
    print(f"Stored {len(mean_vectors)} composer vectors in {output_path}")
    print("--- composer_style_space complete ---")

if __name__ == "__main__":
    run()
