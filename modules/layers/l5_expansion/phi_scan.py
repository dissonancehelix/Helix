import json
from pathlib import Path
import numpy as np

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'data'
PHI = 1.61803398875
INV_PHI = 0.61803398875
TOLERANCE = 0.05 # For fuzzy matching in qualititative-derived numbers

def phi_search():
    print("Searching for Phase 27-29 φ artifact in all domain data...")
    
    matches = []
    
    for p in DOMAINS_DIR.rglob('*.json'):
        if p.name.startswith('phase'): continue
        with open(p, 'r') as f:
            try:
                d = json.load(f)
                metrics = d.get('observable_metrics', [])
                for m in metrics:
                    if not isinstance(m, dict): continue
                    v = m.get('value')
                    try:
                        f_v = float(v)
                        # Check PHI or its components
                        if abs(f_v - PHI) < TOLERANCE or abs(f_v - INV_PHI) < TOLERANCE or abs(f_v - 0.382) < TOLERANCE:
                            matches.append({
                                "id": d.get('id'),
                                "metric": m.get('name'),
                                "value": f_v,
                                "type": "RATIO_APPROXIMATION"
                            })
                    except: continue
            except: continue
            
    print(f"Found {len(matches)} potential φ artifacts.")
    
    with open(ROOT / 'artifacts/phi_artifact_scan.json', 'w') as f:
        json.dump(matches, f, indent=2)

if __name__ == "__main__":
    phi_search()
