"""Atlas Builder.

Compile invariant summaries from probe artifacts into ``codex/atlas/invariants``.
This module aggregates probe run outputs and relies on the centralized
confidence scoring rules in ``core/governance/confidence_scoring.py``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.governance import confidence_scoring
from core.paths import ARTIFACTS_ROOT, ATLAS_ROOT


def _load_json_safe(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def scan_probe_runs(artifacts_root: str | Path = ARTIFACTS_ROOT) -> dict[str, list[dict[str, Any]]]:
    artifacts_root = Path(artifacts_root)
    probes_dir = artifacts_root / "probes"
    results: dict[str, list[dict[str, Any]]] = {}
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


def build_atlas_entry(probe_name: str, run_results: list[dict[str, Any]]) -> dict[str, Any]:
    agg = confidence_scoring.aggregate_run_results(run_results)
    confidence = confidence_scoring.score_confidence(
        agg["observed_domains"],
        agg["pass_rate"],
        agg["mean_signal"],
    )

    versions_seen: list[str] = []
    for result in run_results:
        version = result.get("probe_version", "1.0.0")
        if version and version not in versions_seen:
            versions_seen.append(version)

    return {
        "invariant": probe_name,
        "confidence": confidence,
        "observed_in": agg["observed_domains"],
        "supporting_runs": [
            {
                "run_id": r.get("run_id", "unknown"),
                "domain": r.get("domain", r.get("lab_name", "unknown")),
                "passed": r.get("passed", False),
                "signal": float(r.get("signal", r.get("signal_strength", 0.0))),
            }
            for r in run_results
        ],
        "pass_rate": agg["pass_rate"],
        "mean_signal": agg["mean_signal"],
        "run_count": agg["run_count"],
        "probe_versions_used": versions_seen,
        "latest_probe_version": versions_seen[-1] if versions_seen else "1.0.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def build_atlas(
    artifacts_root: str | Path | None = None,
    atlas_dir: str | Path | None = None,
    verbose: bool = True,
) -> dict[str, Path]:
    artifacts_root = Path(artifacts_root or ARTIFACTS_ROOT)
    atlas_dir = Path(atlas_dir or (ATLAS_ROOT / "invariants"))
    atlas_dir.mkdir(parents=True, exist_ok=True)

    all_runs = scan_probe_runs(artifacts_root)
    written: dict[str, Path] = {}
    index_entries: list[dict[str, Any]] = []

    for probe_name, run_results in sorted(all_runs.items()):
        if not run_results:
            continue
        entry = build_atlas_entry(probe_name, run_results)
        out_path = atlas_dir / f"{probe_name}.json"
        out_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        written[probe_name] = out_path
        index_entries.append({
            "invariant": probe_name,
            "confidence": entry["confidence"],
            "observed_in": entry["observed_in"],
            "run_count": entry["run_count"],
            "pass_rate": entry["pass_rate"],
            "latest_probe_version": entry["latest_probe_version"],
        })
        if verbose:
            print(
                f"[ATLAS_BUILDER] {probe_name}: confidence={entry['confidence']}, "
                f"domains={entry['observed_in']}, runs={entry['run_count']}, "
                f"pass_rate={entry['pass_rate']:.0%}"
            )

    index_path = atlas_dir / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "invariants": index_entries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if verbose:
        print(f"[ATLAS_BUILDER] Atlas built: {len(written)} invariant(s) → {atlas_dir}")
    return written
