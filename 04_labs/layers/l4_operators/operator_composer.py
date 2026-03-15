import json
import re
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
DOMAINS_DIR = ROOT / '04_labs/corpus/domains/domains'
ARTIFACT_DIR = ROOT / '07_artifacts/artifacts/operator_algebra'

def compose():
    from engines.infra.io.persistence import load_domains
    if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Normalized operator tokens
    # This is a proxy for the formal composition system
    structural_tokens = ["sequential", "parallel", "nested", "feedback", "feedforward", "coupled", "decoupled"]
    dynamics_tokens = ["additive", "multiplicative", "local", "global", "convolutional", "recurrent"]
    
    motifs = []
    domains_with_names = load_domains(DOMAINS_DIR)
    
    for _, domain in domains_with_names:
        if not isinstance(domain, dict): continue
        
        txt = (str(domain.get('dynamics_operator', '')) + " " + 
               str(domain.get('perturbation_operator', '')) + " " + 
               str(domain.get('stability_condition', ''))).lower()
        
        found_struct = [t for t in structural_tokens if t in txt]
        found_dyn = [t for t in dynamics_tokens if t in txt]
        
        if found_struct or found_dyn:
            motifs.append({
                "id": domain.get('id', 'unknown'),
                "structural_motifs": found_struct,
                "dynamics_motifs": found_dyn,
                "composition_type": "SEQUENTIAL" if "sequential" in found_struct else "NESTED" if "nested" in found_struct else "UNKNOWN"
            })

    with open(ARTIFACT_DIR / 'operator_motifs.json', 'w') as f:
        json.dump(motifs, f, indent=2)
        
    print(f"Extracted operator motifs from {len(motifs)} domains.")

if __name__ == "__main__":
    compose()
