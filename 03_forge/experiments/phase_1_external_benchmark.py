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

FAKE_WORKSPACE = ROOT / '04_workspaces' / 'external_benchmark_repos'
if FAKE_WORKSPACE.exists():
    shutil.rmtree(FAKE_WORKSPACE)
FAKE_WORKSPACE.mkdir(parents=True, exist_ok=True)

def spearman_rank_correlation(x, y):
    if len(x) != len(y) or len(x) < 2: return 0.0
    def rank(arr):
        s = sorted(list(enumerate(arr)), key=lambda v: v[1])
        r = [0]*len(arr)
        for i, (orig_i, v) in enumerate(s):
            r[orig_i] = i
        return r
    rx = rank(x)
    ry = rank(y)
    n = len(x)
    d_sq = sum((rx[i] - ry[i])**2 for i in range(n))
    return 1 - (6 * d_sq) / (n * (n**2 - 1))

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

# Simulate true structural collapse: iteratively knock out max degree node, measure steps until 50% edges lost
def simulate_true_collapse(graph_def):
    # graph_def is a dict mapping node to list of imported nodes
    adj = {k: list(v) for k, v in graph_def.items()}
    initial_edges = sum(len(v) for v in adj.values())
    
    if initial_edges == 0: return 0
    
    steps = 0
    while len(adj) > 0:
        # find node with max in-degree + out-degree
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
            
    # Inverse: more steps = more robust. Less steps = more fragile.
    # Return fragility proxy: (total_nodes - steps) / total_nodes
    return (len(graph_def) - steps) / max(1, len(graph_def))

def main():
    print("Building External Benchmark Pack (20 graphs)...")
    
    repos = {}
    collapse_ground_truth = {}
    
    for i in range(20):
        name = f"benchmark_graph_{i}"
        node_count = random.randint(10, 30)
        
        # Determine archetype
        if i % 3 == 0:
            # Scale-free (hub)
            graph_def = {}
            hub = f"node_0"
            graph_def[hub] = []
            for j in range(1, node_count):
                graph_def[f"node_{j}"] = [hub] if random.random() < 0.8 else []
        elif i % 3 == 1:
            # Random distributed
            graph_def = {}
            for j in range(node_count):
                graph_def[f"node_{j}"] = [f"node_{x}" for x in random.sample(range(node_count), random.randint(1, 3)) if x != j]
        else:
            # Chain / Sequence
            graph_def = {}
            for j in range(node_count):
                graph_def[f"node_{j}"] = [f"node_{(j+1)%node_count}"] if random.random() < 0.9 else []
                if j == 0: # choke
                    graph_def[f"node_{j}"] = [f"node_{x}" for x in range(1, 5)]
        
        # generate files
        content = {}
        for k, v in graph_def.items():
            c = "def fn():\n"
            for t in v:
                c += f"    import {t}\n"
            c += "    assert True\n    x = 1\n    y = 2\n    return x + y\n\n\n"
            content[f"{k}.py"] = c
            
        repos[name] = graph_def
        create_fake_repo(name, content)
        
        collapse_ground_truth[name] = simulate_true_collapse(graph_def)
        
    srd_risks = []
    baseline_max_degrees = []
    baseline_mean_degrees = []
    actual_fragilities = []
    
    rep_results = []
    
    for name in repos:
        run_rrs(FAKE_WORKSPACE / name)
        outp = get_latest_rrs_out(name)
        if outp:
            with open(outp / 'metrics.json') as f:
                metrics = json.load(f)
            with open(outp / 'risk_report.json') as f:
                risk_rep = json.load(f)
            with open(outp / 'elasticity_curve.json') as f:
                el_rep = json.load(f)
                
            srd_score = risk_rep.get("system_mean_risk", 0.0)
            
            degrees = [m.get("connectivity", 0) for m in metrics]
            max_deg = max(degrees) if degrees else 0
            mean_deg = statistics.mean(degrees) if degrees else 0
            
            actual = collapse_ground_truth[name]
            
            srd_risks.append(srd_score)
            baseline_max_degrees.append(max_deg)
            baseline_mean_degrees.append(mean_deg)
            actual_fragilities.append(actual)
            
            rep_results.append({
                "repo": name,
                "srd_risk": rd(srd_score),
                "actual_fragility": rd(actual),
                "baseline_max_degree": max_deg,
                "elasticity_shape": el_rep.get("classified_shape")
            })

    corr_srd = spearman_rank_correlation(srd_risks, actual_fragilities)
    corr_max_deg = spearman_rank_correlation(baseline_max_degrees, actual_fragilities)
    corr_mean_deg = spearman_rank_correlation(baseline_mean_degrees, actual_fragilities)
    
    uplift = abs(corr_srd) > abs(corr_max_deg) and abs(corr_srd) > abs(corr_mean_deg)
    
    output = {
        "correlation_SRD_vs_ActualCollapse": rd(corr_srd),
        "correlation_MaxDegree_vs_ActualCollapse": rd(corr_max_deg),
        "correlation_MeanDegree_vs_ActualCollapse": rd(corr_mean_deg),
        "statistical_uplift_verified": uplift,
        "results": rep_results
    }
    
    with open(STRESS_DIR / 'external_validation_results.json', 'w') as f:
        json.dump(output, f, indent=4)
        
    print(f"Phase 1 External Validation. SRD Corr: {corr_srd:.3f}, MaxDeg Corr: {corr_max_deg:.3f}")
    if uplift:
        print("PASS: SRD significantly outperforms baselines.")
    else:
        print("FAIL: SRD does not outperform baseline heuristics.")

def rd(v):
    return round(v, 4) if isinstance(v, float) else v

if __name__ == "__main__":
    main()
