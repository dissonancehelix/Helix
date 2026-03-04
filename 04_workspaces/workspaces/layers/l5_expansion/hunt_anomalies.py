from collections import defaultdict

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'domains'

domains = []
for p in DOMAINS_DIR.glob('*.json'):
    with open(p, 'r') as f:
        domains.append(json.load(f))

print("=== WEIRD PATTERN HUNT ===")

# 1. OUTLIERS IN STRONG CLUSTERS
print("\n[Hunting for Outliers in Strong Clusters]")
# We know STOCHASTIC + P4 -> mostly DISTRIBUTIONAL_COLLAPSE. What are the exceptions?
exceptions_p4 = []
for d in domains:
    if d.get('substrate_S1c') == 'STOCHASTIC' and d.get('persistence_ontology') == 'P4_DISTRIBUTIONAL_EQUILIBRIUM':
        b = d.get('boundary_type_primary')
        if b != 'DISTRIBUTIONAL_COLLAPSE':
            exceptions_p4.append((d.get('domain'), b))

print(f"STOCHASTIC + P4 normally yields DISTRIBUTIONAL_COLLAPSE. These {len(exceptions_p4)} domains defied the law:")
for name, b in exceptions_p4[:5]:
    print(f"  - {name} -> {b}")
if len(exceptions_p4) > 5: print("  ... etc")

# 2. CONTINUOUS SYSTEMS THAT FAIL LIKE DISCRETE ONES
print("\n[Hunting for Physics that Shatters Like Code]")
cont_shatter = []
for d in domains:
    s = d.get('substrate_S1c')
    b = d.get('boundary_type_primary')
    if s == 'CONTINUOUS' and b in ['COMBINATORIAL_THRESHOLD', 'GLOBAL_DISCONTINUITY']:
        cont_shatter.append(d.get('domain'))

print(f"Continuous domains normally fail smoothly or divergently. These {len(cont_shatter)} continuous physical domains shattered:")
for name in cont_shatter[:10]:
    print(f"  - {name}")
if len(cont_shatter) > 10: print("  ... etc")

# 3. TEXTUAL CLUES IN NON_GEOMETRIC_ELEMENTS
print("\n[Hunting for Textual Shadows]")
text_to_bound = defaultdict(list)
for d in domains:
    nge = " ".join(d.get('non_geometric_elements', [])).lower()
    b = d.get('boundary_type_primary')
    if 'combinatorics' in nge or 'search' in nge: text_to_bound['search/combinatorics'].append(b)
    if 'invariant' in nge or 'collapse' in nge: text_to_bound['invariant/collapse'].append(b)
    if 'memory' in nge or 'history' in nge: text_to_bound['memory/history'].append(b)
    
for keyword, bs in text_to_bound.items():
    c = Counter(bs)
    print(f"When 'non_geometric_elements' mentions {keyword}: {c.most_common(2)} (N={len(bs)})")

# 4. DIMENSIONLESS 'P0' SURVIVORS
print("\n[Hunting for P0 Dimensionless Entities]")
# P0 implies LOCAL STATE. Global failure + Dimensionality Change = YES for P0 is fundamentally weird.
p0_weird = []
for d in domains:
    if d.get('persistence_ontology') == 'P0_STATE_LOCAL':
        if d.get('boundary_locality') == 'GLOBAL' and d.get('boundary_dimensionality_change') == 'YES':
            p0_weird.append(d.get('domain'))
print(f"State Local (P0) systems are supposed to fail locally. These {len(p0_weird)} failed Globally AND lost mathematical dimensions:")
for name in p0_weird[:5]:
    print(f"  - {name}")

# 5. WEIRD SVD CLUSTERS
# Do some boundary types masquerade as others?
print("\n[Hunting for Masquerading Boundaries]")
bound_subs = defaultdict(list)
for d in domains:
    b = d.get('boundary_type_primary')
    s = d.get('substrate_S1c')
    bound_subs[b].append(s)

for b, subs in bound_subs.items():
    c = Counter(subs)
    top = c.most_common(1)[0]
    total = len(subs)
    # Are there any cases where the top substrate is not the obvious one?
    print(f"Boundary: {b}")
    print(f"  -> Dominant Substrate: {top[0]} ({top[1]/total*100:.1f}%)")
    # Finding the weirdest minority substrate triggering this boundary
    minorities = [x for x in c.most_common() if x[1]/total < 0.1]
    if minorities:
        print(f"  -> Rarest Substrate Triggering This: {minorities[-1][0]} ({minorities[-1][1]} cases)")
