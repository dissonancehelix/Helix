Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Predator–prey Lotka–Volterra oscillatory ecosystems
State space: Population sizes of prey x(t) and predator y(t)
Dynamics operator: Coupled differential equations: dx/dt = αx - βxy, dy/dt = δxy - γy
Perturbation operator: Stochastic population shocks, environmental carrying capacity changes, disease
Stability condition: Trajectories form closed orbits (neutrally stable limit cycles) around fixed point
Failure mode: Local extinction of either species (x=0 or y=0 absorbing states)
Observables: Prey population count, Predator population count, Phase amplitude
Timescale regime: Generations (seasons to years)
Persistence type: PATTERN
Non-geometric elements: Absorbing boundary at zero population, Neutral stability of orbits without carrying capacity
Edge conditions: Low population numbers (demographic stochasticity), Allee effects
Notes: Persistence is a dynamical pattern, not a static state.
