from pathlib import Path
import json
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import LabelEncoder

from sklearn.feature_extraction import DictVectorizer
from engines.infra.io.persistence import save_wrapped, load_domains

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
DOMAINS_DIR = ROOT / '04_labs/corpus/domains/domains'
ARTIFACT_DIR = ROOT / '07_artifacts/artifacts/eigenspace'

def extract_eigenspace(domains):
    if not domains: return None
    X = []
    for _, d in domains:
        s = d.get('substrate_S1c_refined', d.get('substrate_S1c', 'HYBRID'))
        o = d.get('persistence_ontology', 'UNKNOWN')
        X.append({"S1c": s, "Ont": o})
    
    vec = DictVectorizer(sparse=False)
    X_mat = vec.fit_transform(X)
    if X_mat.shape[1] < 1: return None
    
    U, S, Vt = np.linalg.svd(X_mat, full_matrices=False)
    var_exp = (S**2) / np.sum(S**2)
    
    out = {
        "singular_values": S.tolist(),
        "variance_explained": var_exp.tolist(),
        "components": Vt.tolist(),
        "features": vec.get_feature_names_out().tolist()
    }
    save_wrapped(ARTIFACT_DIR / 'baseline_beams_v2.json', out)
    return out

def track():
    if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    domains_with_names = load_domains(DOMAINS_DIR)
    if not domains_with_names:
        print("No domains found for tracking.")
        return
        
    valid_data = []
    ids = []
    
    ontologies = [d.get('persistence_ontology', 'UNKNOWN') for _, d in domains_with_names]
    substrates = [d.get('substrate_S1c', 'UNKNOWN') for _, d in domains_with_names]
    
    le_ont = LabelEncoder()
    le_ont.fit(ontologies)
    
    le_sub = LabelEncoder()
    le_sub.fit(substrates)
    
    for _, d in domains_with_names:
        v = [le_ont.transform([d.get('persistence_ontology', 'UNKNOWN')])[0], 
             le_sub.transform([d.get('substrate_S1c', 'UNKNOWN')])[0]]
        valid_data.append(v)
        ids.append(d.get('id', 'unknown'))
            
    X = np.array(valid_data)
    if X.shape[0] < 2:
        print("Not enough data points for eigenspace tracking.")
        return

    n_comp = min(X.shape[0], X.shape[1], 2)
    svd = TruncatedSVD(n_components=n_comp)
    svd.fit(X)
    
    # Eigenvectors
    evs = svd.components_.tolist()
    
    history_path = ARTIFACT_DIR / 'history.json'
    if history_path.exists():
        with open(history_path, 'r') as f:
            try:
                history = json.load(f)
            except:
                history = []
    else:
        history = []
        
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "dataset_hash": os.environ.get('HELIX_DATASET_HASH', 'unknown'),
        "singular_values": svd.singular_values_.tolist(),
        "eigenvectors": evs
    })
    
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
        
    print(f"Eigenspace drift tracked. Primary SV: {svd.singular_values_[0]:.4f}")

if __name__ == "__main__":
    import datetime
    import os
    track()
