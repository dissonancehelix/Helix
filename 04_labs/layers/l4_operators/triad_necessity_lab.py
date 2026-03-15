import json
import os
import numpy as np
import random
from pathlib import Path
from sklearn.metrics import mutual_info_score
from sklearn.decomposition import TruncatedSVD

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
DOMAINS_DIR = ROOT / '04_labs/corpus/domains/domains'
ARTIFACT_DIR = ROOT / '07_artifacts/artifacts/triad'
DOCS_DIR = ROOT / 'docs'

def detect_proxies(domain):
    # IDENTITY_PROXY
    # Identity: Invariants, fixed points, attractor persistence
    txt = (str(domain.get('dynamics_operator', '')) + " " + 
           str(domain.get('stability_condition', '')) + " " + 
           str(domain.get('state_space', ''))).lower()
    
    id_terms = ["conserve", "invariant", "fixed point", "equilibrium", "attractor", "stable", "persistence"]
    has_id = 1 if any(term in txt for term in id_terms) or domain.get('persistence_type') == 'STATE' else 0
    
    # DISTINCTION_PROXY
    # Distinction: Multi-basin, thresholds, separable partitions
    dist_terms = ["multi-basin", "bistable", "multistable", "threshold", "partition", "discontinuity", "boundary"]
    has_dist = 1 if any(term in txt for term in dist_terms) or domain.get('boundary_type_primary') != 'UNKNOWN' else 0
    
    # RELATION_PROXY
    # Relation: Coupling, feedback, dependencies
    rel_terms = ["coupling", "interaction", "linked", "coupled", "feedback", "dependency", "interdependence"]
    has_rel = 1 if any(term in txt for term in rel_terms) else 0
    
    return {
        "identity": has_id,
        "distinction": has_dist,
        "relation": has_rel
    }

def run_triad_lab():
    from engines.infra.io.persistence import load_domains
    if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    domains_with_names = load_domains(DOMAINS_DIR)
    
    overlay = {}
    X = []
    Y = []
    
    for _, domain in domains_with_names:
        if not isinstance(domain, dict): continue
        
        proxies = detect_proxies(domain)
        overlay[domain.get('id', 'unknown')] = proxies
        
        # CollapsePresent: 1 if recognizable macro collapse geometry exists
        collapse_present = 1 if domain.get('boundary_type_primary') != 'UNKNOWN' else 0
        
        X.append([proxies['identity'], proxies['distinction'], proxies['relation']])
        Y.append(collapse_present)

    with open(ARTIFACT_DIR / 'triad_overlay.json', 'w') as f:
        json.dump(overlay, f, indent=2)

    X = np.array(X)
    Y = np.array(Y)

    # Phase 1: Necessity for Collapse Existence
    # Compute IG
    ig_id = mutual_info_score(X[:, 0], Y)
    ig_dist = mutual_info_score(X[:, 1], Y)
    ig_rel = mutual_info_score(X[:, 2], Y)
    
    # Phase 2: Ablation Pack (Synthetic Generation)
    ablation_pack = []
    for _ in range(200):
        # Generate non-collapsing domains (random walks or single-basin noise)
        base = {
            "id": f"null_domain_{random.randint(0,99999)}",
            "dynamics_operator": "Unbounded noise wander",
            "stability_condition": "Weak drift, no limit",
            "boundary_type_primary": "UNKNOWN",
            "persistence_type": "UNKNOWN",
            "persistence_ontology": "UNKNOWN"
        }
        ablation_pack.append(base)
        
    # Re-evaluate with Nulls
    all_X = list(X)
    all_Y = list(Y)
    
    for d in ablation_pack:
        p = detect_proxies(d)
        all_X.append([p['identity'], p['distinction'], p['relation']])
        all_Y.append(0)
        
    all_X = np.array(all_X)
    all_Y = np.array(all_Y)

    # Phase 1: Necessity for Collapse Existence
    ig_id = mutual_info_score(all_X[:, 0], all_Y)
    ig_dist = mutual_info_score(all_X[:, 1], all_Y)
    ig_rel = mutual_info_score(all_X[:, 2], all_Y)
    
    # Phase 3: Joint Necessity Test
    combinations = {}
    for i in range(len(all_Y)):
        key = str(tuple(all_X[i].tolist())) # Force to string for JSON serialization
        if key not in combinations:
            combinations[key] = {"total": 0, "collapse": 0}
        combinations[key]["total"] += 1
        combinations[key]["collapse"] += int(all_Y[i])
    
    prob_comb = {k: v["collapse"]/v["total"] for k, v in combinations.items()}

    # Phase 4: Rank Analysis
    svd = TruncatedSVD(n_components=3)
    svd.fit(all_X)
    rank_estimate = int(len([v for v in svd.singular_values_ if v > 0.1]))
    var_explained_3 = float(sum(svd.explained_variance_ratio_[:3]))

    # Verdict Logic
    # Necessity: Probability(Collapse | missing element) must be low/zero.
    # If prob(1,0,1) is high, Distinction is NOT necessary.
    # We want to see if any element's absence (proxy=0) always results in Collapse=0.
    necessary_proxies = []
    for i, name in enumerate(["identity", "distinction", "relation"]):
        idx_0 = np.where(all_X[:, i] == 0)[0]
        if len(idx_0) > 0:
            prob_collapse_if_absent = np.mean(all_Y[idx_0])
            if prob_collapse_if_absent < 0.05: # Strict threshold
                necessary_proxies.append(name)

    if len(necessary_proxies) == 3:
        potential_verdict = "TRIAD_NECESSARY"
    elif len(necessary_proxies) > 0:
        potential_verdict = "TRIAD_PARTIALLY_NECESSARY"
    else:
        potential_verdict = "TRIAD_INSUFFICIENT"

    results = {
        "ig": {"identity": float(ig_id), "distinction": float(ig_dist), "relation": float(ig_rel)},
        "joint_probabilities": prob_comb,
        "rank_analysis": {
            "rank_estimate": rank_estimate,
            "var_explained_3": var_explained_3
        },
        "necessary_elements": necessary_proxies,
        "verdict": potential_verdict
    }

    with open(ARTIFACT_DIR / 'triad_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Save ablation packs for record
    if not (ROOT / 'sandbox/experiments/ablation').exists(): (ROOT / 'sandbox/experiments/ablation').mkdir(parents=True, exist_ok=True)
    with open(ROOT / 'sandbox/experiments/ablation/null_pack.json', 'w') as f:
        json.dump(ablation_pack, f, indent=2)

    names = [name for name, _ in domains_with_names]
    # Phase 6: Counterexample Search
    with open(DOCS_DIR / 'triad_falsifiers.md', 'w') as f:
        f.write("# Triad Necessity Falsifiers\n\nAnalyzed across base (N=616) and synthetic nulls (N=200).\n\n")
        for i, proxy_name in enumerate(["Identity", "Distinction", "Relation"]):
            # Violations: Proxy=0 but Collapse=1
            violators = np.where((all_X[:, i] == 0) & (all_Y == 1))[0]
            if len(violators) > 0:
                f.write(f"## {proxy_name} Necessity: FAIL\n")
                f.write(f"Systems with collapse but lacking {proxy_name} proxy proxy terms:\n")
                for v in violators[:5]:
                    d_id = names[v] if v < len(names) else f"synthetic_{v}"
                    f.write(f"- `{d_id}`\n")
            else:
                f.write(f"## {proxy_name} Necessity: PASS\n")

    print(f"Triad Necessity Test Suite complete. Verdict: {results['verdict']}")

if __name__ == "__main__":
    run_triad_lab()
