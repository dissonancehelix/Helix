"""
Regime Detection — 03_engines/analysis/regime_detection.py

Detects parameter bounds where signals reliably emerge or collapse.
"""

def detect_regimes(results: list, probes: list, param_keys: list):
    regimes = {}
    for probe in probes:
        passed_runs = [r for r in results if r['probe_name'] == probe and r['passed']]
        failed_runs = [r for r in results if r['probe_name'] == probe and not r['passed']]
        
        probe_regimes = {}
        for key in param_keys:
            if not passed_runs:
                probe_regimes[key] = "Never detected"
                continue
            
            min_pass = min(r['parameters'][key] for r in passed_runs)
            max_pass = max(r['parameters'][key] for r in passed_runs)
            
            if failed_runs:
                probe_regimes[key] = f"Range: {min_pass} -> {max_pass}"
            else:
                probe_regimes[key] = "Always detected (all ranges)"
        
        regimes[probe] = probe_regimes
        
    import os, json
    out_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '07_artifacts', 'regime_map.json')
    try:
        with open(out_path, 'w') as f:
            json.dump(regimes, f, indent=4)
    except Exception:
        pass
        
    return regimes
