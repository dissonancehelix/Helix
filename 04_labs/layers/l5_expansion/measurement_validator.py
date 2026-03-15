import json
import os
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / '04_labs/corpus/domains/domains'
REGISTRY_PATH = ROOT / 'core/measurement/projection_registry.json'
REPORT_PATH = ROOT / '07_artifacts/artifacts/measurement/leakage_report.json'

def validate():
    if not REGISTRY_PATH.exists():
        print("Registry missing.")
        return

    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)
    valid_ids = {p['id'] for p in registry['projectors']}

    report = {
        "total_domains": 0,
        "total_metrics": 0,
        "valid_metrics": 0,
        "invalid_metrics": 0,
        "failures": []
    }

    if not os.path.exists(ROOT / '07_artifacts/artifacts/measurement'):
        os.makedirs(ROOT / '07_artifacts/artifacts/measurement')

    for p in DOMAINS_DIR.glob('*.json'):
        report["total_domains"] += 1
        with open(p, 'r') as f:
            try:
                domain = json.load(f)
            except: continue
            
            metrics = domain.get('observable_metrics', [])
            if not isinstance(metrics, list): continue
            for m in metrics:
                if not isinstance(m, dict): continue
                report["total_metrics"] += 1
                p_id = m.get('projection_operator_id')
                
                # Check for unit leakage (simple proxy: units must be None if p_id is set)
                # Or if p_id is missing but threshold_value exists
                t_val = m.get('threshold_value')
                
                if t_val is not None:
                    if not p_id:
                        report["invalid_metrics"] += 1
                        report["failures"].append({
                            "domain": domain['id'],
                            "metric": m['name'],
                            "reason": "THRESHOLD_WITHOUT_PROJECTION"
                        })
                    elif p_id not in valid_ids:
                        report["invalid_metrics"] += 1
                        report["failures"].append({
                            "domain": domain['id'],
                            "metric": m['name'],
                            "reason": f"INVALID_PROJECTION_ID: {p_id}"
                        })
                    else:
                        report["valid_metrics"] += 1
                else:
                    # Metric defined but no numeric threshold
                    pass

    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Validated {report['total_metrics']} metrics. Failures: {report['invalid_metrics']}")

if __name__ == "__main__":
    validate()
