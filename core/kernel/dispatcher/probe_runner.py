"""Probe Runner.

Canonical probe orchestration for Helix's HSL -> operators -> compiler flow.
Probe datasets are sourced from ``labs/datasets/<lab_name>`` and artifacts are
written under ``execution/artifacts/probes/<probe>/<run_id>``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.kernel.dispatcher import probe_registry
from core.kernel.graph.storage import atlas_builder
from core.kernel.runtime import artifact_lock, run_manifest
from core.kernel.substrate import sandbox_runner
from core.paths import ARTIFACTS_ROOT, ATLAS_ROOT, LAB_DATASETS_ROOT


LAB_ALIASES = {
    "games": "agents",
}


def _resolve_lab_dir(lab_name: str) -> Path:
    normalized = LAB_ALIASES.get(lab_name, lab_name)
    return LAB_DATASETS_ROOT / normalized


def _load_lab_dataset(probe_name: str, lab_name: str) -> tuple[dict[str, Any], Path]:
    lab_dir = _resolve_lab_dir(lab_name)
    if not lab_dir.exists():
        raise FileNotFoundError(f"Lab dataset directory not found: {lab_dir}")

    specific = lab_dir / f"{probe_name}_dataset.json"
    if specific.exists():
        return json.loads(specific.read_text(encoding="utf-8")), specific

    candidates = sorted(lab_dir.glob("*.json"))
    if candidates:
        first = candidates[0]
        return json.loads(first.read_text(encoding="utf-8")), first

    raise FileNotFoundError(
        f"No dataset found for probe '{probe_name}' in '{lab_name}'. "
        f"Expected {specific} or any JSON file in {lab_dir}."
    )


def run_probe(
    probe_name: str,
    lab_name: str = "games",
    artifacts_root: str | Path | None = None,
    timeout: float = 120.0,
    verbose: bool = True,
    auto_rebuild_atlas: bool = True,
) -> dict[str, Any]:
    artifacts_root = Path(artifacts_root or ARTIFACTS_ROOT)

    record = probe_registry.get_probe(probe_name)
    if record is None:
        raise ValueError(
            f"Probe '{probe_name}' not found. Available: "
            f"{list(probe_registry.discover_probes().keys())}"
        )

    dataset, dataset_path = _load_lab_dataset(probe_name, lab_name)
    run_id = run_manifest.generate_run_id(probe_name)
    manifest = run_manifest.build_run_manifest(
        run_id=run_id,
        probe_name=probe_name,
        dataset=dataset,
        probe_script=record.script_path,
        lab_name=lab_name,
    )
    env_snapshot = run_manifest.capture_env_snapshot()

    run_dir = artifacts_root / "probes" / probe_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    system_input = {
        "dataset_path": str(dataset_path),
        "dataset": dataset,
        "lab_name": lab_name,
        "run_id": run_id,
    }

    if verbose:
        print(f"[PROBE_RUNNER] Probe: {probe_name} ({record.script_path.name})")
        print(f"[PROBE_RUNNER] Dataset: {dataset_path}")
        print(f"[PROBE_RUNNER] Run ID: {run_id}")

    sandbox_result = sandbox_runner.run_probe_sandboxed(
        probe_script=record.script_path,
        system_input_json=system_input,
        artifacts_dir=run_dir,
        timeout=timeout,
        verbose=verbose,
    )

    run_manifest.write_artifact_bundle(
        run_dir=run_dir,
        run_manifest=manifest,
        dataset=dataset,
        env_snapshot=env_snapshot,
    )

    artifacts_present = sorted(p.name for p in run_dir.iterdir() if p.is_file())
    locked = artifact_lock.lock_artifact_run(run_dir)

    if auto_rebuild_atlas:
        atlas_builder.build_atlas(
            artifacts_root=artifacts_root,
            atlas_dir=ATLAS_ROOT / "invariants",
            verbose=verbose,
        )

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
