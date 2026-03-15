"""
Artifact Lock — 03_engines/runtime_hooks/artifact_lock.py

Lock a probe run artifact directory as immutable using chattr +i (Linux/WSL2).
On Windows, warns and returns False — no enforcement applied.
"""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def lock_artifact_run(artifact_dir: str | Path) -> bool:
    """
    Set chattr +i on an artifact directory to make it immutable.

    Args:
        artifact_dir: Path to the run artifact directory to lock.

    Returns:
        True if locked successfully, False otherwise.
    """
    artifact_dir = Path(artifact_dir)

    if not sys.platform.startswith("linux"):
        print(
            f"[ARTIFACT_LOCK] WARNING: lock_artifact_run() requires Linux (WSL2). "
            f"Running on '{sys.platform}' — no enforcement applied."
        )
        return False

    if not artifact_dir.exists():
        print(f"[ARTIFACT_LOCK] Directory not found: {artifact_dir}")
        return False

    try:
        result = subprocess.run(
            ["chattr", "-R", "+i", str(artifact_dir)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return True
        else:
            print(f"[ARTIFACT_LOCK] chattr failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[ARTIFACT_LOCK] chattr not found — install e2fsprogs.")
        return False
