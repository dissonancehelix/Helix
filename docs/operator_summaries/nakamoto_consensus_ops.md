Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Nakamoto-style blockchain consensus
State space: Distributed ledger appending a chain of cryptographic hash blocks
Dynamics operator: Proof-of-Work hashing, block propagation, longest-chain rule adoption
Perturbation operator: Network partitions, adversarial hash power, selfish mining
Stability condition: Honest node hash rate > 50% of total network hash rate
Failure mode: 51% attack, deep chain reorganization, double spending
Observables: Total computational hash rate, Block time, Network latency, Orphan rate
Timescale regime: Minutes (block time) to hours (transaction finality)
Persistence type: STATE
Non-geometric elements: Cryptographic hash collision resistance, Economic incentives
Edge conditions: Difficulty adjustment lag, Network eclipse
Notes: State persistence relies on continuous competitive energy expenditure.
