# Pre-Registration: DCP k_eff Ordering for Unseen Languages

**Date**: 2026-03-22
**Status**: PRE-REGISTERED — predictions locked before UD data collection
**Purpose**: Make DCP cross-linguistic claims falsifiable by predicting before seeing data

---

## What This Is

The grammar_resolution fixtures for 16 languages currently use hand-set weights
(see [cross_domain_formalism.md](cross_domain_formalism.md) for why this matters).
We are now replacing those with UD-treebank-derived weights via
`ud_calibrate_weights.py`.

Before running calibration on *any* new language, we lock in predictions here.
If the post-calibration k_eff ordering matches predictions, DCP has passed a
genuine test. If it doesn't, the theory needs revision — not the data.

---

## Five Unseen Languages (Not Yet in the Suite)

These languages are not in our current 16. We predict their k_eff ordering
before adding UD treebank entries or fixture files.

| Language | ISO | Family | Typological signature |
|----------|-----|--------|----------------------|
| Swahili  | sw  | Bantu (Niger-Congo) | Highly agglutinative noun-class agreement; verb-initial possible |
| Vietnamese | vi | Austroasiatic (Vietic) | Isolating, strict SVO, tonal, zero morphology |
| Persian/Farsi | fa | Iranian (Indo-European) | SOV, case nearly gone, rely on word order + ezafe construction |
| Bengali  | bn  | Indo-Aryan | SOV, moderate morphology, ergativity in perfective aspect |
| Urdu     | ur  | Indo-Aryan | Near-identical to Hindi, SOV + ergative split |

---

## Predictions

### Theoretical basis

k_eff = 1 / Σᵢ wᵢ²

where wᵢ are normalized rule weights. Lower k_eff = sharper compression = more
constrained parse space. The DCP prediction: languages with stronger morphological
disambiguation (high case/agreement density from UD) will have LOWER k_eff because
one rule dominates heavily.

**Core typological predictions:**

- **Rich case morphology** → one rule dominates → k_eff LOW (Finnish-like)
- **Rich verbal agreement** → case + agreement share weight → k_eff MODERATE
- **No morphology, rigid order** → order dominates but weaker than case → k_eff MODERATE-HIGH
- **No morphology, flexible discourse** → pragmatic residual grows → k_eff HIGH (Mandarin-like)

### Language-specific predictions

**Swahili** (Bantu noun-class agreement):
Swahili verbs prefix-agree with both subject and object in person, number,
AND noun class (one of 8-15 classes). This is the richest agreement system
in our suite. Both the case-signal AND agreement-signal will be very high.
When two signals compete, weights spread → k_eff stays moderate.
**Prediction: k_eff ≈ 1.8–2.6** (lower than Hindi, higher than Finnish)

**Vietnamese** (isolating, zero morphology):
No case. No agreement. SVO order rigid. Closest to Mandarin in the typological
space, but with even fewer discourse-structure markers. Word order will dominate
completely.
**Prediction: k_eff ≈ 2.9–4.1** (similar to or slightly above Mandarin 2.6–3.8)

**Persian** (SOV, lost case):
Old Persian had 8 cases; Modern Persian retains traces only in pronoun series.
Primary disambiguation: SOV word order + ezafe (-e) construction for NP linkage.
Agreement is moderate (person/number on verbs but not gender).
**Prediction: k_eff ≈ 3.2–4.4** (higher than Hindi because case nearly gone)

**Bengali** (SOV + aspectual ergativity):
Moderate case system (genitive, locative, objective postpositions). Verb agreement
in perfective erases subject-verb agreement (ergative pivot). Similar typological
profile to Hindi but with less morphological richness.
**Prediction: k_eff ≈ 2.8–3.8** (between Hindi and Persian)

**Urdu** (nearly identical to Hindi):
Urdu and Hindi share grammar; they diverge in script and vocabulary. The ergative
split and postposition system should produce near-identical UD statistics.
**Prediction: k_eff ≈ 2.4–3.6** (within ±0.3 of Hindi's calibrated result)

---

## Predicted Ordering

From lowest k_eff (sharpest compression) to highest:

```
Swahili < Urdu ≈ Hindi < Bengali < Vietnamese ≈ Persian < English
  ~2.2       ~2.5-2.7     ~3.3      ~3.5-4.0      ~3.8-4.4   ~3.5-4.0
```

This ordering prediction is falsifiable. If Vietnamese comes out LOWER than
Hindi (i.e., word-order-dominant languages produce sharper compression than
case-dominant ones), DCP's core claim about morphological pre-compression
would need revision.

---

## Falsification Criteria

The prediction FAILS if:
1. Swahili k_eff > 3.0 (high agreement should produce k_eff below 3.0)
2. Vietnamese k_eff < Hindi k_eff (isolating language should NOT compress faster)
3. Urdu k_eff differs from Hindi by more than ±0.5 (typologically near-identical)
4. Persian k_eff < Bengali k_eff (Persian has less morphology, should be higher)

---

## Protocol

1. Lock this document in git before running `ud_calibrate_weights.py` on any
   new language.
2. Add UD registry entries for the 5 languages above.
3. Run calibration.
4. Compute k_eff from calibrated weights.
5. Compare to predictions here.
6. Update [cross_domain_formalism.md](cross_domain_formalism.md) with outcome.

---

## Why This Matters

Without pre-registration, any result can be explained post-hoc:
> "Of course Swahili has low k_eff — it has rich agreement."

With pre-registration, we can only say that BEFORE seeing the number. The value
of the prediction is that it could have been wrong. If the ordering holds across
5 new languages, DCP is making real cross-linguistic predictions, not fitting curves.
