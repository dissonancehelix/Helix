import json
import re
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / '04_labs/corpus/domains/domains'
REPORT_PATH = ROOT / '07_artifacts/artifacts/measurement/densification_report.json'

def expand():
    from engines.infra.io.persistence import load_domains
    domains_with_names = load_domains(DOMAINS_DIR)
    
    report = {
        "candidate_domains": [],
        "densification_stats": {
            "total_domains": len(domains_with_names),
            "qualitative_found": 0,
            "mapped_confidence": 0,
            "to_be_instrumented": 0
        }
    }

    if not (ROOT / '07_artifacts/artifacts/measurement').exists():
        (ROOT / '07_artifacts/artifacts/measurement').mkdir(parents=True, exist_ok=True)

    for _, domain in domains_with_names:
        if not isinstance(domain, dict): continue
        
        txt = (str(domain.get('dynamics_operator', '')) + " " + 
               str(domain.get('stability_condition', '')) + " " + 
               str(domain.get('edge_conditions', ''))).lower()
        
        # Simple keyword matching for threshold proxies
        keywords = ["threshold", "limit", "critical", "margin", "exceed", "breakpoint", "saturation", "divergence"]
        found = [k for k in keywords if k in txt]
        
        if found:
            report["densification_stats"]["qualitative_found"] += 1
            
            # Check if it already has numeric metrics
            all_metrics = domain.get('observable_metrics', [])
            if not isinstance(all_metrics, list): all_metrics = []
            metrics = [m for m in all_metrics if isinstance(m, dict)]
            numeric_count = sum(1 for m in metrics if m.get('threshold_value') is not None)
            
            if numeric_count == 0:
                report["densification_stats"]["to_be_instrumented"] += 1
                report["candidate_domains"].append({
                    "id": domain.get('id', 'unknown'),
                    "found_keywords": found,
                    "current_metrics_count": len(metrics),
                    "confidence_score": 0.5 # Default heuristic
                })

    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Expansion report generated. Candidates: {report['densification_stats']['to_be_instrumented']}")

if __name__ == "__main__":
    expand()
