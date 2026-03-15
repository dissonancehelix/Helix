import os
import json
import math
import random
from pathlib import Path
from collections import Counter, defaultdict

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
DOMAINS_DIR = ROOT / 'domains'

# Helper to calc entropy
def entropy(labels):
    counts = Counter(labels)
    total = len(labels)
    if total == 0: return 0.0
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

def conditional_entropy(X, Y):
    # conditional entropy H(X | Y)
    # H(X, Y) - H(Y)
    # mathematically: sum over y: P(Y=y) * H(X | Y=y)
    y_counts = Counter(Y)
    total = len(Y)
    
    cond_h = 0.0
    for y_val, c in y_counts.items():
        # filter X where Y == y_val
        x_subset = [x for x, y in zip(X, Y) if y == y_val]
        h_x_given_y = entropy(x_subset)
        cond_h += (c / total) * h_x_given_y
    return cond_h

def information_gain(X, Y):
    return entropy(X) - conditional_entropy(X, Y)

# PART A: TAG BOUNDARY TYPES
domain_files = list(DOMAINS_DIR.glob('*.json'))
domains_data = {}

for df in domain_files:
    with open(df, 'r') as f:
        d = json.load(f)
    did = d['id']
    content = json.dumps(d).lower()
    
    # Simple heuristic to assign boundary types based on Phase 3C taxonomy mappings
    if 'combinatorial' in content or 'syndrome' in content or 'algebraic' in content or 'grammar' in content:
        btype = "COMBINATORIAL_THRESHOLD"
        loc = "GLOBAL"
        dim = "NO"
    elif 'diverge' in content or 'critical' in content or 'singular' in content:
        btype = "SINGULAR_DIVERGENCE"
        loc = "GLOBAL"
        dim = "YES"
    elif 'topolog' in content or 'chern' in content or 'defect' in content:
        btype = "GLOBAL_DISCONTINUITY"
        loc = "GLOBAL"
        dim = "YES"
    elif 'distribution' in content or 'markov' in content or 'probability' in content:
        btype = "DISTRIBUTIONAL_COLLAPSE"
        loc = "GLOBAL"
        dim = "NO"
    else:
        btype = "SMOOTH_HYPERSURFACE"
        loc = "LOCAL"
        dim = "NO"
        
    d['boundary_type_primary'] = btype
    d['boundary_locality'] = loc
    d['boundary_dimensionality_change'] = dim
    
    with open(df, 'w') as f:
        json.dump(d, f, indent=2)
        
    domains_data[did] = d

B = [d['boundary_type_primary'] for d in domains_data.values()]
S = [d['substrate_type'] for d in domains_data.values()]
O = [d.get('persistence_ontology', 'UNKNOWN') for d in domains_data.values()]

# PART B: CONDITIONAL ENTROPY TEST
H_B = entropy(B)
H_B_given_S = conditional_entropy(B, S)
IG = information_gain(B, S)

# PART C: SHUFFLE TEST
S_shuffled = list(S)
random.seed(123)
random.shuffle(S_shuffled)
H_B_given_S_shuff = conditional_entropy(B, S_shuffled)
IG_shuff = information_gain(B, S_shuffled)

# PART D: CROSS-ONTOLOGY CHECK
# Within each ontology, calculate IG
# sum over o: P(O=o) * IG(B|o, S|o)  -- Is it still predictive?
ontologies = set(O)
avg_ig_within_o = 0.0
total = len(O)
for o_val in ontologies:
    b_sub = [b for b, o in zip(B, O) if o == o_val]
    s_sub = [s for s, o in zip(S, O) if o == o_val]
    if len(b_sub) == 0: continue
    
    # IG within this ontology
    ig_in_o = information_gain(b_sub, s_sub)
    avg_ig_within_o += (len(b_sub) / total) * ig_in_o

verdict = ""
if IG > IG_shuff and IG > 0.5 * H_B: # Explain well over half the entropy
    verdict = "PREDICTIVE"
elif IG > IG_shuff:
    verdict = "WEAKLY_PREDICTIVE"
else:
    verdict = "NON_PREDICTIVE"

out = f"""Report:
- H(boundary_type): {H_B:.4f}
- H(boundary_type | substrate_type): {H_B_given_S:.4f}
- Information gain: {IG:.4f}
- Shuffled baseline IG: {IG_shuff:.4f}
- Verdict: {verdict}
"""
print(out)
