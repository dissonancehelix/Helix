# DCP Trajectory Mode: Floor / Stall (LIP)

**Type:** DCP Trajectory Mode
**Status:** Defined — see decision_compression.md
**Last Updated:** 2026-03-25

---

## Overview

The **floor mode** (historically labeled LIP — Local Incompleteness) describes DCP
trajectories where possibility breadth plateaus at a non-zero value and stops narrowing.

The floor arises from structural insufficiency in the evidence stream — not lack of
effort, but a hard limit on what the available evidence can determine.

---

## Signature

- Last 3+ evidence events within ±0.005 of each other
- Final breadth > 0.01
- k low; trajectory visually flat in tail

---

## Floor Sub-types

| Sub-type | Cause | Example |
|---|---|---|
| Evidence exhaustion | No remaining discriminating evidence | D.B. Cooper (~50K viable suspects) |
| Technology gate | Required tool doesn't yet exist | Tamam Shud pre-2019 (IGG not available) |
| Proven barrier | Multiple mathematical barriers established | P vs NP (BGS + Razborov-Rudich + algebrization) |
| Computational wall | Verification cost superexponential | Ramsey R(5,5) (range=6, frozen 15 years) |

The P vs NP case is the strongest instance: the floor is not merely observed but
mathematically proven — three independent barriers block ≥77% of known proof strategies
permanently.

---

## Notes

The "local incompleteness" label reflects the core phenomenon: local evidence is
structurally insufficient to determine the global answer. This is the mechanism
behind DCP floors, not a separate invariant requiring its own probe.

See `codex/atlas/invariants/decision_compression.md` for the full trajectory mode taxonomy.
