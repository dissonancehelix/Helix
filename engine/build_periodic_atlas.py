import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'domains'
REPORTS_DIR = ROOT / 'reports'
OUTPUTS_DIR = ROOT / 'outputs'
DOCS_DIR = ROOT / 'docs'

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

domains = []
for p in DOMAINS_DIR.glob('*.json'):
    with open(p, 'r') as f:
        domains.append((p, json.load(f)))

# B) Reclassification
reclassified = []
b_types_before = defaultdict(list)
b_types_after = defaultdict(list)

for fp, d in domains:
    s = d.get('substrate_S1c', 'UNKNOWN')
    b = d.get('boundary_type_primary', 'UNKNOWN')
    
    b_types_before[s].append(b)
    
    refined_s = s
    if s == 'CONTINUOUS':
        if b in ['COMBINATORIAL_THRESHOLD', 'GLOBAL_DISCONTINUITY']:
            refined_s = 'CONTINUOUS_TOPOLOGICAL'
            reclassified.append(d.get('domain', d.get('id')))
        else:
            refined_s = 'CONTINUOUS_FIELD'
            
    d['substrate_S1c_refined'] = refined_s
    b_types_after[refined_s].append(b)
    
    # Write back the refined tag (optional but good for consistency)
    with open(fp, 'w') as f:
        json.dump(d, f, indent=2)

def get_entropy(labels):
    c = Counter(labels)
    t = len(labels)
    if t == 0: return 0.0
    return -sum((v/t)*math.log2(v/t) for v in c.values() if v > 0)

ent_cont_before = get_entropy(b_types_before['CONTINUOUS'])
ent_cont_field = get_entropy(b_types_after['CONTINUOUS_FIELD'])
ent_cont_top = get_entropy(b_types_after['CONTINUOUS_TOPOLOGICAL'])

weighted_ent_after = (len(b_types_after['CONTINUOUS_FIELD']) * ent_cont_field + len(b_types_after['CONTINUOUS_TOPOLOGICAL']) * ent_cont_top) / max(1, len(b_types_before['CONTINUOUS']))

reclass_md = f"# Topological-Invariant Reclassification Report\n"
reclass_md += f"Separated Continuous substrates failing via discrete thresholds into CONTINUOUS_TOPOLOGICAL.\n"
reclass_md += f"Domains reclassified: {len(reclassified)}\n\n"
reclass_md += f"### Entropy Impact\n"
reclass_md += f"- Before (CONTINUOUS combined): {ent_cont_before:.3f} bits\n"
reclass_md += f"- After (Weighted average of Field + Topological): {weighted_ent_after:.3f} bits\n"
reclass_md += f"- Information Gain: {ent_cont_before - weighted_ent_after:.3f} bits\n\n"
reclass_md += "### Top 10 Reclassified Domains\n"
for a in reclassified[:10]:
    reclass_md += f"- {a}\n"
if len(reclassified) > 10:
    reclass_md += "...\n"

with open(REPORTS_DIR / 'reclassification_report.md', 'w') as f:
    f.write(reclass_md)

# A) Atlas Construction
atlas = {}
all_refined_substrates = set(d['substrate_S1c_refined'] for _, d in domains)
all_ontologies = ['P0_STATE_LOCAL', 'P1_PATTERN_SPATIOTEMPORAL', 'P2_GLOBAL_INVARIANT', 'P3_ALGORITHMIC_SYNDROME', 'P4_DISTRIBUTIONAL_EQUILIBRIUM']

for s in all_refined_substrates:
    atlas[s] = {}
    for o in all_ontologies:
        atlas[s][o] = {
            "boundaries": Counter(),
            "locality_by_timescale": defaultdict(Counter)
        }

for _, d in domains:
    s = d['substrate_S1c_refined']
    o = d.get('persistence_ontology', 'UNKNOWN')
    b = d.get('boundary_type_primary', 'UNKNOWN')
    t = d.get('T1', 'UNKNOWN')
    loc = d.get('boundary_locality', 'UNKNOWN')
    
    if o in atlas.get(s, {}):
        atlas[s][o]["boundaries"][b] += 1
        atlas[s][o]["locality_by_timescale"][t][loc] += 1

# Export Atlas JSON
with open(OUTPUTS_DIR / 'periodic_atlas.json', 'w') as f:
    json.dump(atlas, f, indent=2)

# Export Atlas CSV
csv_lines = ["Substrate,Ontology,Top_Boundary,Total_Count,Global_Slow,Local_Slow,Global_Fast,Local_Fast"]
for s in all_refined_substrates:
    for o in all_ontologies:
        cell = atlas[s][o]
        b_count = sum(cell['boundaries'].values())
        if b_count > 0:
            top_b = cell['boundaries'].most_common(1)[0][0]
            gs = cell['locality_by_timescale']['T1_SLOW_PERTURB']['GLOBAL']
            ls = cell['locality_by_timescale']['T1_SLOW_PERTURB']['LOCAL']
            gf = cell['locality_by_timescale']['T1_FAST_PERTURB']['GLOBAL']
            lf = cell['locality_by_timescale']['T1_FAST_PERTURB']['LOCAL']
            # comparable also global usually
            csv_lines.append(f"{s},{o},{top_b},{b_count},{gs},{ls},{gf},{lf}")
        else:
            csv_lines.append(f"{s},{o},NONE,0,0,0,0,0")

with open(OUTPUTS_DIR / 'periodic_atlas.csv', 'w') as f:
    f.write("\n".join(csv_lines))

atlas_md = "# Periodic Table of Systemic Collapse: Human Readable Report\n\n"
atlas_md += "The Atlas maps predictive structural eigenspace [Substrate x Ontology] to catastrophic boundary types and timescale-localities.\n\n"
atlas_md += "### Clearest Cells (Laws)\n"
for s in all_refined_substrates:
    for o in all_ontologies:
        cell = atlas[s][o]
        total = sum(cell['boundaries'].values())
        if total >= 5:
            top_b, c = cell['boundaries'].most_common(1)[0]
            if c / total >= 0.8:
                atlas_md += f"- **{s} + {o}** -> {top_b} ({(c/total*100):.1f}%, n={total})\n"

with open(REPORTS_DIR / 'atlas_report.md', 'w') as f:
    f.write(atlas_md)

# C) Compatibility Risk Prototype
# Risk metric for HYBRID systems.
hybrid_domains = [d for p, d in domains if d.get('substrate_S1c') == 'HYBRID']
risk_ranks = []

for d in hybrid_domains:
    risk_score = 0
    obs = d.get('measurement_layer', {}).get('obstruction_type', '')
    
    if obs == 'UNITS_NOT_PROJECTABLE': risk_score += 3
    if obs == 'NO_ORDER_PARAMETER': risk_score += 2
    
    o = d.get('persistence_ontology', '')
    if o in ['P2_GLOBAL_INVARIANT', 'P3_ALGORITHMIC_SYNDROME']:
        risk_score += 5
    elif o == 'P4_DISTRIBUTIONAL_EQUILIBRIUM':
        risk_score += 3
    else:
        risk_score += 1 # P0/P1
        
    t = d.get('T1', '')
    t_mult = 1.0
    if t in ['T1_FAST_PERTURB', 'T1_COMPARABLE']:
        t_mult = 1.5
        
    final_score = risk_score * t_mult
    risk_ranks.append((final_score, d.get('domain', d.get('id')), o, obs, t))

risk_ranks.sort(key=lambda x: x[0], reverse=True)

risk_md = "# Structural Compatibility Limit (Risk Prototyping)\n\n"
risk_md += "Ranking cyber-physical (HYBRID) architectures by pure structural failure risk.\n\n"
risk_md += "| Rank | Score | Domain | Ontology | Obstruction | Timescale |\n|---|---|---|---|---|---|\n"
for i, (score, name, ont, obs, t) in enumerate(risk_ranks[:25]):
    risk_md += f"| {i+1} | {score:.1f} | {name} | {ont} | {obs} | {t} |\n"

with open(REPORTS_DIR / 'compatibility_risk.md', 'w') as f:
    f.write(risk_md)

# D) Falsification Hooks
falsifiers_md = """# Falsification Hooks for Helix Laws

To prove this atlas is a testable scientific instrument and not a descriptive myth, we provide absolute structural falsifiers. If any of these counterexamples exist in physical reality or can be synthetically proven to hold mathematically, the associated Helix Law must be revoked or modified.

### 1. Cyber-Physical Brittleness Law
**Claim:** HYBRID systems tracking discrete logic (P2/P3) shatter (Discontinuity/Combinatorial).
**Falsifier Target:** Find or construct a physical system strictly controlled by discrete threshold-logic that fails via smooth continuous deformation (SMOOTH_HYPERSURFACE) when the threshold is violated.

### 2. Maintenance-Noise Aliasing (Equilibrium Collapse)
**Claim:** STOCHASTIC constraints tracking P4 equilibriums deterministically suffer DISTRIBUTIONAL_COLLAPSE due to control-loop aliasing.
**Falsifier Target:** Provide an example of a stochastic controller that perfectly suppresses natural stochastic noise without injecting correlation artifacts over long horizons, breaking via a DIFFERENT boundary (e.g., smoothly stretching instead of correlation collapse).

### 3. Dimensional Conservation Law
**Claim:** Pure physical systems (Continuous/Stochastic) rarely lose dimensions, while Hybrid systems do.
**Falsifier Target:** Find a purely classical Continuous Field that loses its intrinsic manifold dimensions during a standard breakdown (without introducing discrete quantum/topological singularities).

### 4. Fast-Perturbation Snapping (Blast Radius Law)
**Claim:** FAST_PERTURB always triggers GLOBAL boundary locality because noise outpaces relaxation.
**Falsifier Target:** Construct an architecture where a perturbation injected structurally faster than the network's maximum relaxation speed remains mathematically localized inside the network. (This would require a novel super-luminal localized sink).

### 5. Representation Decoupling
**Claim:** Continuous spaces cannot map to Discrete Symbolic without lossy projections (STATE_DIMENSION_MISMATCH).
**Falsifier Target:** Formulate an exact isomorphic mapping (bijection) between a dense Continuous field and a Discrete combinatorial syndrome without introducing a loss operator. 

### 6. Continuous Topological Splitting
**Claim:** CONTINUOUS_TOPOLOGICAL systems fail via discrete leaps (GLOBAL_DISCONTINUITY) despite continuous base fields.
**Falsifier Target:** Find a topological invariant (like a Chern number) that fails by continuously changing into a fractional value without a mathematical gap. 
"""

with open(DOCS_DIR / 'falsifiers_suite.md', 'w') as f:
    f.write(falsifiers_md)

print("Atlas constructed. Reclassification complete. Risk computed. Falsifiers generated.")
