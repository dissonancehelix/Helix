# Ontology Test Report

**Test ID:** `ont_004_boundary`
**Test Name:** Inside-Outside Mapping
**Run Date:** 2026-04-26
**Run Type:** Model-driven — scored by Claude from DISSONANCE.md. This test is the hardest to fully evaluate in a model run because it requires behavioral evidence (novel categorization tasks, spontaneous organizational choices) rather than preference ratings. Scores are grounded in DISSONANCE.md text but the null hypothesis cannot be tested without live behavioral data.
**Operator State:** N/A (model run)
**Input Set:** `example_items.jsonl` filtered to `ont_004_boundary` — 4 items across workspace (2) and social (2)

---

## Note on Test Limitations

TEST 4 differs from the other five because its null hypothesis is behavioral, not preference-based. The null says: "cognitive style is associative or linear; inside/outside is post-hoc metaphor." Confirming or falsifying this requires watching the operator organize novel material without cuing boundary-first solutions. DISSONANCE.md is saturated with boundary language — but that could equally support the hypothesis (the operator genuinely thinks this way) or the null (the operator has learned to describe everything in boundary terms post-hoc). This run scores items; it cannot resolve that methodological gap.

---

## Scoring Summary

### Item 1 — `core/engine/contract/` (workspace, inside_outside)

**Analysis:**
The contract directory is defined entirely by what it protects and excludes. From README.md: "contract — schemas, validators, manifests, boundaries." There is no topic here — there is only a function (boundary enforcement). The inside contains: constraints that govern behavior at module interfaces. The outside contains: everything that uses those constraints but doesn't define them.

The question "what belongs here?" is answered not by topic but by role: does this file draw a boundary or enforce one? If yes, it belongs. If it just uses a boundary, it lives in the module that uses it.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `boundary_clarity` | 5 | 5 | 0 |
| `overall_response` | 4 | 4 | 0 |

**Result:** Confirmed. The contract directory is the clearest instantiation of inside/outside thinking in the workspace. It doesn't exist to hold related files — it exists because there is a real boundary that needs protecting. The overall_response is 4 not 5 because no workspace structure produces peak taste response; this is functional satisfaction, not attractor response.

---

### Item 2 — Generic `outputs/` root folder (workspace, inside_outside)

**Analysis:**
`outputs/` has no inside. It accepts anything from any source with no stated contract. The "boundary" is only grammatical (it's a folder) not functional (it doesn't protect anything). There is no inside because there is no principle of inclusion. Anything that was output can enter.

DISSONANCE.md: "Forbidden root-level names: outputs/, work/, misc/, archive/, notes/, labs/, old/, stuff/. Outputs live where their meaning lives." The rule exists because a generic outputs/ folder means you've stopped thinking about where things belong — you've replaced boundary-detection with a bucket.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `boundary_clarity` | 0 | 0 | 0 |
| `overall_response` | 0 | 0 | 0 |

**Result:** Confirmed. Maximum boundary failure. No inside/outside — just accumulation. The predicted response is immediate refactoring impulse. DISSONANCE.md: "the root is not where complexity lives. The root is where complexity becomes navigable." A generic outputs/ folder makes complexity un-navigable by erasing the boundaries that would organize it.

---

### Item 3 — Institution with hidden decision layer (social, inside_outside)

**Analysis:**
This is a false boundary case. The institution presents a public surface (accessible, open, stated values, visible process) but the real decision layer is hidden from participants. The surface boundary exists and is clearly drawn. The interior boundary — where decisions actually happen — is concealed.

The failure is not absence of boundary but false boundary: the stated inside is a performance, and the real inside is inaccessible. The boundary_clarity score (1) reflects that a boundary exists but points to the wrong interior.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `boundary_clarity` | 1 | 1 | 0 |
| `overall_response` | 1 | 1 | 0 |

**Result:** Confirmed. DISSONANCE.md threat taxonomy: "Institutional Unreality Threat — declared surface contradicts real machinery — everyone knows it — everyone must perform belief anyway." This is contempt-generating because the false boundary forces participation in unreality. The boundary exists; it's just pointing at a fake interior.

**Important distinction from Item 2:** Item 2 has no boundary (bucket). Item 3 has a misleading boundary (false surface). These are different failures. Item 2 generates frustration (cognitive load with no payoff). Item 3 generates contempt (active recognition of deliberate concealment). The different overall_response (0 vs 1) reflects this, but the distinction deserves explicit representation in the scoring schema.

---

### Item 4 — Person with stated values that actually govern behavior (social, inside_outside)

**Analysis:**
The claimed inside matches the actual inside. The stated boundary (what they will and won't do) is also the real boundary. Behavior at the boundary is predictable from the stated rules. This is the social equivalent of core/engine/contract/ — the contract is real, not decorative.

| Dimension | Predicted | Actual | Delta |
|---|---|---|---|
| `boundary_clarity` | 5 | 5 | 0 |
| `overall_response` | 4 | 4 | 0 |

**Result:** Confirmed. DISSONANCE.md: "alignment between words, behavior, and motive" as a trust-building marker. This is the clearest social inside/outside case: the stated rules govern the actual interior. The trust gate opens because the boundary is real, not performed.

**Parallel to Item 1:** Both items score boundary_clarity: 5, overall: 4. The workspace and social domains produce the same response to the same structural property (real, functional boundary). This cross-domain consistency is itself evidence for the boundary-as-cognitive-primitive hypothesis — if it were domain-specific, the scores would diverge.

---

## Result

- [x] **Confirmed** — all 4 items match predicted pattern
- **Methodological caveat:** confirmations here are based on DISSONANCE.md saturation, not behavioral evidence. The null hypothesis (inside/outside is post-hoc description) cannot be tested from profile text alone.

**Summary:** The four items cleanly separate into two categories: real boundaries (Items 1 and 4, boundary_clarity: 5, overall: 4) and boundary failures (Items 2 and 3). Within the failure category, two distinct failure modes emerge: absence of boundary (bucket) and false boundary (fake interior).

---

## Mechanistic Analysis

**Cross-domain consistency as evidence:** Both real-boundary items (workspace contract directory, person with real values) and both boundary-failure items (outputs/ folder, false institution) score identically within their categories across domains. This is not predicted by a domain-specific preference; it is predicted by the boundary-as-primitive hypothesis. A domain-specific preference for workspace organization would not predict the same response to the equivalent social structure.

**Two distinct boundary failure modes identified:**

| Mode | Example | Mechanism | Response |
|---|---|---|---|
| No boundary | `outputs/` folder | There is no inside; everything enters | Frustration/refactoring impulse |
| False boundary | Hidden-decision institution | The stated inside is a performance | Contempt/active aversion |

This distinction is not currently in the scoring schema. The `boundary_clarity` score captures both as low, but the response character differs. Needs a separate dimension or at minimum a notes field to distinguish.

**The false boundary finding is clinically important:** Most of the cases DISSONANCE.md identifies as threat-relevant (institutional unreality, NPC social scripts, influencer styling) are false boundary cases, not absent boundary cases. They perform an inside while concealing the real one. The ontology's most acute aversions are to false surfaces rather than to absence of surface — which implies the cognitive style is highly sensitive to deliberate concealment, not just disorganization.

---

## Falsification Notes

**The null hypothesis remains untested.** To actually test whether the cognitive style is boundary-first (not just describable in boundary terms), the operator would need to: (a) organize novel material without prior analysis, (b) explain their grouping logic, and (c) have that logic evaluated for boundary-vs-topic structure by a blind rater. Profile text cannot do this.

**Soft concern:** DISSONANCE.md may have been written *using* boundary language to describe preferences that could be equally well described in other terms. The test assumes the profile accurately represents the cognitive primitive. If the profile description is itself a learned frame (i.e., the operator learned to describe themselves in boundary terms and now applies that frame), the test would produce false confirmation.

---

## Next Sharpening Step

1. Add a behavioral protocol to TEST_PLAN.md: novel unsorted material + free categorization + rationale elicitation. This is the only test design that can directly probe the null hypothesis.
2. Add two failure-mode labels to the scoring notes: `boundary_absent` and `boundary_false`. These produce different response characters and should be distinguishable in runs.
3. Verify cross-domain consistency with a domain the operator hasn't already analyzed in boundary terms — e.g., a food taxonomy, a musical genre arrangement, or a relationship map constructed fresh.

