import os
import json
import shutil
import subprocess
from pathlib import Path
import random
import statistics

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
STRESS_DIR = ROOT / '06_artifacts' / 'rrs'
STRESS_DIR.mkdir(parents=True, exist_ok=True)

FAKE_WORKSPACE = ROOT / '04_workspaces' / 'blind_forecast_repos'
if FAKE_WORKSPACE.exists():
    shutil.rmtree(FAKE_WORKSPACE)
FAKE_WORKSPACE.mkdir(parents=True, exist_ok=True)

def create_fake_repo(name, files_content):
    repo_dir = FAKE_WORKSPACE / name
    repo_dir.mkdir(parents=True, exist_ok=True)
    for f_name, content in files_content.items():
        with open(repo_dir / f_name, 'w') as f:
            f.write(content)
    return str(repo_dir)

def run_rrs(repo_path):
    cmd = ["python", str(ROOT / "04_workspaces" / "rrs_tool" / "rrs.py"), "scan", repo_path]
    subprocess.run(cmd, capture_output=True, text=True)

def get_latest_rrs_out(repo_name):
    rrs_out_dir = ROOT / '06_artifacts' / 'rrs' / repo_name
    if not rrs_out_dir.exists(): return None
    runs = [d for d in rrs_out_dir.iterdir() if d.is_dir()]
    if not runs: return None
    runs.sort(key=lambda x: x.name, reverse=True)
    return runs[0]

def simulate_true_collapse(graph_def):
    adj = {k: list(v) for k, v in graph_def.items()}
    initial_edges = sum(len(v) for v in adj.values())
    if initial_edges == 0: return 0
    steps = 0
    while len(adj) > 0:
        degrees = {}
        for k in adj: degrees[k] = len(adj[k])
        for k, v in adj.items():
            for t in v:
                if t in degrees: degrees[t] += 1
        if not degrees: break
        target = max(degrees, key=degrees.get)
        del adj[target]
        for k in adj:
            if target in adj[k]:
                adj[k].remove(target)
        steps += 1
        current_edges = sum(len(v) for v in adj.values())
        if current_edges < initial_edges * 0.5:
            break
    # actual horizon (steps / total_nodes)
    return steps / max(1, len(graph_def))

def main():
    print("Building Blind Forecast Pack (15 graphs)...")
    repos = {}
    ground_truth = {}
    
    for i in range(15):
        name = f"forecast_graph_{i}"
        node_count = random.randint(15, 40)
        
        # Determine archetype
        graph_def = {}
        if i % 2 == 0:
            # Scale-free (hub)
            hub = f"node_0"
            graph_def[hub] = []
            for j in range(1, node_count):
                graph_def[f"node_{j}"] = [hub] if random.random() < 0.8 else []
        else:
            # Random distributed
            for j in range(node_count):
                graph_def[f"node_{j}"] = [f"node_{x}" for x in random.sample(range(node_count), random.randint(1, 3)) if x != j]
        
        content = {}
        for k, v in graph_def.items():
            c = "def fn():\n"
            for t in v:
                c += f"    import {t}\n"
            c += "    assert True\n    x = 1\n    y = 2\n    return x + y\n\n\n"
            content[f"{k}.py"] = c
            
        repos[name] = graph_def
        create_fake_repo(name, content)
        ground_truth[name] = simulate_true_collapse(graph_def)

    horizons = []
    actual_horizons = []
    errors = []
    baseline_errors = []
    
    rep_results = []
    
    for name in repos:
        run_rrs(FAKE_WORKSPACE / name)
        outp = get_latest_rrs_out(name)
        if outp:
            with open(outp / 'risk_report.json') as f:
                risk_rep = json.load(f)
            with open(outp / 'metrics.json') as f:
                metrics = json.load(f)
                
            srd_score = risk_rep.get("system_mean_risk", 0.0)
            
            # forecast horizon = (1 - sys_risk). if high risk -> small horizon.
            fho = max(0.01, 1.0 - srd_score)
            actual = ground_truth[name]
            
            # baseline heuristic MAE (mean degree) normalized
            degrees = [m.get("connectivity", 0) for m in metrics]
            mean_deg = statistics.mean(degrees) if degrees else 0
            base_fho = max(0.01, 1.0 - (mean_deg / max(1, len(metrics))))
            
            err = abs(fho - actual)
            base_err = abs(base_fho - actual)
            
            horizons.append(fho)
            actual_horizons.append(actual)
            errors.append(err)
            baseline_errors.append(base_err)
            
            rep_results.append({
                "repo": name,
                "predicted_horizon": round(fho, 4),
                "actual_horizon": round(actual, 4),
                "srd_error": round(err, 4),
                "baseline_error": round(base_err, 4)
            })
            
    mae = statistics.mean(errors) if errors else 0
    b_mae = statistics.mean(baseline_errors) if baseline_errors else 0
    
    output = {
        "mean_absolute_error_SRD": round(mae, 4),
        "mean_absolute_error_Baseline": round(b_mae, 4),
        "calibration_diff": round(mae - b_mae, 4),
        "pass_condition": mae < b_mae,
        "results": rep_results
    }
    
    with open(STRESS_DIR / 'forecast_validation_results.json', 'w') as f:
        json.dump(output, f, indent=4)
        
    print(f"Phase 2 Blind Forecast. SRD MAE: {mae:.3f} | Baseline MAE: {b_mae:.3f}")

if __name__ == "__main__":
    main()
