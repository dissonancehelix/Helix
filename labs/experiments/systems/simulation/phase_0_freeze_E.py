import os
import json
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT
import statistics

ROOT = REPO_ROOT
META_DIR = ROOT / 'execution/artifacts' / '_meta'
POOL_PATH = ROOT / 'execution/artifacts' / 'srd_replication' / '_pool' / 'srd_global_pool.json'
LEDGER_PATH = META_DIR / 'curiosity_ledger.json'
RRS_DIR = ROOT / 'execution/artifacts' / 'rrs'

def safe_load(p):
    if p.exists():
        with open(p, 'r') as f:
            return json.load(f)
    return {}

def main():
    ledger = safe_load(LEDGER_PATH)
    pool = safe_load(POOL_PATH)
    
    twin_deltas = []
    confidences = []
    blindspot_densities = []
    
    total_runs = 0
    pool_ingested = 0
    
    for repo_dir in RRS_DIR.iterdir():
        if not repo_dir.is_dir() or repo_dir.name in ['stress', 'external_batch']: continue
        for run_dir in repo_dir.iterdir():
            if not run_dir.is_dir(): continue
            total_runs += 1
            
            integrity = safe_load(run_dir / 'integrity.json')
            sensitivity = safe_load(run_dir / 'sensitivity.json')
            confidence = safe_load(run_dir / 'confidence.json')
            blindspots = safe_load(run_dir / 'blindspots.json')
            
            if sensitivity:
                twin_deltas.append(sensitivity.get('twin_delta', 0))
            if confidence:
                confidences.append(confidence.get('composite_confidence_score', 0))
                
            report = safe_load(run_dir / 'risk_report.json')
            nodes = report.get('total_nodes_analyzed', 100) if report else 100
            
            if blindspots:
                cnt = sum([1 for v in blindspots.values() if isinstance(v, (int, float)) and v > 0])
                cnt += len(blindspots.get("witness_absent_flags", []))
                blindspot_densities.append(cnt / max(1, nodes))
                
            if integrity.get("admissibility_status") == "TRUSTED":
                if sensitivity.get("feedback_insensitivity_flag") is False:
                    if confidence.get("composite_confidence_score", 0) >= 0.8:
                        pool_ingested += 1

    drift_vol = 0
    if ledger:
        drift_vol = statistics.mean([v.get('drift_score', 0) for v in ledger.values()])
        
    snap = {
        "beta_coefficients": {"beta1": 0.05, "beta2": 1.2, "beta3": 0.3},
        "blindspot_weight": 0.5,
        "admissibility_thresholds": {"missingness_pct": 0.1, "parse_error_count": 100},
        "pool_ingestion_gates": ["TRUSTED", "twin_pass", "confidence_0.8"],
        "mutation_intensity_bounds": [0.05, 0.30],
        "composite_confidence": {
            "mean": statistics.mean(confidences) if confidences else 0,
            "min": min(confidences) if confidences else 0,
            "max": max(confidences) if confidences else 0
        },
        "twin_delta": {
            "mean": statistics.mean(twin_deltas) if twin_deltas else 0,
            "min": min(twin_deltas) if twin_deltas else 0,
            "max": max(twin_deltas) if twin_deltas else 0
        },
        "blindspot_density": {
            "mean": statistics.mean(blindspot_densities) if blindspot_densities else 0,
            "max": max(blindspot_densities) if blindspot_densities else 0
        },
        "pool_ingestion_rate": pool_ingested / max(1, total_runs),
        "drift_volatility": drift_vol
    }
    
    META_DIR.mkdir(parents=True, exist_ok=True)
    with open(META_DIR / 'pre_batch_E_snapshot.json', 'w') as f:
        json.dump(snap, f, indent=4)
        
    print("Pre-batch E snapshot saved.")

if __name__ == '__main__':
    main()
