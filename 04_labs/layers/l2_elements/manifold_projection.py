import os
import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.decomposition import TruncatedSVD
from engines.infra.io.persistence import load_domains, save_wrapped

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
OUT_DIR = ROOT / '07_artifacts/artifacts/latest_attempt/eigenspace'
DOCS_DIR = ROOT / 'docs'

def run_projection():
    print("Helix: Beginning Universal Manifold Projection...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load entire corpus
    domains_items = load_domains(ROOT / '04_labs/corpus/domains', recursive=True)
    domains = [d for _, d in domains_items]
    print(f"Loaded {len(domains)} total domains.")
    
    # 2. Vectorize
    # We flatten the dicts for the vectorizer, ignoring IDs and heavy text blobs
    X_dicts = []
    for d in domains:
        f = {}
        for k, v in d.items():
            if k in ['id', 'notes', 'substrate_formalism', 'observable_metrics']:
                continue
            if isinstance(v, (str, int, float, bool)):
                f[k] = v
            elif isinstance(v, dict):
                # Flatten one level
                for sk, sv in v.items():
                    if isinstance(sv, (str, int, float, bool)):
                        f[f"{k}_{sk}"] = sv
        X_dicts.append(f)
        
    vec = DictVectorizer(sparse=False)
    X_mat = vec.fit_transform(X_dicts)
    print(f"Vectorized Manifold: {X_mat.shape[0]} domains x {X_mat.shape[1]} sparse features.")
    
    # 3. Projection
    n_components = min(50, X_mat.shape[1] - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_proj = svd.fit_transform(X_mat)
    
    var_explained = svd.explained_variance_ratio_
    cum_var = np.cumsum(var_explained)
    
    # 4. Save results
    manifold_data = {
        "n_domains": len(domains),
        "n_features": X_mat.shape[1],
        "explained_variance": var_explained.tolist(),
        "cumulative_variance": cum_var.tolist(),
        "projection": X_proj.tolist(),
        "domain_ids": [d.get('id') for d in domains],
        "feature_names": vec.get_feature_names_out().tolist()
    }
    
    save_wrapped(OUT_DIR / 'universal_manifold.json', manifold_data)
    
    # 5. Generate Atlas
    atlas = f"""# Helix Universal Manifold Atlas

## Projection Stats
- **Domains**: {len(domains)}
- **Feature Space**: {X_mat.shape[1]}
- **Manifold Rank (90% Var)**: {np.argmax(cum_var >= 0.9) + 1}
- **Top 5 Component Variance**: {var_explained[:5].tolist()}

## Structural Interpretation
The manifold represents the compressed state-space of all identified constraint systems. 
A low rank indicates high structural convergence across domains.

| Component | Explained Variance | Cumulative |
| :--- | :--- | :--- |
"""
    for i in range(min(10, len(var_explained))):
        atlas += f"| λ_{i} | {var_explained[i]:.4f} | {cum_var[i]:.4f} |\n"
        
    with open(DOCS_DIR / 'manifold_atlas.md', 'w', encoding='utf-8') as f:
        f.write(atlas)
        
    print(f"Manifold Projection Complete. Atlas generated at {DOCS_DIR / 'manifold_atlas.md'}")

if __name__ == "__main__":
    run_projection()
