import shutil
from pathlib import Path

def prepare_attempt_channel(root_artifacts_dir: Path):
    attempt_dir = root_artifacts_dir / "latest_attempt"
    if attempt_dir.exists():
        shutil.rmtree(attempt_dir)
    attempt_dir.mkdir(parents=True, exist_ok=True)
    return attempt_dir

def promote_to_stable(root_artifacts_dir: Path):
    attempt_dir = root_artifacts_dir / "latest_attempt"
    stable_dir = root_artifacts_dir / "latest_stable"
    
    if stable_dir.exists():
        shutil.rmtree(stable_dir)
        
    shutil.copytree(attempt_dir, stable_dir)
    print("Promoted latest_attempt to latest_stable.")
