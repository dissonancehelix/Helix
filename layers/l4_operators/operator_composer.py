import json
import re
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'data/domains'
ARTIFACT_DIR = ROOT / 'artifacts/operator_algebra'

def compose():
    if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Normalized operator tokens
    # This is a proxy for the formal composition system
    structural_tokens = ["sequential", "parallel", "nested", "feedback", "feedforward", "coupled", "decoupled"]
    dynamics_tokens = ["additive", "multiplicative", "local", "global", "convolutional", "recurrent"]
    
    motifs = []
    for p in DOMAINS_DIR.glob('*.json'):
        with open(p, 'r') as f:
            try:
                domain = json.load(f)
            except: continue
            
            txt = (str(domain.get('dynamics_operator', '')) + " " + 
                   str(domain.get('perturbation_operator', '')) + " " + 
                   str(domain.get('stability_condition', ''))).lower()
            
            found_struct = [t for t in structural_tokens if t in txt]
            found_dyn = [t for t in dynamics_tokens if t in txt]
            
            if found_struct or found_dyn:
                motifs.append({
                    "id": domain['id'],
                    "structural_motifs": found_struct,
                    "dynamics_motifs": found_dyn,
                    "composition_type": "SEQUENTIAL" if "sequential" in found_struct else "NESTED" if "nested" in found_struct else "UNKNOWN"
                })

    with open(ARTIFACT_DIR / 'operator_motifs.json', 'w') as f:
        json.dump(motifs, f, indent=2)
        
    print(f"Extracted operator motifs from {len(motifs)} domains.")

if __name__ == "__main__":
    compose()
