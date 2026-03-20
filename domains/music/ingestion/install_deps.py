"""
Helix Music Lab — Dependency Installer
========================================
Idempotent: checks whether each package is already importable before
calling pip.  Run this before the first master_pipeline.py invocation.

Usage:
    python labs/music_lab/tools/install_deps.py [--check-only]
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys


# ---------------------------------------------------------------------------
# Required packages
# ---------------------------------------------------------------------------

# (import_name, pip_name, tier, required)
PACKAGES: list[tuple[str, str, str, bool]] = [
    # Always required
    ("numpy",       "numpy",           "core",   True),
    ("scipy",       "scipy",           "core",   True),
    ("mutagen",     "mutagen",         "core",   True),
    ("pandas",      "pandas",          "core",   True),
    # Tier C symbolic analysis
    ("pretty_midi", "pretty_midi",     "tier_c", False),
    # Tier C/D symbolic musicology toolchain
    ("music21",     "music21",         "tier_c", False),   # primary musicology toolkit
    ("symusic",     "symusic",         "tier_c", False),   # fast MIDI ingestion
    ("musif",       "musif",           "tier_d", False),   # research-grade feature extraction
    ("musicntwrk",  "musicntwrk",      "tier_d", False),   # harmonic/motif network analysis
    # Tier D MIR
    ("librosa",     "librosa",         "tier_d", False),
    ("muspy",       "muspy",           "tier_d", False),
    ("partitura",   "partitura",       "tier_d", False),  # score parsing + onset features
    ("essentia",    "essentia",        "tier_d", False),  # spectral MIR features
    # Tier D similarity + clustering
    ("faiss",       "faiss-cpu",       "tier_d", False),
    ("sklearn",     "scikit-learn",    "tier_d", False),  # t-SNE, k-means, silhouette
    ("umap",        "umap-learn",      "tier_d", False),  # UMAP dimensionality reduction
    ("hdbscan",     "hdbscan",         "tier_d", False),  # density-based clustering
    # API
    ("anthropic",   "anthropic",       "tier_d", False),  # LLM interpretation layer
]


def _is_installed(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def _pip_install(pip_name: str) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"    ERROR running pip: {e}")
        return False


def run(check_only: bool = False) -> dict[str, str]:
    """
    Check (and optionally install) all dependencies.
    Returns dict of {package: "ok" | "installed" | "missing" | "failed"}.
    """
    status: dict[str, str] = {}
    print("\nHelix Music Lab — Dependency Check")
    print("=" * 50)

    for import_name, pip_name, tier, required in PACKAGES:
        if _is_installed(import_name):
            print(f"  ✓  {pip_name:<20} [{tier}]  already installed")
            status[pip_name] = "ok"
        elif check_only:
            marker = "REQUIRED" if required else "optional"
            print(f"  ✗  {pip_name:<20} [{tier}]  not installed ({marker})")
            status[pip_name] = "missing"
        else:
            print(f"  →  {pip_name:<20} [{tier}]  installing...", end=" ", flush=True)
            ok = _pip_install(pip_name)
            if ok:
                print("done")
                status[pip_name] = "installed"
            else:
                marker = "REQUIRED — pipeline may fail" if required else "optional — degraded mode"
                print(f"FAILED ({marker})")
                status[pip_name] = "failed"

    print()
    missing_required = [k for k, v in status.items()
                        if v in ("missing", "failed")
                        and any(r for i, k2, t, r in PACKAGES if k2 == k)]
    if missing_required:
        print(f"  WARNING: required packages missing: {missing_required}")
    else:
        print("  All required packages satisfied.")
    print()
    return status


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check-only", action="store_true",
                   help="Report status without installing")
    args = p.parse_args()
    result = run(check_only=args.check_only)
    failed_required = [k for k, v in result.items()
                       if v in ("missing", "failed")
                       and any(r for i, k2, t, r in PACKAGES if k2 == k)]
    sys.exit(1 if failed_required else 0)
