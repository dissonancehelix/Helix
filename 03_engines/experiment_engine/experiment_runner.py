"""
Experiment Runner — 03_engines/experiment_engine/experiment_runner.py

Executes large batches of probe runs across parameter spaces defined in yaml plans.
Aggregates results and performs regime detection.
"""

import sys
import os
import json
import itertools
import yaml
from pathlib import Path
from importlib import import_module
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())

def generate_dataset_for_probe(probe_name: str, base_dataset: dict, params: dict) -> dict:
    """Generates a dataset dictionary for the probe given the swept parameters."""
    ds = dict(base_dataset)
    ds.update(params)
    
    agent_count = params.get("agent_count", len(ds.get("agents", [])) if "agents" in ds else 5)
    
    if probe_name == "decision_compression":
        # Generate dummy agents and rounds based on parameters
        comp_strength = params.get("competition_strength", 0.0)
        agents = []
        for i in range(agent_count):
            # If high comp strength, skew the weights
            w = 1.0/agent_count
            if i == 0:
                w += comp_strength * 0.5
            agents.append({"id": f"p_{i}", "influence_weight": w})
        ds["agents"] = agents
        ds["decision_rounds"] = [{"round": 1, "weights": [a["influence_weight"] for a in agents], "outcome": "A"}]
        
    elif probe_name == "oscillator_locking":
        ds["coupling_strength"] = params.get("coupling_strength", params.get("competition_strength", 0.0) * 2)
        oscillators = []
        for i in range(agent_count):
            oscillators.append({"id": f"o_{i}", "initial_phase": 0.0, "natural_frequency": 1.0 + (i*0.01)})
        ds["oscillators"] = oscillators
        
    return ds

def _run_single_probe(probe_name, lab_name, params, artifacts_root, exp_name):
    probe_runner = import_module('03_engines.orchestrator.probe_runner')
    # Use existing code but override dataset
    try:
        probe_runner = import_module("03_engines.orchestrator.probe_runner")
        ds, _ = probe_runner._load_lab_dataset(probe_name, lab_name)
    except Exception:
        ds = {"domain": lab_name}

    ds_swept = generate_dataset_for_probe(probe_name, ds, params)
    
    run_manifest_mod = import_module("03_engines.runtime.run_manifest")
    run_id = run_manifest_mod.generate_run_id(f"{exp_name}_{probe_name}")
    
    # We construct the run manually to place under experiments/<exp_name>/<run_id>
    probe_registry = import_module("03_engines.orchestrator.probe_registry")
    probes_dir = ROOT / "04_labs" / "probes"
    record = probe_registry.get_probe(probe_name, probes_dir)
    probe_script = record.script_path
    
    run_dir = Path(artifacts_root) / "experiments" / exp_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = run_manifest_mod.build_run_manifest(
        run_id=run_id, probe_name=probe_name, dataset=ds_swept,
        probe_script=probe_script, lab_name=lab_name
    )
    manifest["experiment_name"] = exp_name
    manifest["parameters"] = params
    
    env_snapshot = run_manifest_mod.capture_env_snapshot()
    
    system_input = {
        "dataset_path": str(run_dir / "dataset.json"),
        "dataset": ds_swept,
        "lab_name": lab_name,
        "run_id": run_id,
        "parameters": params,
    }
    
    sandbox = import_module("03_engines.substrate.sandbox_runner")
    result = sandbox.run_probe_sandboxed(
        probe_script=probe_script,
        system_input_json=system_input,
        artifacts_dir=run_dir,
        timeout=60.0,
        verbose=False,
    )
    
    artifact_lock = import_module("03_engines.runtime_hooks.artifact_lock")
    run_manifest_mod.write_artifact_bundle(
        run_dir=run_dir,
        run_manifest=manifest,
        dataset=ds_swept,
        env_snapshot=env_snapshot,
    )
    artifact_lock.lock_artifact_run(run_dir)
    
    summary = {
        "probe_name": probe_name, "lab_name": lab_name, "parameters": params,
        "run_id": run_id, "passed": result.passed, "artifact_dir": str(run_dir),
        "probe_result": result.probe_result
    }
    return summary

def run_experiment(exp_name: str):
    exp_path = ROOT / "04_labs" / "experiments" / f"{exp_name}.yaml"
    if not exp_path.exists():
        raise FileNotFoundError(f"Experiment {exp_name} not found at {exp_path}")
        
    with open(exp_path, 'r') as f:
        plan = yaml.safe_load(f)
        
    probes = plan.get("probes", [])
    labs = plan.get("labs", [])
    params_dict = plan.get("parameters", {})
    
    # Generate grid
    keys = list(params_dict.keys())
    values = list(params_dict.values())
    grid = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
    
    artifacts_root = ROOT / "07_artifacts"
    exp_dir = artifacts_root / "experiments" / exp_name
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    # Parallel execution
    tasks = []
    results = []
    
    max_workers = os.cpu_count() or 4
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for probe in probes:
            for lab in labs:
                for params in grid:
                    tasks.append(executor.submit(_run_single_probe, probe, lab, params, artifacts_root, exp_name))
        
        for future in as_completed(tasks):
            try:
                res = future.result()
                results.append(res)
                print(f"[EXP] Completed {res['probe_name']} on {res['lab_name']} | Passed: {res['passed']}")
            except Exception as e:
                print(f"[EXP] Probe run failed: {e}")
                
    # Regime Detection
    regime_det = import_module("03_engines.analysis.regime_detection")
    regime_results = regime_det.detect_regimes(results, probes, keys)
    
    summary = {
        "experiment_name": exp_name,
        "total_runs": len(results),
        "parameter_grid_size": len(grid),
        "results_summary": [
            {"probe": r["probe_name"], "lab": r["lab_name"], "passed": r["passed"], "params": r["parameters"]}
            for r in results
        ],
        "regimes_detected": regime_results
    }
    
    summary_path = exp_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)
        
    print(f"\n[EXP] Summary written to {summary_path}")
