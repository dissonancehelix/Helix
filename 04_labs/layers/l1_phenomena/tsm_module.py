import json
import os
import random
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
ART_DIR = ROOT / '07_artifacts/artifacts'
DOCS_DIR = ROOT / 'docs'

def save_wrapped(path, data):
    from engines.infra.io import persistence as m_io; from engines.infra.platform import environment as m_env
    m_io.save_wrapped(path, data)

def extract_tsm(domains):
    results = []
    
    for _, d in domains:
        flat_txt = json.dumps(d).lower()
        fm = d.get('failure_mode', '').lower()
        sc = d.get('stability_condition', '').lower()
        obs_origin = d.get('measurement_layer', {}).get('obstruction_type', '')

        # Defs
        trace_k = "UNKNOWN"
        commit_k = "UNKNOWN"
        ctrl_k = "UNKNOWN"
        
        # TRACE
        if any(w in flat_txt for w in ['model memory', 'internal model', 'q-table']):
            trace_k = "MODEL_MEMORY"
        elif any(w in flat_txt for w in ['external_memory', 'external memory', 'ledger']):
            trace_k = "EXTERNAL_MEMORY"
        elif any(w in flat_txt for w in ['hysteretic', 'plasticity', 'scarring']):
            trace_k = "HYSTERETIC"
        elif any(w in flat_txt for w in ['accumulat', 'integral', 'trace', 'memory']):
            trace_k = "ACCUMULATOR"
        elif any(w in flat_txt for w in ['markov', 'memoryless', 'instantaneous']):
            trace_k = "MARKOV"
            
        # COMMITMENT
        if any(w in fm or w in sc for w in ['absorbing state', 'behavioral sink']):
            commit_k = "ABSORBING_STATE"
        elif any(w in fm or w in sc for w in ['latched', 'latch', 'irreversible decision', 'commitment']):
            commit_k = "LATCHED_DECISION"
        elif any(w in fm or w in sc for w in ['hysteresis loop', 'irreversible lock-in']):
            commit_k = "HYSTERESIS_LOOP"
        elif any(w in fm or w in sc for w in ['rule change', 'regime change', 'structural change']):
            commit_k = "IRREVERSIBLE_RULE_CHANGE"
        elif any(w in flat_txt for w in ['external lockin', 'sunk cost']):
            commit_k = "EXTERNAL_LOCKIN"
        else:
            if trace_k == "MARKOV" or ("reversible" in flat_txt and commit_k == "UNKNOWN"):
                commit_k = "NONE"

        # CONTROL
        if any(w in sc or w in flat_txt for w in ['homeostatic', 'setpoint', 'pid', 'pi control', 'correction loop']):
            ctrl_k = "HOMEOSTATIC"
        elif any(w in sc or w in flat_txt for w in ['adaptive', 'learning', 'update', 'regret']):
            ctrl_k = "ADAPTIVE"
        elif any(w in sc or w in flat_txt for w in ['arbitration', 'active inference']):
            ctrl_k = "ARBITRATION"
        else:
            if trace_k == "UNKNOWN" and commit_k == "UNKNOWN":
                ctrl_k = "NONE"

        # CLASS
        has_trace = trace_k not in ["UNKNOWN", "MARKOV", "NONE"]
        has_commit = commit_k not in ["UNKNOWN", "NONE"]
        has_ctrl = ctrl_k not in ["UNKNOWN", "NONE"]
        
        if has_trace and has_commit and has_ctrl:
            tsm_class = "TRACE+COMMIT+CONTROL"
        elif has_trace and has_commit:
            tsm_class = "TRACE+COMMIT"
        elif has_trace and not has_commit and not has_ctrl:
            tsm_class = "TRACE_ONLY"
        elif not has_trace and has_commit and not has_ctrl:
            tsm_class = "COMMIT_ONLY"
        elif not has_trace and not has_commit and not has_ctrl:
            tsm_class = "NONE"
        else:
            tsm_class = "NONE"
            
        tsm_status = "DEFINED" if tsm_class != "NONE" else "UNDEFINED"
        
        obstruction = None
        if tsm_status == "UNDEFINED":
            if "coupled" in flat_txt: obstruction = "MULTIPLE_COUPLED_STATE_SPACES"
            elif trace_k == "EXTERNAL_MEMORY": obstruction = "EXTERNALIZED_STATE"
            elif "ambiguous" in sc: obstruction = "AMBIGUOUS_CONTROL_LOOP"
            elif obs_origin == "UNITS_NOT_PROJECTABLE": obstruction = "UNITS_NOT_PROJECTABLE"
            elif "witness" not in flat_txt and tsm_class == "NONE": obstruction = "WITNESS_ABSENT"
            else: obstruction = "SCHEMA_INSUFFICIENT"
            
        results.append({
            "domain_id": d.get("id", "unknown"),
            "tsm_status": tsm_status,
            "tsm_class": tsm_class,
            "trace_kind": trace_k,
            "commitment_kind": commit_k,
            "control_kind": ctrl_k,
            "obstruction": obstruction,
            "provenance": ["categorical_witness"] if tsm_status == "DEFINED" else []
        })

    summary = {
        "coverage_percent": round((sum(1 for r in results if r['tsm_status'] == 'DEFINED') / len(results) * 100) if results else 0, 2),
        "total": len(domains),
        "defined": sum(1 for r in results if r['tsm_status'] == 'DEFINED'),
        "undefined": sum(1 for r in results if r['tsm_status'] == 'UNDEFINED'),
        "distribution": dict(Counter([r['tsm_class'] for r in results])),
        "obstructions": dict(Counter([r['obstruction'] for r in results if r['obstruction']]))
    }
    
    final_output = {
        "summary": summary,
        "detail": results
    }
    
    save_wrapped(ART_DIR / 'tsm/tsm_overlay.json', final_output)
    
    # Generate MD report
    report_md = f"""Derived From:
- /artifacts/tsm/tsm_overlay.json
- /artifacts/run_manifest.json (dataset_hash: {os.environ.get('HELIX_DATASET_HASH', 'unknown')})

# TSM Overlay Report (Trajectory Stabilization Mechanism)

## Coverage & Overview
This atlas measures the emergence of state retention (memory), internal state commitments, and feedback control loops across domains.

**Coverage:** {summary['coverage_percent']}% ({summary['defined']} / {summary['total']} domains)

## Structural Breakdown
| TSM Class | Count |
| --- | --- |
"""
    for cls, count in summary['distribution'].items():
        report_md += f"| {cls} | {count} |\n"

    report_md += "\n## Obstruction Distribution\n| Type | Count |\n| --- | --- |\n"
    for obs, count in summary['obstructions'].items():
        report_md += f"| {obs} | {count} |\n"

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DOCS_DIR / 'tsm_overlay_report.md', 'w', encoding='utf-8') as f:
        f.write(report_md)
        
    return results

if __name__ == "__main__":
    from engines.infra.io import persistence as m_io; from engines.infra.platform import environment as m_env
    m_env.init_random(42)
    ext_domains = m_io.load_domains()
    extract_tsm(ext_domains)
