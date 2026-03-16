import os
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Paths
BASE_DIR = Path("/home/dissonance/Helix")
STREAMS_DIR = BASE_DIR / "artifacts/music_lab/event_streams"
PATCHES_DIR = BASE_DIR / "artifacts/music_lab/patches"
SIGNALS_DIR = BASE_DIR / "artifacts/music_lab/composer_style_signals"

def generate_composer_signals():
    print("Generating High-Level Composer Style Signals...")
    
    # Load cluster definitions if available
    cluster_path = PATCHES_DIR / "patch_clusters.json"
    
    signals = []
    
    for stream_file in STREAMS_DIR.glob("*.parquet"):
        if "patch_clusters" in stream_file.name: continue
        
        track_name = stream_file.stem
        edf = pd.read_parquet(stream_file)
        
        # 1. Rhythmic Entropy (from waits)
        # We look for the distribution of 0x61, 0x62, 0x63, 0x7x wait commands
        waits = edf[edf['ts'].diff() > 0]['ts'].diff()
        rhythmic_entropy = waits.std() / waits.mean() if not waits.empty else 0
        
        # 2. Bass Channel Mapping
        # Heuristic: Channel with most low-frequency / rhythmic activity
        # On Genesis, Ch 2 is often Bass.
        ch_activity = edf['type'].value_counts()
        
        # 3. Patch Usage Distribution
        # Load the corresponding patch file
        patch_file = PATCHES_DIR / f"{track_name}_patches.parquet"
        if patch_file.exists():
            pdf = pd.read_parquet(patch_file)
            # Find most common Algorithm (Reg 0xB0)
            common_algo = pdf[176].mode()[0] if 176 in pdf.columns else None # 176 is 0xB0
            # Common total level (Volume) for ops
            common_tl = pdf[64].mean() if 64 in pdf.columns else 0 # 0x40
        else:
            common_algo = None
            common_tl = 0

        # PCM Usage (Drums)
        # Register 0x2A is PCM data
        pcm_events = edf[edf['reg'] == 0x2A]
        pcm_density = len(pcm_events) / len(edf) if not edf.empty else 0

        signals.append({
            "track": track_name,
            "rhythmic_entropy": float(rhythmic_entropy),
            "pcm_density": float(pcm_density),
            "common_algo": int(common_algo) if common_algo is not None else -1,
            "event_count": len(edf)
        })

    pd.DataFrame(signals).to_parquet(SIGNALS_DIR / "chip_style_signals.parquet")
    print(f"Signals generated for {len(signals)} tracks.")

if __name__ == "__main__":
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    generate_composer_signals()
