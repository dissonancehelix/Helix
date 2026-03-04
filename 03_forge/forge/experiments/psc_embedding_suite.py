import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA

from psc_data import generate_synthetic_embedding
from psc_metrics import compute_knn_overlap
from psc_mutations import get_transforms
from psc_reporting import write_artifacts

SEED = 42
np.random.seed(SEED)
ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACT_DIR = ROOT / '06_artifacts/artifacts' / 'psc_embedding'

def run_embedding_psc():
    script_name = "psc_embedding_suite.py"
    X_raw = generate_synthetic_embedding(intrinsic_rank=5, noise_lvl=0.05)
    
    pca_base = PCA(n_components=10, random_state=SEED)
    X_pca_base = pca_base.fit_transform(X_raw)
    base_expl_var = pca_base.explained_variance_ratio_
    base_top_dominance = float(base_expl_var[0])
    
    results = {}
    obstructions = []
    
    transforms = get_transforms(SEED)
    pss_records = []
    
    for t_name, t_func in transforms.items():
        try:
            X_trans = t_func(X_raw)
            pca_trans = PCA(n_components=10, random_state=SEED)
            X_pca_trans = pca_trans.fit_transform(X_trans)
            
            ret_overlap = compute_knn_overlap(X_pca_base, X_pca_trans, k=20)
            trans_top_dominance = float(pca_trans.explained_variance_ratio_[0])
            dom_drift = abs(base_top_dominance - trans_top_dominance)
            pss = ret_overlap * (1.0 - dom_drift)
            
            results[t_name] = {
                "retention_overlap": ret_overlap, "dominance_drift": dom_drift, 
                "pss": pss, "top_variance_ratio": trans_top_dominance
            }
            pss_records.append(pss)
        except Exception as e:
            obstructions.append(f"{t_name} failure: {str(e)}")
            
    mean_pss = float(np.mean(pss_records))
    verdict = "STABLE" if mean_pss >= 0.85 else "UNSTABLE" if mean_pss < 0.60 else "INDETERMINATE"
    
    write_artifacts(
        ARTIFACT_DIR, SEED, np.__version__, pd.__version__, X_raw, 
        verdict, mean_pss, base_top_dominance, results, script_name, obstructions
    )
    print(f"Embedding PSC Suite complete. Verdict: {verdict}")

if __name__ == "__main__":
    run_embedding_psc()
