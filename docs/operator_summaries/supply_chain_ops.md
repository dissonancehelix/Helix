Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Global supply chain cascade failures
State space: Directed graph of supplier-buyer inventory levels and lead times
Dynamics operator: Order fulfilling, production scheduling, transportation logistics
Perturbation operator: Demand shocks, supplier bankruptcies, logistical blockages, natural disasters
Stability condition: Buffer inventories > perturbation amplitude; localized containment of node failures
Failure mode: Cascading stockouts, bullwhip effect runaway, systemic network collapse
Observables: Inventory on hand, Order backlog, Delivery lead time variability, Network connectivity
Timescale regime: Days to months (production cycles and logistical transport)
Persistence type: STATE
Non-geometric elements: Network topology (hubs/scale-free), Information asymmetry (bullwhip)
Edge conditions: Just-in-time (JIT) minimal buffers, Correlated multi-region shocks
Notes: Systemic interconnectedness converts local perturbations into propagating cascades without sufficient buffer capacity.
