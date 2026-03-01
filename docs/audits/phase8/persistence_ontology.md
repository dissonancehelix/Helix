Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Persistence Ontology (Axis Zero)

## P0_STATE_LOCAL
- **Definition**: Persistence is staying in or near a defined state (basin, fixed point, steady state).
- **Inclusion criteria**: Energy barriers, local attractors, metric gradient descent return maps.
- **Exclusion criteria**: Traveling waves, discrete algorithmic corrections, macroscopic topological features.
- **Canonical observables**: Escape rate, potential energy gradient, variance bound.
- **Typical failure boundary signature**: Smooth deterministic exit from basin (bifurcation) or rare-event stochastic escape.

## P1_PATTERN_SPATIOTEMPORAL
- **Definition**: Persistence is maintaining a dynamic pattern across time or space (wave, cycle, oscillation, shock, norm pattern).
- **Inclusion criteria**: Limit cycles, standing waves, continuous stochastic equilibria over spatial graphs.
- **Exclusion criteria**: Static fixed points, purely combinatorial syndrome projections.
- **Canonical observables**: Phase amplitude, cycle period, pattern entropy.
- **Typical failure boundary signature**: Phase decoherence, amplitude collapse, singular divergence of correlation length.

## P2_GLOBAL_INVARIANT
- **Definition**: Persistence is maintaining a topological or global invariant (winding number, Chern class, homology class).
- **Inclusion criteria**: Quantized flux, knot invariants, bulk-edge correspondence systems.
- **Exclusion criteria**: Local metric attractors lacking discrete global invariants.
- **Canonical observables**: Topological integer invariants, winding numbers.
- **Typical failure boundary signature**: Discontinuous phase boundary crossing, singular defect insertion/annihilation.

## P3_ALGORITHMIC_SYNDROME
- **Definition**: Persistence is maintaining membership in a code or constraint set under active algorithmic correction or projection.
- **Inclusion criteria**: Error correcting codes, syntactic grammar rules, formal logic consistency maintenance.
- **Exclusion criteria**: Continuous analog flow restoration, purely physical thermodynamic relaxation.
- **Canonical observables**: Syndrome parity, Hamming distance, constraint violation count.
- **Typical failure boundary signature**: Discrete threshold crossing (e.g. error weight > d/2 capacity).

## P4_DISTRIBUTIONAL_EQUILIBRIUM
- **Definition**: Persistence is maintaining a stable probability distribution or ensemble over types or variants.
- **Inclusion criteria**: Stationary distributions in Markov processes, population equilibria, evolutionary stable strategies.
- **Exclusion criteria**: Purely deterministic single trajectories, discrete topological invariants.
- **Canonical observables**: Kullback-Leibler divergence, stationary state probabilities, Shannon entropy.
- **Typical failure boundary signature**: Ergodic measure collapse, absorbing state trapping.
