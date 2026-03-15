"""
Orphan Search — 04_labs/research/orphan_search.py

Finds files in 07_artifacts/ that have no corresponding entry in any run_manifest.json.
"The shadows of runs that git forgot."
"""

import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())

def find_orphans():
    artifacts_dir = ROOT / "07_artifacts"
    manifests = artifacts_dir.rglob("run_manifest.json")
    
    recorded_files = set()
    for manifest in manifests:
        try:
            with open(manifest, 'r') as f:
                data = json.load(f)
                # Some manifests list filenames, some list relative paths
                for file_path in data.get("artifacts", {}).keys():
                    recorded_files.add(Path(file_path).resolve())
                recorded_files.add(manifest.resolve())
                # Also include sister files
                for sibling in manifest.parent.iterdir():
                    recorded_files.add(sibling.resolve())
        except Exception:
            continue
            
    all_files = set()
    for f in artifacts_dir.rglob("*"):
        if f.is_file():
            all_files.add(f.resolve())
            
    orphans = all_files - recorded_files
    return [str(o) for o in orphans]

if __name__ == "__main__":
    orphans = find_orphans()
    print(json.dumps(orphans, indent=2))
