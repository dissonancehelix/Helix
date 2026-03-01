Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Reparameterization Results

## Metrics Table
| Metric | Old (Phase 2b/3) | New (Phase 8) | % Change |
|---|---|---|---|
| Obstruction Entropy (H) | 2.2706 | 1.6739 | -26.28% |
| Distinct Obstruction Types | 7 | 4 | - |
| Mapping Yield Rate | 0.0000 | 0.0000 | - |

## Verdict
**SUPPORTS_H***

## Top 5 Obstruction Types
### Old
- PERSISTENCE_TYPE_MISMATCH: 132
- NON_GEOMETRIC_RULESET: 68
- TOPOLOGICAL_INCOMPATIBILITY: 57
- STATE_DIMENSION_MISMATCH: 38
- SEMANTIC_MISMATCH: 38
### New
- STATE_DIMENSION_MISMATCH: 38
- NON_GEOMETRIC_RULESET: 34
- TOPOLOGICAL_INCOMPATIBILITY: 10
- SEMANTIC_MISMATCH: 6

## Top MAP candidates

## Top NO_MAP candidates
- adaptive_immunity <-> lotka_volterra (Reason: STATE_DIMENSION_MISMATCH)
- chern_insulator <-> homological_algebra (Reason: NON_GEOMETRIC_RULESET)
- chern_insulator <-> knot_invariants (Reason: NON_GEOMETRIC_RULESET)
- chern_insulator <-> protein_folding (Reason: STATE_DIMENSION_MISMATCH)
- chern_insulator <-> quantum_error_correction (Reason: STATE_DIMENSION_MISMATCH)
- chern_insulator <-> supply_chain (Reason: STATE_DIMENSION_MISMATCH)
- chern_insulator <-> tokamak_plasma (Reason: STATE_DIMENSION_MISMATCH)
- chern_insulator <-> traffic_shockwaves (Reason: STATE_DIMENSION_MISMATCH)
- constitutional_law <-> language_grammar (Reason: SEMANTIC_MISMATCH)
- constitutional_law <-> nakamoto_consensus (Reason: SEMANTIC_MISMATCH)
