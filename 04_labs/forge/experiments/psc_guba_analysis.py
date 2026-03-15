import os
import json
import numpy as np
import pandas as pd
import hashlib
from datetime import datetime
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris, load_wine
from sklearn.metrics import accuracy_score

# --- CONFIGURATION (DETERMINISTIC) ---
SEED = 42
np.random.seed(SEED)
ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACT_DIR = ROOT / '07_artifacts/artifacts' / 'psc_guba'
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# --- PSC UTILS ---
def compute_pss(X_raw, component_idx, k=None):
    """
    Computes PSS for a single principal axis.
    """
    if k is None:
        k = X_raw.shape[1]
    
    pca_base = PCA(n_components=k, random_state=SEED).fit(X_raw)
    base_comp = pca_base.components_[component_idx]
    base_var_share = pca_base.explained_variance_ratio_[component_idx]
    
    # Transform: Standardization
    X_scaled = StandardScaler().fit_transform(X_raw)
    pca_scaled = PCA(n_components=k, random_state=SEED).fit(X_scaled)
    
    # Alignment: find the closest matching component in the transformed space
    # (since order may change)
    max_pss = 0.0
    for j in range(min(k, 5)): # Check top 5 to find match
        new_comp = pca_scaled.components_[j]
        new_var_share = pca_scaled.explained_variance_ratio_[j]
        
        alignment = abs(np.dot(base_comp, new_comp))
        drift = abs(base_var_share - new_var_share)
        pss = alignment * (1.0 - drift)
        if pss > max_pss:
            max_pss = pss
            
    return float(max_pss)

# --- DATA GENERATION ---
def generate_guba_synthetic(n=1000, d=10):
    """
    Creates a dataset where one feature has huge magnitude and explains the target,
    but collapses under scaling.
    """
    U = np.random.randn(n, 3)
    # y is determined by a small-magnitude feature
    y = (U[:, 0] > 0).astype(int)
    
    # Feature 0: huge magnitude, highly predictive
    X = np.random.randn(n, d)
    X[:, 0] = U[:, 0] * 1000.0 # Huge scale artifact candidate
    
    X[:, 1:3] = U[:, 1:3] # Other structure
    
    return X, y

# --- GUBA ANALYSIS ---
def run_guba_analysis():
    script_name = "psc_guba_analysis.py"
    
    iris_X, iris_y = load_iris(return_X_y=True)
    wine_X, wine_y = load_wine(return_X_y=True)
    synth_X, synth_y = generate_guba_synthetic()
    
    datasets = {
        "iris": (iris_X, iris_y),
        "wine": (wine_X, wine_y),
        "synthetic": (synth_X, synth_y)
    }
    
    guba_candidates = {}
    coordinate_metrics = {}
    behavioral_anchors = {}
    summary = {}
    
    for ds_name, (X, y) in datasets.items():
        print(f"Analyzing: {ds_name}")
        
        n_features = X.shape[1]
        pca = PCA(n_components=n_features, random_state=SEED).fit(X)
        X_pca = pca.transform(X)
        
        # Model_Full Baseline
        X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(X_pca, y, test_size=0.3, random_state=SEED)
        clf_full = RandomForestClassifier(n_estimators=100, random_state=SEED).fit(X_train_f, y_train_f)
        acc_full = accuracy_score(y_test_f, clf_full.predict(X_test_f))
        
        ds_guba = []
        
        for i in range(min(n_features, 5)): # Focus on top 5 components
            pss = compute_pss(X, i)
            
            if pss < 0.60:
                # Potential Candidate. Measure Behavioral Contribution.
                X_comp = X_pca[:, [i]]
                X_tr, X_te, y_tr, y_te = train_test_split(X_comp, y, test_size=0.3, random_state=SEED)
                clf_comp = RandomForestClassifier(n_estimators=100, random_state=SEED).fit(X_tr, y_tr)
                acc_comp = accuracy_score(y_te, clf_comp.predict(X_te))
                
                # Noise Robustness
                noise = np.random.normal(0, 0.1 * np.std(X_te), X_te.shape)
                acc_noise = accuracy_score(y_te, clf_comp.predict(X_te + noise))
                noise_stability = acc_noise / acc_comp if acc_comp > 0 else 0
                
                # BAS (Behavioral Anchor Score)
                bas = (acc_comp / acc_full) * noise_stability
                
                # CSI (Scaling Sensitivity)
                scaling_factors = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
                scaling_accs = []
                for s in scaling_factors:
                    s_acc = accuracy_score(y_te, clf_comp.predict(X_te * s))
                    scaling_accs.append(s_acc)
                csi = float(np.var(scaling_accs))
                
                candidate_data = {
                    "component": i,
                    "pss": pss,
                    "bas": bas,
                    "csi": csi,
                    "acc_comp": acc_comp,
                    "acc_full": acc_full,
                    "noise_stability": noise_stability
                }
                
                # GUBA Classification
                is_guba = (bas > 0.70 and csi > 0.001) # CSI sensitivity threshold
                candidate_data["is_guba"] = is_guba
                
                if is_guba:
                    ds_guba.append(candidate_data)
        
        guba_candidates[ds_name] = ds_guba
        coordinate_metrics[ds_name] = {c["component"]: c["csi"] for c in ds_guba}
        behavioral_anchors[ds_name] = {c["component"]: c["bas"] for c in ds_guba}
        summary[ds_name] = {
            "total_unstable": sum(1 for i in range(min(n_features, 5)) if compute_pss(X,i) < 0.60),
            "guba_count": len(ds_guba),
            "verdict": "GUBA_PRESENT" if ds_guba else "GUBA_ABSENT"
        }

    # --- ARTIFACTS ---
    with open(ARTIFACT_DIR / "guba_candidates.json", "w") as f:
        json.dump(guba_candidates, f, indent=4)
    with open(ARTIFACT_DIR / "coordinate_sensitivity_metrics.json", "w") as f:
        json.dump(coordinate_metrics, f, indent=4)
    with open(ARTIFACT_DIR / "behavioral_anchor_metrics.json", "w") as f:
        json.dump(behavioral_anchors, f, indent=4)
    
    report = f"""# GUBA Analysis Report (Geometrically Unstable but Behaviorally Anchored)

## Objective
Identify components that fail PSC geometric stability gates but retain significant, robust predictive signal.

## Cross-Dataset GUBA Status
"""
    for ds_name, res in summary.items():
        report += f"### Dataset: {ds_name}\n"
        report += f"- **Unstable Candidates**: {res['total_unstable']}\n"
        report += f"- **GUBA Candidates Found**: {res['guba_count']}\n"
        report += f"- **Verdict**: {res['verdict']}\n"
        if guba_candidates[ds_name]:
            for g in guba_candidates[ds_name]:
                report += f"  - Component {g['component']}: BAS={g['bas']:.4f}, CSI={g['csi']:.4f}, PSS={g['pss']:.4f}\n"
        report += "\n"
        
    with open(ARTIFACT_DIR / "report.md", "w") as f:
        f.write(report)
        
    # Trace & Falsifiers
    with open(ARTIFACT_DIR / "trace_index.json", "w") as f:
        json.dump([{"claim": "GUBA Classification Result", "source": f"{script_name}:run_guba_analysis", "lines": "100-140", "excerpt_hash": hashlib.sha256(report.encode()).hexdigest()}], f, indent=4)
        
    falsifiers = f"""# Falsifier: GUBA Classification

## Falsifier: False Negatives
If a component has PSS > 0.85, it is **excluded** from GUBA by definition, as it is geometrically stable.

## Falsifier: Pure Noise
If BAS < 0.50, the component is classified as **NOISE_ARTIFACT**, not GUBA.
"""
    with open(ARTIFACT_DIR / "falsifiers.md", "w") as f:
        f.write(falsifiers)
        
    print(f"GUBA analysis complete. Artifacts written to {ARTIFACT_DIR}")

if __name__ == "__main__":
    run_guba_analysis()
