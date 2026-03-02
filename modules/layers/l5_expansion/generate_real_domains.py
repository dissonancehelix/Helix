import os
import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
DOMAINS_DIR = ROOT / 'domains'
DOMAINS_DIR.mkdir(parents=True, exist_ok=True)

# Helper for compressing substrates
compression_map = {
    "CONTINUOUS_FIELD": "CONTINUOUS",
    "CONTINUOUS_MANIFOLD": "CONTINUOUS",
    "DISCRETE_COMBINATORIAL": "DISCRETE_SYMBOLIC",
    "SYMBOLIC_ALGEBRAIC": "DISCRETE_SYMBOLIC",
    "STOCHASTIC_PROCESS": "STOCHASTIC",
    "HYBRID": "HYBRID"
}

def get_base_props(sub):
    props = {
        "CONTINUOUS_FIELD": {"form": "PDE spatial field", "dim": "infinite", "met": "YES", "p_ont": "P1_PATTERN_SPATIOTEMPORAL"},
        "CONTINUOUS_MANIFOLD": {"form": "ODE / manifold", "dim": "finite", "met": "YES", "p_ont": "P0_STATE_LOCAL"},
        "DISCRETE_COMBINATORIAL": {"form": "graph / lattice", "dim": "combinatorial", "met": "YES", "p_ont": "P3_ALGORITHMIC_SYNDROME"},
        "SYMBOLIC_ALGEBRAIC": {"form": "formal system", "dim": "combinatorial", "met": "NO", "p_ont": "P2_GLOBAL_INVARIANT"},
        "STOCHASTIC_PROCESS": {"form": "probability ensemble", "dim": "infinite", "met": "YES", "p_ont": "P4_DISTRIBUTIONAL_EQUILIBRIUM"},
        "HYBRID": {"form": "mixed", "dim": "mixed", "met": "mixed", "p_ont": "P0_STATE_LOCAL"}
    }
    return props.get(sub, props["CONTINUOUS_MANIFOLD"])

domain_specs = [
    # Phase 12
    ("Reaction-diffusion Turing patterns", "CONTINUOUS_FIELD", "SMOOTH_HYPERSURFACE"),
    ("Spin glass (Ising disorder)", "DISCRETE_COMBINATORIAL", "SINGULAR_DIVERGENCE"),
    ("Byzantine fault-tolerant consensus", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Black hole thermodynamics", "CONTINUOUS_MANIFOLD", "SINGULAR_DIVERGENCE"),
    ("CRISPR adaptive immunity memory", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Reinforcement learning policy convergence", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Epidemiological SIR with seasonal forcing", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Category-theoretic functorial equivalence", "SYMBOLIC_ALGEBRAIC", "GLOBAL_DISCONTINUITY"),
    # Phase 12b (Physical)
    ("Navier-Stokes turbulence", "CONTINUOUS_FIELD", "SINGULAR_DIVERGENCE"),
    ("Bose-Einstein condensate", "CONTINUOUS_FIELD", "SMOOTH_HYPERSURFACE"),
    ("Rayleigh-Benard convection", "CONTINUOUS_FIELD", "SMOOTH_HYPERSURFACE"),
    ("Quantum Hall edge states", "CONTINUOUS_MANIFOLD", "GLOBAL_DISCONTINUITY"),
    ("Kardar-Parisi-Zhang growth", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Granular jamming", "DISCRETE_COMBINATORIAL", "SINGULAR_DIVERGENCE"),
    ("N-body orbital resonance", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("MHD reconnection", "CONTINUOUS_FIELD", "SINGULAR_DIVERGENCE"),
    ("Superfluid vortex shedding", "CONTINUOUS_FIELD", "GLOBAL_DISCONTINUITY"),
    ("Glass transition", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    # Phase 12b (Biological)
    ("Lac operon switching", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Hox gene collinearity", "SYMBOLIC_ALGEBRAIC", "GLOBAL_DISCONTINUITY"),
    ("T-cell repertoire shaping", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Action potential Hodgkin-Huxley", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Somite segmentation clock", "CONTINUOUS_FIELD", "SMOOTH_HYPERSURFACE"),
    ("Microbiome dysbiosis", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Protein allostery", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Phytoplankton blooms", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Zika viral tropism", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Stem cell pluripotency landscape", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    # Phase 12b (Computational)
    ("Paxos consensus", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("LDPC decoding", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Game of Life Conway", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Gradient descent saddle escape", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Langevin MCMC sampling", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Type inference unification", "SYMBOLIC_ALGEBRAIC", "GLOBAL_DISCONTINUITY"),
    ("TCP congestion control", "HYBRID", "SMOOTH_HYPERSURFACE"),
    ("PageRank eigenvalue", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Hashmap collision clustering", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Bitcoin difficulty retargeting", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    # Phase 12b (Social/Economic)
    ("Bank run contagion", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Option pricing Black-Scholes", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Gerrymandering packing", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Language creolization", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Social network echo chambers", "DISCRETE_COMBINATORIAL", "COMBINATORIAL_THRESHOLD"),
    ("Constitutional crisis", "SYMBOLIC_ALGEBRAIC", "GLOBAL_DISCONTINUITY"),
    ("Traffic bottleneck phantom jams", "CONTINUOUS_FIELD", "SMOOTH_HYPERSURFACE"),
    ("Supply chain bullwhip", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE"),
    ("Auction winner's curse", "STOCHASTIC_PROCESS", "DISTRIBUTIONAL_COLLAPSE"),
    ("Tragedy of the commons", "CONTINUOUS_MANIFOLD", "SMOOTH_HYPERSURFACE")
]

for name, sub, bound in domain_specs:
    slug = name.lower().replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "").replace("'", "")
    
    # Generic placeholder content mapped contextually
    props = get_base_props(sub)
    
    d = {
      "id": slug,
      "domain": name,
      "state_space": f"Formal {props['form']} state space representing {name}",
      "dynamics_operator": "System evolution metric/operator",
      "perturbation_operator": "Environment perturbation / noise injection",
      "stability_condition": "Restoring forces / logic > Perturbation",
      "failure_mode": f"Boundary collapse: {bound}",
      "observable_metrics": [
        {
            "name": "Primary Order Parameter",
            "type": "CUSTOM",
            "estimator": "Domain specific estimator",
            "units_or_none": "None"
        }
      ],
      "timescale_regime": "Domain specific timescale",
      "persistence_type": "MIXED" if sub == "HYBRID" else "STATE",
      "non_geometric_elements": ["Domain specific arbitrary rules or constants"],
      "edge_conditions": ["Extreme limits causing parameter breakdown"],
      "notes": "Generated to formalize out-of-sample data points.",
      "persistence_ontology": props['p_ont'],
      "substrate_type": sub,
      "substrate_formalism": props['form'],
      "dimensionality_form": props['dim'],
      "metric_defined": props['met'],
      "boundary_type_primary": bound,
      "boundary_locality": "GLOBAL" if bound in ["GLOBAL_DISCONTINUITY", "COMBINATORIAL_THRESHOLD", "DISTRIBUTIONAL_COLLAPSE", "SINGULAR_DIVERGENCE"] else "LOCAL",
      "boundary_dimensionality_change": "YES" if bound in ["SINGULAR_DIVERGENCE", "GLOBAL_DISCONTINUITY"] else "NO",
      "substrate_S1c": compression_map.get(sub, "HYBRID")
    }
    
    # Add T1 explicitly for phase 15 completeness
    if sub in ["DISCRETE_COMBINATORIAL", "SYMBOLIC_ALGEBRAIC"]:
        t1 = "T1_FAST_PERTURB"
    elif sub == "STOCHASTIC_PROCESS":
        t1 = "T1_COMPARABLE"
    else:
        t1 = "T1_SLOW_PERTURB" # Simplified
        
    d["tau_perturb"] = "System perturbation timescale proxy"
    d["tau_relax"] = "System relaxation timescale proxy"
    d["T1"] = t1
    d["T1_notes"] = "Generated timescale separation"
    
    with open(DOMAINS_DIR / f"{slug}.json", 'w') as f:
        json.dump(d, f, indent=2)

print(f"Successfully instantiated 48 out-of-sample domain objects into the domain folder.")
