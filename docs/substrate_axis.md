Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# S1: Substrate Embedding Type
**Definition**: The formal type of state space and update semantics that the domain lives in.

## CONTINUOUS_FIELD
- state representation: Infinite-dimensional function space, distributions
- dynamics operator type: Partial Differential Equations (PDE), integral operators
- distance / metric availability: YES (L2, Sobolev, Wasserstein)
- dimensionality notion: infinite
- noise model default: additive continuous / thermal fluctuations
- typical obstruction signatures it should resolve: STATE_DIMENSION_MISMATCH with discrete systems

## CONTINUOUS_MANIFOLD
- state representation: Finite-dimensional smooth or topological manifold
- dynamics operator type: Ordinary Differential Equations (ODE), Langevin, smooth vector fields
- distance / metric availability: YES (Euclidean, Riemannian)
- dimensionality notion: finite
- noise model default: additive / multiplicative (stochastic calculus)
- typical obstruction signatures it should resolve: STATE_DIMENSION_MISMATCH, TOPOLOGICAL_INCOMPATIBILITY (local vs global)

## DISCRETE_COMBINATORIAL
- state representation: Finite sets, graphs, lattices, codes
- dynamics operator type: Discrete updates, cellular automata, logical gates
- distance / metric availability: YES (Hamming, graph distance)
- dimensionality notion: combinatorial
- noise model default: adversarial bit flips, discrete randomized errors
- typical obstruction signatures it should resolve: NON_GEOMETRIC_RULESET against continuous maps

## SYMBOLIC_ALGEBRAIC
- state representation: Proof objects, formal syntactic systems, homological chain complexes
- dynamics operator type: Rewriting systems, inference rules, boundary operators
- distance / metric availability: NO (often only identity/isomorphism)
- dimensionality notion: combinatorial
- noise model default: none (strict consistency)
- typical obstruction signatures it should resolve: SEMANTIC_MISMATCH, NON_GEOMETRIC_RULESET

## STOCHASTIC_PROCESS
- state representation: Probability measures, ensemble states, Markov kernels
- dynamics operator type: Master equations, Fokker-Planck, random walks
- distance / metric availability: YES (Kullback-Leibler, Total Variation)
- dimensionality notion: infinite (distributions over combinatorial/finite spaces)
- noise model default: intrinsic (noise is the driving force)
- typical obstruction signatures it should resolve: STOCHASTIC_DOMINANCE, MAINTENANCE_NOISE_ALIASING

## HYBRID
- state representation: Mixed (e.g., continuous values on discrete graphs)
- dynamics operator type: Coupled equations
- distance / metric availability: mixed
- dimensionality notion: mixed
- noise model default: mixed
- typical obstruction signatures it should resolve: TIMESCALE_NONALIGNMENT
