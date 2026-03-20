# Invariant: Oscillator Locking

**Type:** Invariant
**Status:** Verified
**Origin:** Helix probe — games, language, music
**Last Updated:** 2026-03-16

---

## Domain Coverage

- Substrates: games, language, music
- Mean signal: 0.9912
- Pass rate: 100.0% (3 runs)

## Mechanism

Structural pattern detected across substrates: games, language, music.

## Predictions

1. Signal > threshold in all tested substrates
2. Pass rate >= 100%

## Falsifiers

1. Any substrate showing signal < 0.20 under equivalent conditions
2. Replication failure across substrates

## Evidence

- Source: `codex/atlas/oscillator_locking.json`

- `oscillator_locking_20260315_041601_522c1d` (games, signal=0.9994) PASS
- `oscillator_locking_20260315_041604_705e4a` (language, signal=0.9998) PASS
- `oscillator_locking_20260315_041608_5b1924` (music, signal=0.9743) PASS

## Linked Experiments

- See atlas registry

## Notes

Auto-compiled from `codex/atlas/oscillator_locking.json`.
