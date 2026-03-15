"""
Atlas Builder — 03_engines/atlas/atlas_builder.py

Scan all probe run artifacts and generate Atlas invariant entries in 06_atlas/.

Reads:  07_artifacts/probes/<probe_name>/<run_id>/probe_result.json
        07_artifacts/probes/<probe_name>/<run_id>/run_manifest.json
Writes: 06_atlas/<probe_name>.json
        06_atlas/index.json
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any


ROOT = Path("c:/Users/dissonance/Desktop/Helix")


# ---------------------------------------------------------------------------
# Artifact scanning
# ---------------------------------------------------------------------------

def _load_json_safe(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def scan_probe_runs(
    artifacts_root: str | Path,
) -> dict[str, list[dict]]:
    """
    Scan all probe artifact directories and load probe_result.json files.

    Returns:
        dict mapping probe_name → list of enriched result dicts.
    """
    artifacts_root = Path(artifacts_root)
    probes_dir = artifacts_root / "probes"
    results: dict[str, list[dict]] = {}

    if not probes_dir.exists():
        return results

    for probe_dir in sorted(probes_dir.iterdir()):
        if not probe_dir.is_dir():
            continue
        probe_name = probe_dir.name
        results.setdefault(probe_name, [])

        for run_dir in sorted(probe_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            result = _load_json_safe(run_dir / "probe_result.json")
            manifest = _load_json_safe(run_dir / "run_manifest.json")
            if result is None:
                continue
            if manifest:
                result.setdefault("lab_name", manifest.get("lab_name", "unknown"))
                result.setdefault("run_id", manifest.get("run_id", run_dir.name))
                result.setdefault("probe_version", manifest.get("probe_version", "1.0.0"))
                result.setdefault("probe_code_hash", manifest.get("probe_code_hash", ""))
            results[probe_name].append(result)

    return results


# ---------------------------------------------------------------------------
# Atlas entry builder
# ---------------------------------------------------------------------------

def build_atlas_entry(
    probe_name: str,
    run_results: list[dict],
) -> dict[str, Any]:
    """
    Build a single Atlas invariant entry from a list of probe run results.
    """
    scoring = import_module("03_engines.atlas.confidence_scoring")
    agg = scoring.aggregate_run_results(run_results)
    confidence = scoring.score_confidence(
        agg["observed_domains"], agg["pass_rate"], agg["mean_signal"]
    )

    supporting_runs = [
        {
            "run_id": r.get("run_id", "unknown"),
            "domain": r.get("domain", r.get("lab_name", "unknown")),
            "passed": r.get("passed", False),
            "signal": float(r.get("signal", r.get("signal_strength", 0.0))),
        }
        for r in run_results
    ]

    # Probe version history
    versions_seen: list[str] = []
    for r in run_results:
        v = r.get("probe_version", "1.0.0")
        if v and v not in versions_seen:
            versions_seen.append(v)
    latest_version = versions_seen[-1] if versions_seen else "1.0.0"

    return {
        "invariant": probe_name,
        "confidence": confidence,
        "observed_in": agg["observed_domains"],
        "supporting_runs": supporting_runs,
        "pass_rate": agg["pass_rate"],
        "mean_signal": agg["mean_signal"],
        "run_count": agg["run_count"],
        "probe_versions_used": versions_seen,
        "latest_probe_version": latest_version,
        "last_updated": datetime.now(tz=timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Top-level builder
# ---------------------------------------------------------------------------

def build_atlas(
    artifacts_root: str | Path | None = None,
    atlas_dir: str | Path | None = None,
    verbose: bool = True,
) -> dict[str, Path]:
    """
    Scan all probe artifacts and write Atlas entries to 06_atlas/.

    Returns:
        dict mapping probe_name → atlas file path written.
    """
    if artifacts_root is None:
        artifacts_root = ROOT / "07_artifacts"
    if atlas_dir is None:
        atlas_dir = ROOT / "06_atlas"

    artifacts_root = Path(artifacts_root)
    atlas_dir = Path(atlas_dir)
    atlas_dir.mkdir(parents=True, exist_ok=True)

    all_runs = scan_probe_runs(artifacts_root)
    written: dict[str, Path] = {}
    index_entries: list[dict] = []

    for probe_name, run_results in sorted(all_runs.items()):
        if not run_results:
            continue
        entry = build_atlas_entry(probe_name, run_results)
        out_path = atlas_dir / f"{probe_name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        written[probe_name] = out_path

        if verbose:
            domains = entry["observed_in"]
            print(
                f"[ATLAS_BUILDER] {probe_name}: "
                f"confidence={entry['confidence']}, "
                f"domains={domains}, "
                f"runs={entry['run_count']}, "
                f"pass_rate={entry['pass_rate']:.0%}"
            )

        index_entries.append({
            "invariant": probe_name,
            "confidence": entry["confidence"],
            "observed_in": entry["observed_in"],
            "run_count": entry["run_count"],
            "pass_rate": entry["pass_rate"],
            "latest_probe_version": entry["latest_probe_version"],
        })

    index_path = atlas_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "invariants": index_entries,
            },
            f,
            indent=2,
        )

    if verbose:
        print(f"[ATLAS_BUILDER] Atlas built: {len(written)} invariant(s) → {atlas_dir}")

    return written
