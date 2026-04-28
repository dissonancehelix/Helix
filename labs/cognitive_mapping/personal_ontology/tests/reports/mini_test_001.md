# Mini-Test Report 001

**Date:** 2026-04-26
**Run type:** Model-driven synthesis — all six personal ontology tests scored from DISSONANCE.md by Claude.
**Source runs:** `runs/ont_001_friction_run_01.md` through `runs/ont_006_bridge_run_01.md` + `runs/synthesis_run_01.md`
**Status:** Items marked [VERIFY] require live operator input before being treated as confirmed.

---

## Summary by Test

### TEST 1 — Useful Friction vs Waste Friction
**Result: Confirmed across all 7 items. No edge cases.**

The useful/waste distinction does real discriminating work. Low-friction items score overall 3–4 with predicted decay. High useful-friction items (EFT, IDM, difficult Spanish grammar) score 4–5 with persistence. High waste-friction items (laggy menus, social noise, unskippable cutscenes) score 0–1 regardless of surface quality.

A simple "likes easy things" model would not produce this profile — low friction (3) and high useful friction (4–5) score differently, which requires the two-axis distinction to be real.

**Key finding:** Waste friction tolerance is not flat. EFT (waste_friction: 1, useful_friction: 5, overall: 5) showed that waste friction degrades overall_response only when useful friction cannot compensate. The tolerance band scales with the useful friction ceiling.

---

### TEST 2 — Channel Convergence
**Result: Confirmed for environments. Held structurally for attraction. [VERIFY: attraction items 1–3]**

Environment items (drawn directly from DISSONANCE.md text) confirmed cleanly. Forested mountain camp at dusk and rain/train/library items both scored overall 5 with high convergence (5) and low artificiality (0–1). The fragmented stimuli (industrial noise, bright open floor plan) scored overall 1–2 with low convergence (1–2).

The core claim — moderate convergence outperforms high single channel — is the sharpest empirical prediction in the suite. It held on environments. The three attraction items are structurally inferred from profile principles, not named examples; one case of high overall_response for a single-dominant-channel stimulus would falsify the model.

**[VERIFY]:** Attraction items 1–3 need live operator ratings with channels rated independently before gestalt.

---

### TEST 3 — Inspection Deepening / Collapse
**Result: Confirmed. Highest discriminating power of the six tests.**

The binary (deepen vs collapse) maps cleanly onto DISSONANCE.md's surface-as-portal vs surface-as-mask distinction. Outer Wilds is the anchor case for deepening (initial 3 → post-inspection 5). The articulate NPC is the anchor case for collapse (initial 4 → post-inspection 0).

The initial/post-inspection delta is the right measurement — this test does work that a simple preference rating would miss entirely.

**Key finding:** Collapse magnitude is domain-sensitive. Social collapse (NPC: 4 → 0, contempt, active aversion) is sharper and more aversive than artifact collapse (generic ambient track: 3 → 1, inertness). Both are collapse — but they're not equivalent events and should not be averaged.

---

### TEST 4 — Boundary / Inside-Outside Mapping
**Result: Confirmed at the scoring level. Methodologically incomplete.**

All four items matched predicted pattern. Real-boundary items (contract/ directory, person whose stated values govern behavior) both scored boundary_clarity 5, overall 4. Boundary-failure items scored 0–1. Cross-domain consistency — identical scores for equivalent structural properties in workspace and social domains — is itself evidence for the boundary-as-primitive hypothesis.

**Caveat:** The null hypothesis cannot be tested from profile text. DISSONANCE.md is saturated in boundary language, which could mean the operator genuinely thinks this way, or that he has learned to describe associative preferences in boundary terms post-hoc. Only a novel unsorted categorization task with rationale elicitation can distinguish these.

**Key finding:** Two distinct boundary failure modes — `boundary_absent` (frustration/refactoring impulse) vs `boundary_false` (contempt/active aversion). Most of DISSONANCE.md's threat taxonomy is false-boundary, not absent-boundary.

**[VERIFY]:** All items — null hypothesis requires behavioral evidence.

---

### TEST 5 — Continuity Through Transformation
**Result: Confirmed across all 5 items.**

Identity tracks invariant survival, not surface or substrate. Trails series scored overall 5. Franchise breakage scored overall 0. Helix workspace refactors scored overall 5. The remaster (overall 4) and self-model (overall 4) demonstrate graded preservation.

**Unresolved edge case:** Timbral texture. DISSONANCE.md lists timbral weight and texture as a core taste mechanic. The theory currently treats it as surface. If it's identity-bearing for specific loved tracks, a remaster that removes analog warmth produces experienced identity loss even with arrangement intact.

**[VERIFY]:** Item 2 (timbral texture). Item 5 (self-model continuity — too self-referential as scored; need a specific discontinuity memory from 2020–2026).

---

### TEST 6 — Consciousness Bridge
**Result: Claim tier audit correct with one fix. Empirical anomaly flagged.**

All 5 thought experiment items confirmed. **cl_010 corrected from `philosophical_primitive` to `analogy`.** Interior_signal / continuity_preservation independence confirmed across items: LLM (3/0) and split-brain hemisphere (3/1) both show strong self-modeling without temporal thread.

**Key anomaly:** Schechter/Pinto split-brain research. If split-brain patients genuinely report unity without confabulation under conditions designed to isolate hemispheres, the non-branching continuity requirement (cl_004) is under direct empirical pressure.

**[VERIFY]:** Teleporter intuition without theoretical priming (cl_007 — cannot be confirmed from a document written by the person who holds the theory).

---

## Cross-Test Model Strength

| Test | Confidence | Discriminating Power | Falsifiability |
|---|---|---|---|
| TEST 1 — Friction | High | High | High |
| TEST 2 — Convergence | Medium | High | Moderate |
| TEST 3 — Inspection | High | Very high | High |
| TEST 4 — Boundary | Medium | Moderate | Low (no behavioral data) |
| TEST 5 — Continuity | High (mostly) | High | High |
| TEST 6 — Bridge | Medium | Low (conceptual) | Low (needs live trials) |

---

## Items Requiring Live Verification

| Test | Item | Reason |
|---|---|---|
| TEST 2 | Attraction Items 1–3 | Structurally inferred, not from named DISSONANCE.md examples |
| TEST 4 | All items | Null hypothesis untested without novel categorization task |
| TEST 5 | Item 2 (remaster) | Timbral texture edge case — need specific track |
| TEST 5 | Item 5 (self-model) | Too self-referential; need specific discontinuity memory |
| TEST 6 | Teleporter intuition | Needs unprimed operator response |
| TEST 6 | Split-brain prediction | Needs engagement with Schechter/Pinto research |

---

## Recommended Next Actions

1. **Highest-value:** Live TEST 3 run — two unanalyzed items, inspection ladder, compare deltas
2. **Highest-risk assumption:** TEST 2 attraction predictions — one falsifying case ends the convergence claim
3. Add Schechter/Pinto to EMPIRICAL_CONTACTS.md as direct pressure on cl_004
4. Resolve timbral texture: invariant or surface property? Add specific test case
5. Design novel categorization task for TEST 4 null hypothesis
