# Invariant: Regime Transition

**Type:** Invariant
**Status:** Candidate — first empirical evidence 2026-03-25
**Origin:** Helix Atlas — Phase 8 upgrade; first evidence from math domain probes
**Last Updated:** 2026-03-25

---

## Domain Coverage

- Math (confirmed: prime gaps trajectory 2013)
- Dynamical systems (phase transitions) — theoretical
- Evolutionary systems (fitness landscape crossings) — theoretical
- Network systems (percolation, cascade thresholds) — theoretical

---

## Mechanism

Complex systems exhibit qualitatively distinct operational regimes separated by
sharp transition boundaries. Near transition boundaries, the system's macroscopic
behavior changes discontinuously relative to smooth changes in control parameters.
These transitions are detectable as a sudden step-change in the DCP trajectory —
a step-ratio significantly above mean step size.

---

## First Empirical Evidence

**Prime gaps / Zhang 2013** (`core/probes/math/probes/math_probe_prime_gaps.py`):
- Pre-transition: 164 years of slow drift in P(solvable), 0.10 → 0.45
- Transition event: Zhang's bounded gaps proof (2013-05-14)
- Step ratio: 3.1× mean — above the 3× detection threshold
- Post-transition: DCP k=15, R²=0.985 — rapid logistic collapse (70M → 246 in 14 months)
- GPY 2005 was a near-transition that failed to cross the boundary

**Detection signature**: step_ratio = max_single_step / mean_step_size > 3.0

---

## Relationship to DCP

Regime transition is detectable *within* a DCP trajectory as a discontinuity.
It is not redundant with DCP — DCP models the shape of possibility space narrowing
within a regime; regime transition marks the boundary between two distinct DCP phases.

A full trajectory may contain:
1. Pre-transition DCP phase (one k, one R²)
2. Transition event (step_ratio >> 1)
3. Post-transition DCP phase (different k, different R²)

Prime gaps shows exactly this: pre-transition k≈0.5, R²≈0; post-transition k=15, R²=0.985.

---

## Predictions

1. Step ratio > 3× mean at transition boundary
2. Pre- and post-transition DCP phases have measurably different k values
3. Near-transition events (like GPY 2005) show elevated step ratio but below threshold
4. Systems with multiple regime transitions show multiple discontinuities in DCP trajectory

---

## Falsifiers

1. Any claimed regime transition with step_ratio < 2× mean
2. Pre/post k values that are statistically indistinguishable
3. The step-ratio signature appearing uniformly throughout a trajectory (no localization)

---

## Evidence

- `artifacts/math_prime_gaps.json` — step_ratio=3.1, pre/post k contrast confirmed
- All other domains: not yet tested

---

## Next Steps

- Test in language domain: grammar shift events (e.g., major language contact/creolization)
- Test in music domain: harmonic language shifts (common practice → atonality)
- Test in games domain: rule changes that create new strategic regimes
