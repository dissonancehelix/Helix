import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def print_status():
    atlas_index = ROOT / 'codex/atlas' / 'index.json'
    violation_log = ROOT / 'execution/artifacts' / 'artifacts' / 'substrate_violation_log.json'
    
    total_experiments = 0
    mean_pss = 0.0
    mean_bas = 0.0
    bic_count = 0
    rdc_count = 0
    last_failure = "None"
    
    if atlas_index.exists():
        try:
            with open(atlas_index, 'r') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                total_experiments = len(data)
                
                sum_pss, sum_bas = 0, 0
                for d in data:
                    sum_pss += d.get("PSS", 0)
                    sum_bas += d.get("BAS", 0)
                    cls = d.get("classification", "")
                    if cls == "BIC": bic_count += 1
                    elif cls == "RDC": rdc_count += 1
                    
                    if d.get("fragility_gradient", 0) > 0.5:
                        last_failure = f"{d.get('domain', 'unknown')} at {d.get('timestamp', '')}"
                        
                if total_experiments > 0:
                    mean_pss = sum_pss / total_experiments
                    mean_bas = sum_bas / total_experiments
        except:
            pass
            
    violation_count = 0
    if violation_log.exists():
        try:
            with open(violation_log, 'r') as f:
                vdata = json.load(f)
                violation_count = len(vdata)
        except:
            pass

    print("============================================================")
    print("HELIX RUNTIME STATUS DASHBOARD")
    print("============================================================")
    print(f"Total experiments: {total_experiments}")
    print(f"Stability distribution: Mean PSS = {mean_pss:.4f}, Mean BAS = {mean_bas:.4f}")
    if total_experiments > 0:
        print(f"BIC vs RDC count: {bic_count} BIC / {rdc_count} RDC")
    else:
        print("BIC vs RDC count: 0 BIC / 0 RDC")
    print(f"Last hostility failure: {last_failure}")
    print(f"Active isolates count: 0") # Hardcoded for now unless domain_data counted
    print(f"Substrate violation count: {violation_count}")
    print(f"Drift summary: {'Clear' if violation_count == 0 else 'Compromised'}")
    print("============================================================")

if __name__ == '__main__':
    print_status()
