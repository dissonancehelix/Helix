"""
Run Manifest — 03_engines/runtime/run_manifest.py

Build, hash, and persist run manifests for probe execution tracking.
Every probe run gets a unique run_id, dataset hash, probe code hash,
probe version, and environment snapshot written to 07_artifacts/.
"""

from __future__ import annotations
import hashlib
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


HELIX_VERSION = "0.4.0"


# ---------------------------------------------------------------------------
# Probe version extraction
# ---------------------------------------------------------------------------

def extract_probe_version(probe_script: str | Path) -> str:
    """
    Look for VERSION = "..." or __version__ = "..." in probe script source.
    Returns "1.0.0" if not found.
    """
    try:
        src = Path(probe_script).read_text(encoding="utf-8", errors="ignore")
        for pattern in [
            r'^\s*VERSION\s*=\s*["\']([^"\']+)["\']',
            r'^\s*__version__\s*=\s*["\']([^"\']+)["\']',
        ]:
            m = re.search(pattern, src, re.MULTILINE)
            if m:
                return m.group(1)
    except OSError:
        pass
    return "1.0.0"


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------

def compute_file_hash(path: str | Path) -> str:
    """SHA-256 of a file's contents."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def compute_data_hash(data: dict) -> str:
    """SHA-256 of a JSON-serialised dict (sorted keys)."""
    serialised = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(serialised).hexdigest()


# ---------------------------------------------------------------------------
# Run ID
# ---------------------------------------------------------------------------

def generate_run_id(probe_name: str) -> str:
    """
    Produce a unique, time-stamped run identifier.
    Format: <probe_name>_<YYYYMMDD_HHMMSS>_<hex6>
    """
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:6]
    return f"{probe_name}_{ts}_{suffix}"


# ---------------------------------------------------------------------------
# Environment snapshot
# ---------------------------------------------------------------------------

def capture_env_snapshot(sandbox_limits: dict | None = None) -> dict:
    """Capture lightweight environment metadata for reproducibility."""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "sandbox_limits": sandbox_limits or {},
        "captured_at": datetime.now(tz=timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Manifest builder
# ---------------------------------------------------------------------------

def build_run_manifest(
    run_id: str,
    probe_name: str,
    dataset: dict,
    probe_script: str | Path,
    lab_name: str = "",
    sandbox_limits: dict | None = None,
) -> dict:
    """
    Build a run manifest dict for a single probe execution.

    Returns a dict suitable for writing to run_manifest.json.
    """
    probe_script = Path(probe_script)
    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "probe_name": probe_name,
        "lab_name": lab_name,
        "dataset_hash": compute_data_hash(dataset),
        "probe_code_hash": compute_file_hash(probe_script),
        "probe_version": extract_probe_version(probe_script),
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "sandbox_limits": sandbox_limits or {},
        "helix_version": HELIX_VERSION,
    }


# ---------------------------------------------------------------------------
# Artifact bundle writer
# ---------------------------------------------------------------------------

def write_artifact_bundle(
    run_dir: str | Path,
    run_manifest: dict,
    dataset: dict,
    env_snapshot: dict,
) -> dict:
    """
    Write the standard artifact bundle files to run_dir.

    Files written:
        run_manifest.json   — structured run metadata
        dataset_hash.txt    — hex hash of dataset used
        env_snapshot.json   — environment at run time

    Returns dict of {filename: path_written}.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    manifest_path = run_dir / "run_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2)
    written["run_manifest.json"] = manifest_path

    hash_path = run_dir / "dataset_hash.txt"
    hash_path.write_text(run_manifest.get("dataset_hash", ""), encoding="utf-8")
    written["dataset_hash.txt"] = hash_path

    env_path = run_dir / "env_snapshot.json"
    with open(env_path, "w", encoding="utf-8") as f:
        json.dump(env_snapshot, f, indent=2)
    written["env_snapshot.json"] = env_path

    return written
