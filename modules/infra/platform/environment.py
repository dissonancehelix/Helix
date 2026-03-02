import os
import subprocess
from pathlib import Path

def get_git_commit(root):
    try:
        res = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=str(root))
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None

def get_schema_version(root):
    import json
    manifest_path = Path(root) / 'core/manifest.json'
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('version', 'unknown')
    return 'unknown'
