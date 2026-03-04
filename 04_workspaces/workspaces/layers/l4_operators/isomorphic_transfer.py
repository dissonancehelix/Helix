import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist
from runtime.infra.io.persistence import save_wrapped

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
MANIFOLD_FILE = ROOT / '06_artifacts/artifacts/latest_attempt/eigenspace/universal_manifold.json'
OUT_DIR = ROOT / '06_artifacts/artifacts/latest_attempt/operator_algebra'

def run_isomorphic_transfer():
    print("Helix: Beginning Isomorphic Operator Transfer Analysis...")
    if not MANIFOLD_FILE.exists():
        print("Error: Manifold Projection not found. Run manifold_projection.py first.")
        return
        
    with open(MANIFOLD_FILE, 'r') as f:
        data = json.load(f)
        
    X = np.array(data['data']['projection'])
    ids = data['data']['domain_ids']
    
    # Calculate pairwise distances in the manifold
    distances = cdist(X, X, metric='cosine')
    
    transfers = []
    # Load all domains to check stability vs pathology
    from runtime.infra.io.persistence import load_domains
    domain_items = load_domains(ROOT / '04_workspaces/workspaces/domain_data', recursive=True)
    domain_map = {d.get('id'): d for _, d in domain_items}
    
    # We look for pairs (A, B) where A is stable and B is pathological but they are close
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            dist = distances[i, j]
            if dist < 0.05: # Threshold for "Isomorphic"
                id_a, id_b = ids[i], ids[j]
                d_a, d_b = domain_map.get(id_a), domain_map.get(id_b)
                
                if not d_a or not d_b: continue
                
                # Check for "Stability Gap"
                # For this logic, we'll assume domains with 'failure_reason' or in 'counterexamples' are pathological
                # And those without are stable proxies
                # This is a heuristic for the transfer engine
                is_path_a = "failure_reason" in d_a or "mutant" in id_a
                is_path_b = "failure_reason" in d_b or "mutant" in id_b
                
                if is_path_a != is_path_b:
                    stable_id = id_a if not is_path_a else id_b
                    path_id = id_b if not is_path_a else id_a
                    
                    stable_dom = domain_map[stable_id]
                    path_dom = domain_map[path_id]
                    
                    transfers.append({
                        "source_id": stable_id,
                        "target_id": path_id,
                        "distance": float(dist),
                        "transfer_operator": stable_dom.get("dynamics_operator", "UNKNOWN"),
                        "targeted_failure": path_dom.get("failure_mode", "UNKNOWN"),
                        "rationale": f"Isomorphic geometry (manifold dist: {dist:.4f}) suggests Operator {stable_id} can regulate {path_id}."
                    })
                    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_wrapped(OUT_DIR / 'isomorphic_transfers.json', transfers)
    print(f"Transfer Analysis Complete. Detected {len(transfers)} isomorphic transfer opportunities.")

if __name__ == "__main__":
    run_isomorphic_transfer()
