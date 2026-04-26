# Cross-Domain DCP Formalism

**Status**: DRAFT — not yet tested against empirical data from all three domains
**Date**: 2026-03-22

---

## The Problem

We observed that k_eff values from language grammar resolution (~2.0–4.0) overlap
with the Kuramoto critical coupling zone (~2.5–3.0). This was presented as evidence
that language and oscillator synchronization share a common mechanism.

That comparison was post-hoc and analogical. Two systems having numbers in the same
range is not evidence of a shared mechanism. This document writes the actual shared
equation and specifies what evidence would make the analogy real.

---

## The Shared Quantity

In both systems, the central observable is **k_eff**: the effective number of
distinguishable trajectories or states the system occupies.

**Definition (domain-neutral)**:

```
k_eff = 1 / Σᵢ pᵢ²
```

where pᵢ is the probability (weight) of the i-th trajectory, and the sum runs
over all trajectories with pᵢ > 0. This is the inverse Herfindahl–Hirschman
index, equivalently the exponential of the Shannon entropy under base-e.

k_eff = N means all trajectories have equal weight (maximally uncertain).
k_eff = 1 means one trajectory dominates completely (collapsed/locked).

---

## Language Instantiation

In the grammar_resolution model, each *agent* (grammatical rule) carries weight
wᵢ representing how much of the disambiguation work it does. After UD calibration,
wᵢ comes from actual treebank statistics (case density, agreement density,
order rigidity).

The pᵢ in the shared formula ARE the wᵢ (normalized):

```
p_case       = w_case / Σ w_j
p_agreement  = w_agreement / Σ w_j
p_word_order = w_word_order / Σ w_j
p_pragmatic  = w_pragmatic / Σ w_j

k_eff_language = 1 / (p_case² + p_agreement² + p_word_order² + p_pragmatic²)
```

A **DCP event** in language = the moment one rule fires and drives k_eff from its
pre-constraint value toward 1. The compression happens when a morphological signal
(case marker, agreement suffix) is encountered and one parse interpretation is
selected over others.

---

## Kuramoto Instantiation

The Kuramoto model describes N coupled oscillators with natural frequencies ωᵢ
and coupling constant K. Above the critical coupling K_c, oscillators synchronize.

The order parameter r(t) = |⟨e^{iθⱼ}⟩| measures global synchrony: r=0 is
incoherent, r=1 is fully locked.

For the Kuramoto system, the **trajectory distribution** is:
- Pre-synchronization (K < K_c): oscillators are independent, each exploring its
  own phase trajectory. With N oscillators, pᵢ = 1/N → k_eff = N.
- At criticality (K = K_c): a subset of oscillators begins to lock. The locked
  cluster has weight proportional to the fraction that synchronize, r².
  k_eff_kuramoto ≈ 1 / r²(K) for K near K_c.
- Post-synchronization (K >> K_c): r → 1, k_eff → 1.

The same formula:

```
k_eff_kuramoto = 1 / Σᵢ pᵢ²
```

where pᵢ is now the fraction of oscillators in synchronized cluster i.

---

## The Shared Structure

Both systems exhibit a **transition** from high k_eff (many trajectories) to low
k_eff (few trajectories) triggered by a **coupling threshold**.

| Domain   | Coupling constant K | Critical threshold | k_eff before | k_eff after |
|----------|--------------------|--------------------|--------------|-------------|
| Language | Rule weight w₁     | dominant_mass ≥ 0.70 | ~3–4       | ~1.5–2     |
| Kuramoto | Physical K         | K_c (Lorentzian ω) | ~N         | ~1         |

The DCP event in language IS the transition from k_eff_pre to k_eff_post.
The synchronization event in Kuramoto IS the same transition.

---

## What Would Make This a Real Discovery

The current comparison rests on:
1. Both systems use the same k_eff formula ✓ (trivially true — we defined it for both)
2. Both systems show a transition from high to low k_eff ✓ (also trivially true
   for any system with phases)
3. The transition thresholds occur in overlapping numeric ranges ✗ (post-hoc)

To make this a real discovery, we need at least one of:

### A. Cross-prediction
Predict the dominant coupling constant for a language FROM Kuramoto theory
(not from the language's own data), then test whether the grammar_resolution
weights match.

Kuramoto K_c = 2 * std(ω) / π for Lorentzian frequency distribution.
Analogously: "coupling strength" in language = how strongly a rule fires =
something we can measure independently of the weights (e.g., frequency of the
disambiguation context in corpus).

If we measure: K_language = frequency(morphological_context) independently,
and predict: k_eff = f(K_language) using the Kuramoto formula, then check
whether this matches the UD-derived k_eff — THAT would be cross-prediction.

### B. The DCP event timing
Kuramoto predicts WHEN synchronization occurs (as a function of K).
Language: predict WHICH WORD POSITION in the sentence the compression event
fires (the word that bears the disambiguating morpheme).

If both follow the same trajectory: k_eff decreasing monotonically as the
"constraint density" increases across the sentence, with a phase transition
at the same relative point in both domains — that would be structural identity,
not analogy.

### C. A quantity that only appears if the mechanism is shared
The Kuramoto model predicts the **order parameter** r as a function of K.
If language disambiguation follows the same r(K) curve — not just the same
formula for k_eff, but the same functional form of the TRANSITION — that
would be a genuine prediction.

Currently we cannot test A, B, or C because:
- We don't have K_language measured independently
- We don't have sentence-position-resolved k_eff traces
- We don't have r(K) curves for language

These are the next real experiments.

---

## Current Claim (honest)

DCP is currently a **CANDIDATE** invariant. The shared formula is a productive
hypothesis, not a confirmed mechanism. The evidence:

1. The k_eff formula applies to both systems ✓ (by construction)
2. Grammar_resolution fixtures show k_eff in expected range per language ✓
   (now data-derived via UD calibration, not hand-set)
3. Null model signal gap emerges independently (not hand-tuned) ✓
4. Cross-domain transition analogy is suggestive, not proven ✗

The claim we CAN make: **morphologically-rich languages show lower k_eff than
morphologically-poor languages** — and this is now testable because the weights
come from UD treebanks, not from our beliefs. If the k_eff ordering after UD
calibration matches typological predictions (see ud_preregistration.md), DCP
has earned its "Candidate" classification.

The claim we CANNOT yet make: that language disambiguation and oscillator
synchronization are the same phenomenon governed by the same equation.
