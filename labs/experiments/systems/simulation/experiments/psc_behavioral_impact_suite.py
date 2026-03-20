import os
import numpy as np
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris, load_wine
from sklearn.metrics import accuracy_score

from psc_impact_utils import compute_psc_per_component, generate_synthetic_rank_dataset
from psc_impact_reporting import write_impact_artifacts

SEED = 42
np.random.seed(SEED)
ROOT = REPO_ROOT
ARTIFACT_DIR = ROOT / 'execution/artifacts' / 'psc_behavioral_impact'

def run_behavioral_impact_suite():
    iris_X, iris_y = load_iris(return_X_y=True)
    wine_X, wine_y = load_wine(return_X_y=True)
    synth_X, synth_y = generate_synthetic_rank_dataset(seed=SEED) if 'generate_synthetic_rank_dataset' in globals() else generate_synthetic_rank_dataset()
    
    datasets = {
        "iris": (iris_X, iris_y),
        "wine": (wine_X, wine_y),
        "synthetic": (synth_X, synth_y)
    }
    
    perf_matrix = {}
    drift_metrics = {}
    summary_results = {}
    
    for ds_name, (X, y) in datasets.items():
        print(f"Processing: {ds_name}")
        n_features = X.shape[1]
        pca = PCA(n_components=n_features, random_state=SEED).fit(X)
        X_pca = pca.transform(X)
        
        pss_scores = compute_psc_per_component(X, seed=SEED)
        
        stable_idx = [i for i, pss in enumerate(pss_scores) if pss >= 0.85]
        unstable_idx = [i for i, pss in enumerate(pss_scores) if pss < 0.60]
        
        X_stable = X_pca[:, stable_idx] if stable_idx else np.zeros((X.shape[0], 1))
        X_unstable = X_pca[:, unstable_idx] if unstable_idx else np.zeros((X.shape[0], 1))
        
        models_data = {
            "Model_Full": X_pca, "Model_Stable": X_stable, "Model_Unstable": X_unstable
        }
        
        ds_matrix = {}
        for m_name, X_m in models_data.items():
            X_train, X_test, y_train, y_test = train_test_split(X_m, y, test_size=0.3, random_state=SEED)
            clf = RandomForestClassifier(n_estimators=100, random_state=SEED).fit(X_train, y_train)
            
            acc_raw = accuracy_score(y_test, clf.predict(X_test))
            X_test_noise = X_test + np.random.normal(0, 0.1 * np.std(X_test, axis=0), X_test.shape)
            acc_noise = accuracy_score(y_test, clf.predict(X_test_noise))
            mask = np.random.rand(*X_test.shape) > 0.2
            X_test_dropout = X_test * mask
            acc_dropout = accuracy_score(y_test, clf.predict(X_test_dropout))
            
            ds_matrix[m_name] = {"acc_raw": acc_raw, "acc_noise": acc_noise, "acc_dropout": acc_dropout}
            
        perf_matrix[ds_name] = ds_matrix
        
        full_raw = ds_matrix["Model_Full"]["acc_raw"]
        stable_raw = ds_matrix["Model_Stable"]["acc_raw"]
        p_delta = full_raw - stable_raw
        
        def get_stability_ratio(m_results):
            accs = [m_results["acc_raw"], m_results["acc_noise"], m_results["acc_dropout"]]
            return min(accs) / max(accs) if max(accs) > 0 else 0
            
        drift_metrics[ds_name] = {
            "full_stability_ratio": get_stability_ratio(ds_matrix["Model_Full"]),
            "stable_stability_ratio": get_stability_ratio(ds_matrix["Model_Stable"]),
            "unstable_stability_ratio": get_stability_ratio(ds_matrix["Model_Unstable"]),
            "full_stable_delta": p_delta
        }
        
        summary_results[ds_name] = {
            "components_analyzed": n_features, "stable_count": len(stable_idx),
            "unstable_count": len(unstable_idx),
            "verdict": "H1_SUCCESS" if get_stability_ratio(ds_matrix["Model_Unstable"]) < 0.60 else "H2_SUCCESS"
        }

    write_impact_artifacts(ARTIFACT_DIR, summary_results, perf_matrix, drift_metrics)
    print(f"Impact Suite Complete. Artifacts written to {ARTIFACT_DIR}")

if __name__ == "__main__":
    run_behavioral_impact_suite()
