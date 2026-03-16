import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from labs.music_lab.chip.vgm_parser import run_vgm_extraction
from labs.music_lab.chip.fm_patch_extractor import YM2612Analytic
from labs.music_lab.engine_inference import EngineInferenceEngine
from labs.music_lab.smps_reconstructor import SMPSReconstructor
from labs.music_lab.channel_profiler import ChannelProfiler
from labs.music_lab.chip.chip_detector import VGMChipDetector

# Paths
BASE_DIR = Path("/home/dissonance/Helix")
LIB_DIR = Path("/mnt/c/Users/dissonance/Music/VGM/S/Sonic 3 & Knuckles")
STREAMS_DIR = BASE_DIR / "artifacts/music_lab/event_streams"
PATCHES_DIR = BASE_DIR / "artifacts/music_lab/patches"
SIGNALS_DIR = BASE_DIR / "artifacts/music_lab/composer_style_signals"
DETECTION_DIR = BASE_DIR / "artifacts/music_lab/engine_detection"
STRUCTURE_DIR = BASE_DIR / "artifacts/music_lab/smps_inference"
PROFILES_DIR = BASE_DIR / "artifacts/music_lab/channel_profiles"
CHIPS_DIR = BASE_DIR / "artifacts/music_lab/vgm_inventory"

def _calc_entropy(data: pd.Series) -> float:
    if data.empty: return 0.0
    val_probs = data.value_counts(normalize=True)
    return -np.sum(val_probs * np.log2(val_probs + 1e-9))

def process_corpus():
    print(f"--- Music Lab: Comprehensive Corpus Analysis ---")
    
    # Ensure dirs
    for d in [STREAMS_DIR, PATCHES_DIR, SIGNALS_DIR, DETECTION_DIR, STRUCTURE_DIR, PROFILES_DIR, CHIPS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    libraries = [LIB_DIR]
    all_engine_results = []
    corpus_summary = []
    all_inventory = []
    
    for lib in libraries:
        if not lib.exists(): continue
        tracks = [f for f in os.listdir(lib) if f.endswith('.vgz')]
        
        for track_name in tracks:
            track_path = lib / track_name
            stream_path = STREAMS_DIR / f"{track_name}.parquet"
            
            # 0. Chip Detection
            with open(track_path, 'rb') as f:
                raw_data = f.read()
                detector = VGMChipDetector(raw_data)
            chips = detector.detect_chips()
            vgm_version = detector.get_vgm_version()
            duration = detector.get_duration_samples()

            # 1. Raw Extraction
            if not stream_path.exists():
                run_vgm_extraction(str(track_path), str(stream_path))
            
            edf = pd.read_parquet(stream_path)
            events = edf.to_dict('records')
            
            # 2. Engine Inference
            inference = EngineInferenceEngine(events)
            engine_data = inference.infer()
            engine_data['track'] = track_name
            all_engine_results.append(engine_data)
            
            # 3. Structural Reconstruct (SMPS/GEMS)
            structure = {}
            if engine_data['engine'] == "SMPS":
                reconstructor = SMPSReconstructor(events)
                structure = reconstructor.extract_structure()
                pd.to_pickle(structure, STRUCTURE_DIR / f"{track_name}_smps.pkl")
            
            # 4. Channel Architecture Profiling
            profiler = ChannelProfiler(events)
            profile = profiler.profile()
            pd.to_pickle(profile, PROFILES_DIR / f"{track_name}_profile.pkl")
            
            # 5. Patch Extraction
            analytic = YM2612Analytic(edf)
            patches = analytic.extract_synthesis_parameters()
            patch_path = PATCHES_DIR / f"{track_name}_patches.parquet"
            patches.to_parquet(patch_path)
            
            # 6. Style Signals
            algo_counts = patches[0xB0].value_counts(normalize=True).to_dict() if 0xB0 in patches else {}
            sig = {
                "track": track_name,
                "engine": engine_data['engine'],
                "conf": engine_data['confidence'],
                "mean_algorithm": patches[0xB0].mean() if 0xB0 in patches else 0,
                "algo_entropy": _calc_entropy(patches[0xB0]) if 0xB0 in patches else 0,
                "pcm_weight": edf[edf['reg'] == 0x2A].shape[0] / len(edf) if not edf.empty else 0,
                "rhythm_entropy": structure.get('stats', {}).get('channel_notes', {}).get(0, {}).get('rhythm_entropy', 0) if structure else 0
            }
            for a in range(8):
                sig[f"algo_{a}_ratio"] = algo_counts.get(a, 0)
            
            corpus_summary.append(sig)

            # 7. Inventory entry
            inventory_entry = {
                "track": track_name,
                "version": vgm_version,
                "duration_samples": duration,
                "chips": ",".join([c['chip'] for c in chips]),
                "engine": engine_data['engine']
            }
            all_inventory.append(inventory_entry)
            
            print(f"Processed {track_name}: Engine={engine_data['engine']} Chips={inventory_entry['chips']}")

    # Save outputs
    pd.DataFrame(all_engine_results).to_parquet(DETECTION_DIR / "global_engine_catalog.parquet")
    pd.DataFrame(corpus_summary).to_parquet(SIGNALS_DIR / "unified_style_signals.parquet")
    pd.DataFrame(all_inventory).to_parquet(CHIPS_DIR / "vgm_chip_inventory.parquet")
    print(f"--- Analysis Complete. Global catalog updated. ---")

if __name__ == "__main__":
    process_corpus()
