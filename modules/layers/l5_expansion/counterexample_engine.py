import json
import random
import os
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'data/domains'
FALSIFIERS_PACK = ROOT / 'data/packs/counterexamples/domains'
ARTIFACT_DIR = ROOT / 'artifacts/counterexamples'

def mutate():
    if not ARTIFACT_DIR.exists(): ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if not FALSIFIERS_PACK.exists(): FALSIFIERS_PACK.mkdir(parents=True, exist_ok=True)

    mutation_matrix = []
    
    # Structural Mutation Operators
    def op_remove_feedback(d):
        d['dynamics_operator'] = d.get('dynamics_operator', '').replace('feedback', 'feedforward')
        d['stability_condition'] = d.get('stability_condition', '').replace('restoring', 'damped')
        return d, "remove_feedback"
        
    def op_linearize(d):
        d['dynamics_operator'] = d.get('dynamics_operator', '') + " (Linearized approximation applied)"
        return d, "linearize"
        
    def op_alter_locality(d):
        d['boundary_locality'] = "GLOBAL" if d.get('boundary_locality') == "LOCAL" else "LOCAL"
        return d, "alter_locality"

    mutation_ops = [op_remove_feedback, op_linearize, op_alter_locality]
    
    # Sampling domains for mutation
    domains = [p for p in DOMAINS_DIR.glob('*.json') if not p.name.startswith('phase')]
    sample_size = min(len(domains), 10) # Bounded
    
    for d_path in random.sample(domains, sample_size):
        with open(d_path, 'r') as f:
            try:
                base = json.load(f)
            except: continue
            
            # Create a mutation
            mutator = random.choice(mutation_ops)
            mutated, op_name = mutator(base.copy())
            
            mid = f"mutant_{op_name}_{base['id']}"
            mutated['id'] = mid
            mutated['parent_id'] = base['id']
            mutated['mutation_operation'] = op_name
            
            with open(FALSIFIERS_PACK / f"{mid}.json", 'w') as f:
                json.dump(mutated, f, indent=2)
                
            mutation_matrix.append({
                "original": base['id'],
                "operation": op_name,
                "mutant_id": mid,
                "edit_distance": 1 # Atomic
            })

    with open(ARTIFACT_DIR / 'mutation_matrix.json', 'w') as f:
        json.dump(mutation_matrix, f, indent=2)
        
    # Placeholder for docs update
    with open(ROOT / 'docs/counterexample_falsifiers.md', 'w') as f:
        f.write("# Counterexample Falsifiers\n\nAutomatically generated mutations of base domains to detect structural collapse flips.\n\n")
        for m in mutation_matrix:
            f.write(f"- Mutant `{m['mutant_id']}` derived from `{m['original']}` via `{m['operation']}`.\n")

    print(f"Generated {len(mutation_matrix)} counterexamples.")

if __name__ == "__main__":
    mutate()
