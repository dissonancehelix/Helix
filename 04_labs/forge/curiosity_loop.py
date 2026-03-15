import os
import json
from pathlib import Path
from datetime import datetime

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
RRS_ARTIFACTS = ROOT / '07_artifacts' / 'rrs'
META_DIR = ROOT / '07_artifacts' / '_meta'
META_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_PATH = META_DIR / 'curiosity_ledger.json'
PROPOSED_PATH = META_DIR / 'proposed_experiments.json'

def load_json_safe(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_curiosity_loop():
    ledger = load_json_safe(LEDGER_PATH)
    
    proposed_experiments = []
    
    # Iterate through all RRS runs
    if not RRS_ARTIFACTS.exists():
        print("No RRS artifacts found.")
        return
        
    for repo_dir in RRS_ARTIFACTS.iterdir():
        if not repo_dir.is_dir() or repo_dir.name == 'stress': continue
        repo = repo_dir.name
        
        # In a real situation, would aggregate or pick latest run
        # but here we just process all run_ids
        for run_dir in repo_dir.iterdir():
            if not run_dir.is_dir(): continue
            
            integrity = load_json_safe(run_dir / 'integrity.json')
            sensitivity = load_json_safe(run_dir / 'sensitivity.json')
            stability = load_json_safe(run_dir / 'stability.json')
            blindspots = load_json_safe(run_dir / 'blindspots.json')
            confidence = load_json_safe(run_dir / 'confidence.json')
            risk_report = load_json_safe(run_dir / 'risk_report.json')
            
            if not integrity or not confidence: continue
            
            # Extract features for self-correction & ledger
            missingness = integrity.get("missingness_pct", 0)
            twin_delta = sensitivity.get("twin_delta", 0)
            node_count = risk_report.get("total_nodes_analyzed", 100)
            
            blindspot_count = sum([1 for x in blindspots.values() if isinstance(x, (int, float)) and x > 0]) + len(blindspots.get("witness_absent_flags", []))
            b_density = blindspot_count / max(1, node_count)
            
            beta_cv = max(stability.get("coefficient_drift", {}).values()) if stability.get("coefficient_drift") else 0
            
            # --- SELF-CORRECTION RULES (MECHANICAL) ---
            downgraded = False
            correction_events = []
            
            if missingness > 0.10:
                correction_events.append("downgraded confidence due to missingness > 0.10")
                downgraded = True
                
            if twin_delta < 0.001:
                correction_events.append("FEEDBACK_INSENSITIVITY marked. Needs stronger mutation.")
                
            if beta_cv > 0.15:
                correction_events.append("CV Threshold breached. Fork normalizer / require holdout.")
                
            # Compute Curiosity uncertainty metrics
            uncertainty = (sensitivity.get("null_variance", 0) * 0.1) + twin_delta + beta_cv
            
            run_lbl = f"{repo}_GSSD_Core"
            entry = ledger.get(run_lbl, {})
            entry["uncertainty_score"] = round(uncertainty, 4)
            entry["drift_score"] = round(beta_cv, 4)
            entry["falsifier_pressure_index"] = len(correction_events)
            entry["blindspot_density"] = round(b_density, 4)
            entry["last_tested_timestamp"] = datetime.utcnow().isoformat() + "Z"
            entry["last_mutation_intensity"] = 0.05
            entry["confidence_trend"] = "DOWNGRADED" if downgraded else "STABLE"
            
            ledger[run_lbl] = entry
            
            # Generate proposals based on uncertainty
            if twin_delta < 0.001:
                proposed_experiments.append({
                    "id": f"EXP_A_{repo}",
                    "type": "Increase mutation intensity",
                    "target": repo,
                    "expected_uncertainty_reduction": round(0.5, 4),
                    "estimated_compute_cost": "LOW",
                    "reason": "Feedback insensitivity recorded. Must verify if boundary is rigid or mapping is numb."
                })
            
            if beta_cv > 0.15:
                proposed_experiments.append({
                    "id": f"EXP_E_{repo}",
                    "type": "Holdout retest",
                    "target": repo,
                    "expected_uncertainty_reduction": round(0.8, 4),
                    "estimated_compute_cost": "HIGH",
                    "reason": "High drift volatility. Coefficient stability unverified."
                })
                
            if b_density > 0.05:
                proposed_experiments.append({
                    "id": f"EXP_C_{repo}",
                    "type": "Blindspot densification probe",
                    "target": repo,
                    "expected_uncertainty_reduction": round(0.4, 4),
                    "estimated_compute_cost": "MEDIUM",
                    "reason": "Unobservable elements (dead code, reflection) high. Need explicit trace mappings."
                })

    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, indent=4)
        
    # Rank candidates by hypothetical EUR / Cost mapping (High -> 3, Med -> 2, Low -> 1)
    def cost_val(c):
        return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(c, 2)
        
    proposed_experiments.sort(key=lambda x: x["expected_uncertainty_reduction"] / cost_val(x["estimated_compute_cost"]), reverse=True)
    
    top_5 = proposed_experiments[:5]
    with open(PROPOSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(top_5, f, indent=4)
        
    print(f"Curiosity Loop completed. Updated Ledger and Proposed {len(top_5)} Experiments. Awaiting human approval.")

if __name__ == '__main__':
    run_curiosity_loop()
