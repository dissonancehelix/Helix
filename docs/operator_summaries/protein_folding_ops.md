Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Protein folding energy landscapes
State space: Conformational space of polypeptide backbone and side-chain dihedral angles
Dynamics operator: Molecular dynamics driven by free energy minimization (funnel landscape)
Perturbation operator: Thermal fluctuations, pH changes, denaturants, mechanical force
Stability condition: Native state free energy minimum separated by sufficiently high kinetic barrier (ΔG_fold < 0 and E_a large)
Failure mode: Unfolding, misfolding, amyloid aggregation
Observables: Fraction folded, Radius of gyration, Heat capacity C_p, FRET efficiency
Timescale regime: Microseconds to seconds (folding trajectory and residence time)
Persistence type: STATE
Non-geometric elements: Topological knots in native fold, Frustration in non-native contacts, Sequence specificity
Edge conditions: High temperature (T > T_m), Extreme crowding
Notes: Structure is trapped in a deep local minimum of a funnel-shaped free energy landscape.
