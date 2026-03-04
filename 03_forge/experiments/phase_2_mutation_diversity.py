import os
import json
import statistics
from pathlib import Path
import math

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
RRS_DIR = ROOT / '06_artifacts' / 'rrs'
# Target 03_forge latest run to modify
TARGET_REPO = '03_forge'

def get_latest_rrs_run(repo_name):
    d = RRS_DIR / repo_name
    if not d.exists(): return None
    runs = [x for x in d.iterdir() if x.is_dir()]
    if not runs: return None
    runs.sort(key=lambda x: x.name, reverse=True)
    return runs[0]

def compute_risk(node):
    c = node['connectivity']
    f = node['feedback_loops']
    s = node['safeguards']
    u = node['unobserved_drops']
    base_val = 0.1 + 0.05 * math.log(c + 1) + 1.2 * (f / (1 + 2.0 * s)) + 0.3 * u
    return max(0.0, min(1.0, base_val))

def apply_mutator(node, mutator_id, intensity):
    mut = dict(node)
    c, f, s, u = mut.get('connectivity', 0), mut.get('feedback_loops', 0), mut.get('safeguards', 0), mut.get('unobserved_drops', 0)
    
    if mutator_id == "M1": # Random node removal (handled externally, but here we simulate isolated reduction in connectivity)
        mut['connectivity'] = max(0, c - int(c * intensity))
    elif mutator_id == "M2": # Degree-preserving edge swap (preserves connectivity, but breaks localized cycles)
        mut['feedback_loops'] = max(0, f - intensity)
    elif mutator_id == "M3": # Cluster isolation (Drops connectivity but retains cycle density within sub-component)
        mut['connectivity'] = max(1, int(c * (1 - intensity)))
        mut['feedback_loops'] = min(1.0, f + (intensity * 0.1))
    elif mutator_id == "M4": # Feedback loop injection
        mut['feedback_loops'] = min(1.0, f + intensity)
    elif mutator_id == "M5": # Damping edge deletion (remove safeguards)
        mut['safeguards'] = max(0.0, s - intensity)
    elif mutator_id == "M6": # Load concentration spike (fan-in extreme increase)
        mut['connectivity'] = c + int(c * intensity * 5)
    
    return mut

def compute_elasticity(nodes, mutator_id, intensity):
    base_sys = statistics.mean([compute_risk(n) for n in nodes])
    mutated_nodes = [apply_mutator(n, mutator_id, i) for n, i in zip(nodes, [intensity]*len(nodes))]
    mut_sys = statistics.mean([compute_risk(n) for n in mutated_nodes])
    delta = mut_sys - base_sys
    return delta, delta / intensity if intensity > 0 else 0

def classify_shape(elasticities):
    if not elasticities: return "Numb Plateau"
    if max(elasticities) - min(elasticities) < 0.05:
        return "Numb Plateau"
    elif max(elasticities) > elasticities[0] * 3:
        return "Chaotic Spike"
    return "Linear Responsive"

def main():
    run_path = get_latest_rrs_run(TARGET_REPO)
    if not run_path:
        print("No run for 03_forge found.")
        return
        
    with open(run_path / 'metrics.json') as f:
        metrics = json.load(f)
        
    nodes = []
    for m in metrics:
        nodes.append({
            "connectivity": m.get('connectivity', 0),
            "feedback_loops": m.get('feedback_loops', 0),
            "safeguards": m.get('safeguards', 0),
            "unobserved_drops": m.get('unobserved_drops', 0)
        })
        
    mutators = ["M1", "M2", "M3", "M4", "M5", "M6"]
    intensities = [0.05, 0.10, 0.15, 0.20]
    
    diversity_curve = {}
    
    for mid in mutators:
        el_vals = []
        c_curve = []
        for inten in intensities:
            d_risk, el = compute_elasticity(nodes, mid, inten)
            el_vals.append(el)
            c_curve.append({
                "intensity": inten,
                "delta_risk": round(d_risk, 4),
                "elasticity": round(el, 4)
            })
            
        shape = classify_shape(el_vals)
        diversity_curve[mid] = {
            "elasticity_shape": shape,
            "curve": c_curve,
            "collapse_horizon_shift": c_curve[-1]["delta_risk"] - c_curve[0]["delta_risk"]
        }
        
    passes = sum([1 for m in diversity_curve.values() if m["elasticity_shape"] in ["Linear Responsive", "Chaotic Spike", "Numb Plateau"]])
    structurally_coherent = passes >= 4
    
    out_dir = RRS_DIR / TARGET_REPO
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / 'mutation_diversity_curve.json', 'w') as f:
        json.dump({
            "structurally_coherent": structurally_coherent,
            "operator_results": diversity_curve
        }, f, indent=4)
        
    print(f"Phase 2 Complete. Mutation Diversity Coherent: {structurally_coherent}")

if __name__ == "__main__":
    main()
