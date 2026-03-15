import os
import json
import itertools
import math
import random
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
PHASE10_DIR = ROOT / 'phase10'
DOMAINS_DIR = ROOT / 'domains'

PHASE10_DIR.mkdir(parents=True, exist_ok=True)

# Load domains
domain_files = list(DOMAINS_DIR.glob('*.json'))
domains_data = {}
for df in domain_files:
    with open(df, 'r') as f:
        d = json.load(f)
        domains_data[d['id']] = d

domain_ids = sorted(list(domains_data.keys()))

def get_obstruction(d1, d2):
    n1 = ' '.join(d1.get('non_geometric_elements', []) + [d1.get('notes','')]).lower()
    n2 = ' '.join(d2.get('non_geometric_elements', []) + [d2.get('notes','')]).lower()
    
    # Substrate mismatches usually trigger these
    if ('symbol' in n1 or 'rule' in n1) != ('symbol' in n2 or 'rule' in n2):
        return "NON_GEOMETRIC_RULESET"
    if ('topolog' in n1) != ('topolog' in n2):
        return "TOPOLOGICAL_INCOMPATIBILITY"
    if ('stochas' in n1) != ('stochas' in n2):
        return "STOCHASTIC_DOMINANCE"
    if ('semantic' in n1 or 'norm' in n1) != ('semantic' in n2 or 'norm' in n2):
        return "SEMANTIC_MISMATCH"
        
    return "STATE_DIMENSION_MISMATCH"

def attempt_map(A, B):
    # Mapping constraint logic based on structural primitives
    ob = get_obstruction(A, B)
    if A['substrate_type'] == B['substrate_type'] and A['dimensionality_form'] == B['dimensionality_form']:
        # if substrate matches perfectly, we assume operators can be mapped linearly
        # EXCEPT if topological incompatibility still exists
        if ob == "TOPOLOGICAL_INCOMPATIBILITY":
            return "NO_MAP", ob
        return "MAP", None
        
    # Standard obstruction failure
    return "NO_MAP", ob

def calc_entropy(counts, total):
    if total == 0: return 0.0
    return -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)

def run_regime(gate_func):
    attempted = 0
    map_count = 0
    nomaps = 0
    obs_list = []
    
    for A_id, B_id in itertools.permutations(domain_ids, 2):
        A = domains_data[A_id]
        B = domains_data[B_id]
        if gate_func(A, B):
            attempted += 1
            res, ob = attempt_map(A, B)
            if res == "MAP":
                map_count += 1
            else:
                nomaps += 1
                obs_list.append(ob)
                
    H = calc_entropy(Counter(obs_list), len(obs_list))
    yield_rate = (map_count / attempted) if attempted > 0 else 0.0
    return attempted, map_count, nomaps, H, yield_rate, obs_list

# PART A: Regimes
results = {}

# (0,0) Baseline: No gating
r0 = run_regime(lambda A, B: True)
results['No_Gating'] = r0

# (1,1) Regime 1: Strict (Ontology + Substrate)
r1 = run_regime(lambda A, B: A['persistence_ontology'] == B['persistence_ontology'] and A['substrate_type'] == B['substrate_type'])
results['Strict_(1,1)'] = r1

# (1,0) Regime 2: Ontology-Only
r2 = run_regime(lambda A, B: A['persistence_ontology'] == B['persistence_ontology'])
results['Ontology_Only_(1,0)'] = r2

# (0,1) Regime 3: Substrate-Only
r3 = run_regime(lambda A, B: A['substrate_type'] == B['substrate_type'])
results['Substrate_Only_(0,1)'] = r3

with open(PHASE10_DIR / 'gate_comparison.md', 'w') as f:
    f.write("# Phase 10: Gate Relaxation\n\n")
    for name, data in results.items():
        att, mc, nm, H, yr, obs = data
        f.write(f"## {name}\n")
        f.write(f"- Attempted: {att}\n- MAP: {mc}\n- NO_MAP: {nm}\n")
        f.write(f"- Entropy: {H:.4f}\n- Yield: {yr:.4f}\n\n")

# PART B: CROSS-SUBSTRATE WITHIN-ONTOLOGY
ontologies = set(d['persistence_ontology'] for d in domains_data.values())
cross_sub_res = {}
for ont in ontologies:
    att, mc, nm, H, yr, obs = run_regime(lambda A, B: A['persistence_ontology'] == ont and B['persistence_ontology'] == ont)
    if nm > 0:
        top_ob = Counter(obs).most_common(1)[0][0]
    else:
        top_ob = "NONE"
    cross_sub_res[ont] = (H, top_ob, yr)

# PART C: CONTROLLED NOISE INJECTION
# Shuffle 20% of substrate labels
import copy
noisy_domains = copy.deepcopy(domains_data)
keys = list(noisy_domains.keys())
random.seed(42) # Determinism for audit predictability
k_shuffle = random.sample(keys, max(1, int(0.2 * len(keys))))
shuffled_substrates = [noisy_domains[k]['substrate_type'] for k in k_shuffle]
random.shuffle(shuffled_substrates)

for i, k in enumerate(k_shuffle):
    noisy_domains[k]['substrate_type'] = shuffled_substrates[i]

noise_att, noise_mc, noise_nm, noise_H, noise_yr, noise_obs = 0,0,0,0,0,[]
for A_id, B_id in itertools.permutations(domain_ids, 2):
    A = noisy_domains[A_id]
    B = noisy_domains[B_id]
    # Strict regime on noisy data
    if A['persistence_ontology'] == B['persistence_ontology'] and A['substrate_type'] == B['substrate_type']:
        noise_att += 1
        res, ob = attempt_map(A, B)
        if res == "MAP": noise_mc += 1
        else: 
            noise_nm += 1
            noise_obs.append(ob)
noise_H = calc_entropy(Counter(noise_obs), len(noise_obs))

# PART D: ENTROPY SURFACE
surface_md = f"""# Entropy Surface Grid
- (0,0) [No gating]: {r0[3]:.4f}
- (1,0) [Ontology Strict]: {r2[3]:.4f}
- (0,1) [Substrate Strict]: {r3[3]:.4f}
- (1,1) [Both Strict]: {r1[3]:.4f}
"""
with open(PHASE10_DIR / 'entropy_surface.md', 'w') as f:
    f.write(surface_md)

# PART E: VERDICT
baseline_H = r0[3]
ont_H = r2[3]
sub_H = r3[3]
strict_H = r1[3]

verdict = ""
interpretation = ""

if strict_H == 0 and noise_H > 0:
    # Substrate axis is structurally meaningful because breaking it resurrects entropy
    verdict = "FUNDAMENTAL_AXIS"
    interpretation = "S1 captures genuine physical alignment. Scrambling substrate types artificially forces structurally identical mechanics apart or unmappable mechanisms together, predictably shattering structural mapping and drastically increasing obstruction entropy."
elif strict_H == 0 and noise_H == 0:
    verdict = "PARTITION_KEY"
    interpretation = "S1 is merely isolating non-interacting subsets trivially. Changing the labels does not generate new complex obstructions because the underlying dynamics were fully disjoint."
elif sub_H < ont_H:
    verdict = "FUNDAMENTAL_AXIS"
    interpretation = "Substrate gating strictly dominates Persistence Ontology gating in dropping obstruction entropy, capturing deeper formal mechanics governing domain failure."
else:
    verdict = "CONDITIONAL_AXIS"
    interpretation = "S1 aids in resolving STATE_DIMENSION_MISMATCH but relies on the upstream Persistence Ontology to maintain topological / energetic context."

output_str = f"""Entropy values:
Baseline (0,0): {baseline_H:.4f}
Ontology (1,0): {ont_H:.4f}
Substrate (0,1): {sub_H:.4f}
Strict (1,1): {strict_H:.4f}
Noise Injection (20% shuffle): {noise_H:.4f}

Yield values:
Baseline (0,0): {r0[4]:.4f}
Ontology (1,0): {r2[4]:.4f}
Substrate (0,1): {r3[4]:.4f}
Strict (1,1): {r1[4]:.4f}

Verdict: {verdict}

Structural Interpretation:
{interpretation}
"""
print(output_str)
with open(PHASE10_DIR / 'verdict.md', 'w') as f:
    f.write(output_str)

