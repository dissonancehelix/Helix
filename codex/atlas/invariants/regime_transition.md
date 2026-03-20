# Invariant: Regime Transition

**Type:** Invariant
**Status:** Exploratory
**Origin:** Helix Atlas — Phase 8 upgrade
**Last Updated:** 2026-03-15

---

## Domain Coverage

- Dynamical systems (phase transitions)
- Evolutionary systems (fitness landscape crossings)
- Network systems (percolation, cascade thresholds)

---

## Mechanism

Complex systems exhibit qualitatively distinct operational regimes separated by sharp transition boundaries. Near transition boundaries, the system's macroscopic behavior changes discontinuously (or near-discontinuously) relative to smooth changes in control parameters. These transitions are detectable as a sudden shift in the distribution of system-level observables.

---

## Predictions

1. Transition signal is detectable as a sharp change in observable distribution width
2. Systems near transition boundaries show elevated variance in macroscopic observables
3. Transition point location is reproducible across independent runs under identical parameters

---

## Falsifiers

1. Any system claimed to have a regime transition that shows only smooth, continuous changes
2. Transition boundaries that shift unpredictably under identical parameters
3. Elevated variance that is uniformly distributed (not localized to transition region)

---

## Evidence

- No runs yet. Probe implementation pending (Phase 8).

---

## Linked Experiments

- Probe: `labs/invariants/regime_transition_probe.py` (Phase 8)

---

## Notes

Candidate status. Best-understood of the three pending invariants; mathematical basis well-established.
