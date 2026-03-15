from collections import defaultdict

import json
import os
import random
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
ART_DIR = ROOT / '07_artifacts/artifacts'
DATA_DIR = ROOT / 'data' / 'domains'

try:
    import numpy as np
    from sklearn.metrics import mutual_info_score
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

def save_wrapped(path, data):
    from engines.infra.io import persistence as m_io; from engines.infra.platform import environment as m_env
    m_io.save_wrapped(path, data)

def compute_ig(x_labels, y_labels):
    if not NUMPY_AVAILABLE or len(x_labels) == 0: return 0.0
    return mutual_info_score(x_labels, y_labels)

def load_domains():
    domains = []
    for p in sorted(DATA_DIR.glob('*.json')):
        with open(p, 'r', encoding='utf-8') as f:
            domains.append((p.name, json.load(f)))
    return domains

def run_memory_suites():
    if not NUMPY_AVAILABLE: return
    domains = load_domains()

    report = {
        "suite_1_purity": {},
        "suite_2_temporal_commitment": {},
        "suite_3_tsm_clustering": {},
        "suite_4_reversibility_gradient": {},
        "suite_5_orthogonality": {}
    }

    # ==========================================
    # SUITE 1 - Memory Purity Test
    # ==========================================
    mem_1 = []
    Y_b, Y_l, Y_obs, Y_ont, Y_sub = [], [], [], [], []
    
    for _, d in domains:
        flat_d = json.dumps(d).lower()
        has_memory = 1 if "memory" in flat_d else 0
        mem_1.append(has_memory)
        
        Y_b.append(str(d.get('boundary_type_primary', 'UNKNOWN')))
        Y_l.append(str(d.get('T1', 'UNKNOWN')))
        Y_obs.append(str(d.get('measurement_layer', {}).get('obstruction_type', 'UNKNOWN')))
        Y_ont.append(str(d.get('persistence_ontology', 'UNKNOWN')))
        Y_sub.append(str(d.get('substrate_S1c_refined', d.get('substrate_S1c', 'UNKNOWN'))))
        
    ig_b = compute_ig(mem_1, Y_b)
    
    null_igs = []
    mem_shuff = list(mem_1)
    for _ in range(20):
        random.shuffle(mem_shuff)
        null_igs.append(compute_ig(mem_shuff, Y_b))
        
    n_mean = float(np.mean(null_igs))
    n_std = float(np.std(null_igs))
    
    report["suite_1_purity"] = {
        "ig_boundary": round(ig_b, 4),
        "ig_locality": round(compute_ig(mem_1, Y_l), 4),
        "ig_obstruction": round(compute_ig(mem_1, Y_obs), 4),
        "ig_ontology": round(compute_ig(mem_1, Y_ont), 4),
        "ig_substrate": round(compute_ig(mem_1, Y_sub), 4),
        "null_mean": round(n_mean, 4),
        "null_std": round(n_std, 4),
        "decision": "SIGNAL_PERSISTS" if ig_b > n_mean + 3*n_std else "SIGNAL_COLLAPSES"
    }

    # ==========================================
    # SUITE 2 - Temporal Commitment Test
    # ==========================================
    temporal_mem = []
    mem_b_counts = defaultdict(int)
    total_mem = 0
    
    for _, d in domains:
        flat_txt = json.dumps(d).lower()
        fm = d.get('failure_mode', '').lower()
        sc = d.get('stability_condition', '').lower()
        
        is_mem = False
        if any(w in fm or w in sc or w in flat_txt for w in ['absorbing', 'accumulat', 'non-invert', 'hysteresis', 'histor']):
            is_mem = True
            
        temporal_mem.append(1 if is_mem else 0)
        
        if is_mem:
            total_mem += 1
            mem_b_counts[str(d.get('boundary_type_primary', 'UNKNOWN'))] += 1
            
    p_given_mem = {k: round(v / total_mem, 4) if total_mem > 0 else 0 for k, v in mem_b_counts.items()}
    
    report["suite_2_temporal_commitment"] = {
        "memory_positive_count": total_mem,
        "P_BoundaryType_given_memory": p_given_mem,
        "bias_detected": bool(len([v for v in p_given_mem.values() if v > 0.3]) > 0)
    }

    # ==========================================
    # SUITE 3 - TSM (Trajectory Stabilization Mechanism)
    # ==========================================
    tsm_domains = []
    tsm_substrates = defaultdict(int)
    
    for i, (_, d) in enumerate(domains):
        if mem_1[i] == 1:
            b_type = str(d.get('boundary_type_primary', 'UNKNOWN'))
            obs = str(d.get('measurement_layer', {}).get('obstruction_type', 'UNKNOWN'))
            
            if "EXTERNAL" not in b_type and obs != "SCHEMA_INSUFFICIENT":
                sub = str(d.get('substrate_S1c_refined', d.get('substrate_S1c', 'UNKNOWN')))
                tsm_domains.append(d.get('id', 'unknown'))
                tsm_substrates[sub] += 1
                
    clusters = {k: v for k, v in tsm_substrates.items() if v > 1}
    
    report["suite_3_tsm_clustering"] = {
        "tsm_count": len(tsm_domains),
        "clusters": clusters,
        "structure_classification": "STRUCTURAL_PHENOMENON" if len(clusters) > 0 and len(tsm_domains) > 0 else "GENERIC_PROPERTY"
    }

    # ==========================================
    # SUITE 4 - Reversibility Gradient Test
    # ==========================================
    depth_scores = []
    
    for _, d in domains:
        flat_txt = json.dumps(d).lower()
        score = 0
        if any(w in flat_txt for w in ['global histor', 'long-term depend', 'irreversible accumulation']):
            score = 3
        elif any(w in flat_txt for w in ['multi-step', 'cascade', 'accumulat']):
            score = 2
        elif any(w in flat_txt for w in ['local memory', 'hysteresis', 'plasticity', 'memory']):
            score = 1
            
        depth_scores.append(score)
        
    depth_global = []
    depth_comb = []
    depth_dist = []
    
    for i, b in enumerate(Y_b):
        if "GLOBAL" in b or "MACRO" in b: depth_global.append(depth_scores[i])
        if "COMBINATORIAL" in b: depth_comb.append(depth_scores[i])
        if "DISTRIBUTIONAL" in b: depth_dist.append(depth_scores[i])
        
    report["suite_4_reversibility_gradient"] = {
        "avg_depth_global_collapse": round(float(np.mean(depth_global)) if depth_global else 0, 4),
        "avg_depth_combinatorial_collapse": round(float(np.mean(depth_comb)) if depth_comb else 0, 4),
        "avg_depth_distributional_collapse": round(float(np.mean(depth_dist)) if depth_dist else 0, 4),
        "correlation_detected": True if (depth_global and np.mean(depth_global) > 0.5) else False
    }

    # ==========================================
    # SUITE 5 - Kernel Orthogonality Matrix
    # ==========================================
    # Joint representation over 2 Kernel-1 axes. Can memory be reconstructed?
    # H(X) = IG(X, X)
    h_mem = compute_ig(mem_1, mem_1)
    
    # Simple check: Does any pair (Sub, Ont) determine Mem?
    # We join strings to create a combined variable
    sub_ont = [f"{s}_{o}" for s, o in zip(Y_sub, Y_ont)]
    ig_mem_sub_ont = compute_ig(mem_1, sub_ont)
    
    ratio = ig_mem_sub_ont / h_mem if h_mem > 0 else 0
    
    report["suite_5_orthogonality"] = {
        "H_memory": round(h_mem, 4),
        "IG_memory_given_sub_ont": round(ig_mem_sub_ont, 4),
        "reconstruction_ratio": round(ratio, 4),
        "orthogonality": "DERIVATIVE" if ratio > 0.8 else "INDEPENDENT"
    }

    save_wrapped(ART_DIR / 'memory/memory_suites_report.json', report)
    return report

if __name__ == "__main__":
    run_memory_suites()
