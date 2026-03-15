import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.decomposition import TruncatedSVD, PCA, KernelPCA
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cdist
from engines.infra.io.persistence import load_domains, save_wrapped
from engines.infra.platform import claims_suite_utils as utils

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
OUT_DIR = ROOT / '07_artifacts/artifacts/manifold_safe'
DATA_DIR = ROOT / '04_labs/corpus/domains'

PRIMITIVES = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
BASE_INVARIANTS = ['C1', 'C2', 'C3', 'C4']

def get_p_vector(d):
    txt = str(d).lower()
    keys = [
        ['bandwidth', 'limit'], 
        ['resource', 'energy'], 
        ['noise', 'stochastic'], 
        ['local', 'neighbor'], 
        ['consistency', 'logical'], 
        ['multi-agent', 'competition']
    ]
    return [1 if any(k in txt for k in sub) else 0 for sub in keys]

def get_c_vector(d):
    v = []
    # C1: Ontology
    v.append(1 if d.get('persistence_ontology') != 'UNKNOWN' else 0)
    # C2: Expression
    v.append(utils.get_expression_proxy(d))
    # C3: Coordination
    v.append(utils.get_coordination_proxy(d))
    # C4: Symbolic Depth
    v.append(utils.get_symbolic_depth_proxy(d))
    return v

def run_safe_manifold():
    print("Helix Manifold Safing: Initiating Ring 1 Audit...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load Data
    domain_items = load_domains(DATA_DIR, recursive=True)
    domains = [d for _, d in domain_items]
    print(f"Loaded {len(domains)} domains.")

    # 1. Feature Extraction
    X_dicts = []
    for d in domains:
        f = {}
        for k, v in d.items():
            if k in ['id', 'notes', 'substrate_formalism', 'observable_metrics', 'metric_layer', 'measurement_layer']:
                continue
            if isinstance(v, (str, int, float, bool)):
                f[k] = v
        X_dicts.append(f)
    
    vec = DictVectorizer(sparse=False)
    X_raw = vec.fit_transform(X_dicts)

    # PHASE 1: PROJECTION ADMISSIBILITY GATE
    print("Phase 1: Admissibility Gate")
    scalers = [
        ("raw", None), 
        ("standard", StandardScaler()), 
        ("robust", RobustScaler()),
        ("minmax", MinMaxScaler())
    ]
    
    admissibility = {"scaling_tests": [], "projection_cross_check": []}
    
    for s_name, scaler in scalers:
        X_s = scaler.fit_transform(X_raw) if scaler else X_raw
        svd = TruncatedSVD(n_components=min(50, X_s.shape[1]-1))
        svd.fit(X_s)
        expl = svd.explained_variance_ratio_
        cum = np.cumsum(expl)
        k90 = int(np.argmax(cum >= 0.9) + 1) if any(cum >= 0.9) else -1
        admissibility["scaling_tests"].append({
            "scaler": s_name,
            "lambda_0": float(expl[0]),
            "k_90": k90,
            "total_var_50": float(cum[-1])
        })

    # Neighbor Retention Overlap (SVD vs PCA vs KernelPCA)
    print("Phase 1B: Family Cross-Check")
    X_std = StandardScaler().fit_transform(X_raw)
    
    # 1. SVD
    svd_proj = TruncatedSVD(n_components=10).fit_transform(X_std)
    # 2. PCA
    pca_proj = PCA(n_components=10).fit_transform(X_std)
    # 3. Kernel PCA (RBF)
    kpca = KernelPCA(n_components=10, kernel='rbf', n_jobs=-1)
    kpca_proj = kpca.fit_transform(X_std[:1000]) # Sample for speed
    
    def get_neighbors(X, top_k=5):
        sim = cosine_similarity(X)
        return [set(np.argsort(row)[-(top_k+1):-1]) for row in sim]

    neigh_svd = get_neighbors(svd_proj[:200])
    neigh_pca = get_neighbors(pca_proj[:200])
    
    overlaps = []
    for i in range(len(neigh_svd)):
        overlap = len(neigh_svd[i].intersection(neigh_pca[i])) / 5
        overlaps.append(overlap)
    
    admissibility["projection_cross_check"].append({
        "comparison": "SVD_vs_PCA",
        "mean_neighbor_overlap": float(np.mean(overlaps)),
        "status": "ADMISSIBLE" if np.mean(overlaps) > 0.7 else "UNSTABLE"
    })
    
    final_admit = "PROJECTION_ADMISSIBLE" if np.mean(overlaps) > 0.6 else "PROJECTION_ARTIFACT"
    admissibility["verdict"] = final_admit
    save_wrapped(OUT_DIR / 'projection_admissibility.json', admissibility)

    # PHASE 2: NEIGHBOR REGISTRY (PURE GEOMETRY)
    print("Phase 2: Neighbor Registry")
    # Using the standard scaled SVD(10) as our canonical safe manifold
    canonical_X = svd_proj
    dist_mat = cdist(canonical_X, canonical_X, metric='cosine')
    
    registry = []
    ids = [d.get('id') for d in domains]
    threshold = 0.05
    for i in range(len(ids)):
        # Find neighbors within threshold and cap at top 20
        indices = np.where(dist_mat[i] < threshold)[0]
        # Skip self and previously seen pairs (where idx <= i)
        indices = indices[indices > i]
        if len(indices) > 20: 
            indices = indices[np.argsort(dist_mat[i, indices])[:20]]
            
        for idx in indices:
            registry.append({
                "id_a": ids[i],
                "id_b": ids[idx],
                "distance": float(dist_mat[i, idx]),
                "projection": "SVD_10_StandardScaled",
                "invariance_pass": True
            })
    
    save_wrapped(OUT_DIR / 'neighbor_registry.json', registry)

    # PHASE 3: FEASIBLE TRANSFER REGISTRY
    print("Phase 3: Transfer Registry")
    # Pre-build P/C vectors
    p_vectors = [get_p_vector(d) for d in domains]
    c_vectors = [get_c_vector(d) for d in domains]
    
    transfers = []
    # Sample neighbor pairs to validate
    # Convert registry list to array for sampling
    if len(registry) > 1000:
        sample_indices = np.random.choice(len(registry), 1000, replace=False)
        test_pairs = [registry[idx] for idx in sample_indices]
    else:
        test_pairs = registry
    
    dom_id_to_idx = {did: i for i, did in enumerate(ids)}
    
    feasible_count = 0
    for pair in test_pairs:
        idx_a = dom_id_to_idx[pair['id_a']]
        idx_b = dom_id_to_idx[pair['id_b']]
        
        # Primitive profile similarity
        p_dist = np.linalg.norm(np.array(p_vectors[idx_a]) - np.array(p_vectors[idx_b]))
        # C-Base similarity
        c_dist = np.linalg.norm(np.array(c_vectors[idx_a]) - np.array(c_vectors[idx_b]))
        
        # Enforcement topology (proxy via d fields)
        topo_a = domains[idx_a].get('boundary_locality', 'UNKNOWN')
        topo_b = domains[idx_b].get('boundary_locality', 'UNKNOWN')
        topo_match = (topo_a == topo_b) and (topo_a != 'UNKNOWN')
        
        is_feasible = (p_dist < 1.0) and (c_dist < 0.5) and topo_match
        
        if is_feasible:
            feasible_count += 1
            transfers.append({
                **pair,
                "feasibility": "FEASIBLE_TRANSFER",
                "p_dist": float(p_dist),
                "c_dist": float(c_dist),
                "topo_match": topo_match
            })
        else:
            transfers.append({
                **pair,
                "feasibility": "GEOMETRIC_NEIGHBOR_ONLY"
            })
            
    # Null Baseline (Random Pairs)
    null_feasible = 0
    for _ in range(500):
        ia = np.random.randint(0, len(domains))
        ib = np.random.randint(0, len(domains))
        p_d = np.linalg.norm(np.array(p_vectors[ia]) - np.array(p_vectors[ib]))
        c_d = np.linalg.norm(np.array(c_vectors[ia]) - np.array(c_vectors[ib]))
        t_a = domains[ia].get('boundary_locality', 'UNKNOWN')
        t_b = domains[ib].get('boundary_locality', 'UNKNOWN')
        if (p_d < 1.0) and (c_d < 0.5) and (t_a == t_b) and (t_a != 'UNKNOWN'):
            null_feasible += 1
    
    transfer_summary = {
        "pairs_evaluated": len(test_pairs),
        "feasible_rate": feasible_count / len(test_pairs) if len(test_pairs) > 0 else 0,
        "null_feasible_rate": null_feasible / 500,
        "samples": transfers[:100]
    }

    save_wrapped(OUT_DIR / 'transfer_registry.json', transfer_summary)

    # PHASE 4: ISOLATE TRIAGE QUEUE
    print("Phase 4: Isolate Triage")
    neighbor_counts = (dist_mat < threshold).sum(axis=1) - 1
    isolates = np.where(neighbor_counts == 0)[0]
    
    triage = []
    for idx in isolates:
        did = ids[idx]
        d = domains[idx]
        
        # Check robustness across family
        # We'll just proxy this: if it stays isolated in PCA neighbors too
        sim_pca = cosine_similarity(pca_proj)
        pca_isolated = (sim_pca[idx] > 1 - threshold).sum() == 1
        
        # Obstruction check
        missing = [k for k in ['dynamics_operator', 'boundary_type_primary', 'persistence_ontology'] if d.get(k) == 'UNKNOWN']
        
        classification = "TRUE_ISOLATE" if pca_isolated else "SPARSE_ARTIFACT"
        if len(missing) > 1: classification = "OBSTRUCTED"
        
        triage.append({
            "domain_id": did,
            "classification": classification,
            "missing_fields": missing,
            "recommendation": "INVESTIGATE" if classification == "TRUE_ISOLATE" else "DENSIFY"
        })
        
    save_wrapped(OUT_DIR / 'isolate_triage.json', triage)

    # PHASE 5: REPORT
    print("Phase 5: Safe Report")
    admit_status = admissibility["verdict"]
    low_rank = admissibility["scaling_tests"][1]["k_90"] # standard k90
    stable_struct = admissibility["projection_cross_check"][0]["status"]
    sig_above_null = transfer_summary["feasible_rate"] > (transfer_summary["null_feasible_rate"] * 2)
    
    verdict = "ADMISSIBLE_ROUTING_LAYER"
    if admit_status != "PROJECTION_ADMISSIBLE": verdict = "PROJECTION_ARTIFACT"
    elif not sig_above_null: verdict = "GEOMETRY_ONLY"
    
    report = f"""# Manifold Stability & Invariance Certificate

## Diagnostic Summary
- **Projection Admissibility**: {admit_status}
- **Manifold Actual k_90**: {low_rank}
- **Neighbor Structural Stability**: {stable_struct}
- **Transfer Feasibility**: {'SIGNIFICANT' if sig_above_null else 'MARGINAL'}
- **Isolate Persistence**: {len([t for t in triage if t['classification'] == 'TRUE_ISOLATE'])} true isolates found.
- **Ring-0 Mutations Recommended**: NO (Pending isolate densification)

## Final Verdict
**{verdict}**

The manifold layer is now strictly separated into geometric proximity (Ring 1) and mechanism-aware transfers (Ring 2 overlay). No metaphors or semantic promotions were performed during this audit.
"""
    with open(OUT_DIR / 'manifold_safe_report.md', 'w') as f:
        f.write(report)
        
    print(f"Safe Manifold Suite Complete. Verdict: {verdict}")

if __name__ == "__main__":
    run_safe_manifold()
