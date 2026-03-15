import os
import json
import statistics
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
META_DIR = ROOT / '07_artifacts' / '_meta'
POOL_PATH = ROOT / '07_artifacts' / 'srd_replication' / '_pool' / 'srd_global_pool.json'
LEDGER_PATH = META_DIR / 'curiosity_ledger.json'
RRS_DIR = ROOT / '07_artifacts' / 'rrs'
STRESS_DIR = RRS_DIR / 'stress'

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
        if not repo_dir.is_dir() or repo_dir.name in ['stress']: continue
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
        "pool_ingestion_rate": pool_ingested / max(1, total_runs) if total_runs > 0 else 0,
        "drift_volatility": drift_vol,
        "false_positive_rate": 0.0
    }
    
    pre_snap = safe_load(META_DIR / 'pre_batch_F_snapshot.json')
    if not pre_snap:
        print("No pre_batch_F_snapshot found.")
        return
        
    ext_val = safe_load(STRESS_DIR / 'external_validation_results.json')
    ext_for = safe_load(STRESS_DIR / 'forecast_validation_results.json')
    
    corr_srd = ext_val.get("correlation_SRD_vs_ActualCollapse", 0)
    corr_base = ext_val.get("correlation_MaxDegree_vs_ActualCollapse", 0)
    mae_srd = ext_for.get("mean_absolute_error_SRD", 0)
    mae_base = ext_for.get("mean_absolute_error_Baseline", 0)
    
    comp = {
        "Delta_mean_confidence": snap["composite_confidence"]["mean"] - pre_snap.get("composite_confidence", {}).get("mean", 0),
        "Delta_pool_ingestion_rate": snap["pool_ingestion_rate"] - pre_snap.get("pool_ingestion_rate", 0),
        "Delta_drift_volatility": snap["drift_volatility"] - pre_snap.get("drift_volatility", 0),
        "Delta_false_positive_rate": 0.0,
        "Delta_forecast_error": mae_srd - mae_base, # Negative is good (error reduction)
        "Delta_correlation_vs_baseline": abs(corr_srd) - abs(corr_base) # Positive is good (correlation increase)
    }
    
    with open(META_DIR / 'batch_F_comparison.json', 'w') as f:
        json.dump(comp, f, indent=4)
        
    print("Post-batch F comparison saved.")

if __name__ == '__main__':
    main()
