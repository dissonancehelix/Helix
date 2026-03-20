import os
import shutil
import json
from pathlib import Path
from datetime import datetime

import subprocess

# Determine root
ROOT = Path(__file__).resolve().parent.parent.parent

ROOT_WHITELIST = {
    '.git',
    '.gitignore',
    '.agents',
    'HELIX.md',
    'OPERATOR.md',
    'REBUILD_CHECKPOINT.md',
    'operator.json',
    'helix.py',
    '00_kernel',
    '01_basis',
    '02_governance',
    '03_engines',
    '04_labs',
    '05_applications',
    'codex/atlas',
    'execution/artifacts',
    'docs',
}

def get_git_commit():
    try:
        res = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=str(ROOT))
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"

def scan_root(strict_mode=False):
    """
    Scans the Helix repository root for non-whitelisted items.
    Moves violations to 06_artifacts/quarantine/ and logs them in root_drift_log.json.
    If strict_mode is True, aborts execution via SystemExit if violations are found.
    """
    artifacts_dir = ROOT / 'execution/artifacts' / 'artifacts'
    quarantine_dir = artifacts_dir / 'quarantine'
    drift_log_path = artifacts_dir / 'root_drift_log.json'
    
    violations = []
    
    for item in ROOT.iterdir():
        if item.name not in ROOT_WHITELIST:
            violations.append(item)
            
    if not violations:
        return True
        
    # We have violations
    if strict_mode:
        print(f"[ROOT GUARDIAN] STRICT MODE: Root drift detected. Execution halted.")
        for v in violations:
            print(f"  - Invalid top-level item: {v.name}")
        import sys
        sys.exit(1)
        
    print(f"[ROOT GUARDIAN] Non-whitelisted items detected. Moving to quarantine...")
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing log if any
    log_entries = []
    if drift_log_path.exists():
        try:
            with open(drift_log_path, 'r') as f:
                log_entries = json.load(f)
        except Exception:
            pass
            
    commit_hash = get_git_commit()
    timestamp = datetime.now().isoformat()
    
    for v in violations:
        dest_path = quarantine_dir / v.name
        
        # Avoid collisions in quarantine
        counter = 1
        while dest_path.exists():
            dest_path = quarantine_dir / f"{v.name}_{counter}"
            counter += 1
            
        orig_path_str = str(v)
        dest_path_str = str(dest_path)
        
        try:
            shutil.move(orig_path_str, dest_path_str)
            print(f"  Quarantined: {v.name}")
            
            log_entries.append({
                "timestamp": timestamp,
                "commit": commit_hash,
                "file_moved": v.name,
                "original_path": orig_path_str,
                "destination_path": dest_path_str
            })
        except Exception as e:
            print(f"  [ERROR] Failed to move {v.name}: {e}")
            
    # Write log
    try:
        with open(drift_log_path, 'w') as f:
            json.dump(log_entries, f, indent=4)
    except Exception as e:
        print(f"[ROOT GUARDIAN] Failed to write drift log: {e}")
        
    return False

if __name__ == '__main__':
    scan_root()
