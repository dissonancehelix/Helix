import json
import random
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
OUTPUT_FILE = ROOT / '04_labs/corpus/domains/domains_extreme_expansion.json'

REGIMES = [
    "High-dimensional continuous systems",
    "Purely symbolic / combinatorial systems",
    "Social / institutional collapse",
    "Ecological cascades",
    "Neural / cognitive models",
    "Pathological adversarial constructions"
]

BOUNDARY_TYPES = [
    "SMOOTH_HYPERSURFACE",
    "COMBINATORIAL_THRESHOLD",
    "NETWORK_CASCADE",
    "STOCHASTIC_JUMP",
    "GLOBAL_DISCONTINUITY"
]

ONTOLOGIES = [
    "P0_STATE_LOCAL",
    "P1_STRUCTURAL_INVARIANT",
    "P2_TOPOLOGICAL_BASIN",
    "P3_INFORMATION_TRACE"
]

SUBSTRATES = [
    "CONTINUOUS_MANIFOLD",
    "DISCRETE_GRAPH",
    "HYBRID_DYNAMIC",
    "SYMBOLIC_SPACE"
]

EXPRESSION_PRIMITIVES = [
    "BRANCHING", "SLACK", "RECOMBINATION", "EXPLORATION", "DIVERSITY", "REDUNDANCY"
]

def generate_domain(idx, regime):
    # Determine basic structure based on regime but allow for overlap
    if regime == "High-dimensional continuous systems":
        substrate = "CONTINUOUS_MANIFOLD"
        boundary = random.choice(["SMOOTH_HYPERSURFACE", "GLOBAL_DISCONTINUITY"])
        ontology = random.choice(["P0_STATE_LOCAL", "P1_STRUCTURAL_INVARIANT"])
    elif regime == "Purely symbolic / combinatorial systems":
        substrate = "DISCRETE_GRAPH"
        boundary = "COMBINATORIAL_THRESHOLD"
        ontology = random.choice(["P2_TOPOLOGICAL_BASIN", "P3_INFORMATION_TRACE"])
    elif regime == "Social / institutional collapse":
        substrate = "HYBRID_DYNAMIC"
        boundary = random.choice(["NETWORK_CASCADE", "STOCHASTIC_JUMP"])
        ontology = random.choice(["P1_STRUCTURAL_INVARIANT", "P2_TOPOLOGICAL_BASIN"])
    elif regime == "Pathological adversarial constructions":
        # Invert typical associations
        substrate = random.choice(SUBSTRATES)
        boundary = random.choice(BOUNDARY_TYPES)
        ontology = random.choice(ONTOLOGIES)
    else:
        substrate = random.choice(SUBSTRATES)
        boundary = random.choice(BOUNDARY_TYPES)
        ontology = random.choice(ONTOLOGIES)

    # Expression primitives
    # Typical: more branching -> combinatorial/network
    # Pathological: high branching -> smooth
    primitives = []
    if regime == "Pathological adversarial constructions":
        if boundary == "SMOOTH_HYPERSURFACE":
            primitives = random.sample(EXPRESSION_PRIMITIVES, 3) # High branching for smooth
    else:
        if boundary in ["COMBINATORIAL_THRESHOLD", "NETWORK_CASCADE"]:
            primitives = random.sample(EXPRESSION_PRIMITIVES, random.randint(1, 4))

    return {
        "id": f"extreme_{regime.replace(' ', '_').lower()}_{idx}",
        "regime": regime,
        "persistence_ontology": ontology,
        "substrate_type": substrate,
        "boundary_type_primary": boundary,
        "expression_primitives": primitives,
        "dynamics_operator": f"Extreme expansion operator for {regime}",
        "notes": f"Adversarial expansion domain {idx} in {regime}"
    }

def run_expansion():
    print("Generating extreme expansion domains (N=2000)...")
    domains = []
    for i in range(2000):
        regime = random.choice(REGIMES)
        domains.append(generate_domain(i, regime))
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(domains, f, indent=2)
    print(f"Expansion complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_expansion()
