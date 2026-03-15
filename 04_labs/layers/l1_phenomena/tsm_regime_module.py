import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
ART_DIR = ROOT / '07_artifacts/artifacts'
PACK_DIR = ROOT / 'data' / 'domains_identity_pack'

def save_wrapped(path, data):
    from engines.infra.io import persistence as m_io; from engines.infra.platform import environment as m_env
    m_io.save_wrapped(path, data)

def extract_regime(domains):
    results = []
    
    for _, d in domains:
        flat_txt = json.dumps(d).lower()
        fm = d.get('failure_mode', '').lower()
        sc = d.get('stability_condition', '').lower()
        
        # persistence_regime
        regime = "UNDEFINED"
        prov = []
        if any(w in sc or w in fm for w in ['homeostatic', 'correction', 'maintenance', 'clearance', 'setpoint']):
            regime = "PERSISTS"
            prov.append('stability_condition')
        elif any(w in fm for w in ['drift', 'degrade', 'washout', 'forgetting', 'relapse', 'weakens']):
            regime = "DRIFTS"
            prov.append('failure_mode')
        elif any(w in fm for w in ['latch', 'irreversible', 'regime change', 'reorg', 'lock']):
            regime = "FLIPS"
            prov.append('failure_mode')
        elif any(w in fm for w in ['divergence', 'explosion', 'overload', 'shock', 'catastrophic', 'collapse', 'conflict', 'oscillation']):
            regime = "SHATTERS"
            prov.append('failure_mode')
            
        # If still undefined, fallback based on keywords
        if regime == "UNDEFINED":
            if "stable" in sc: regime = "PERSISTS"
            elif "sink" in fm: regime = "FLIPS"
            elif "diverge" in fm: regime = "SHATTERS"
            else:
                regime = "UNDEFINED"
                
        # trace_location
        trace_loc = "UNKNOWN"
        state = d.get('state_space', '').lower()
        if any(w in flat_txt for w in ['external_memory', 'external memory', 'ledger', 'environment', 'case law']):
            trace_loc = "EXTERNALIZED"
        elif any(w in flat_txt for w in ['internal', 'synaptic', 'q-table', 'receptor', 'b-cell', 'model']):
            trace_loc = "INTERNAL"
        else:
            trace_loc = "UNKNOWN"
            
        results.append({
            "domain_id": d.get("id"),
            "persistence_regime": regime,
            "trace_location": trace_loc,
            "provenance": prov if regime != "UNDEFINED" else []
        })
        
    summary = {
        "total": len(domains),
        "defined": sum(1 for r in results if r['persistence_regime'] != 'UNDEFINED'),
        "regime_distribution": dict(Counter([r['persistence_regime'] for r in results])),
        "trace_location_distribution": dict(Counter([r['trace_location'] for r in results]))
    }
    
    final_output = {
        "summary": summary,
        "detail": results
    }
    
    save_wrapped(ART_DIR / 'tsm/persistence_regime_overlay.json', final_output)
    return results

if __name__ == "__main__":
    pass
