import hashlib
import json
from pathlib import Path

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def validate_artifact_integrity(manifest_path):
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    for path_str, expected_hash in manifest.get("artifacts", {}).items():
        if not Path(path_str).exists() or compute_sha256(path_str) != expected_hash:
            return False
    return True
