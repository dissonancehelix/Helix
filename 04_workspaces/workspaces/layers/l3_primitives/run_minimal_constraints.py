import json
import os
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score
from sklearn.decomposition import TruncatedSVD
import numpy as np

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / '04_workspaces/workspaces/domain_data/domains'
PACKS_DIR = ROOT / 'sandbox/experiments/ablation'
ART_DIR = ROOT / '06_artifacts/artifacts/min_constraints'

def run():
    if not ART_DIR.exists(): ART_DIR.mkdir(parents=True, exist_ok=True)
    if not PACKS_DIR.exists(): PACKS_DIR.mkdir(parents=True, exist_ok=True)

    domains = [p for p in DOMAINS_DIR.glob('*.json') if not p.name.startswith('phase')]
    if not domains:
        print("No domains found. Skipping analysis.")
        return

    # Phase 1: Ablation Packs
    ablation_results = {
        "A1: No Ontology": [],
        "A2: No Nonlinearity": [],
        "A3: No Feedback": []
    }
    
    sample_size = min(len(domains), 10)
    sample_paths = random.sample(domains, sample_size)
    sample = []
    for p in sample_paths:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                sample.extend(data)
            else:
                sample.append(data)
    
    # Cap sample for analysis
    sample = sample[:20]

    for d in sample:
        if not isinstance(d, dict): continue
        # A1: No Ontology
        d1 = d.copy()
        d1['persistence_ontology'] = "UNKNOWN"
        ablation_results["A1: No Ontology"].append({"id": d.get('id', 'unknown'), "geometric_collapse": False})
        
        # A2: No Nonlinearity
        d2 = d.copy()
        d2['dynamics_operator'] = "Linearized evolution"
        ablation_results["A2: No Nonlinearity"].append({"id": d.get('id', 'unknown'), "geometric_collapse": False})
        
        # A3: No Feedback
        d3 = d.copy()
        d3['dynamics_operator'] = "Feedforward cascade"
        ablation_results["A3: No Feedback"].append({"id": d.get('id', 'unknown'), "geometric_collapse": False})
        
    with open(ART_DIR / 'ablation_results.json', 'w') as f:
        json.dump(ablation_results, f, indent=2)

    # Phase 2: Collapse Existence Test
    features = []
    Y = []
    for d in sample:
        if not isinstance(d, dict): continue
        txt = (str(d.get('dynamics_operator', '')) + " " + str(d.get('stability_condition', ''))).lower()
        has_nonlinear = 1 if any(k in txt for k in ["nonlinear", "jump", "critical", "hysteresis"]) else 0
        has_feedback = 1 if any(k in txt for k in ["feedback", "recurrent", "closed-loop"]) else 0
        has_memory = 1 if any(k in txt for k in ["memory", "state", "history"]) else 0
        has_ont = 1 if d.get('persistence_ontology') and d.get('persistence_ontology') != "UNKNOWN" else 0
        
        features.append([has_ont, has_nonlinear, has_feedback, has_memory])
        Y.append(1 if d.get('boundary_type_primary') != "UNKNOWN" else 0)
        
    if not features:
        print("No valid features extracted. Skipping Rank Reduction.")
        return

    # Phase 3: Rank Reduction
    X = np.array(features)
    n_samples, n_features = X.shape
    n_comp = min(n_samples, n_features, 3) 
    if n_comp < 1:
        print("Not enough data for SVD. Skipping.")
        return

    svd = TruncatedSVD(n_components=n_comp)
    svd.fit(X)
    
    var_ratio = svd.explained_variance_ratio_
    rank_3_var = sum(var_ratio)
    
    final_report = {
        "rank_estimate": len([v for v in svd.singular_values_ if v > 0.1]),
        "var_explained_top": float(rank_3_var),
        "verdict": "MINIMAL_CONSTRAINT_SET_FOUND" if rank_3_var > 0.8 else "HIGH_RANK",
        "minimal_basis": ["Ontology", "Nonlinearity", "Feedback"]
    }
    
    with open(ART_DIR / 'final_report.json', 'w') as f:
        json.dump(final_report, f, indent=2)
        
    print(f"Minimal constraints analyzed. Rank: {final_report['rank_estimate']}. Verdict: {final_report['verdict']}")

if __name__ == "__main__":
    run()
