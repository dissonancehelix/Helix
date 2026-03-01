Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Traffic flow shockwaves (Lighthill–Whitham–Richards PDE)
State space: Vehicle density ρ(x,t) and flow q(ρ) on a 1D spatial domain
Dynamics operator: Continuity equation ∂ρ/∂t + ∂q/∂x = 0
Perturbation operator: Local density fluctuations (braking, merging)
Stability condition: Density ρ < critical density ρ_c (free flow regime)
Failure mode: Shockwave formation (kinematic wave propagating upstream)
Observables: Vehicle density ρ, Average velocity v, Flow rate q
Timescale regime: Seconds to minutes (vehicle reaction times and wave propagation)
Persistence type: PATTERN
Non-geometric elements: Kinematic wave speed discontinuity, Jam density limit
Edge conditions: Capacity bottlenecks, Extreme density ρ → ρ_max
Notes: Shockwaves represent a topological discontinuity in the density field.
