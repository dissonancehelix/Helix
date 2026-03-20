# Model: Control Subspace Collapse

**Type:** Model
**Status:** Candidate
**Origin:** Derived from Decision Compression invariant
**Last Updated:** 2026-03-15

---

## Domain Coverage

- Games, Language, Music (via Decision Compression evidence)
- Mathematical: linear algebra / dynamical systems

---

## Mechanism

The Control Subspace Collapse model proposes that commitment dynamics
in complex systems can be described as a projection onto a low-dimensional
control manifold. Prior to commitment, the system's state evolves in a
high-dimensional phase space. As commitment approaches, eigenvectors
associated with low-variance directions decay, effectively projecting
the state onto a lower-rank subspace.

Formally: if A(t) is the influence matrix at time t before commitment,
the rank of the effective control subspace rank(A(t)) decreases
monotonically as t → 0 (commitment).

This model would explain why Decision Compression appears across
substrate types — the collapse is a property of any system that must
resolve a high-dimensional state into a discrete commitment.

---

## Predictions

1. The control subspace dimension is measurable via PCA on influence vectors
2. Eigenvalue decay rate predicts commitment proximity
3. Systems with more agents / higher initial dimensionality will show
   more dramatic compression ratios
4. The collapsed subspace aligns with the eventual committed state's
   principal components

---

## Falsifiers

1. Influence matrices that do not show rank reduction pre-commitment
2. Commitment events where post-commitment dimensionality exceeds
   pre-commitment dimensionality
3. Random (non-monotonic) eigenvalue trajectories near commitment
4. Failure of PCA alignment between collapsed subspace and committed state

---

## Evidence

- Supported by: `codex/atlas/invariants/decision_compression.md`
- Mathematical basis: requires formal proof (not yet produced)

---

## Linked Experiments

- `codex/atlas/experiments/decision_compression_sweep.md`
- Proposed: PCA analysis of influence matrices from existing runs

---

## Notes

This model is a candidate explanation for Decision Compression.
It is not yet verified — it is the current best mechanistic hypothesis.
A formal eigenvalue analysis of existing artifact data could promote
this from Candidate to Provisional in Phase 8.
