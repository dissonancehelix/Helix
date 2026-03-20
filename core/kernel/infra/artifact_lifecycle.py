import os
import json
import tarfile
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT

ARTIFACT_ROOT = REPO_ROOT / 'execution/artifacts'
KEEP = {"latest", "best", "controls", "archive"}

def compress_directory(src_dir, dest_file):
    with tarfile.open(dest_file, "w:gz") as tar:
        tar.add(src_dir, arcname=src_dir.name)

def compact_track(track_path):
    archive_dir = track_path / "archive"
    archive_dir.mkdir(exist_ok=True)

    for run in track_path.iterdir():
        if not run.is_dir():
            continue
        if run.name in KEEP:
            continue

        archive_path = archive_dir / f"{run.name}.tar.gz"
        if archive_path.exists():
            continue

        compress_directory(run, archive_path)

        for root, dirs, files in os.walk(run, topdown=False):
            for f in files:
                os.remove(Path(root) / f)
            for d in dirs:
                os.rmdir(Path(root) / d)
        os.rmdir(run)

def compact_all():
    print("Starting Artifact Compaction...")
    for track in ARTIFACT_ROOT.iterdir():
        if not track.is_dir():
            continue
        compact_track(track)
        print(f"Compacted track: {track.name}")
    print("Artifact Compaction Complete.")
