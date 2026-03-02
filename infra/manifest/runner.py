import datetime
import hashlib
import json
import sys
from pathlib import Path

def generate_run_manifest(root, artifacts_dir, dataset_hash, schema_version, commit_hash):
    manifest = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": commit_hash,
        "schema_version": schema_version,
        "dataset_hash": dataset_hash,
        "bootstrap_seed": 42,
        "dependency_versions": {"numpy": "locked", "scikit-learn": "locked"},
        "python_version": sys.version.split(' ')[0],
        "artifact_hashes": {}
    }
    
    art_path = Path(artifacts_dir)
    for p in art_path.rglob('*.json'):
        # Exclusion logic should be passed or centralized
        rel_path = p.relative_to(art_path).as_posix()
        hasher = hashlib.sha256()
        hasher.update(p.read_bytes())
        manifest["artifact_hashes"][rel_path] = hasher.hexdigest()
        
    manifest_file = art_path / 'run_manifest.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest
