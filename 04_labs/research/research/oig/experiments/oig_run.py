import json
import random
import math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
ARTIFACTS_DIR = ROOT / '07_artifacts' / 'oig'

def generate_oig_graph(n=40):
    g = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i+1, n):
            if random.random() < 0.15:
                g[i].add(j)
                g[j].add(i)
    return g

def simulate_cascade(graph, lag_steps, intervention_time):
    caps = {k: len(v)*1.5+2 for k, v in graph.items()}
    loads = {k: len(v)*1.0+1 for k, v in graph.items()}
    loads[0] += 20.0 # injection
    
    failed = set()
    steps = 0
    changed = True
    delay = lag_steps
    while changed and steps < 50:
        changed = False
        new_fails = [k for k in graph if k not in failed and loads[k] > caps[k]]
        
        # apply intervention if we hit intervention time
        if steps == intervention_time + delay:
            # intervention halves all loads
            for k in loads: loads[k] *= 0.5
            
        for nf in new_fails:
            failed.add(nf)
            changed = True
            for n in graph[nf]:
                if n not in failed:
                    loads[n] += (loads[nf] / max(1, len(graph[nf])))
        steps += 1
    return len(failed) / len(graph)

def detection_lag_effects(g):
    lags = [0, 1, 2, 4, 8]
    res = {}
    for l in lags:
        res[f"lag_{l}_steps"] = simulate_cascade(g, lag_steps=l, intervention_time=2)
    return res

def intervention_window(g):
    windows = [1, 2, 3, 5, 10]
    res = {}
    for w in windows:
        col_vol = simulate_cascade(g, lag_steps=0, intervention_time=w)
        res[f"window_{w}_steps"] = col_vol
        if col_vol > 0.5:
            res["critical_threshold_failed_at"] = w
            break
    if "critical_threshold_failed_at" not in res:
        res["critical_threshold_failed_at"] = "no_failure"
    return res

def observability_sweep(g):
    blindspot_mass = [0.0, 0.1, 0.2, 0.4, 0.8]
    res = {}
    for b in blindspot_mass:
        # higher blindspot = higher lag
        effective_lag = int(b * 10)
        col = simulate_cascade(g, lag_steps=effective_lag, intervention_time=1)
        res[f"blind_mass_{b}"] = col
    return res

def main():
    print("Running OIG Protocol...")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    g = generate_oig_graph()
    
    d_lags = detection_lag_effects(g)
    with open(ARTIFACTS_DIR / 'detection_lag_effects.json', 'w') as f:
        json.dump(d_lags, f, indent=4)
        
    w_map = intervention_window(g)
    with open(ARTIFACTS_DIR / 'intervention_window_map.json', 'w') as f:
        json.dump(w_map, f, indent=4)
        
    o_sweep = observability_sweep(g)
    with open(ARTIFACTS_DIR / 'observability_sensitivity.json', 'w') as f:
        json.dump(o_sweep, f, indent=4)
        
    crit = w_map.get("critical_threshold_failed_at", "no_failure")
    with open(ARTIFACTS_DIR / 'oig_verdict.json', 'w') as f:
        json.dump({
            "critical_intervention_window": crit,
            "verdict": "OIG_LATE_INTERVENTION_FAILS" if crit != "no_failure" else "OIG_INCONCLUSIVE"
        }, f, indent=4)
        
    print("OIG Protocol Complete.")

if __name__ == "__main__":
    main()
