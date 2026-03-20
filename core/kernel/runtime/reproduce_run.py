"""
Reproducibility Engine — 03_engines/runtime/reproduce_run.py

Re-runs a previous probe execution and compares numerical outputs
within defined tolerances to verify deterministic reproduction.
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Tolerance definitions
# ---------------------------------------------------------------------------

TOLERANCES: dict[str, float] = {
    "signal_strength": 0.001,
    "signal":          0.001,
    "decision_dimension": 0.01,
    "order_parameter_R":  0.01,
    "compression_ratio":  0.01,
    "mean_signal":        0.01,
}

EXACT_FIELDS: set[str] = {"passed", "probe_name", "domain"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_run_dir(run_id: str, artifacts_root: Path) -> Path | None:
    """Scan execution/artifacts/probes/*/run_id for the original run directory."""
    probes_root = artifacts_root / "probes"
    if not probes_root.exists():
        return None
    for probe_dir in probes_root.iterdir():
        if not probe_dir.is_dir():
            continue
        candidate = probe_dir / run_id
        if candidate.is_dir():
            return candidate
    return None


def _compare_results(original: dict, reproduced: dict) -> list[dict]:
    """
    Return list of mismatches between original and reproduced probe_result.
    Each mismatch: {field, original_value, reproduced_value, tolerance, exact}.
    """
    mismatches = []

    all_fields = set(original.keys()) | set(reproduced.keys())
    for field in sorted(all_fields):
        orig_val = original.get(field)
        repr_val = reproduced.get(field)

        if field in EXACT_FIELDS:
            if orig_val != repr_val:
                mismatches.append({
                    "field": field,
                    "original_value": orig_val,
                    "reproduced_value": repr_val,
                    "tolerance": None,
                    "exact": True,
                    "match": False,
                })
        elif field in TOLERANCES:
            tol = TOLERANCES[field]
            try:
                diff = abs(float(orig_val) - float(repr_val))
                if diff > tol:
                    mismatches.append({
                        "field": field,
                        "original_value": orig_val,
                        "reproduced_value": repr_val,
                        "tolerance": tol,
                        "actual_diff": diff,
                        "exact": False,
                        "match": False,
                    })
            except (TypeError, ValueError):
                if orig_val != repr_val:
                    mismatches.append({
                        "field": field,
                        "original_value": orig_val,
                        "reproduced_value": repr_val,
                        "tolerance": tol,
                        "exact": False,
                        "match": False,
                    })

    return mismatches


# ---------------------------------------------------------------------------
# Atlas degradation flag
# ---------------------------------------------------------------------------

def _flag_atlas_degraded(
    invariant_name: str,
    run_id: str,
    atlas_dir: Path,
    verbose: bool = False,
) -> None:
    """Mark atlas entry as DEGRADED if reproducibility fails."""
    atlas_file = atlas_dir / f"{invariant_name}.json"
    if not atlas_file.exists():
        return
    try:
        entry = json.loads(atlas_file.read_text(encoding="utf-8"))
        non_repro = entry.get("non_reproducible_runs", [])
        if run_id not in non_repro:
            non_repro.append(run_id)
        entry["non_reproducible_runs"] = non_repro
        entry["reproducibility_flag"] = "DEGRADED"
        atlas_file.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        if verbose:
            print(f"  [atlas] {invariant_name} flagged DEGRADED — run {run_id} non-reproducible")
    except Exception as exc:  # noqa: BLE001
        if verbose:
            print(f"  [atlas] Could not update degradation flag: {exc}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def reproduce_run(
    run_id: str,
    artifacts_root: str | Path | None = None,
    atlas_dir: str | Path | None = None,
    verbose: bool = True,
) -> dict:
    """
    Re-run a previous probe execution and compare outputs within tolerance.

    Steps:
    1. Locate original run directory in execution/artifacts/probes/*/
    2. Load probe_result.json + run_manifest.json
    3. Re-run probe via probe_runner.run_probe(auto_rebuild_atlas=False)
    4. Compare field-by-field within TOLERANCES
    5. Write reproduce_result.json to execution/artifacts/repro_checks/<run_id>/
    6. If mismatch: flag atlas entry with DEGRADED + record non_reproducible_runs

    Returns
    -------
    dict with keys:
        reproducible, run_id, mismatches, repro_run_id,
        probe_name, lab_name, original_dir, repro_dir
    """
    from pathlib import Path as _Path
    import sys

    _root = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())

    if artifacts_root is None:
        artifacts_root = _root / "execution/artifacts"
    else:
        artifacts_root = _Path(artifacts_root)

    if atlas_dir is None:
        atlas_dir = _root / "codex/atlas"
    else:
        atlas_dir = _Path(atlas_dir)

    if verbose:
        print(f"[reproduce] Locating run: {run_id}")

    # 1. Find original run dir
    run_dir = _find_run_dir(run_id, artifacts_root)
    if run_dir is None:
        return {
            "reproducible": False,
            "run_id": run_id,
            "error": f"Run directory not found for run_id={run_id}",
            "mismatches": [],
        }

    # 2. Load original results
    probe_result_path = run_dir / "probe_result.json"
    manifest_path = run_dir / "run_manifest.json"

    if not probe_result_path.exists():
        return {
            "reproducible": False,
            "run_id": run_id,
            "error": "probe_result.json not found in original run dir",
            "mismatches": [],
        }

    original_result = json.loads(probe_result_path.read_text(encoding="utf-8"))
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    probe_name = manifest.get("probe_name") or original_result.get("probe_name", "")
    lab_name = manifest.get("lab_name") or original_result.get("domain", "games")

    if not probe_name:
        return {
            "reproducible": False,
            "run_id": run_id,
            "error": "Cannot determine probe_name from manifest or probe_result",
            "mismatches": [],
        }

    if verbose:
        print(f"[reproduce] probe={probe_name}  lab={lab_name}")
        print(f"[reproduce] Original run dir: {run_dir}")

    # 3. Re-run probe
    sys.path.insert(0, str(_root))
    try:
        from engines.orchestrator import probe_runner  # type: ignore
        repro = probe_runner.run_probe(
            probe_name=probe_name,
            lab_name=lab_name,
            artifacts_root=artifacts_root,
            verbose=False,
            auto_rebuild_atlas=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "reproducible": False,
            "run_id": run_id,
            "error": f"Re-run failed: {exc}",
            "mismatches": [],
            "probe_name": probe_name,
            "lab_name": lab_name,
        }

    repro_probe_result = repro.get("probe_result", {}) or {}
    repro_run_id = repro.get("run_id", "")
    repro_artifact_dir = repro.get("artifact_dir", "")

    if verbose:
        print(f"[reproduce] Re-run ID: {repro_run_id}")

    # 4. Compare
    mismatches = _compare_results(original_result, repro_probe_result)
    reproducible = len(mismatches) == 0

    if verbose:
        if reproducible:
            print("[reproduce] ✓ REPRODUCIBLE — all fields within tolerance")
        else:
            print(f"[reproduce] ✗ NOT REPRODUCIBLE — {len(mismatches)} mismatch(es):")
            for mm in mismatches:
                print(f"    {mm['field']}: {mm['original_value']} → {mm['reproduced_value']}")

    # 5. Write reproduce_result.json
    repro_checks_dir = artifacts_root / "repro_checks" / run_id
    repro_checks_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "reproducible": reproducible,
        "run_id": run_id,
        "repro_run_id": repro_run_id,
        "probe_name": probe_name,
        "lab_name": lab_name,
        "original_dir": str(run_dir),
        "repro_dir": str(repro_artifact_dir),
        "mismatches": mismatches,
        "tolerances_used": TOLERANCES,
        "exact_fields_checked": sorted(EXACT_FIELDS),
    }

    repro_result_path = repro_checks_dir / "reproduce_result.json"
    repro_result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if verbose:
        print(f"[reproduce] Result written: {repro_result_path}")

    # 6. Flag atlas degraded on mismatch
    if not reproducible:
        _flag_atlas_degraded(probe_name, run_id, atlas_dir, verbose=verbose)

    return result
