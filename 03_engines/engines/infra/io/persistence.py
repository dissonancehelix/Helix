import json
import os
from pathlib import Path
import hashlib

def save_wrapped(path, data):
    ds_hash = os.environ.get('HELIX_DATASET_HASH', 'unknown')
    schema_ver = os.environ.get('HELIX_SCHEMA_VERSION', 'unknown')
    git_commit = os.environ.get('HELIX_GIT_COMMIT', 'unknown')
    bootstrap_seed = os.environ.get('HELIX_BOOTSTRAP_SEED', '42')
    
    # Sort keys for deterministic JSON serialization
    payload_str = json.dumps(data, sort_keys=True)
    art_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
    
    wrapper = {
        "generated_by": "helix.py run",
        "dataset_hash": ds_hash,
        "schema_version": schema_ver,
        "git_commit": git_commit,
        "artifact_hash": art_hash,
        "bootstrap_seed": int(bootstrap_seed),
        "data": data
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(wrapper, f, indent=2, sort_keys=True)

def archive_artifacts(artifacts_dir, archive_dir, dataset_hash):
    import datetime
    import shutil
    manifest_path = Path(artifacts_dir) / 'run_manifest.json'
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            old_manifest = json.load(f)
        old_hash = old_manifest.get('dataset_hash')
        if old_hash and old_hash != dataset_hash:
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            archive_path = Path(archive_dir) / f"{timestamp}_{old_hash}"
            archive_path.mkdir(parents=True, exist_ok=True)
            for item in Path(artifacts_dir).iterdir():
                if item.name == 'archive': continue
                shutil.move(str(item), str(archive_path / item.name))
            print(f"Archived previous run to {archive_path}")

def load_domains(data_dir=None, recursive=False):
    if data_dir is None:
        data_dir = os.environ.get('HELIX_DOMAINS_DIR', '04_labs/corpus/domains/domains')
    domains = []
    path_obj = Path(data_dir)
    if not path_obj.exists():
        return []
        
    pattern = '**/*.json' if recursive else '*.json'
    # Explicitly walk and sort to ensure deterministic loading order
    for p in sorted(path_obj.glob(pattern)):
        with open(p, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        # Use a synthetic ID if needed, but usually these have 'id'
                        name = f"{p.stem}_{idx}.json"
                        domains.append((name, item))
                else:
                    domains.append((p.name, data))
            except json.JSONDecodeError:
                print(f"Warning: Failed to decode {p}")
                continue
    return domains
