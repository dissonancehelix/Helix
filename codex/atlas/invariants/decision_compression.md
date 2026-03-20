# Invariant: Decision Compression

**Type:** Invariant
**Status:** Verified
**Origin:** Helix probe — games, language, music
**Last Updated:** 2026-03-16

---

## Domain Coverage

- Substrates: games, language, music
- Mean signal: 0.4338
- Pass rate: 100.0% (7 runs)

## Mechanism

Structural pattern detected across substrates: games, language, music.

## Predictions

1. Signal > threshold in all tested substrates
2. Pass rate >= 100%

## Falsifiers

1. Any substrate showing signal < 0.20 under equivalent conditions
2. Replication failure across substrates

## Evidence

- Source: `codex/atlas/decision_compression.json`

- `decision_compression_20260315_040912_9b9715` (games, signal=0.4649) PASS
- `decision_compression_20260315_040916_72dd2a` (language, signal=0.3938) PASS
- `decision_compression_20260315_040916_7c0ec2` (music, signal=0.4273) PASS
- `decision_compression_20260315_041601_7b4116` (games, signal=0.4649) PASS
- `decision_compression_20260315_041604_e4fc0c` (language, signal=0.3938) PASS
- `decision_compression_20260315_041608_953714` (music, signal=0.4273) PASS
- `decision_compression_20260315_042458_8672e2` (games, signal=0.4649) PASS

## Linked Experiments

- See atlas registry

## Notes

Auto-compiled from `codex/atlas/decision_compression.json`.
