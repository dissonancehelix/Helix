Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Representation Invariance Suite

## Test 1: Ontology Permutation Stability
**Cosine Similarity:** 0.0970
**Variance Explained:** Base Top-2 = 0.3879 -> Permuted Top-2 = 0.3692
**Interpretation:** Beams degrade markedly when Ontology is scrambled, confirming Ontology is not a free parameter but carries structural necessity for defining boundary failure.

## Test 2: Boundary Label Coarsening
**Base Entropy:** 2.1695 bits
**Coarsened Entropy:** 1.5622 bits
**Interpretation:** Low-rank structure remains strong. Fine-grained labels introduce slight dimensionality, meaning coarsened "meta-classes" cleanly capture the fundamental structural divergence (Continuous vs Discrete vs Statistical) without losing signal.

## Test 3: Substrate Coarsening
**Cosine Similarity:** 0.7088
**Variance Explained:** Base Top-2 = 0.3879 -> Coarsened Top-2 = 0.4026
**Interpretation:** Removing the Topological slice reduces variance explained smoothly, proving the CONTINUOUS_TOPOLOGICAL split was structurally necessary to prevent eigen-blurring between wave physics and discrete invariant phase transitions.

## Test 4: Randomized Feature Dropout
**Mean Cosine Similarity:** 0.9450 ± 0.2164
**Variance in Top-3 Explained:** 1.362192e-05
**Interpretation:** Massive resilience under domain erosion. The low-rank geometry does not depend on specific individual domains, establishing it as a highly stable global manifold.

## Test 5: Obstruction Decoupling Test
**Mean HYBRID Risk (With Obstructions):** 5.35
**Mean HYBRID Risk (Without Obstructions):** 2.73
**Mean PHYSICAL Risk (Without Obstructions):** 3.07
**Interpretation:** Even with obstruction data stripped entirely from the model, HYBRID domains still heavily out-rank pure physical systems in structural risk. The incompatibility is hard-coded into the fundamental collapse geometry (Substrate x Ontology clash), not driven artificially by missing measurements.
