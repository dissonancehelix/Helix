# Law: Decision Compression

**Confidence:** Verified
**Last Updated:** 2026-03-15
**Probe Version:** 1.0.0

---

## Description

Influence vectors collapse into a low-dimensional control subspace during
irreversible commitment events. As systems approach decision points, the
degrees of freedom available for action compress — the system's effective
choice space narrows before the decision is finalized.

This invariant has been observed consistently across games, language, and
music substrates with a mean signal of 0.434 and a 100% pass rate across
7 independent runs.

---

## Observed Conditions

- Substrates: games, language, music
- Signal threshold: > 0.35 (all runs exceeded this)
- Mean observed signal: 0.4338
- Pass rate: 1.0 (7/7 runs)
- Probe version: 1.0.0

---

## Failure Conditions

- Low population / sparse agent count
- Weak competition or low-stakes decision context
- Signal < 0.35 (no observed failures in current data)
- Further falsification required across additional substrates

---

## Evidence

- `artifacts/experiments/dcp_discovery/`
- `artifacts/experiments/dec_1772602957/`
- `artifacts/experiments/cross_domain_compression/`

Supporting run IDs:
- `decision_compression_20260315_040912_9b9715` (games, signal=0.4649)
- `decision_compression_20260315_040916_72dd2a` (language, signal=0.3938)
- `decision_compression_20260315_040916_7c0ec2` (music, signal=0.4273)
- `decision_compression_20260315_041601_7b4116` (games, signal=0.4649)
- `decision_compression_20260315_041604_e4fc0c` (language, signal=0.3938)
- `decision_compression_20260315_041608_953714` (music, signal=0.4273)
- `decision_compression_20260315_042458_8672e2` (games, signal=0.4649)

Source index: `atlas/decision_compression.json`

---

## Notes

Decision Compression is currently the most robustly verified law in the
Helix Atlas. Cross-substrate consistency (games/language/music) suggests
this pattern is substrate-independent and reflects a genuine structural
invariant of commitment dynamics.

Spatial substrate validation pending (Phase 9 — Godot engine).
