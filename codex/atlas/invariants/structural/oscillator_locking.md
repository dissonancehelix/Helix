# Law: Oscillator Locking

**Confidence:** Verified
**Last Updated:** 2026-03-15
**Probe Version:** 1.0.0

---

## Description

Coupled oscillating subsystems synchronize into phase-locked states when
interaction strength crosses a critical threshold. Once locking occurs,
the system resists perturbation — phase coherence is maintained against
moderate noise.

This invariant has been observed across games, language, and music substrates
with near-perfect signal (mean 0.991) and a 100% pass rate across 3 runs.

---

## Observed Conditions

- Substrates: games, language, music
- Signal threshold: > 0.95 (all runs well above this)
- Mean observed signal: 0.9912
- Pass rate: 1.0 (3/3 runs)
- Probe version: 1.0.0

---

## Failure Conditions

- Interaction strength below critical coupling threshold
- Excessive noise drowning synchrony signal
- Heterogeneous natural frequencies with insufficient coupling
- Further adversarial testing needed

---

## Evidence

- `artifacts/experiments/oscillator_locking/` (if present)

Supporting run IDs:
- `oscillator_locking_20260315_041601_522c1d` (games, signal=0.9994)
- `oscillator_locking_20260315_041604_705e4a` (language, signal=0.9998)
- `oscillator_locking_20260315_041608_5b1924` (music, signal=0.9743)

Source index: `codex/atlas/oscillator_locking.json`

---

## Notes

Oscillator Locking shows the strongest signal of any current Helix law
(mean 0.991). The near-unity pass rate across all substrates makes this
a high-priority candidate for spatial validation via the Godot engine
in Phase 9.

The slight dip in the music substrate (0.974 vs 0.999 in games/language)
warrants investigation — it may reflect looser temporal coupling in
musical structures compared to discrete game mechanics and linguistic rhythm.
