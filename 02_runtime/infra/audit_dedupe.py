import os
import json
import shutil
from pathlib import Path

ROOT = Path("c:/Users/dissonance/Desktop/Helix")
ARTIFACTS_DIR = ROOT / "06_artifacts"

def deduplicate_artifacts():
    print("Deduplicating Artifacts...")
    for track in ARTIFACTS_DIR.iterdir():
        if not track.is_dir() or track.name == 'archive':
            continue
        
        # Group by hash signature -> list of (timestamp, run_path)
        signatures = {}
        for run in track.iterdir():
            if not run.is_dir() or run.name == "archive" or run.name in ["latest", "best", "controls"]:
                continue
            
            manifest_path = run / "run_manifest.json"
            if not manifest_path.exists():
                print(f"No manifest in {run}, skipping dedupe check.")
                continue
            
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # We need dataset_hash, commit_hash, parameter set
                # For fake/experimental runs, parameter set might be encoded arbitrarily. 
                # Let's extract what we can.
                dataset_hash = manifest.get("dataset_hash", "")
                commit_hash = manifest.get("commit_hash", "")
                params = str(manifest.get("parameters", ""))
                
                sig = f"{dataset_hash}_{commit_hash}_{params}"
                if sig not in signatures:
                    signatures[sig] = []
                # try to get timestamp
                timestamp = os.path.getmtime(manifest_path)
                signatures[sig].append((timestamp, run))
            except Exception as e:
                print(f"Error reading {manifest_path}: {e}")
                
        # Deduplicate
        for sig, runs in signatures.items():
            if len(runs) > 1:
                runs.sort(key=lambda x: x[0], reverse=True)
                newest = runs[0]
                for old_run in runs[1:]:
                    print(f"Removing duplicate run: {old_run[1]}")
                    shutil.rmtree(old_run[1])

if __name__ == "__main__":
    deduplicate_artifacts()
