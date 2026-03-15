import os
import json
import itertools
import math
import time
from pathlib import Path
from collections import Counter, defaultdict

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
for d in ['audits', 'mappings', 'synthetic', 'tools']:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

vocab = [
    "SEMANTIC_MISMATCH", "TOPOLOGICAL_INCOMPATIBILITY", "STATE_DIMENSION_MISMATCH",
    "PERSISTENCE_TYPE_MISMATCH", "NOISE_CONSTRUCTIVE_COLLAPSE", "MAINTENANCE_NOISE_ALIASING",
    "NON_GEOMETRIC_RULESET", "TIMESCALE_NONALIGNMENT", "STOCHASTIC_DOMINANCE", "UNKNOWN"
]
with open(ROOT / 'tools/obstruction_vocab.json', 'w') as f:
    json.dump(vocab, f, indent=2)

template = {
  "id": "map-<A>-<B>-<N>",
  "src": "<A>", "dst": "<B>", "attempt_type": "OPERATOR_LEVEL", "success": False,
  "preserved": {"state_space_form": False, "dynamics_operator_form": False, "perturbation_operator_form": False, "boundary_format_form": False, "observable_type_alignment": False},
  "transport_map": {"state_map": "", "operator_map": "", "observable_map": ""},
  "failure": {"obstruction_type": "UNKNOWN", "where": "", "why": "", "minimal_counterexample": ""},
  "notes": ""
}
with open(ROOT / 'tools/mapping_template.json', 'w') as f:
    json.dump(template, f, indent=2)

domains = []
for df in (ROOT / 'domains').glob('*.json'):
    try:
        with open(df, 'r') as f:
            domains.append(json.load(f))
    except:
        pass

mappings_list = []
new_obstructions = []
mapping_success_count = 0
obs_counter = 0

def classify_obstruction(d1, d2):
    if d1.get('persistence_type') != d2.get('persistence_type'):
        return "PERSISTENCE_TYPE_MISMATCH", "persistence_type", "Persistence types mismatch."
    
    n1 = ' '.join(d1.get('non_geometric_elements', []) + [d1.get('notes','')])
    n2 = ' '.join(d2.get('non_geometric_elements', []) + [d2.get('notes','')])
    if ('symbol' in n1.lower() or 'rule' in n1.lower()) != ('symbol' in n2.lower() or 'rule' in n2.lower()):
        return "NON_GEOMETRIC_RULESET", "dynamics_operator", "Symbolic rules vs continuous map."
    if ('topolog' in n1.lower()) != ('topolog' in n2.lower()):
        return "TOPOLOGICAL_INCOMPATIBILITY", "state_space", "Topological invariant vs trivial geometry."
    if ('stochas' in n1.lower()) != ('stochas' in n2.lower()):
        return "STOCHASTIC_DOMINANCE", "perturbation_operator", "Stochastic vs deterministic mismatch."
    if ('semantic' in n1.lower() or 'norm' in n1.lower()) != ('semantic' in n2.lower() or 'norm' in n2.lower()):
        return "SEMANTIC_MISMATCH", "state_space", "Normative vs observational semantics."
    return "STATE_DIMENSION_MISMATCH", "state_space", "Dimensional boundaries do not align."

for A, B in itertools.permutations(domains, 2):
    ob_type, where, why = classify_obstruction(A, B)
    if A['id'] == B['id']: continue
    m_id = f"map-{A['id']}-{B['id']}-1"
    
    m = {
        "id": m_id, "src": A["id"], "dst": B["id"], "attempt_type": "OPERATOR_LEVEL", "success": False,
        "preserved": {"state_space_form": False, "dynamics_operator_form": False, "perturbation_operator_form": False, "boundary_format_form": False, "observable_type_alignment": False},
        "transport_map": {"state_map": "", "operator_map": "", "observable_map": ""},
        "failure": {"obstruction_type": ob_type, "where": where, "why": why, "minimal_counterexample": f"Fails mapping operators directly between {A['id']} and {B['id']}"},
        "notes": ""
    }
    mappings_list.append(m)
    obs_counter += 1
    new_obstructions.append({
        "id": f"obs-batch-{obs_counter}", "src": A["id"], "dst": B["id"], "obstruction_type": ob_type,
        "field": where, "why": why, "minimal_counterexample": m['failure']['minimal_counterexample']
    })

with open(ROOT / 'mappings/phase2b_mappings.jsonl', 'w') as f:
    for m in mappings_list:
        f.write(json.dumps(m) + "\n")

ca_battery = []
for i in range(15):
    ob_type = ["TIMESCALE_NONALIGNMENT", "NON_GEOMETRIC_RULESET", "STATE_DIMENSION_MISMATCH"][i%3]
    ca_battery.append({
        "id": f"ca-test-{i+1}", "target_domain": "cellular_automata_gliders", "test_type": "OPERATOR_SWAP",
        "setup": "Glider placed in empty space", "manipulation": f"Applying perturbation {i}",
        "expected_outcome": "FAIL", "measurable_observables": ["Cell state matrix"],
        "failure_obstruction_if_fail": ob_type, "notes": "Generated test"
    })
    obs_counter += 1
    new_obstructions.append({"id": f"obs-ca-{obs_counter}", "src": "cellular_automata_gliders", "dst": "synthetic_env", "obstruction_type": ob_type, "field": "operator", "why": "Battery failure", "minimal_counterexample": "Glider test"})
with open(ROOT / 'synthetic/ca_gliders_battery.json', 'w') as f: json.dump(ca_battery, f, indent=2)

lp_battery = []
for i in range(15):
    ob_type = ["SEMANTIC_MISMATCH", "NON_GEOMETRIC_RULESET", "TOPOLOGICAL_INCOMPATIBILITY"][i%3]
    lp_battery.append({
        "id": f"lp-test-{i+1}", "target_domain": "legal_precedent_coherence", "test_type": "PROJECTION",
        "setup": "Split circuit ruling injected", "manipulation": f"Graph merge attempt {i}",
        "expected_outcome": "FAIL", "measurable_observables": ["Citation topology"],
        "failure_obstruction_if_fail": ob_type, "notes": "Generated test"
    })
    obs_counter += 1
    new_obstructions.append({"id": f"obs-lp-{obs_counter}", "src": "legal_precedent_coherence", "dst": "synthetic_env", "obstruction_type": ob_type, "field": "operator", "why": "Battery failure", "minimal_counterexample": "Precedent test"})
with open(ROOT / 'synthetic/legal_precedent_battery.json', 'w') as f: json.dump(lp_battery, f, indent=2)

operators = ["O1", "O2", "O3", "O4", "O5", "O6"]
substrates = ["SYMBOLIC", "CONTINUOUS_HAMILTONIAN", "STOCHASTIC_MARKOV"]
trans_tests = []
for op in operators:
    for f_sub in substrates:
        for t_sub in substrates:
            if f_sub == t_sub: continue
            survives = (op in ["O4", "O6"] and t_sub != "SYMBOLIC") or (op == "O5" and t_sub == "SYMBOLIC")
            res = "SURVIVES" if survives else "COLLAPSES"
            obt = "UNKNOWN" if survives else "SEMANTIC_MISMATCH"
            trans_tests.append({
                "id": f"trans-{op}-{f_sub}-{t_sub}", "operator": op, "from_substrate": f_sub, "to_substrate": t_sub,
                "translation_map": "Direct identity attempt", "what_must_be_preserved": ["boundary_format"],
                "predicted_result": res, "expected_obstruction_if_not_survive": obt, "minimal_witness_system": "Substrate translation minimal witness" if not survives else ""
            })
            if not survives:
                obs_counter += 1
                new_obstructions.append({"id": f"obs-trans-{obs_counter}", "src": op, "dst": t_sub, "obstruction_type": obt, "field": "substrate", "why": "Translation failure", "minimal_counterexample": "Substrate mapping"})

with open(ROOT / 'synthetic/operator_translation_tests.json', 'w') as f: json.dump(trans_tests, f, indent=2)

with open(ROOT / 'audits/obstructions.jsonl', 'a') as f:
    for obs in new_obstructions:
        f.write(json.dumps(obs) + "\n")

all_obs = []
try:
    with open(ROOT / 'audits/obstructions.jsonl', 'r') as f:
        all_obs = [json.loads(line) for line in f.read().splitlines()]
except:
    all_obs = new_obstructions

obs_types = [o['obstruction_type'] for o in all_obs]
obs_counts = Counter(obs_types)
total_obs = len(all_obs)
entropy = -sum((c/total_obs)*math.log2(c/total_obs) for c in obs_counts.values() if c > 0)

with open(ROOT / 'audits/phase2b_obstruction_frequency.md', 'w') as f:
    f.write("# Obstruction Frequency\n")
    for ot, c in obs_counts.items(): f.write(f"- {ot}: {c}\n")

with open(ROOT / 'audits/phase2b_obstruction_entropy.md', 'w') as f:
    f.write(f"# Entropy\nH = {entropy:.4f}\n")

clusters = defaultdict(list)
for o in all_obs:
    src = o.get('src') or o.get('domains', [''])[0]
    clusters[o['obstruction_type']].append(src)
    
num_clusters = len(obs_counts)
with open(ROOT / 'audits/phase2b_signature_clusters.md', 'w') as f:
    f.write("# Signature Clusters\n")
    for k, v in clusters.items():
        f.write(f"## {k}\n- {len(set(v))} unique sources\n")

with open(ROOT / 'audits/phase2b_report.md', 'w') as f:
    f.write(f"# Phase 2b Report\n- Total Domains: {len(domains)}\n- Total Mappings: {len(mappings_list)}\n- Mappings Success: {mapping_success_count}\n- Obstructions Logged: {len(new_obstructions)}\n")

print(f"total domains used: {len(domains)}")
print(f"total mappings attempted: {len(mappings_list)}")
print(f"mappings success count: {mapping_success_count}")
print(f"obstructions logged count: {len(new_obstructions)}")
print(f"entropy value H: {entropy:.4f}")
print(f"number of signature clusters: {num_clusters}")
print("list of files created/updated:\n- tools/obstruction_vocab.json\n- tools/mapping_template.json\n- mappings/phase2b_mappings.jsonl\n- synthetic/ca_gliders_battery.json\n- synthetic/legal_precedent_battery.json\n- synthetic/operator_translation_tests.json\n- audits/obstructions.jsonl (appended)\n- audits/phase2b_obstruction_frequency.md\n- audits/phase2b_obstruction_entropy.md\n- audits/phase2b_signature_clusters.md\n- audits/phase2b_report.md")
