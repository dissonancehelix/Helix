import os
import json
import math
import random
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
from collections import Counter

ROOT = REPO_ROOT
AUDITS_DIR = ROOT / 'audits'
DOMAINS_DIR = ROOT / 'domains'

# Original domains vs new domains:
original_slugs = {
    "adaptive_immunity", "bond_percolation", "cellular_automata_gliders", "chern_insulator",
    "constitutional_law", "homological_algebra", "knot_invariants", "language_grammar",
    "legal_precedent_coherence", "lotka_volterra", "nakamoto_consensus", "protein_folding",
    "quantum_error_correction", "stabilizer_code_passive", "supermajority_amendment",
    "supply_chain", "tokamak_plasma", "traffic_shockwaves"
    # Actually there are 18 early domains maybe? Originally 16 or 24.
}

def load_real_domains():
    all_domains = []
    for p in DOMAINS_DIR.glob('*.json'):
        with open(p, 'r') as f:
            all_domains.append(json.load(f))
    return all_domains

domains = load_real_domains()

def entropy(labels):
    c = Counter(labels)
    t = len(labels)
    if t == 0: return 0.0
    return -sum((v/t)*math.log2(v/t) for v in c.values() if v > 0)
    
def cond_entropy(X, Y):
    yc = Counter(Y)
    t = len(Y)
    ch = 0
    for yv, yc_val in yc.items():
        xsub = [x for x, y in zip(X, Y) if y == yv]
        ch += (yc_val/t) * entropy(xsub)
    return ch

# For Phase 12b: we predict Boundary based on Substrate.
def map_substrate_to_pred(sub):
    m = {
        "CONTINUOUS_FIELD": "SMOOTH_HYPERSURFACE",
        "CONTINUOUS_MANIFOLD": "SMOOTH_HYPERSURFACE",
        "DISCRETE_COMBINATORIAL": "COMBINATORIAL_THRESHOLD",
        "SYMBOLIC_ALGEBRAIC": "GLOBAL_DISCONTINUITY",
        "STOCHASTIC_PROCESS": "DISTRIBUTIONAL_COLLAPSE",
        "HYBRID": "UNKNOWN"
    }
    return m.get(sub, "UNKNOWN")

preds = []
truths = []
subs = []
modes = []
t1_vals = []

for d in domains:
    # Phase 12b logic
    sub = d.get('substrate_type', 'UNKNOWN')
    true_bound = d.get('boundary_type_primary', 'UNKNOWN')
    pred = map_substrate_to_pred(sub)
    
    preds.append(pred)
    truths.append(true_bound)
    subs.append(sub)
    
    # Phase 15 logic
    t1 = d.get('T1', 'T1_COMPARABLE')
    if sub in ["DISCRETE_COMBINATORIAL", "SYMBOLIC_ALGEBRAIC"]:
        mode = "catastrophic"
    elif sub == "STOCHASTIC_PROCESS":
        mode = "intermittent"
    else:
        mode = "asymptotic"
        
    modes.append(mode)
    t1_vals.append(t1)

correct = sum(1 for p, t in zip(preds, truths) if p == t)
acc = correct / len(domains)

ig_sub = entropy(truths) - cond_entropy(truths, subs)

# CI Bootstrap
random.seed(42)
accs = []
n = len(domains)
for _ in range(1000):
    idx = [random.randint(0, n-1) for _ in range(n)]
    sc = sum(1 for i in idx if preds[i] == truths[i])
    accs.append(sc/n)
accs.sort()
ci_low = accs[int(0.025 * len(accs))]
ci_high = accs[int(0.975 * len(accs))]

# T1 metric
ig_mode_sub = entropy(modes) - cond_entropy(modes, subs)
sub_t1 = [f"{s}_{t}" for s, t in zip(subs, t1_vals)]
ig_mode_sub_t1 = entropy(modes) - cond_entropy(modes, sub_t1)
delta_ig = ig_mode_sub_t1 - ig_mode_sub

output = f"""- Real Phase 12b accuracy (over {n} domains): Acc {acc:.1%} (95% CI: [{ci_low:.1%}, {ci_high:.1%}])
- Real IG(boundary | substrate): {ig_sub:.3f} bits
- Real Delta IG from adding T1: {delta_ig:.3f} bits
"""
print(output)
