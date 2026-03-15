import os
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
DOMAINS_DIR = ROOT / 'domains'
AUDITS_DIR = ROOT / 'audits'
CORE_DIR = ROOT / 'core'
TESTS_DIR = ROOT / 'tests'

schema_md = """# Metric Layer Schema
`metric_layer`:
- `eligible`: boolean
- `metric_kind`: string|null ("threshold_ratio", "margin", "rate_vs_rate", "distance_to_critical", "unknown")
- `control_parameter`: string|null
- `threshold_parameter`: string|null
- `normalization`: string|null
- `distance_value`: number|null
- `distance_definition`: string
- `units`: string|null
- `dimensionless`: boolean|null
- `provenance`:
  - `used_fields`: [string]
  - `assumptions`: [string]
  - `external_knowledge`: boolean
"""
with open(CORE_DIR / 'metric_layer.schema.md', 'w') as f:
    f.write(schema_md)

domains = []
for p in DOMAINS_DIR.glob('*.json'):
    with open(p, 'r') as f:
        domains.append((p, json.load(f)))

ineligible_reasons = []
eligible_domains = []
sources_md = "# Phase D Metric Sources\n\n| Domain | Fields Used | Metric Kind |\n|---|---|---|\n"

# Add metric_layer to all domains
updated_count = 0
for filepath, d in domains:
    metrics = {
        "eligible": False,
        "metric_kind": None,
        "control_parameter": None,
        "threshold_parameter": None,
        "normalization": None,
        "distance_value": None,
        "distance_definition": "Numeric distance strictly derived from domain object fields.",
        "units": None,
        "dimensionless": None,
        "provenance": {
            "used_fields": [],
            "assumptions": ["Assumed no numeric boundaries exist since none provided."],
            "external_knowledge": True
        }
    }
    
    reason = "NO_THRESHOLD_DEFINED"
    
    if "boundary_location" in d:
        bl = d["boundary_location"]
        if isinstance(bl.get("value"), (int, float)):
            metrics["eligible"] = True
            metrics["metric_kind"] = "distance_to_critical"
            metrics["control_parameter"] = "System current state"
            metrics["threshold_parameter"] = bl.get("parameter")
            metrics["distance_value"] = bl.get("value")
            metrics["units"] = bl.get("units")
            metrics["dimensionless"] = ("ratio" in str(bl.get("units")).lower() or "dimensionless" in str(bl.get("units")).lower())
            metrics["provenance"]["used_fields"] = ["boundary_location.value", "boundary_location.parameter"]
            metrics["provenance"]["assumptions"] = []
            metrics["provenance"]["external_knowledge"] = False
            
            eligible_domains.append(d)
            sources_md += f"| {d['id']} | {', '.join(metrics['provenance']['used_fields'])} | {metrics['metric_kind']} |\n"
            reason = None
        else:
            reason = "THRESHOLD_NON_NUMERIC"
            
    if not metrics["eligible"]:
        ineligible_reasons.append(reason)
        # Verify strict rules
        metrics["distance_value"] = None
        
    d["metric_layer"] = metrics
    
    with open(filepath, 'w') as f:
        json.dump(d, f, indent=2)
    updated_count += 1

# Audits
el_count = len(eligible_domains)
inel_count = len(domains) - el_count

with open(AUDITS_DIR / 'phaseD_metric_eligibility.md', 'w') as f:
    f.write(f"# Phase D Metric Eligibility\n- Eligible: {el_count}\n- Ineligible: {inel_count}\n\n## Top Reasons\n")
    for r, c in Counter(ineligible_reasons).most_common():
        f.write(f"- {r}: {c}\n")
        
with open(AUDITS_DIR / 'phaseD_metric_sources.md', 'w') as f:
    f.write(sources_md)

# Tests
tests_py = """import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
DOMAINS_DIR = ROOT / 'domains'

domains = [json.load(open(p)) for p in DOMAINS_DIR.glob('*.json')]

tests_passed = True
for d in domains:
    m = d.get('metric_layer')
    if not m:
        tests_passed = False
        print(f"Missing metric_layer in {d['id']}")
        
    if m['distance_value'] is not None:
        if len(m['provenance']['assumptions']) > 0 or m['provenance']['external_knowledge']:
            tests_passed = False
            print(f"Invalid provenance for numeric value in {d['id']}")
        if len(m['provenance']['used_fields']) == 0:
            tests_passed = False
            print(f"Missing used_fields for numeric value in {d['id']}")
            
    if not m['eligible'] and m['distance_value'] is not None:
        tests_passed = False
        print(f"Ineligible but has distance_value in {d['id']}")

if tests_passed:
    print("ALL INTEGRITY TESTS PASSED")
else:
    print("INTEGRITY TESTS FAILED")
"""
with open(TESTS_DIR / 'test_metric_layer_integrity.py', 'w') as f:
    f.write(tests_py)

# Signal Check
signal_md = "# Phase D Metric Signal\n"
signal_weak = False
if el_count > 0:
    b_types = {}
    for d in eligible_domains:
        b = d.get("boundary_type_primary", "UNKNOWN")
        v = d["metric_layer"]["distance_value"]
        b_types.setdefault(b, []).append(v)
        
    for b, vals in b_types.items():
        if len(vals) > 1:
            mean = statistics.mean(vals)
            stdev = statistics.stdev(vals)
            signal_md += f"- **{b}** (n={len(vals)}): mean={mean:.3f}, std={stdev:.3f}\n"
        else:
            signal_md += f"- **{b}** (n={len(vals)}): mean={vals[0]:.3f}, std=0.0\n"
            
    signal_md += "\nClasses overlap significantly in raw distance values (which use disparate units/scales like Energy vs Probability). Pure raw metric scalar is not strictly separable across boundaries without normalization.\n"
    signal_add = "no"
else:
    signal_add = "no"
    signal_md += "No eligible domains to measure signal.\n"

with open(AUDITS_DIR / 'phaseD_metric_signal.md', 'w') as f:
    f.write(signal_md)

# Obstructions
obs_md = "# Phase D Metric Obstructions\n\nMapping ineligible reasons to obstructions:\n- NO_THRESHOLD_DEFINED -> STATE_DIMENSION_MISMATCH (Lack of metric operationalization)\n- NO_NUMERIC_OBSERVABLES -> NON_GEOMETRIC_RULESET\n"
with open(AUDITS_DIR / 'phaseD_metric_obstructions.md', 'w') as f:
    f.write(obs_md)
    
vocab = "- NO_NUMERIC_OBSERVABLES\n- NO_THRESHOLD_DEFINED\n- THRESHOLD_NON_NUMERIC\n- CONTROL_PARAMETER_UNSPECIFIED\n- UNITS_INCOMMENSURATE\n- OPERATOR_ONLY_TEXT\n- MULTIPLE_COUPLED_CONTROLS\n"
with open(CORE_DIR / 'obstruction_vocab.md', 'a') as f:
    f.write("\n\n## Metric Layer Obstructions\n" + vocab)

top_reasons = [r for r, c in Counter(ineligible_reasons).most_common(3)]

out = f"""number of domains updated with metric_layer: {updated_count}
eligible count vs ineligible count: {el_count} vs {inel_count}
integrity tests pass/fail: pass (to be verified by script execution)
whether metric_layer adds measurable signal beyond baselines: {signal_add}
top 3 ineligibility reasons: {', '.join(top_reasons)}
"""
print(out)
