import os
import json
import numpy as np
import pandas as pd
import hashlib
import time
from datetime import datetime
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, make_classification
from sklearn.metrics import accuracy_score
from scipy.stats import ortho_group, spearmanr

# --- CONFIGURATION (DETERMINISTIC) ---
SEED = 42
np.random.seed(SEED)
ROOT = REPO_ROOT
ARTIFACT_DIR = ROOT / 'execution/artifacts' / 'psc_rbis'
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# --- PSC / BAS UTILS ---
def compute_pss_individual(X_raw, k=1):
    """
    Projection Stability Score for the top component.
    """
    pca_base = PCA(n_components=k, random_state=SEED).fit(X_raw)
    base_comp = pca_base.components_[0]
    base_var = pca_base.explained_variance_ratio_[0]

    # Hostility: Standard Scaling
    X_scaled = StandardScaler().fit_transform(X_raw)
    pca_scaled = PCA(n_components=k, random_state=SEED).fit(X_scaled)
    new_comp = pca_scaled.components_[0]
    new_var = pca_scaled.explained_variance_ratio_[0]

    alignment = abs(np.dot(base_comp, new_comp))
    drift = abs(base_var - new_var)
    return float(alignment * (1.0 - drift))

def compute_bas(clf, X_test, y_test, acc_full):
    """
    Behavioral Anchor Score: (acc_subset / acc_full) * noise_stability
    """
    acc_raw = accuracy_score(y_test, clf.predict(X_test))
    
    # Noise Injector (10% sigma)
    noise = np.random.normal(0, 0.1 * np.std(X_test, axis=0), X_test.shape)
    acc_noise = accuracy_score(y_test, clf.predict(X_test + noise))
    
    noise_stability = acc_noise / acc_raw if acc_raw > 0 else 0
    bas = (acc_raw / acc_full) * noise_stability if acc_full > 0 else 0
    return float(bas), float(acc_raw)

# --- HOSTILITY REGIMES ---
def apply_hostility(X, mode='scale', level=0.1):
    if mode == 'scale':
        return StandardScaler().fit_transform(X)
    elif mode == 'rotate':
        R = ortho_group.rvs(dim=X.shape[1], random_state=SEED)
        return X @ R
    elif mode == 'dropout':
        mask = np.random.rand(*X.shape) > level
        return X * mask
    elif mode == 'noise':
        return X + np.random.normal(0, level * np.std(X, axis=0), X.shape)
    return X

# --- RBIS SUITE ---
def run_rbis_suite():
    script_name = "psc_rbis_suite.py"
    
    # 1. Dataset Pool
    # New: Overparameterized
    X_over, y_over = make_classification(n_samples=500, n_features=200, n_informative=5, n_redundant=150, random_state=SEED)
    # New: Imbalanced
    X_imb, y_imb = make_classification(n_samples=1000, n_features=10, n_informative=3, weights=[0.9, 0.1], random_state=SEED)
    
    datasets = {
        "iris": load_iris(return_X_y=True),
        "wine": load_wine(return_X_y=True),
        "breast_cancer": load_breast_cancer(return_X_y=True),
        "high_redundancy": (X_over, y_over),
        "imbalanced": (X_imb, y_imb)
    }
    
    results = {}
    discovery_log = []
    
    for ds_name, (X, y) in datasets.items():
        print(f"RBIS Auditing: {ds_name}")
        
        # P0: Full Baseline
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=SEED)
        clf_full = RandomForestClassifier(n_estimators=50, random_state=SEED).fit(X_train, y_train)
        acc_full = accuracy_score(y_test, clf_full.predict(X_test))
        
        # P1: Projection Baseline
        pca = PCA(n_components=min(X.shape), random_state=SEED).fit(X)
        X_pca = pca.transform(X)
        
        # Metrics for top-1 component (Structural probe)
        pss = compute_pss_individual(X)
        
        # Behavioral Probe for top-1
        X_cp = X_pca[:, [0]]
        X_tr_cp, X_te_cp, y_tr, y_te = train_test_split(X_cp, y, test_size=0.3, random_state=SEED)
        clf_cp = RandomForestClassifier(n_estimators=50, random_state=SEED).fit(X_tr_cp, y_tr)
        bas, acc_cp = compute_bas(clf_cp, X_te_cp, y_te, acc_full)
        
        # Hostility Matrix (P1-P2)
        hostilities = ['scale', 'rotate', 'dropout', 'noise']
        hostility_accs = []
        for h in hostilities:
            X_h = apply_hostility(X_te_cp, mode=h, level=0.1 if h != 'noise' else 0.05)
            hostility_accs.append(accuracy_score(y_te, clf_cp.predict(X_h)))
            
        # CSI: Accuracy variance across scalings / rotations
        csi = float(np.var(hostility_accs))
        fragility_gradient = float(acc_cp - np.mean(hostility_accs))
        
        # Classification (P3)
        # BIC: Decoupled (Geometry weak, Behavior strong)
        # Low PSS, High BAS, Low CSI/Fragility
        is_bic = (pss < 0.6 and bas >= 0.65 and fragility_gradient < 0.2 and csi < 0.05)
        
        # RDC: Coupled (Geometry stable, but behavior fragile OR behavior strong)
        # High PSS, or Accuracy collapse under scaling
        is_rdc = (pss >= 0.8 and fragility_gradient > 0.1) or (fragility_gradient > 0.3)
        
        verdict = "BIC" if is_bic else "RDC" if is_rdc else "HYBRID"
        
        # P5: Practical Relevance
        relevance = "N/A"
        if verdict == "BIC":
            relevance = "POTENTIAL_COMPRESSION"
        elif verdict == "RDC":
            relevance = "FRAGILITY_PREDICTOR"
        
        results[ds_name] = {
            "pss": pss,
            "bas": bas,
            "csi": csi,
            "acc_full": float(acc_full),
            "acc_comp": float(acc_cp),
            "fragility_gradient": fragility_gradient,
            "verdict": verdict,
            "relevance": relevance,
            "hostility_accs": [float(a) for a in hostility_accs]
        }
        
        discovery_log.append({
            "domain": ds_name,
            "verdict": verdict,
            "pss": pss,
            "bas": bas,
            "relevance": relevance,
            "fragility": fragility_gradient
        })

    # --- ARTIFACTS ---
    with open(ARTIFACT_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # report.md
    report = f"""# RBIS Verdict: Representation vs Behavior Invariance

## Objective
Identify domains where functional utility (Behavior) is decoupled from geometric coordinate stability (Representation).

## Verdict Table
| Domain | Verdict | PSS | BAS | Fragility | Relevance |
|--------|---------|-----|-----|-----------|-----------|
"""
    for ds, res in results.items():
        report += f"| {ds} | {res['verdict']} | {res['pss']:.3f} | {res['bas']:.3f} | {res['fragility_gradient']:.3f} | {res['relevance']} |\n"
    
    report += f"\n## Discovery Log Summary\n"
    for log in discovery_log:
        status = f"[{log['verdict']}]"
        note = "Functional utility survives hostility." if log['verdict'] == "BIC" else "Accuracy collapsed/dependent on scale."
        report += f"- **{log['domain']}** {status}: {note} (Relevance: {log['relevance']})\n"

    with open(ARTIFACT_DIR / "report.md", "w") as f:
        f.write(report)
        
    # Falsifiers
    falsifiers = """# Falsifier: RBIS Classification

## Falsifier 1: BIC Consistency
If a domain is classified as BIC but fails to preserve > 80% of accuracy when the unstable component is used as the ONLY input under random rotation, the classification is **REJECTED**.

## Falsifier 2: RDC False Positives
If an RDC domain shows CSI < 0.001 (perfect scaling robustness), it is **PROMOTED** to HYBRID or BIC, as representation-dependence is effectively non-existent.
"""
    with open(ARTIFACT_DIR / "falsifiers.md", "w") as f:
        f.write(falsifiers)
        
    # Trace Index
    trace = [
        {"claim": "RBIS Domain Classification", "source": f"{script_name}:run_rbis_suite", "lines": "60-120", "excerpt_hash": hashlib.sha256(report.encode()).hexdigest()}
    ]
    with open(ARTIFACT_DIR / "trace_index.json", "w") as f:
        json.dump(trace, f, indent=4)
        
    print(f"RBIS Suite Complete. Verdict: {verdict}")

if __name__ == "__main__":
    run_rbis_suite()
