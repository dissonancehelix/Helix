# Operator: Commitment Probe

**Type:** Operator
**Status:** Active
**Origin:** Helix Phase 7 probe suite
**Last Updated:** 2026-03-15

---

## Domain Coverage

- Games, Language, Music (validated)
- General: any system with discrete commitment events

---

## Mechanism

The Commitment Probe operator measures compression signal in influence
distributions at commitment boundaries. It applies to any dataset or
simulation that has identifiable irreversible transition points.

Pipeline:
1. Identify commitment events in the substrate (domain-specific)
2. Extract influence vectors in a window before each commitment
3. Compute effective rank of the influence matrix
4. Measure signal = 1 - (rank_at_commitment / max_rank)
5. Compare against threshold (default: 0.35)

The operator is reusable across substrates — only the commitment
identification step is domain-specific.

---

## Predictions

Applying this operator to any genuine commitment-containing system
should return signal > 0.35 if Decision Compression is a true invariant.

---

## Falsifiers

Returns signal < 0.20 on a substrate that contains genuine irreversible
commitment events under equivalent conditions to validated substrates.

---

## Evidence

- Used in: `atlas/experiments/decision_compression_sweep.md`
- Results: 7/7 runs passed, signal range 0.39–0.46

---

## Linked Experiments

- `atlas/invariants/decision_compression.md`
- `atlas/experiments/decision_compression_sweep.md`

---

## Notes

This is a reusable diagnostic tool. Any new substrate being tested for
Decision Compression should use this operator to ensure comparability
of results across the Atlas.
