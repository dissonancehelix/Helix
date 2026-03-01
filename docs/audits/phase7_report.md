Derived From:
- /artifacts/run_manifest.json (dataset_hash: bca19c5253d22a90be3ea77329f285214f0d4b385f6996aa6b7242c95a758d4d)
- /artifacts/eigenspace/baseline_beams_v2.json
- /artifacts/obstruction/obstruction_spectrum.json
- /artifacts/periodic_atlas/periodic_atlas.json
- /artifacts/risk/risk_scores.json
- /artifacts/invariance/invariance_suite.json
- /artifacts/counterexamples/synthetic_results.json

# Phase 7 — Mechanism Renormalization & Boundary Minimality

## Second-order Independence Matrix

Attempting reduction of A2, A3, and A4 to abstract stability response operator F:
- **A3 (Temporal flux)**: Tested emergence from the asymmetry of F under time-reversal T. F(t) != F(-t) strictly necessitates M > 0 (active flux). Reduction succeeds formally. 
- **A4 (Perturbation scaling)**: Tested emergence from geometric curvature properties grad^2 F and higher moments. Scale-divergent bounds (O4) map to singularities in grad^2 F = 0, while rare-event stochasticity bounds (O1) map to deep isolated minima grad^2 F >> 0. Reduction succeeds formally.
- **A2 (Mechanism type)**: Tested emergence from topological singularity class of F. Continuous metric gradients map to smooth connected sheets of F, but discrete topological constraints (Q in Z) cannot be derived purely from the local geometry of F without specifying global boundary conditions of the state space manifold. Reduction fails. Obstruction type: TOPOLOGICAL_INCOMPATIBILITY.

| | A2 (Mechanism) | A3 (Temporal) | A4 (Perturbation Scaling) |
| :--- | :--- | :--- | :--- |
| **A2** | - | Independent (Global vs Local) | Independent |
| **A3** | Independent | - | Dependent (Derived from F) |
| **A4** | Independent | Dependent (Derived from F) | - |

## Boundary Type Taxonomy

- **O1 (Energy Barrier)**: Crossing in parameter manifold format: E_a / kT <= 1. Topologically a continuous codimension-1 hypersurface. Crossing is smooth and exponentially accelerating, not discrete.
- **O2 (Discrete Topological)**: Crossing format: Singularity insertion or boundary annihilation dQ != 0. Not a codimension-1 hypersurface; represents a global discontinuous jump in the manifold dimension or connectivity.
- **O3 (Throughput-Driven)**: Crossing format: Eigenvalue sign change of the contractive mapping Jacobian Re(\lambda_max) >= 0. Topologically a continuous codimension-1 hypersurface (bifurcation boundary).
- **O4 (Critical Divergence)**: Crossing format: Divergence of susceptibility limit \chi -> \infty. Topologically a singular boundary (second-order phase transition).
- **O5 (Error Correction)**: Crossing format: Syndrome weight exceeds Hamming distance threshold w >= d/2. Not a codimension-1 hypersurface; fundamentally a discrete algorithmic discontinuity acting over combinatorial sets.
- **O6 (Kinematic Advection)**: Crossing format: Loss of contractive mapping vector flow bounding perturbations. Continuous codimension-1 hypersurface.

## Invariant Manifold Applicability Map

Testing persistence via formal expression: Distance(x, M) < \epsilon under perturbation P.

- **Applicable Domains (Continuous Geometric Convergence):**
  - Continuous advection regimes (O6).
  - Energy basin gradient descent (O1).
  - Throughput-maintained steady states (O3) possessing defined Lyapunov manifolds.
  
- **Manifold Applicability Failure Points:**
  - **Systems where invariant is discrete**: Fails in topological knot invariants (O2) and surface codes, where "distance" is quantized and \epsilon-vicinity is meaningless without a continuous metric.
  - **Systems where manifold itself changes dimensionality**: Fails in critical divergence (O4), where correlation lengths scaling to infinity cause the invariant subspace to span the entire macroscopic domain, destroying the concept of localized bounded distance x -> M.
  - **Systems where invariant is algorithmic**: Fails in algorithmic rule sets (O5) where projection operators map non-metric combinatorial spaces discretely, lacking a formally smooth distance function.

## Discrete Irreducibility Report

Testing whether algorithmic projection (O5) is expressible as the limit of a continuous contraction operator C(x, t) as t -> \infty.

- **Formal Result**: No. Continuous contraction operators compress continuous phase spaces to a single defined attractor geometry. Algorithmic projection dynamically maps orthogonal syndrome sub-spaces into an explicitly coded subset relying on discrete logic gates.
- **Minimal Obstruction Formalization**: A continuous contraction requires infinite resolution to discern between infinitely close bit-flip probability amplitudes, destroying finite-time threshold separability.
- **Obstruction Type**: Information-theoretic (analog noise accumulation overrides digital finite-threshold correction without a non-linear discrete measurement collapse operator).

## Substrate Invariance Table

| Operator | Hamiltonian Substrate | Informational / Symbolic Substrate | Cybernetic / Control Substrate | Invariance Result |
| :--- | :--- | :--- | :--- | :--- |
| **O1 (Barrier)** | Native (Potential Energy) | Demands Reinterpretation (Cost function) | Demands Reinterpretation (Error limits) | Requires Reinterpretation |
| **O2 (Topological)** | Native (Quantized Flux) | Native (Homology groups) | Collapses (No native invariants) | Requires Reinterpretation |
| **O3 (Throughput)** | Native (Dissipative Systems) | Collapses (Symbols do not dissipate energy) | Native (Feedback Loops) | Requires Reinterpretation |
| **O4 (Criticality)** | Native (Phase Transitions) | Native (Percolation thresholds) | Native (Edge-of-stability training) | Survives Translation |
| **O5 (Algorithmic)** | Collapses (Hamiltonian cannot compute) | Native (Code distance) | Native (Digital error correction) | Requires Reinterpretation |
| **O6 (Kinematic)** | Native (Fluid Advection) | Collapses (No flow gradients) | Native (Attractor dynamics) | Requires Reinterpretation |
