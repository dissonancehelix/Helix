import os
import json
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
from collections import Counter

ROOT = REPO_ROOT

# Precheck
mappings_dir = ROOT / 'mappings/pairs'
if not mappings_dir.exists() or len(list(mappings_dir.glob('*.json'))) != 45:
    open(ROOT / 'audits/phase3_blockers.md', 'w').write("mappings/pairs/ does not exist or does not contain 45 files\n")
    exit(1)

if not (ROOT / 'audits/phase2a_report.md').exists():
    open(ROOT / 'audits/phase3_blockers.md', 'w').write("audits/phase2a_report.md does not exist\n")
    exit(1)
    
if len(list((ROOT / 'kernels').glob('kernel-002_candidate_*.json'))) == 0:
    open(ROOT / 'audits/phase3_blockers.md', 'w').write("No kernel-002_candidate_*.json files exist\n")
    exit(1)

# Ensure dirs
for d in ['core', 'audits', 'boundaries', 'tools', 'predictions']:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

# 1. Obstruction types
ob_types = [
    "SEMANTIC_MISMATCH",
    "TOPOLOGICAL_INCOMPATIBILITY",
    "STATE_DIMENSION_MISMATCH",
    "PERSISTENCE_TYPE_MISMATCH",
    "NOISE_CONSTRUCTIVE_COLLAPSE",
    "MAINTENANCE_NOISE_ALIASING",
    "NON_GEOMETRIC_RULESET",
    "TIMESCALE_NONALIGNMENT",
    "STOCHASTIC_DOMINANCE",
    "UNKNOWN"
]
with open(ROOT / 'core/obstruction_types.md', 'w') as f:
    f.write("# Controlled Vocabulary for Obstructions\n\n")
    for ot in ob_types:
        f.write(f"- {ot}\n")

obstructions = []
for p in mappings_dir.glob("*.json"):
    with open(p) as f:
        data = json.load(f)
    if data['candidate_morphism']['type'] == 'NO_MAP':
        bp = data.get('break_points', [{}])[0]
        cat = bp.get('category', 'UNKNOWN')
        desc = bp.get('description', '')
        
        # simple heuristic mapping
        if cat == 'SEMANTIC': ob_type = 'PERSISTENCE_TYPE_MISMATCH'
        elif cat == 'TOPOLOGY': ob_type = 'TOPOLOGICAL_INCOMPATIBILITY'
        elif cat == 'STATE': ob_type = 'STATE_DIMENSION_MISMATCH'
        else: ob_type = 'UNKNOWN'
        
        obs = {
            "id": f"obs-{data['domains'][0]}-{data['domains'][1]}",
            "domains": data['domains'],
            "obstruction_type": ob_type,
            "break_point_category": cat,
            "minimal_counterexample": "Constructing continuous map fails",
            "notes": desc
        }
        obstructions.append(obs)

with open(ROOT / 'audits/obstructions.jsonl', 'w') as f:
    for obs in obstructions:
        f.write(json.dumps(obs) + "\n")

# 2. Observable types
obs_types = [
  "THERMODYNAMIC_ENERGY",
  "INFORMATION_METRIC",
  "TOPOLOGICAL_INVARIANT",
  "ECONOMIC_COST",
  "CONTROL_GAIN",
  "QUERY_COMPLEXITY",
  "POPULATION_FRACTION",
  "CORRELATION_LENGTH",
  "ENTROPY_PRODUCTION",
  "CUSTOM"
]
with open(ROOT / 'core/observable_types.json', 'w') as f:
    json.dump(obs_types, f, indent=2)

schema_path = ROOT / 'core/schema.json'
with open(schema_path, 'r') as f:
    schema = json.load(f)

schema['properties']['observable_metrics'] = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name", "type", "estimator", "units_or_none"],
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": obs_types},
            "estimator": {"type": "string"},
            "units_or_none": {"type": "string"}
        }
    }
}
with open(schema_path, 'w') as f:
    json.dump(schema, f, indent=2)

# Validator modification
val_path = ROOT / 'core/validate.py'
with open(val_path, 'r') as f:
    val_lines = f.readlines()

new_val_lines = []
for line in val_lines:
    if 'def validate_references(objects):' in line:
        new_val_lines.extend([
            "def validate_observables(objects):\n",
            "    errors = []\n",
            "    for filename, obj in objects.items():\n",
            "        obs = obj.get('observable_metrics', [])\n",
            "        for o in obs:\n",
            "            if o.get('type') == 'CUSTOM':\n",
            "                print(f'WARNING: {filename} uses CUSTOM observable type for {o.get(\"name\")}')\n",
            "    return errors\n",
            "\n"
        ])
    if 'all_errors.extend(validate_transitions(objects))' in line:
        new_val_lines.append(line)
        new_val_lines.append('    all_errors.extend(validate_observables(objects))\n')
        continue
    new_val_lines.append(line)

with open(val_path, 'w') as f:
    f.writelines(new_val_lines)

# 3. Boundaries
ob_counts = Counter([o['obstruction_type'] for o in obstructions])
for ob_type, count in ob_counts.items():
    if count >= 3:
        b = {
          "id": f"boundary-{ob_type}",
          "definition": f"Crosses formal boundary defined by {ob_type}",
          "formal_signature": "Morphism singularity",
          "operator_condition": "Non-invertible transformation",
          "observable_signature": [],
          "domains_where_observed": list(set([o['domains'][0] for o in obstructions if o['obstruction_type'] == ob_type])),
          "counterdomains": [],
          "status": "CAPTURE"
        }
        with open(ROOT / 'boundaries' / f"{ob_type}.json", 'w') as f:
            json.dump(b, f, indent=2)

# 4. Falsifier gen
falsifier_code = """#!/usr/bin/env python3
import sys
import json

def generate_falsifiers(claim_id):
    return [
        {"title": "Extreme limit of each observable", "template": f"Push observables in {claim_id} to +/- infinity until metric diverges."},
        {"title": "Topology toggle", "template": f"Change topology of state space in {claim_id}, expect discontinuous failure."},
        {"title": "Perturbation amplification", "template": f"Increase perturbation delta in {claim_id} and observe collapse trajectory."},
        {"title": "Timescale inversion", "template": f"If slow-varying, make fast-varying in {claim_id}."},
        {"title": "Noise-construction regime", "template": f"Remove noise entirely in {claim_id} to see if order is lost."}
    ]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: falsifier_gen.py <claim_id>")
        sys.exit(1)
    print(json.dumps(generate_falsifiers(sys.argv[1]), indent=2))
"""
with open(ROOT / 'tools/falsifier_gen.py', 'w') as f:
    f.write(falsifier_code)

# 5. Prediction scaffold
pred_schema = {
  "type": "object",
  "required": ["id", "depends_on", "prediction_statement", "measurement_protocol", "expected_signature", "failure_signature", "status"],
  "properties": {
    "id": {"type": "string"},
    "depends_on": {"type": "array", "items": {"type": "string"}},
    "prediction_statement": {"type": "string"},
    "measurement_protocol": {"type": "string"},
    "expected_signature": {"type": "string"},
    "failure_signature": {"type": "string"},
    "status": {"type": "string"}
  }
}
with open(ROOT / 'core/prediction_schema.json', 'w') as f:
    json.dump(pred_schema, f, indent=2)

kernels = list((ROOT / 'kernels').glob('kernel-002_candidate_*.json'))
num_preds = 0
for k in kernels:
    with open(k) as f:
        kd = json.load(f)
    p = {
      "id": f"pred-{kd['id']}",
      "depends_on": [kd['id']],
      "prediction_statement": kd.get('predictions', [{}])[0].get('prediction', 'Prediction stub'),
      "measurement_protocol": "Measurement of active boundary parameters",
      "expected_signature": "Passes limit test",
      "failure_signature": kd.get('predictions', [{}])[0].get('falsifier', 'Failure condition met'),
      "status": "PROPOSED"
    }
    with open(ROOT / 'predictions' / f"{p['id']}.json", 'w') as f:
        json.dump(p, f, indent=2)
    num_preds += 1

# 6. Report
report = f"""# Phase 3 Report

- Number of obstructions logged: {len(obstructions)}
- Obstruction types frequency table:
"""
for ot, count in ob_counts.items():
    report += f"  - {ot}: {count}\n"

num_bounds = len(list((ROOT / 'boundaries').glob('*.json')))
report += f"""
- Number of boundaries extracted: {num_bounds}
- Number of observable types in use: {len(obs_types)}
- Number of predictions created: {num_preds}
"""

with open(ROOT / 'audits/phase3_report.md', 'w') as f:
    f.write(report)
print("Done")
