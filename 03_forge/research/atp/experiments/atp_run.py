import json
import random
import time
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / '06_artifacts' / 'atp'

def generate_graph(n=40):
    g = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i+1, n):
            if random.random() < 0.15:
                g[i].add(j)
                g[j].add(i)
    return g

def controlled_fragmentation(graph):
    total_edges = sum(len(v) for v in graph.values()) // 2
    removals = [0.05, 0.10, 0.20, 0.30]
    results = []
    
    for pct in removals:
        g = {k: set(v) for k, v in graph.items()}
        target_remove = int(total_edges * pct)
        
        edges = []
        for u in g:
            for v in g[u]:
                if u < v: edges.append((u, v))
        random.shuffle(edges)
        
        for u, v in edges[:target_remove]:
            g[u].remove(v)
            g[v].remove(u)
            
        # Constrained rewiring
        recovery_latency = 0
        current_edges = sum(len(v) for v in g.values()) // 2
        
        while current_edges < total_edges * (1.0 - pct*0.5) and recovery_latency < 50:
            u, v = random.sample(list(g.keys()), 2)
            if u != v and v not in g[u]:
                g[u].add(v)
                g[v].add(u)
                current_edges += 1
            recovery_latency += 1
            
        continuity = current_edges / float(max(1, total_edges))
        results.append({
            "removal_pct": pct,
            "recovery_latency_steps": recovery_latency,
            "structural_continuity_retention": continuity
        })
    return results

def redundancy_injection(graph):
    g = {k: set(v) for k, v in graph.items()}
    caps = {k: len(v)*1.5+2 for k, v in g.items()}
    loads = {k: len(v)*1.0+1 for k, v in g.items()}
    
    # baseline collapse threshold
    def test_collapse(gr, ext_load):
        ld = {k: v for k, v in loads.items()}
        ld[0] += ext_load
        failed = set()
        changed = True
        while changed:
            changed = False
            for k in gr:
                if k not in failed and ld[k] > caps[k]:
                    failed.add(k)
                    changed = True
                    for n in gr[k]:
                        if n not in failed:
                            ld[n] += (ld[k] / max(1, len(gr[k])))
        return len(failed) / len(gr)
        
    baseline_threshold = 0
    for l in range(10, 100, 5):
        if test_collapse(g, l) > 0.5:
            baseline_threshold = l
            break
            
    # inject redundancy
    paths_added = 0
    while paths_added < 20:
        u, v = random.sample(list(g.keys()), 2)
        if u != v and v not in g[u]:
            g[u].add(v)
            g[v].add(u)
            paths_added += 1
            
    redundant_threshold = 0
    for l in range(10, 100, 5):
        if test_collapse(g, l) > 0.5:
            redundant_threshold = l
            break
            
    return baseline_threshold, redundant_threshold

def recovery_half_life(graph):
    total_edges = sum(len(v) for v in graph.values()) // 2
    g = {k: set(v) for k, v in graph.items()}
    
    # Major perturbation (remove 60% edges)
    edges = []
    for u in g:
        for v in g[u]:
            if u < v: edges.append((u, v))
                
    random.shuffle(edges)
    removed = edges[:int(total_edges * 0.6)]
    for u, v in removed:
        g[u].remove(v)
        g[v].remove(u)
        
    steps = 0
    while sum(len(v) for v in g.values()) // 2 < total_edges * 0.8:
        u, v = random.sample(list(g.keys()), 2)
        if v not in g[u] and u != v:
            g[u].add(v)
            g[v].add(u)
        steps += 1
        if steps > 1000: break
    return steps

def main():
    print("Running ATP Protocol...")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    g = generate_graph()
    
    frag_results = controlled_fragmentation(g)
    with open(ARTIFACTS_DIR / 'reconfiguration_latency.json', 'w') as f:
        json.dump(frag_results, f, indent=4)
        
    bt, rt = redundancy_injection(g)
    with open(ARTIFACTS_DIR / 'adaptive_thresholds.json', 'w') as f:
        json.dump({
            "baseline_collapse_load": bt,
            "redundant_collapse_load": rt,
            "collapse_delay_uplift": rt - bt
        }, f, indent=4)
        
    hl = recovery_half_life(g)
    with open(ARTIFACTS_DIR / 'recovery_curves.json', 'w') as f:
        json.dump({
            "half_life_steps_to_80pct": hl
        }, f, indent=4)
        
    with open(ARTIFACTS_DIR / 'atp_verdict.json', 'w') as f:
        json.dump({
            "adaptive_capacity_established": rt > bt,
            "verdict": "ATP_ADAPTIVE_DYNAMICS_OBSERVED" if rt > bt else "ATP_FAILED"
        }, f, indent=4)
        
    print("ATP Protocol Complete.")

if __name__ == "__main__":
    main()
