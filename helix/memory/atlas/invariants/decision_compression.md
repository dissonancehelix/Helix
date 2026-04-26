# Invariant: Decision Compression

**Type:** Invariant
**Status:** Verified
**Origin:** Helix probe — games, language, music
**Last Updated:** 2026-03-25

---

## Domain Coverage

- Substrates verified: games, language, music, math (2026-03-25)
- Mean signal: 0.4338
- Pass rate: 100.0% (7 runs across original substrates)

---

## Mechanism

Possibility space in any system working toward resolution narrows logistically
over time. The shape of narrowing is described by:

  `breadth(t) = 1 / (1 + exp(k × (t - t₀)))`

where k is the steepness of collapse and t₀ is the inflection point.

**k sorts by coupling mechanism — universal across domains:**

| Coupling type | k range | Examples |
|---|---|---|
| Continuous/simultaneous | 50–75 | Kuramoto oscillators, music rhythm, Ramsey (physics-like compute) |
| Cognitive/belief networks | 15–20 | GWT belief nets, Cicada 3301 (designed), prime gaps post-transition |
| Language/discrete sequential | 7–12 | Grammar resolution, chess piece exchange |
| Non-logistic / flat | ~0–1 | Wow! Signal, Voynich, Spanish agreement |

Note: Spanish agreement (k=0) is a counterexample to simple domain→k mapping.
The true moderating variable is **coupling discreteness**, not domain label.
Continuous/simultaneous coupling → high k; discrete/sequential → low k.

---

## Trajectory Modes

DCP trajectories exhibit distinct qualitative patterns. Former candidate invariants
EIP and LIP have been dissolved and reclassified as DCP modes:

### Collapse (EIP mode)
- Breadth → near-zero; irreversible by construction
- Examples: Tamam Shud (solved 2022, k=20), Fermat's Last Theorem
- Signature: final breadth < 0.01, no direction reversals after collapse

### Floor / Stall (LIP mode)
- Breadth plateaus at non-zero value; structurally blocked from closing
- Sub-types by floor cause:
  - **Evidence exhaustion**: D.B. Cooper (breadth ~0.01, ~50K suspects, no discriminator)
  - **Technology gate**: Tamam Shud pre-2019 (IGG not yet available)
  - **Proven barrier**: P vs NP (3 mathematical barriers eliminate 77% of proof strategies)
  - **Computational wall**: Ramsey R(5,5) (range=6, frozen 15 years, superexponential cost)
- Signature: last 3+ events within ±0.005, final breadth > 0.01

### Oscillating
- Breadth ping-pongs; direction changes ≥ 3; k ≈ 1, R² < 0.1
- Examples: Wow! Signal (5 direction changes), abc conjecture (2), 'Oumuamua (6)
- Signature: no net convergence, competing hypotheses repeatedly challenge each other

### Anti-convergent
- Breadth (hypothesis count) expands over time; trend > +0.05
- Example: Voynich Manuscript (1 → 6 hypotheses over 112 years)
- Signature: net hypothesis count increasing, no eliminations sticking

### Latent collapse
- Long plateau followed by rapid collapse triggered by new tool/technology
- Example: Tamam Shud (74-year plateau, then IGG → solved in 12 months)
- Signature: plateau + sudden drop > 5× mean step size
- Prediction: other cold cases with known DNA on record are in latent collapse waiting

---

## Regime Transition Interaction

A single DCP trajectory may contain a **regime transition** — a discontinuity
separating two distinct DCP phases with different k values. See `regime_transition.md`.

Example: prime gaps — pre-transition k≈0 (164 years), Zhang 2013 transition
(step_ratio=3.1×), post-transition k=15 R²=0.985 (14 months, 70M→246).

---

## Predictions

1. Logistic shape holds in any domain with a well-defined possibility space
2. k is determined by coupling discreteness, not domain label
3. Trajectory mode (collapse/floor/oscillating/anti-convergent/latent) is
   predictable from the structural properties of the evidence stream
4. Technology-gated floors (latent collapse mode) are distinguishable from
   evidence-exhausted floors by: floor age, known missing tool type, and
   whether evidence events have stalled or are absent

---

## Falsifiers

1. Any substrate showing signal < 0.20 under equivalent conditions
2. Replication failure across substrates
3. k values that do not sort by coupling discreteness
4. A trajectory that is simultaneously logistic and has direction changes > 3

---

## Evidence

Original substrate runs:
- `decision_compression_20260315_040912_9b9715` (games, signal=0.4649) PASS
- `decision_compression_20260315_040916_72dd2a` (language, signal=0.3938) PASS
- `decision_compression_20260315_040916_7c0ec2` (music, signal=0.4273) PASS
- `decision_compression_20260315_041601_7b4116` (games, signal=0.4649) PASS
- `decision_compression_20260315_041604_e4fc0c` (language, signal=0.3938) PASS
- `decision_compression_20260315_041608_953714` (music, signal=0.4273) PASS
- `decision_compression_20260315_042458_8672e2` (games, signal=0.4649) PASS

Math domain probes (2026-03-25):
- `artifacts/math_ramsey.json` — k=75, R²=0.905 (compute-gated floor)
- `artifacts/math_prime_gaps.json` — k=15, R²=0.985 post-transition (regime transition)
- `artifacts/math_pnp.json` — k=10, R²=0.932 (proven-barrier floor)
- `artifacts/math_abc_mochizuki.json` — k=5, R²=0.635 oscillating

Mystery domain probes (2026-03-25) — `core/probes/math/probes/mystery_dcp_*.py`:
- D.B. Cooper: k=100, R²=0.999, plateau (evidence-exhausted floor)
- Cicada 3301: k=15–30 (designed collapse, cognitive range)
- Wow! Signal: k=1, R²=0.035 (oscillating, 5 direction changes)
- Oumuamua: k=1 oscillating (two-hypothesis race, evidence closed)
- Tamam Shud: k=20, R²=0.918 (latent collapse — solved 2022)
- Voynich: k=0.5, expanding (anti-convergent, +5 hypotheses over 112 years)
- SETI: solution k=7, R²=0.969 (coverage problem, 6/10 Fermi solutions remain)

GWT / cognition probes:
- Chess piece exchange: k=7–20 (language/cognitive range, discrete captures)
- GWT belief networks: k=15–20 (cognitive range confirmed)
- LLM agent: Bayesian accumulator — DCP not visible across turns, only within trace

---

## Notes

DCP is the primary structural invariant of Helix. EIP and LIP have been dissolved
into DCP trajectory modes. Regime Transition is a separate invariant that interacts
with DCP (detectable as discontinuity within a DCP trajectory).
