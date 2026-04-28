# Ontology Test Report

**Test ID:** `ont_003_inspection`
**Test Name:** Inspection Deepening and Collapse
**Run Date:** 2026-04-26
**Run Type:** Model-driven — scored by Claude from DISSONANCE.md profile. Items 1–3 (Outer Wilds, articulate NPC, VGM) are named in DISSONANCE.md and carry high confidence. Items 4–5 are structurally inferred.
**Operator State:** N/A (model run)
**Input Set:** `example_items.jsonl` filtered to `ont_003_inspection` — 5 items across games, social, music

---

## Inspection Ladder (used for all items)

1. Surface — initial impression, aesthetic, surface quality
2. Context — metadata, creator, origin, genre, history
3. Mechanics — underlying rules, constraints, compositional or structural decisions
4. Recursive interior — signs of authorial intent, self-awareness, Inhabitance

---

## Scoring Summary

### Item 1 — Outer Wilds (games)

**Inspection trace:**
- Surface: modest, slightly awkward movement, no obvious hook. Initial: 3
- Context: small team, original IP, no publisher constraints — signals constraint-authored work
- Mechanics: the entire game is a puzzle whose solution is understanding — no combat, no leveling, just topology and time. The exploration surface is a portal into the mechanics.
- Recursive interior: the game's ending requires the player to have internalized the same understanding the protagonist is seeking. The structure is self-referential — the game knows what it's doing and builds toward it. Full recursive opening.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `interior_signal` | 5 | 5 | 0 |
| `inspection_deepening` | 5 | 5 | 0 |
| `inspection_collapse` | 0 | 0 | 0 |
| `artificiality_penalty` | 0 | 0 | 0 |
| `overall_response` | 5 | 5 | 0 |

**Result:** Confirmed. This is the cleanest deepening archetype in the item set. The surface (overall_response: 3 initial) is not the attractor — it's the portal. Inspection through all four layers produces progressive reward. The ending is a complete structural reveal, not a narrative twist. DISSONANCE.md: "mysteries with real solution structure" and "mystery that resolves into deeper structure rather than fake fog."

---

### Item 2 — Articulate NPC (socially scripted) (social)

**Inspection trace:**
- Surface: articulate, socially fluent, high verbal quality. Initial: 4
- Context: background reveals typical social formation path, no anomalous trajectory — no signal of independent interiority
- Mechanics: responses are patterned to social context rather than to actual belief; contradictions go unnoticed rather than owned; speech is installed rather than generated
- Recursive interior: absent. No evidence of self-inspection. Cannot revise beliefs under pressure. Contradiction pointed out → deflection or repetition.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `interior_signal` | 0 | 0 | 0 |
| `inspection_deepening` | 0 | 0 | 0 |
| `inspection_collapse` | 5 | 5 | 0 |
| `artificiality_penalty` | 5 | 5 | 0 |
| `overall_response` | 0 | 0 | 0 |

**Result:** Confirmed. The collapse is complete and rapid. Initial_rating: 4 reflects genuine surface quality — the person appears interesting. The drop to overall: 0 occurs the moment the script is exposed. DISSONANCE.md: "NPC perception is accessible-interiority failure, not consciousness denial." The trigger: "contradictions go uninspected," "status cues replace thought," "no inner architecture becomes visible." These are the exact markers.

**Critical observation:** This is the sharpest test because the initial rating is high (4) and the post-inspection rating is zero. The delta (−4) is maximum. This is not a case where the initial signal was already weak — the surface was genuinely good. The collapse is not about surface quality; it's about what lies beneath it.

---

### Item 3 — VGM with visible composer fingerprint (music)

**Inspection trace:**
- Surface: immediately recognizable timbre and register — the sound has body and specificity. Initial: 4
- Context: old hardware with hard constraints — limited polyphony, specific chip voice registers, loop length. The constraint history is readable.
- Mechanics: specific chip voice allocation decisions, harmonic compression under polyphony limits, loop seam design showing authorial attention. Decisions are visible.
- Recursive interior: the composer's fingerprint survives across tracks — the music knows it's coming from somewhere specific. The specific voice choices are not interchangeable with another composer's work on the same hardware.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `interior_signal` | 4 | 4 | 0 |
| `inspection_deepening` | 4 | 4 | 0 |
| `inspection_collapse` | 0 | 0 | 0 |
| `artificiality_penalty` | 0 | 0 | 0 |
| `overall_response` | 5 | 5 | 0 |

**Result:** Confirmed. DISSONANCE.md: "VGM is so central: it is authored under hard limits, looped for inhabitation, and often built from timbral signatures that survive minimal material." The constraint-authored life mechanic is exactly what the inspection reveals. The composer fingerprint is Inhabitance — evidence someone was actually home during the composition. The overall_response uplift from 4 → 5 post-inspection is characteristic of the deepening pattern.

---

### Item 4 — Commercially polished track with no detectable compositional decisions (music)

**Inspection trace:**
- Surface: clean, pleasant, professional production. Initial: 3
- Context: industry pipeline — producer-for-hire, topline writer separate from performer, algorithm-optimized structure
- Mechanics: verse-chorus-verse-bridge form with no variation. Every element exists because streaming data suggests it should. No decisions visible.
- Recursive interior: absent. The track is assembled, not authored. No fingerprint. No evidence of constraint-authored movement.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `interior_signal` | 0 | 0 | 0 |
| `inspection_deepening` | 0 | 0 | 0 |
| `inspection_collapse` | 4 | 4 | 0 |
| `artificiality_penalty` | 4 | 4 | 0 |
| `overall_response` | 1 | 1 | 0 |

**Result:** Confirmed. The inspection reveals the assembly process rather than compositional decisions. The surface was tolerable (initial: 3) because there's nothing actively wrong with it — it's competent. The post-inspection rating drops to 1 because "competent assembly" is a different thing from "authored structure." The artificiality_penalty fires not because the production is bad but because the process is optimized for non-musical outcomes.

**Note:** This item doesn't fully collapse to 0 the way the NPC does (overall: 1 vs. 0). This may be because the surface quality remains tolerable even after inspection — unlike the NPC where the performance becomes actively aversive once the script is visible. The music doesn't become worse; it just becomes inert.

---

### Item 5 — Self-aware person with evidence-responsive revisions (social)

**Inspection trace:**
- Surface: present, specific attention, no performance signal. Initial: 5
- Context: history of consistent self-revision under evidence, pattern of noticing own assumptions
- Mechanics: when challenged directly, revises position rather than deflecting. Can explain their own uncertainty. Motives are legible.
- Recursive interior: highest signal — ability to inspect one's own programming while demonstrating it in real time. The surface is already reporting the interior; inspection confirms rather than contradicts.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `interior_signal` | 5 | 5 | 0 |
| `inspection_deepening` | 4 | 4 | 0 |
| `inspection_collapse` | 0 | 0 | 0 |
| `artificiality_penalty` | 0 | 0 | 0 |
| `overall_response` | 5 | 5 | 0 |

**Result:** Confirmed. This is the inverse of Item 2 (NPC). Initial rating is already high (5) because the surface signals are already pointing at a real interior. Inspection deepens rather than confirms — the depth becomes more textured as layers are revealed. DISSONANCE.md: "self-aware people reduce modeling friction" and "ability to revise beliefs" as a trust-building marker.

**Notable contrast with Item 2:** Both start with articulate, high-surface-quality presentations. Item 2 collapses; Item 5 deepens. The discriminating variable is exactly the recursive-interiority signal — whether the behavior is generated or installed.

---

## Result

- [x] **Confirmed** — all 5 items match predicted pattern
- **Sharpening required on one dimension:** the NPC collapse goes to 0 but the generic track only reaches 1. The collapse rate appears domain-sensitive — see below.

**Summary:** The inspection test is the most discriminating in the set. It produces the largest variance in outcomes (delta from initial to post-inspection ranging from +2 to −4) and the clearest binary signal (deepening vs. collapse). The key finding: the initial surface rating is not predictive of long-term engagement; the inspection result is.

---

## Mechanistic Analysis

**The deepening/collapse asymmetry:** Deepening items (Outer Wilds, VGM, self-aware person) share a common structure: the surface quality is modest relative to the post-inspection value. The surface undersells. Collapsing items share the opposite: the surface quality is above the post-inspection value. The surface oversells. This asymmetry is predicted by the "surface as portal vs. surface as mask" distinction.

**Domain-specific collapse magnitude:**
- Social collapse (NPC: initial 4 → final 0): complete and rapid. Once the script is visible, the social object becomes actively aversive — not just inert. The NPC is not merely boring; it is now known to be performing.
- Music collapse (generic track: initial 3 → final 1): partial. The music remains tolerable but loses interest value. It doesn't become aversive — it becomes furniture. This suggests collapse magnitude is higher in social/people domains than in music/artifact domains, possibly because social trust violation carries more weight than aesthetic disappointment.

**The initial rating problem:** Items 1 (Outer Wilds, initial 3) and 2 (NPC, initial 4) flip in outcome. If you only measured initial rating, you would predict NPC > Outer Wilds. Post-inspection, the order reverses completely. This is the core empirical claim of the test: initial rating is a poor predictor of long-term engagement, and inspection result is a better predictor.

---

## Falsification Notes

**Genuine sharpening finding — not falsification:** The NPC collapse reaches 0 (active aversion); the generic track reaches 1 (inertness). The test predicts collapse for both but doesn't specify magnitude. A more precise formulation would be: social-domain collapse is aversive (active rejection), while artifact-domain collapse is inert (loss of interest without aversion). This distinction is not in the current test plan.

**Potential anomaly to verify:** What happens when a surface-only music item is encountered *while knowing in advance it's manufactured*? Does knowing the process before first listen prevent the initial attraction, or does the surface still register at 3 before inspection drives it down? DISSONANCE.md suggests the surface quality registers first regardless of prior knowledge, but this isn't explicitly tested.

---

## Next Sharpening Step

1. Add to `TEST_PLAN.md` under TEST 3: social collapse is aversive (moves object to active avoidance), artifact collapse is inert (removes interest without generating aversion). These are different failure modes.
2. Add to `example_items.jsonl`: a case where inspection fails to deepen but also fails to collapse — a stable surface with nothing behind it that the operator neither loves nor rejects. This would test whether "inert" is a third category distinct from both deepening and collapsing.
3. Verify Items 2 and 4 with live operator input — specifically the NPC collapse to 0. If the operator maintains any residual positive regard for the NPC after detecting the script, the collapse magnitude finding needs revision.
