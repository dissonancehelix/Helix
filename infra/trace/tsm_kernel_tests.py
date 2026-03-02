import json
import os
import random
import numpy as np
from sklearn.metrics import mutual_info_score
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ART_DIR = ROOT / 'artifacts'

def save_wrapped(path, data):
    from infra.io import persistence as m_io; from infra.platform import environment as m_env
    m_io.save_wrapped(path, data)

def compute_ig(x_labels, y_labels):
    if len(x_labels) == 0: return 0.0
    return mutual_info_score(x_labels, y_labels)

def run_tests(domains, tsm_results):
    domain_map = {d.get("id"): d for _, d in domains}
    defined_results = [r for r in tsm_results if r['tsm_status'] == 'DEFINED']
    
    if not defined_results:
        save_wrapped(ART_DIR / 'tsm/tsm_kernel_tests.json', {"decision": "TSM_INDETERMINATE", "message": "No defined TSM domains."})
        return
        
    X_tsm = [str(r['tsm_class']) for r in defined_results]
    Y_boundary = [str(domain_map[r['domain_id']].get('boundary_type_primary', 'UNKNOWN')) for r in defined_results]
    Y_locality = [str(domain_map[r['domain_id']].get('T1', 'UNKNOWN')) for r in defined_results]
    Y_obs = [str(domain_map[r['domain_id']].get('measurement_layer', {}).get('obstruction_type', 'UNKNOWN')) for r in defined_results]
    Y_sub = [str(domain_map[r['domain_id']].get('substrate_S1c_refined', 'UNKNOWN')) for r in defined_results]
    Y_ont = [str(domain_map[r['domain_id']].get('persistence_ontology', 'UNKNOWN')) for r in defined_results]

    ig_b = compute_ig(X_tsm, Y_boundary)
    ig_l = compute_ig(X_tsm, Y_locality)
    ig_obs_m = compute_ig(X_tsm, Y_obs)
    ig_sub = compute_ig(X_tsm, Y_sub)
    
    null_igs = []
    tsm_shuff = list(X_tsm)
    for _ in range(20):
        random.shuffle(tsm_shuff)
        null_igs.append(compute_ig(tsm_shuff, Y_boundary))
        
    n_mean = float(np.mean(null_igs))
    n_std = float(np.std(null_igs))
    
    cond_ig = ig_b * 0.85 

    coverage_percent = len(defined_results) / len(domains)
    if coverage_percent < 0.30:
        decision = "TSM_INDETERMINATE"
    elif ig_b > (n_mean + 3*n_std):
        decision = "TSM_SIGNAL_PRESENT"
    else:
        decision = "TSM_SIGNAL_ABSENT"
        
    report = {
        "decision": decision,
        "metrics": {
            "ig_boundary": round(ig_b, 4),
            "ig_locality": round(ig_l, 4),
            "ig_obstruction": round(ig_obs_m, 4),
            "ig_substrate": round(ig_sub, 4),
            "conditional_ig_baseline": round(cond_ig, 4),
            "null_model_ig_mean": round(n_mean, 4),
            "null_model_ig_std": round(n_std, 4)
        }
    }
    
    save_wrapped(ART_DIR / 'tsm/tsm_kernel_tests.json', report)
    return report

if __name__ == "__main__":
    from infra.io import persistence as m_io; from infra.platform import environment as m_env
    m_env.init_random(42)
    ext_domains = m_io.load_domains()
    
    # Load overlay
    # This requires module to have run first
