"""
Probe Runner — 03_engines/orchestrator/probe_runner.py

Orchestrate a single probe run end-to-end:
  1. Discover probe script via probe_registry
  2. Load lab dataset ({probe_name}_dataset.json or first .json fallback)
  3. Build run manifest + env snapshot
  4. Execute probe in sandbox subprocess
  5. Write artifact bundle (manifest, dataset hash, env snapshot)
  6. Lock artifact dir (Linux/WSL2 only)
  7. Optionally rebuild Atlas

CLI: helix probe-run <probe> [--lab <lab>]
"""

from __future__ import annotations
import json
from importlib import import_module
from pathlib import Path
from typing import Any


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def _load_lab_dataset(probe_name: str, lab_name: str) -> tuple[dict, Path]:
    """
    Load dataset for a probe in a lab.

    Resolution order:
      1. 04_labs/<lab_name>/<probe_name>_dataset.json  (probe-specific)
      2. First .json file alphabetically in 04_labs/<lab_name>/

    Returns (dataset_dict, dataset_path).
    Raises FileNotFoundError if no dataset found.
    """
    lab_dir = ROOT / "04_labs" / lab_name
    if not lab_dir.exists():
        raise FileNotFoundError(f"Lab directory not found: {lab_dir}")

    # Probe-specific dataset (preferred)
    specific = lab_dir / f"{probe_name}_dataset.json"
    if specific.exists():
        with open(specific, "r", encoding="utf-8") as f:
            return json.load(f), specific

    # Fallback: first .json alphabetically
    candidates = sorted(lab_dir.glob("*.json"))
    if candidates:
        with open(candidates[0], "r", encoding="utf-8") as f:
            return json.load(f), candidates[0]

    raise FileNotFoundError(
        f"No dataset found for probe '{probe_name}' in lab '{lab_name}'. "
        f"Expected {specific} or any .json in {lab_dir}"
    )


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_probe(
    probe_name: str,
    lab_name: str = "games",
    artifacts_root: str | Path | None = None,
    timeout: float = 120.0,
    verbose: bool = True,
    auto_rebuild_atlas: bool = True,
) -> dict[str, Any]:
    """
    Run a single probe against a lab dataset.

    Args:
        probe_name:         Name of the probe (e.g. 'decision_compression').
        lab_name:           Lab to source the dataset from (e.g. 'games').
        artifacts_root:     Root for artifact output (default: ROOT/07_artifacts).
        timeout:            Max probe subprocess execution time in seconds.
        verbose:            Print progress messages.
        auto_rebuild_atlas: If True, rebuild Atlas after artifact bundle write.

    Returns:
        Summary dict with run_id, passed, timed_out, duration_seconds,
        artifact_dir, artifacts_present, and probe metadata.
    """
    if artifacts_root is None:
        artifacts_root = ROOT / "07_artifacts"
    artifacts_root = Path(artifacts_root)

    # --- Load probe modules ---
    probe_registry = import_module("03_engines.orchestrator.probe_registry")
    run_manifest_mod = import_module("03_engines.runtime.run_manifest")
    sandbox = import_module("03_engines.substrate.sandbox_runner")
    artifact_lock = import_module("03_engines.runtime_hooks.artifact_lock")

    # --- Discover probe ---
    probes_dir = ROOT / "04_labs" / "probes"
    record = probe_registry.get_probe(probe_name, probes_dir)
    if record is None:
        raise ValueError(
            f"Probe '{probe_name}' not found in {probes_dir}. "
            f"Available: {list(probe_registry.discover_probes(probes_dir).keys())}"
        )

    probe_script = record.script_path
    if verbose:
        print(f"[PROBE_RUNNER] Probe: {probe_name} ({probe_script.name})")

    # --- Load dataset ---
    dataset, dataset_path = _load_lab_dataset(probe_name, lab_name)
    if verbose:
        print(f"[PROBE_RUNNER] Dataset: {dataset_path.name} ({lab_name})")

    # --- Build run ID + manifest ---
    run_id = run_manifest_mod.generate_run_id(probe_name)
    if verbose:
        print(f"[PROBE_RUNNER] Run ID: {run_id}")

    manifest = run_manifest_mod.build_run_manifest(
        run_id=run_id,
        probe_name=probe_name,
        dataset=dataset,
        probe_script=probe_script,
        lab_name=lab_name,
    )
    env_snapshot = run_manifest_mod.capture_env_snapshot()

    # --- Prepare artifact directory ---
    run_dir = artifacts_root / "probes" / probe_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # --- System input for probe ---
    system_input = {
        "dataset_path": str(dataset_path),
        "dataset": dataset,
        "lab_name": lab_name,
        "run_id": run_id,
    }

    # --- Execute probe in sandbox ---
    if verbose:
        print(f"[PROBE_RUNNER] Running probe in sandbox (timeout={timeout}s)...")

    sandbox_result = sandbox.run_probe_sandboxed(
        probe_script=probe_script,
        system_input_json=system_input,
        artifacts_dir=run_dir,
        timeout=timeout,
        verbose=verbose,
    )

    status = "PASS" if sandbox_result.passed else (
        "TIMEOUT" if sandbox_result.timed_out else "FAIL"
    )
    if verbose:
        print(
            f"[PROBE_RUNNER] Sandbox result: {status} "
            f"(returncode={sandbox_result.returncode}, "
            f"{sandbox_result.duration_seconds:.2f}s)"
        )

    # --- Write artifact bundle ---
    run_manifest_mod.write_artifact_bundle(
        run_dir=run_dir,
        run_manifest=manifest,
        dataset=dataset,
        env_snapshot=env_snapshot,
    )

    artifacts_present = sorted(p.name for p in run_dir.iterdir() if p.is_file())
    locked = artifact_lock.lock_artifact_run(run_dir)

    if verbose:
        print(
            f"[PROBE_RUNNER] Artifact bundle written: {run_dir}\n"
            f"[PROBE_RUNNER] Complete. artifacts={artifacts_present}, locked={locked}"
        )

    # --- Auto-rebuild Atlas ---
    if auto_rebuild_atlas:
        try:
            atlas_builder = import_module("03_engines.atlas.atlas_builder")
            atlas_builder.build_atlas(
                artifacts_root=artifacts_root,
                atlas_dir=ROOT / "06_atlas",
                verbose=False,
            )
        except Exception as e:
            if verbose:
                print(f"[PROBE_RUNNER] Atlas auto-rebuild skipped: {e}")

    return {
        "run_id": run_id,
        "probe_name": probe_name,
        "lab_name": lab_name,
        "passed": sandbox_result.passed,
        "timed_out": sandbox_result.timed_out,
        "returncode": sandbox_result.returncode,
        "duration_seconds": sandbox_result.duration_seconds,
        "artifact_dir": str(run_dir),
        "artifacts_present": artifacts_present,
        "probe_result": sandbox_result.probe_result,
        "locked": locked,
    }
