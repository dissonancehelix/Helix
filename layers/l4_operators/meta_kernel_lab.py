import json
import random
import os
from infra.hashing.integrity import compute_content_hash
import argparse
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.metrics import mutual_info_score, accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.feature_extraction.text import CountVectorizer

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / os.environ.get('HELIX_DOMAINS_DIR', 'data/domains')
ART_DIR = ROOT / 'artifacts' / 'meta_kernel'
DOCS_DIR = ROOT / 'docs'

def ig(x, y):
    if not len(x): return 0.0
    return float(mutual_info_score(x, y))

def compute_null_stats(X, Y, n_iter):
    n_c = []
    s_c = list(X)
    for _ in range(n_iter):
        random.shuffle(s_c)
        n_c.append(ig(s_c, Y))
    nm = np.mean(n_c)
    nstd = np.std(n_c)
    z = (ig(X, Y) - nm) / nstd if nstd else 0
    pval = sum(1 for n in n_c if n >= ig(X, Y)) / len(n_c)
    return float(z), float(pval)

def compute_dropout_drift(X, Y, drops=[0.1, 0.2, 0.3], n_iter=50):
    drifts = []
    for do in drops:
        do_igs = []
        for _ in range(n_iter):
            idx = random.sample(range(len(X)), int(len(X)*(1-do)))
            dx = [X[i] for i in idx]
            dy = [Y[i] for i in idx]
            do_igs.append(ig(dx, dy))
        drifts.append(np.std(do_igs) if len(do_igs) else 0)
    return float(max(drifts) if drifts else 0)

def compute_leakage(X_class, Z_cat):
    le_x = LabelEncoder().fit_transform(X_class)
    le_z = LabelEncoder().fit_transform(Z_cat)
    lr = LogisticRegression(max_iter=1000)
    lr.fit(le_z.reshape(-1, 1), le_x)
    return float(accuracy_score(le_x, lr.predict(le_z.reshape(-1, 1))))

def extract_features(domains):
    features = defaultdict(dict)
    
    # R1: Motif tokens
    r1_tokens = ["feedback", "threshold", "consensus", "hysteresis", "repair", "buffering", "gradient", "cascade", "cycle", "equilibrium"]
    # R2: Topology
    r2_tokens = ["centralized", "distributed", "local", "global", "layered", "network", "hierarchy", "mesh"]
    # R3: Failure Adjacency
    r3_tokens = ["integer", "jump", "continuous", "divergence", "smooth", "abrupt", "collapse", "degrade", "shatter", "drift"]
    # R4: Obstruction subclasses - we'll just use the obstruction string
    
    for d in domains:
        did = d['id']
        txt = (str(d.get('dynamics', '')) + " " + str(d.get('perturbation', '')) + " " + 
               str(d.get('stability_condition', '')) + " " + str(d.get('failure_mode', ''))).lower()
               
        # R1
        f1 = [t for t in r1_tokens if t in txt]
        features[did]['R1'] = f1
        
        # R2
        f2 = [t for t in r2_tokens if t in txt]
        features[did]['R2'] = f2
        
        # R3
        f3 = [t for t in r3_tokens if t in txt]
        features[did]['R3'] = f3
        
        # R4
        ml = d.get('measurement_layer') or {}
        obs = ml.get('obstruction_type') or 'UNKNOWN'
        obs = obs.lower()
        if obs != 'unknown' and obs != 'none':
            features[did]['R4'] = [obs.split('_')[0]]
        else:
            features[did]['R4'] = []
            
    return features

def propose_axes(domains, features):
    axes = {}
    
    for family in ['R1', 'R2', 'R3', 'R4']:
        vocab = list(set([t for did in features for t in features[did][family]]))
        if not vocab: continue
        
        X_mat = []
        dids = []
        for d in domains:
            did = d['id']
            dids.append(did)
            vec = [1 if v in features[did][family] else 0 for v in vocab]
            X_mat.append(vec)
            
        X_mat = np.array(X_mat)
        
        # Unsupervised clustering if enough features
        if X_mat.shape[1] >= 2:
            km = KMeans(n_clusters=min(5, len(vocab)), random_state=42, n_init='auto')
            labels = km.fit_predict(X_mat)
            
            axis_data = {}
            for i, did in enumerate(dids):
                # If feature vector is all 0, assign UNKNOWN
                if sum(X_mat[i]) == 0:
                    axis_data[did] = "UNKNOWN"
                else:
                    axis_data[did] = f"C_{labels[i]}"
                    
            axes[f"Axis_{family}_KMeans"] = {
                "family": family,
                "data": axis_data
            }
            
            # Spectral 
            if len(dids) > 10:
                sc = SpectralClustering(n_clusters=min(3, len(vocab)), random_state=42, affinity='nearest_neighbors')
                labels = sc.fit_predict(X_mat)
                axis_data = {}
                for i, did in enumerate(dids):
                    if sum(X_mat[i]) == 0:
                        axis_data[did] = "UNKNOWN"
                    else:
                        axis_data[did] = f"S_{labels[i]}"
                axes[f"Axis_{family}_Spectral"] = {
                    "family": family,
                    "data": axis_data
                }
                
    return axes

def compress_axes(axes, min_support_pct=0.03):
    compressed = {}
    for aname, adata in axes.items():
        data = adata['data']
        total = len(data)
        counts = Counter(data.values())
        
        mapping = {}
        for k, v in counts.items():
            if k == "UNKNOWN": 
                mapping[k] = "UNKNOWN"
            elif (v / total) < min_support_pct:
                mapping[k] = "OTHER"
            else:
                mapping[k] = k
                
        # Remap and ensure <= 7 labels
        new_data = {}
        for did, val in data.items():
            new_val = mapping.get(val, "OTHER")
            new_data[did] = new_val
            
        final_counts = Counter(new_data.values())
        if len([k for k in final_counts.keys() if k != "UNKNOWN"]) > 7:
            # Drop smallest into OTHER
            ordered = sorted([(k,v) for k,v in final_counts.items() if k not in ["UNKNOWN", "OTHER"]], key=lambda x: x[1], reverse=True)
            keep = set([x[0] for x in ordered[:6]])
            for did in new_data:
                if new_data[did] not in keep and new_data[did] != "UNKNOWN":
                    new_data[did] = "OTHER"
                    
        compressed[aname] = {
            "family": adata['family'],
            "data": new_data,
            "labels": list(set(new_data.values()))
        }
    return compressed

def isotopic_rotation_test(axis_data, Y_b):
    # Simulate re-encoding by shuffling labels for "OTHER" or mapping random subsets
    # A true robust axis shouldn't rely on arbitrary re-arrangements
    valid_dids = [did for did, v in axis_data.items() if v != "UNKNOWN"]
    if not valid_dids: return False
    
    # Just a proxy check: does IG completely collapse if we merge the top 2 labels?
    vals = [axis_data[did] for did in valid_dids]
    yb = [Y_b[did] for did in valid_dids]
    
    ig_base = ig(vals, yb)
    
    counts = Counter(vals)
    top_2 = [k for k,v in counts.most_common(2) if k != "UNKNOWN"]
    if len(top_2) < 2: return True # Cannot test
    
    # Rotate: merge top 2
    rot_vals = [v if v not in top_2 else "MERGED" for v in vals]
    ig_rot = ig(rot_vals, yb)
    
    # If it collapses > 70%, it's fragile
    if ig_base > 0 and (ig_rot / ig_base) < 0.3:
        return False
    return True

def run_lab(bounded=False):
    random.seed(42)
    np.random.seed(42)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    domains = []
    # Try finding domains
    for p in DOMAINS_DIR.glob('*.json'):
        with open(p, 'r') as f:
            domains.append(json.load(f))
    
    if bounded:
        n_perms = 5000
    else:
        n_perms = 50000
        
    print(f"Loaded {len(domains)} domains.")
    
    features = extract_features(domains)
    raw_axes = propose_axes(domains, features)
    
    with open(ART_DIR / 'candidates_raw.json', 'w') as f:
        json.dump(raw_axes, f, indent=2)
        
    comp_axes = compress_axes(raw_axes)
    
    with open(ART_DIR / 'candidates_compressed.json', 'w') as f:
        json.dump(comp_axes, f, indent=2)
        
    # Build target arrays
    Y_b = {d["id"]: d.get("boundary_type_primary", "UNKNOWN") for d in domains}
    Y_loc = {d["id"]: d.get("T1", "UNKNOWN") for d in domains}
    Y_obs = {d["id"]: ((d.get("measurement_layer") or {}).get("obstruction_type") or "UNKNOWN") for d in domains}
    
    # K1 + K2 for leakage
    # we don't have K2 primitives strictly for base 616 in the domain object, so we proxy with substrate+ontology+boundary for leakage testing of generic structures
    Z_leak = {}
    for d in domains:
        s = d.get('substrate_S1c_refined', d.get('substrate_S1c', 'UNKNOWN'))
        o = d.get('persistence_ontology', 'UNKNOWN')
        # We assume if K1 easily predicts it, it's leaky
        Z_leak[d["id"]] = f"{s}_{o}"
        
    scores = {}
    survivors = {}
    failures = {}
    registry = {"axes": []}
    
    for aname, adata in comp_axes.items():
        data = adata["data"]
        valid_dids = [did for did, v in data.items() if v != "UNKNOWN"]
        if len(valid_dids) < 10: 
            failures[aname] = "Insufficient support"
            continue
            
        X_a = [data[did] for did in valid_dids]
        y_b = [Y_b[did] for did in valid_dids]
        y_l = [Y_loc[did] for did in valid_dids]
        y_o = [Y_obs[did] for did in valid_dids]
        z_l = [Z_leak[did] for did in valid_dids]
        
        ig_b = ig(X_a, y_b)
        ig_l = ig(X_a, y_l)
        ig_o = ig(X_a, y_o)
        
        # Null
        z_score, pval = compute_null_stats(X_a, y_b, n_perms)
        
        # Drift
        drift = compute_dropout_drift(X_a, y_b)
        
        # Leakage
        leak_acc = compute_leakage(X_a, z_l)
        
        # Invariance
        inv_pass = isotopic_rotation_test(data, Y_b)
        
        # Verdict decision
        if leak_acc >= 0.85:
            verdict = "DEAD (Tautological/Leaky)"
        elif not inv_pass:
            verdict = "DEAD (Fragile Rotation)"
        elif pval <= 0.01 and z_score >= 3 and drift <= 0.05:
            verdict = "SURVIVOR"
        else:
            verdict = "DEAD (Statistical Null)"
            
        res = {
            "family": adata["family"],
            "labels": adata["labels"],
            "metrics": {
                "ig_BoundaryType": ig_b,
                "ig_Locality": ig_l,
                "ig_Obstruction": ig_o,
                "z_score": z_score,
                "p_value": pval,
                "dropout_drift": drift,
                "leakage_accuracy": leak_acc,
                "invariance_pass": inv_pass
            },
            "decision": verdict,
            "K3_CANDIDATE_ELIGIBLE": verdict == "SURVIVOR" and len(adata["labels"]) <= 5
        }
        scores[aname] = res
        registry["axes"].append({"id": aname, **res})
        
        if verdict == "SURVIVOR":
            survivors[aname] = res
        else:
            failures[aname] = res
            
    with open(ART_DIR / 'axis_scores.json', 'w') as f: json.dump(scores, f, indent=2)
    with open(ART_DIR / 'axis_survivors.json', 'w') as f: json.dump(survivors, f, indent=2)
    with open(ART_DIR / 'axis_failures.json', 'w') as f: json.dump(failures, f, indent=2)
    with open(ART_DIR / 'registry.json', 'w') as f: json.dump(registry, f, indent=2)
    
    # Falsifiers doc
    fmd = "# Meta-Kernel Falsifiers\n\nGenerated mathematically for SURVIVOR axes.\n\n"
    for sname, sdata in survivors.items():
        fmd += f"## Axis: {sname}\n"
        fmd += f"- **Counterexample Class**: Domains expressing `{sname}` labels but demonstrating a boundary distribution identical to random chance (IG drops < 0.05).\n"
        fmd += f"- **Substrate Constraint Break**: If `{sname}` becomes highly predictable solely from `Substrate_S1c` (Accuracy >= 0.85), the axis collapses into tautology.\n"
        fmd += f"- **Reproduction**: Run `python engine/meta_kernel_lab.py` and inspect `artifacts/meta_kernel/axis_scores.json`.\n\n"
        
    with open(DOCS_DIR / 'meta_kernel_falsifiers.md', 'w') as f:
        f.write(fmd)
        
    # Report doc
    rmd = f"""# Meta-Kernel Discovery Lab Report

- **Total Candidates Generated:** {len(raw_axes)}
- **Total Compressed Evaluated:** {len(comp_axes)}
- **Total Survivors:** {len(survivors)}
- **Total Failures:** {len(failures)}

## Survivors
"""
    for sname, sdata in survivors.items():
        rmd += f"### {sname}\n"
        rmd += f"- Family: {sdata['family']}\n"
        rmd += f"- Labels: {sdata['labels']}\n"
        rmd += f"- IG(BoundaryType): {sdata['metrics']['ig_BoundaryType']:.3f}\n"
        rmd += f"- Z-Score: {sdata['metrics']['z_score']:.2f}\n"

    rmd += "\n## Failure Analysis\n"
    leaky = sum(1 for k, v in failures.items() if "Tautological" in v['decision'])
    fragile = sum(1 for k, v in failures.items() if "Fragile" in v['decision'])
    stat = sum(1 for k, v in failures.items() if "Statistical" in v['decision'])
    
    rmd += f"- Leaky (Derivative of K1/K2): {leaky}\n"
    rmd += f"- Fragile (Failed isotopic rotation): {fragile}\n"
    rmd += f"- Statistical (Failed nulls/drift): {stat}\n"
    
    rmd += "\n## Recommended Next Action\n"
    if len(survivors) > 0:
        rmd += "Execute external pack replication on the surviving axes to confirm they persist outside the base corpus."
    else:
        rmd += "Redesign candidate generator definitions; current structural proxies are indistinguishable from noise or highly tautological to Substrate."
        
    with open(DOCS_DIR / 'meta_kernel_report.md', 'w') as f:
        f.write(rmd)
        
    # Lab instructions doc
    lmd = """# Meta-Kernel Discovery Lab Protocol

## Purpose
The Meta-Kernel Lab automatically proposes candidate structural axes from domain objects and attempts to mathematically destroy them. Only structurally invariant, non-tautological axes survive.

## Execution
Run a full suite:
`python engine/meta_kernel_lab.py`

Run a bounded CI suite (faster, 5k perms):
`python engine/meta_kernel_lab.py --bounded`

## Outputs
- `artifacts/meta_kernel/*`: Holds all raw and compressed candidate matrices, scores, and registry.
- `docs/meta_kernel_report.md`: Summary of discovery run.
- `docs/meta_kernel_falsifiers.md`: Auto-generated break conditions for any surviving axes.
"""
    with open(DOCS_DIR / 'meta_kernel_lab.md', 'w') as f:
        f.write(lmd)
        
    print(f"Lab run complete. Evaluated {len(comp_axes)} axes. Survivors: {len(survivors)}. Failures: {len(failures)}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--bounded', action='store_true', help="Run bounded test (5k permutations)")
    args = parser.parse_args()
    
    run_lab(bounded=args.bounded)
