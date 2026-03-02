from sklearn.feature_extraction import DictVectorizer
from infra.io.persistence import save_wrapped

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ART_DIR = ROOT / 'artifacts'

def extract_eigenspace(domains):
    X = []
    for _, d in domains:
        s = d.get('substrate_S1c_refined', d.get('substrate_S1c', 'HYBRID'))
        o = d.get('persistence_ontology', 'UNKNOWN')
        X.append({"S1c": s, "Ont": o})
    
    vec = DictVectorizer(sparse=False)
    X_mat = vec.fit_transform(X)
    U, S, Vt = np.linalg.svd(X_mat, full_matrices=False)
    var_exp = (S**2) / np.sum(S**2)
    
    out = {
        "singular_values": S.tolist(),
        "variance_explained": var_exp.tolist(),
        "components": Vt.tolist(),
        "features": vec.get_feature_names_out().tolist()
    }
    save_wrapped(ART_DIR / 'eigenspace/baseline_beams_v2.json', out)
    return out

def extract_obstructions(domains):
    obs_X = []
    for _, d in domains:
        obs = d.get('measurement_layer', {}).get('obstruction_type')
        if obs:
            obs_X.append({
                "Substrate": d.get('substrate_S1c_refined', 'UNKNOWN'),
                "Ontology": d.get('persistence_ontology', 'UNKNOWN'),
                "Boundary": d.get('boundary_type_primary', 'UNKNOWN'),
                "Obstruction": obs
            })
    vec = DictVectorizer(sparse=False)
    if not obs_X: return None
    X_mat = vec.fit_transform(obs_X)
    U, S, Vt = np.linalg.svd(X_mat, full_matrices=False)
    var_exp = (S**2) / np.sum(S**2)
    
    out = {
        "singular_values": S.tolist(),
        "variance_explained": var_exp.tolist()
    }
    save_wrapped(ART_DIR / 'obstruction/obstruction_spectrum.json', out)
    return out

DOMAINS_DIR = ROOT / 'data/domains'
ARTIFACT_DIR = ROOT / 'artifacts/eigenspace'

def track():
    if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    domains = [p for p in DOMAINS_DIR.glob('*.json') if not p.name.startswith('phase')]
    valid_data = []
    ids = []
    
    # Simple feature vector from ontology and substrate
    le_ont = LabelEncoder()
    onts = [json.load(open(p))['persistence_ontology'] for p in domains]
    le_ont.fit(onts)
    
    le_sub = LabelEncoder()
    subs = [json.load(open(p)).get('substrate_S1c', 'UNKNOWN') for p in domains]
    le_sub.fit(subs)
    
    for p in domains:
        with open(p, 'r') as f:
            d = json.load(f)
            v = [le_ont.transform([d['persistence_ontology']])[0], 
                 le_sub.transform([d.get('substrate_S1c', 'UNKNOWN')])[0]]
            valid_data.append(v)
            ids.append(d['id'])
            
    X = np.array(valid_data)
    svd = TruncatedSVD(n_components=2)
    svd.fit(X)
    
    # Eigenvectors
    evs = svd.components_.tolist()
    
    history_path = ARTIFACT_DIR / 'history.json'
    if history_path.exists():
        with open(history_path, 'r') as f:
            history = json.load(f)
    else:
        history = []
        
    history.append({
        "timestamp": "latest",
        "dataset_hash": "placeholder_hash",
        "singular_values": svd.singular_values_.tolist(),
        "eigenvectors": evs
    })
    
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
        
    print(f"Eigenspace drift tracked. Primary SV: {svd.singular_values_[0]:.4f}")

if __name__ == "__main__":
    track()
