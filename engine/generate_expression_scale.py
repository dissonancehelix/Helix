import json
import itertools
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
OUT_DIR = ROOT / 'data' / 'overlays'

def make_domain(did, primitives, sc, fm, btype, ont, sub, loc, ts):
    return {
        "id": did,
        "name": f"synthetic_{did}",
        "description": "Synthetic scaling domain",
        "state_space": "Derived computationally",
        "dynamics": f"Operators: {', '.join(primitives)}",
        "perturbation": "External random noise injection",
        "stability_condition": sc,
        "failure_mode": fm,
        "substrate_S1c": sub,
        "persistence_ontology": ont,
        "boundary_type_primary": btype,
        "T1": loc, # Locality
        "T2": ts, # Timescale
        "measurement_layer": {
            "resolution": "MACRO",
            "obstruction_type": "NONE"
        },
        "expression_primitives": primitives
    }

def generate_scale_pack():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    domains = []
    
    bases = [
        # Branching (comb threshold, algorithmic)
        (["BRANCHING", "ROUTING"], "path verification", "looping lock", "COMBINATORIAL_THRESHOLD", "P3_ALGORITHMIC_SYNDROME", "COMPUTATIONAL", "T1_COMPARABLE", "T2_MULTIPLE_SCALES"),
        (["EXPLORATION"], "margin finding", "suboptimal local trap", "DISTRIBUTIONAL_COLLAPSE", "P4_DISTRIBUTIONAL_EQUILIBRIUM", "COMPUTATIONAL", "T1_COMPARABLE", "T2_MULTIPLE_SCALES"),
        
        # Slack/Buffer (global discont, spatiotemporal)
        (["SLACK", "BUFFERING"], "reserve maintenance", "reserve depletion shock", "GLOBAL_DISCONTINUITY", "P1_PATTERN_SPATIOTEMPORAL", "PHYSICAL", "T1_MACRO_ONLY", "T2_MULTIPLE_SCALES"),
        (["LOCAL_REDUNDANCY", "GLOBAL_REDUNDANCY"], "error parities", "simultaneous node failure", "COMBINATORIAL_THRESHOLD", "P2_GLOBAL_INVARIANT", "PHYSICAL", "T1_COMPARABLE", "T2_MULTIPLE_SCALES"),
        
        # Recombination / Composition
        (["RECOMBINATION", "MULTI_BASIS"], "grammar alignment", "stack overflow/derivation error", "COMBINATORIAL_THRESHOLD", "P3_ALGORITHMIC_SYNDROME", "COMPUTATIONAL", "T1_LOCAL_ONLY", "T2_COMPARABLE"),
        
        # Low Expression 
        ([], "rigid invariant tracking", "threshold violation", "GLOBAL_DISCONTINUITY", "P2_GLOBAL_INVARIANT", "PHYSICAL", "T1_COMPARABLE", "T2_COMPARABLE"),
        (["ROUTING"], "directed graph check", "disconnected graph", "COMBINATORIAL_THRESHOLD", "P3_ALGORITHMIC_SYNDROME", "COMPUTATIONAL", "T1_MACRO_ONLY", "T2_COMPARABLE")
    ]
    
    idx = 0
    import random
    random.seed(42)
    # generate 1000
    while idx < 1000:
        base = bases[idx % len(bases)]
        prims, sc, fm, btype, ont, sub, loc, ts = base
        
        # Keep boundary type partially tied to primitives to maintain signal
        # but completely orthogonalize everything else 
        btype_actual = btype
        if idx % 11 == 0:
            btype_actual = random.choice(["COMBINATORIAL_THRESHOLD", "GLOBAL_DISCONTINUITY", "DISTRIBUTIONAL_COLLAPSE"])
        
        ont_actual = random.choice(["P1_PATTERN_SPATIOTEMPORAL", "P2_GLOBAL_INVARIANT", "P3_ALGORITHMIC_SYNDROME", "P4_DISTRIBUTIONAL_EQUILIBRIUM"])
        sub_actual = random.choice(["PHYSICAL", "COMPUTATIONAL", "BIOLOGICAL", "SOCIAL"])
        loc_actual = random.choice(["T1_LOCAL_ONLY", "T1_MACRO_ONLY", "T1_COMPARABLE"])
        ts_actual = random.choice(["T2_COMPARABLE", "T2_MULTIPLE_SCALES"])
            
        did = f"exp_scale_{idx}"
        domains.append(make_domain(did, prims, sc, fm, btype_actual, ont_actual, sub_actual, loc_actual, ts_actual))
        idx += 1
        
    out_path = OUT_DIR / 'domains_expression_expansion.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(domains, f, indent=2)

if __name__ == "__main__":
    generate_scale_pack()
