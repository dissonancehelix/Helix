# Cross-Test Synthesis — Run 01

**Date:** 2026-04-26
**Run type:** Model-driven (Claude from DISSONANCE.md). All predictions should be treated as model outputs, not confirmed operator responses. Items marked with `[VERIFY]` require live operator input before being treated as confirmed.

---

## What Held

**TEST 1 — Useful vs Waste Friction:** Clean across all 7 items. No edge cases. The useful/waste distinction is well-grounded in DISSONANCE.md and maps correctly across music, games, workspace, and social. The theory does real discriminating work here — "low friction" and "high useful friction" produce different overall_response profiles (3 vs 4–5), which a simple "likes easy things" model would not predict.

**TEST 2 — Channel Convergence:** Held cleanly for environments (Items 4–5 are drawn directly from DISSONANCE.md text). Held structurally for attraction (Items 1–3 require live verification). The core finding — moderate convergence outperforms high single channel — is the sharpest empirical claim in the test set and needs a live attraction test to move from model-predicted to confirmed. `[VERIFY: attraction items 1–3]`

**TEST 3 — Inspection Deepening/Collapse:** The strongest-performing test. The binary (deepen vs collapse) maps cleanly onto DISSONANCE.md's surface-as-portal vs surface-as-mask distinction. Outer Wilds and the articulate NPC are the anchor cases — both named or clearly derivable from the profile. The initial/post-inspection delta is the right measurement: this test does work that a simple preference rating would miss.

**TEST 4 — Boundary/Inside-Outside:** Confirmed at the scoring level but methodologically incomplete. The null hypothesis (inside/outside is post-hoc description, not a cognitive primitive) cannot be tested from profile text. The model produces the right predictions, but those predictions are drawn from a document saturated in boundary language. `[VERIFY: novel categorization task needed]`

**TEST 5 — Continuity Through Transformation:** Held well. Trails and workspace are the most secure cases. The breakage archetype (franchise abandoning mechanical invariants) maps correctly. The timbral texture question on Item 2 (remaster) is the only live edge case. `[VERIFY: timbral texture as invariant or surface property for specific loved tracks]`

**TEST 6 — Consciousness Bridge:** Functionally a claim tier audit rather than a preference test. All tier assignments correct with one fix (cl_010 promoted from philosophical_primitive to analogy — corrected in CLAIM_LEDGER.yaml). Key empirical anomaly: the Schechter/Pinto split-brain unity research directly challenges the non-branching prediction and needs to be addressed before that claim can be treated as empirically supported. `[VERIFY: teleporter intuition without theoretical priming]`

---

## What Needs Sharpening

**1. Waste friction tolerance is not flat — it gates on useful friction ceiling.**

The model treats useful_friction and waste_friction as independent scores and overall_response as their net. But the EFT case shows this is wrong: waste_friction: 1 produces no degradation when useful_friction: 5. A better rule: waste friction degrades overall_response only when useful friction cannot compensate. The tolerance band widens proportionally to the useful friction ceiling. This needs a specific formula or at minimum an explicit rule in TEST_PLAN.md.

**2. Two distinct boundary failure modes need separate treatment.**

`boundary_absent` (outputs/ folder: no inside exists) and `boundary_false` (hidden-decision institution: the stated inside is a performance) produce different response characters. Absent boundary → frustration/cognitive friction. False boundary → contempt/aversion. The scoring schema doesn't distinguish these. Both score boundary_clarity: 0–1, but the emotional register of the response differs significantly. Needs a notes tag or sub-dimension.

**3. Inspection collapse magnitude is domain-sensitive.**

Social collapse (NPC: initial 4 → final 0, active aversion) is sharper than artifact collapse (generic track: initial 3 → final 1, inertness). The theory predicts collapse in both domains but doesn't predict that social collapse is more complete and more aversive. This may matter: if the operator can tolerate inert music but cannot tolerate an exposed NPC, these are not equivalent collapse events. Needs explicit statement in TEST_PLAN.md.

**4. Timbral texture — invariant or surface property in music.**

DISSONANCE.md lists timbral weight and texture as a core taste mechanic. The theory currently treats it as surface (a substrate property that can change without identity loss). But if timbral texture is deeply bound to the identity of a specific track, a remaster that removes the warmth might feel like identity loss. This edge case is unresolved. Add a specific test case: a loved track with known analog warmth, remastered to digital sterility, and ask whether it feels like the same track.

**5. cl_010 (gradual neuron replacement) was miscategorized as philosophical_primitive.**

Now corrected to analogy. This matters: the claim illustrates the continuity principle by analogy but doesn't ground it empirically or philosophically for biological systems. If it were a primitive, it would need no further support. As an analogy, it requires additional support from empirical cases before it can do real theoretical work.

---

## What Was Anomalous or Deserves Pressure

**Anomaly 1: Split-brain unity challenge.** The Schechter/Pinto research argues that split-brain patients do not show the dramatic behavioral disunity that Gazzaniga's early work suggested. If this is correct, the non-branching prediction is under empirical pressure. The theory needs to engage with this directly — not by dismissing it, but by specifying what would and wouldn't count as disunity for the purposes of the claim.

**Anomaly 2: The self-model case (Item 5, TEST 5) is too self-referential.** Scoring continuity of the operator's self-model using the operator's own self-description document isn't a test — it's a mirror. The only real test here is whether the operator can identify a point in their own history where something felt discontinuous: a change that felt like loss rather than evolution. If no such point exists, the transformation_tolerance: 5 reading is provisional at best.

**Anomaly 3: TEST 6 is structurally different from tests 1–5 and probably shouldn't be run in the same format.** Tests 1–5 are measurable against actual preference responses. Test 6 is primarily conceptual — it tests whether the theory correctly classifies its own claims and predicts intuitions about thought experiments. The scoring schema (0–5 dimensions) doesn't fully map onto this. A better format for Test 6 would be: for each thought experiment, write the prediction, then ask the operator their intuition without prior framing, then compare. The current format scores how well the model models the cases, not whether the model is correct.

---

## Items That Need Live Operator Verification

| Test | Item | Reason |
|---|---|---|
| TEST 2 | Attraction Items 1–3 | Not drawn from explicit DISSONANCE.md text; structurally inferred |
| TEST 4 | All items | Null hypothesis untested without novel categorization task |
| TEST 5 | Item 2 (remaster) | Timbral texture edge case — need specific track example |
| TEST 5 | Item 5 (self-model) | Too self-referential; need specific discontinuity memory |
| TEST 6 | Teleporter intuition | Needs unprimed operator response |
| TEST 6 | Split-brain prediction | Needs engagement with Schechter/Pinto research |

---

## Model Strength Assessment

| Test | Model confidence | Discriminating power | Falsifiability |
|---|---|---|---|
| TEST 1 — Friction | High | High | High |
| TEST 2 — Convergence | Medium (environments high, attraction needs verify) | High | Moderate |
| TEST 3 — Inspection | High | Very high (largest deltas) | High |
| TEST 4 — Boundary | Medium (confirmed predictions, untestable null) | Moderate | Low without behavioral data |
| TEST 5 — Continuity | High (Trails/workspace), Medium (remaster/self) | High | High |
| TEST 6 — Bridge | Medium (tier audit solid, intuitions need verify) | Low (conceptual test) | Low without live trials |

**Highest-value next test:** Live TEST 3 run — pick two items the operator hasn't pre-analyzed, run the inspection ladder, compare. The inspection test has the highest discriminating power and the most immediately actionable format.

**Highest-risk model assumption:** TEST 2 attraction predictions. The convergence hypothesis for environmental preferences is well-grounded (DISSONANCE.md is explicit). The convergence hypothesis for attraction is structurally consistent but drawn from profile principles rather than named examples. A single case where the operator reports high overall_response for a single-dominant-channel stimulus would falsify the convergence prediction.

---

## Recommended Next Actions

1. Add the waste-friction tolerance rule to `TEST_PLAN.md` TEST 1 implementation notes
2. Add boundary failure mode tags (`boundary_absent`, `boundary_false`) to scoring notes
3. Add collapse magnitude domain-sensitivity to `TEST_PLAN.md` TEST 3
4. Add the timbral texture test case to `example_items.jsonl`
5. Add Schechter/Pinto to `inhabited_continuity/EMPIRICAL_CONTACTS.md`
6. Schedule live TEST 3 run with two unanalyzed items
7. Schedule live TEST 2 attraction verification with operator-rated items
