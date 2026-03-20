# Experiment: Decision Compression Sweep

**Type:** Experiment
**Status:** Completed
**Origin:** Helix Phase 7 — cross-domain probe suite
**Last Updated:** 2026-03-15

---

## Domain Coverage

- Games, Language, Music
- 7 runs total, all passed

---

## Mechanism

Ran the decision_compression probe across three substrates with fixed
parameters (probe version 1.0.0). Each run measured the compression signal
in influence distributions at commitment boundaries.

---

## Predictions

Prior prediction: signal > 0.35 across all domains.
Result: all runs exceeded threshold (min 0.3938, max 0.4649).

---

## Falsifiers

N/A — experiment completed. Results become evidence for the invariant.
Any future run showing signal < 0.20 under identical parameters would
be a falsifying data point.

---

## Evidence

- `codex/atlas/decision_compression.json`
- Run IDs: see `codex/atlas/invariants/decision_compression.md`

---

## Linked Experiments

- `codex/atlas/invariants/decision_compression.md`
- `codex/atlas/models/control_subspace_collapse.md`

---

## Notes

This experiment established the initial verified status of the
Decision Compression invariant. A follow-up sweep with extended
parameter ranges is planned for Phase 8.
