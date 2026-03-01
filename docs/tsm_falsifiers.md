Derived From:
- /artifacts/tsm/tsm_overlay.json
- /artifacts/tsm/tsm_kernel_tests.json
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)

# TSM Falsifiers (Trajectory Stabilization Mechanism)

The following counterexamples, if found in physical networks, would explicitly break the underlying Identity/Persistence Atlas laws:

1. **Catastrophic Failure under Slow Perturbation for TSM_FULL:**
   A `TRACE+COMMIT+CONTROL` system that fails via unmitigated global cascades (`GLOBAL_DISCONTINUITY`) when exposed to strictly slow adiabatic perturbations, structurally breaking the adaptive/arbitration resilience guarantee.

2. **Stable Identity Invariants in Pure Markov Systems:**
   A `MARKOV` system (no internal memory, zero prior state interaction) exhibiting fully stable, goal-directed identity invariants (like `SETPOINT` or `POLICY_BASIN`) without relying on externally stored state (`EXTERNALIZED_STATE`), proving identity metrics do not inherently demand internal substrate traces.

3. **Non-Essential Trace Dependence:**
   A system correctly classified as `TSM_FULL` (possessing memory, latches, and control) where structurally zeroing or ablating the `TRACE` entirely does *not* significantly increase the probability of early collapse or decrease the effective `persistence_ontology` scale, meaning the trace was redundant tracking rather than an active structural persistence element.
