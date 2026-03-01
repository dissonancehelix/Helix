# Phase 4B: Boundary Primitive Stress Test

## PART 1 — Boundary Primitive Inversion Tests

### boundary_primitive_1 (Dimensionality mismatch preventing continuous map)
- **Synthetic Domain 1 (Holds):** Flat 2D interface sliding on 3D substrate.
- **Synthetic Domain 2 (Holds locally, fails globally):** Compact 2D manifold embedded in 3D; local patches map isometrically, but global topology prevents continuous total mapping.
- **Synthetic Domain 3 (Violates but persists):** Holographic duality (e.g. AdS/CFT analog) where state space maps from N to N-1 dimensions exactly, preserving all information and persistence without collapse.
- **Test Result:** Neither necessary nor sufficient.
- **Log:**
  - state_space: Holographic boundary
  - operator: Conformal mapping
  - perturbation mechanism: Boundary injection
  - persistence observable: Bulk action
  - collapse condition: Information loss

### boundary_primitive_2 (Discrete Invariant Constraint)
- **Synthetic Domain 1 (Holds):** 1D ring array with discrete trapped winding number.
- **Synthetic Domain 2 (Holds locally, fails globally):** 2D lattice with discrete bulk topological defect that persists locally but drifts to the open macroscopic boundary and annihilates (fails globally).
- **Synthetic Domain 3 (Violates but persists):** 2D continuous limit cycle attractor without any quantized discrete invariant, persisting solely via continuous dynamic flow.
- **Test Result:** Sufficient (for protection against smooth bulk perturbations), but not Necessary (other persistence forms exist).
- **Log:**
  - state_space: Lattice with open boundaries
  - operator: Defect random walk
  - perturbation mechanism: Thermal boundary collisions
  - persistence observable: Bulk defect count
  - collapse condition: Boundary annihilation

### boundary_primitive_3 (Rule-based vs geometric state space division)
- **Synthetic Domain 1 (Holds):** Discrete graph-rewriting grammar without distance metric.
- **Synthetic Domain 2 (Holds locally, fails globally):** Local rule-based cellular automaton updating over a globally expanding continuous geometric grid.
- **Synthetic Domain 3 (Violates but persists):** Smooth billiard-ball computer using pure continuous geometry to simulate rule-based logic gates.
- **Test Result:** Neither necessary nor sufficient.
- **Log:**
  - state_space: Continuous geometric domain
  - operator: Ideal elastic collision
  - perturbation mechanism: Continuous trajectory deflection
  - persistence observable: Logic gate truth table completion
  - collapse condition: Phase volume expansion (chaos)

## PART 2 — Irreducible Obstruction Re-Attack

- **PERSISTENCE_TYPE_MISMATCH**
  - Minimal formal parameter: Ratio of structural formation time to observation tracking window.
  - Reduction: A hidden timescale separation.
- **TIMESCALE_NONALIGNMENT**
  - Minimal formal parameter: Ratio of perturbation correlation sequence time to system relaxation time (Deborah number analog).
  - Reduction: A hidden timescale separation.
- **SEMANTIC_MISMATCH**
  - Minimal formal parameter: Incommensurability of observable dimensional units (no formal mapping function exists).
  - Reduction: Truly irreducible heterogeneity.
- **STOCHASTIC_DOMINANCE**
  - Minimal formal parameter: Ratio of deterministic advection or restoring force forcing to stochastic diffusion variance (Péclet number analog).
  - Reduction: A hidden stochastic regime shift.

## PART 3 — Predictive Extraction Attempt

- **Boundary Primitive 2 (Discrete Invariant)** survives as SUFFICIENT.
- **Prediction derived:** "If boundary primitive 2 (Discrete Invariant Constraint) is absent in domain *quantum_error_correction* (i.e. replacing discrete syndrome measurements with continuous analog uncorrected channels), then observable *Logical error rate* must cross threshold *0.5 (randomization)* continuously without a finite distance threshold before collapse."

## PART 4 — Collapse Audit Summary
(See output)
