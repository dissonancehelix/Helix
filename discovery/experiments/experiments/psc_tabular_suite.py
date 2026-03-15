import os
import json
import numpy as np
import pandas as pd
import hashlib
from datetime import datetime
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.datasets import load_iris, load_wine

# --- CONFIGURATION (DETERMINISTIC) ---
SEED = 42
np.random.seed(SEED)
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
ARTIFACT_DIR = ROOT / '07_artifacts/artifacts' / 'psc_tabular'
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# --- PSC UTILS ---
def compute_subspace_stability(X1, X2, k=3):
    """
    Subspace stability: principal angles/cosine alignment between PCA components.
    """
    pca1 = PCA(n_components=k, random_state=SEED).fit(X1)
    pca2 = PCA(n_components=k, random_state=SEED).fit(X2)
    
    V1 = pca1.components_.T
    V2 = pca2.components_.T
    
    # Calculate subspace overlap via singular values of V1' @ V2
    M = V1.T @ V2
    _, S, _ = np.linalg.svd(M)
    return float(np.mean(S))

def run_tabular_psc():
    script_name = "psc_tabular_suite.py"
    
    datasets = {
        "iris": load_iris(return_X_y=True)[0],
        "wine": load_wine(return_X_y=True)[0]
    }
    
    all_results = {}
    obstructions = []
    
    for ds_name, X_raw in datasets.items():
        # Baseline: PCA on Raw
        pca_base = PCA(n_components=2, random_state=SEED).fit(X_raw)
        base_top_dominance = float(pca_base.explained_variance_ratio_[0])
        
        transforms = {
            "T_standard": lambda X: StandardScaler().fit_transform(X),
            "T_minmax": lambda X: MinMaxScaler().fit_transform(X),
            "T_robust": lambda X: RobustScaler().fit_transform(X),
            "T_noise": lambda X: X + np.random.normal(0, 0.01 * np.std(X, axis=0), X.shape)
        }
        
        ds_pss_records = []
        ds_results = {}
        
        for t_name, t_func in transforms.items():
            try:
                X_trans = t_func(X_raw)
                
                # Subspace Stability (Overlap)
                sub_stability = compute_subspace_stability(X_raw, X_trans, k=2)
                
                # Dominance Drift
                pca_trans = PCA(n_components=2, random_state=SEED).fit(X_trans)
                trans_top_dominance = float(pca_trans.explained_variance_ratio_[0])
                dom_drift = abs(base_top_dominance - trans_top_dominance)
                
                # PSS
                pss = sub_stability * (1.0 - dom_drift)
                ds_results[t_name] = {
                    "sub_stability": sub_stability,
                    "dominance_drift": dom_drift,
                    "pss": pss
                }
                ds_pss_records.append(pss)
                
            except Exception as e:
                obstructions.append(f"{ds_name}:{t_name} failure: {str(e)}")
        
        mean_pss = float(np.mean(ds_pss_records))
        verdict = "STABLE" if mean_pss >= 0.85 else "UNSTABLE" if mean_pss < 0.60 else "INDETERMINATE"
        
        all_results[ds_name] = {
            "verdict": verdict,
            "mean_pss": mean_pss,
            "base_top_dominance": base_top_dominance,
            "transform_results": ds_results
        }

    # --- ARTIFACTS ---
    
    # A) run_manifest.json
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seed": SEED,
        "environment": {
            "sklearn_version": "1.0+",
            "numpy": np.__version__
        },
        "datasets": list(datasets.keys())
    }
    with open(ARTIFACT_DIR / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)
        
    # B) results.json
    with open(ARTIFACT_DIR / "results.json", "w") as f:
        json.dump(all_results, f, indent=4)
        
    # C) report.md
    report = f"""# PSC Tabular Discovery Report

## Objective
Evaluate whether PCA "dominance claims" in standard tabular datasets are intrinsic structural properties or scaling artifacts.

"""
    for ds_name, res in all_results.items():
        report += f"### Dataset: {ds_name}\n"
        report += f"- **Verdict**: {res['verdict']}\n"
        report += f"- **Mean PSS**: {res['mean_pss']:.4f}\n\n"
        report += "| Transform | SubspaceStability | DominanceDrift | PSS |\n"
        report += "|-----------|-------------------|----------------|-----|\n"
        for t_name, t_res in res['transform_results'].items():
            report += f"| {t_name} | {t_res['sub_stability']:.4f} | {t_res['dominance_drift']:.4f} | {t_res['pss']:.4f} |\n"
        report += "\n"
        
    with open(ARTIFACT_DIR / "report.md", "w") as f:
        f.write(report)
        
    # D) trace_index.json
    trace = [
        {"claim": "Tabular Stability Comparison", "source": f"{script_name}:run_tabular_psc", "lines": "50-100", "excerpt_hash": hashlib.sha256(report.encode()).hexdigest()}
    ]
    with open(ARTIFACT_DIR / "trace_index.json", "w") as f:
        json.dump(trace, f, indent=4)
        
    # E) obstruction_log.json
    with open(ARTIFACT_DIR / "obstruction_log.json", "w") as f:
        json.dump(obstructions, f, indent=4)
        
    print(f"Tabular PSC Suite complete.")

if __name__ == "__main__":
    run_tabular_psc()
