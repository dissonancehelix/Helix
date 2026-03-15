import json
import time
from pathlib import Path

TAU_STALE = 86400 * 7

def check_clock(stable_dir: Path):
    clock_file = stable_dir / "instrument_health" / "clock.json"
    if not clock_file.exists():
        return "STALE"
    try:
        with open(clock_file, 'r') as f:
            data = json.load(f)
        if time.time() - data.get("last_successful_run_timestamp", 0) > TAU_STALE:
            return "STALE"
        return "HEALTHY"
    except:
        return "STALE"

def update_clock(attempt_dir: Path, ds_hash: str, schema_ver: str, commit_hash: str):
    health_dir = attempt_dir / "instrument_health"
    health_dir.mkdir(parents=True, exist_ok=True)
    clock_data = {
        "last_successful_run_timestamp": time.time(),
        "last_full_validation_timestamp": time.time(),
        "dataset_hash": ds_hash,
        "schema_version": schema_ver,
        "git_commit_hash": commit_hash,
        "entropy_signature_hash": "TBD"
    }
    with open(health_dir / "clock.json", "w", encoding='utf-8') as f:
        json.dump(clock_data, f, indent=2)
