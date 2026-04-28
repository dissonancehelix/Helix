# Unresolved Edge Cases

Cases where the model-driven Run 01 produced a prediction but could not confirm or falsify it. Each case requires live operator input or a specific test design before the prediction can be treated as anything more than a model-generated hypothesis.

---

## Edge Case 1 — Attraction Convergence Requires Live Ratings

**Test:** TEST 2 — Channel Convergence
**Status:** Unresolved — inferred, not confirmed

**The issue:** The convergence model for attraction (items 1–3 in `example_items.jsonl`) is structurally derived from DISSONANCE.md principles, not from named examples. The model predicted that peak attraction requires multi-channel convergence — facial architecture, tonal depth, body structure, and presentation/styling must align without contradiction for overall_response to reach 4–5.

The environment items (named and explicit in DISSONANCE.md) confirmed cleanly. The attraction items did not. They cannot be confirmed from profile text alone because the profile describes the principle but does not name specific cases with known channel-by-channel ratings.

**What falsifies it:** A single reported case where one channel dominates at 5 (e.g., exceptional facial architecture) while others contradict, but overall_response is still 4–5. This would mean a single strong channel can dominate convergence — falsifying the multi-channel model for attraction specifically.

**What would confirm it:** Live ratings where channels are scored independently before gestalt, across at least 3–4 items with varying channel profiles. If gestalt tracks convergence and not any single peak channel, the model is confirmed.

**Required test design:** Channels must be rated in isolation before gestalt is recorded. Do not rate overall first. Use descriptive structural labels (facial architecture type, styling register, tonal contrast level) rather than photos or names.

---

## Edge Case 2 — Timbral Texture May Be Identity-Bearing, Not Mere Surface

**Test:** TEST 5 — Continuity Through Transformation
**Status:** Unresolved — edge case on Item 2 (remaster)

**The issue:** DISSONANCE.md lists timbral weight and texture as a core taste mechanic. The Run 01 model assigned it to the surface layer — a substrate property that can change without identity loss, analogous to art style in games.

But timbral texture may be differently categorized for specific deeply-loved tracks. A remaster that improves technical quality but removes analog warmth (or replaces a particular hardware synthesis texture with digital sterility) might produce experienced identity loss — not preference degradation, but felt discontinuity — even when the arrangement, harmonic structure, loop seam, and compositional decisions all survive unchanged.

If this is true, timbral texture is an invariant for those tracks, not a surface. It would require upgrading "timbral weight and texture" from taste mechanic to identity invariant (at least in specific cases), and revising the predicted score for substrate-change remasters downward.

**What falsifies the current model (timbral = surface):** The operator reports a specific remaster of a loved track that feels wrong due to timbral texture loss, and the judgment is stable over time (not just first-listen novelty aversion).

**Required test design:** Pick one specific loved track with known analog warmth or hardware synthesis character. Find or produce a remaster that changes the timbral texture significantly while preserving arrangement. Rate: does this feel like the same track, or a different track? Repeat after one week to check stability.

---

## Edge Case 3 — Boundary Language May Be Post-Hoc Unless Tested with Novel Categorization

**Test:** TEST 4 — Inside-Outside Mapping
**Status:** Unresolved — methodological gap in null hypothesis

**The issue:** DISSONANCE.md is saturated with boundary language. This is true for an obvious reason: the profile was written by the operator, who uses boundary framing to describe everything. This creates a circularity problem. The test confirms that the model can predict boundary-structured responses from boundary-structured input. It does not confirm that boundary-first organization is the operator's actual cognitive primitive — rather than a learned description frame applied post-hoc to preferences that could be equally described in other terms.

The null hypothesis says: inside/outside is a metaphor used in description, not an active organizational primitive. If the null is true, the operator's actual sorting behavior when given novel material would produce flat topic clusters indistinguishable from a standard categorical organizer.

DISSONANCE.md cannot adjudicate between these. Profile text cannot test its own organizational primitive.

**What would confirm the hypothesis (boundary is primitive):** Given novel unsorted material in a domain the operator hasn't already mapped in boundary terms — a food taxonomy, a relationship map, an unfamiliar codebase structure — the operator spontaneously groups by boundary function (what does this protect, what does it exclude) rather than by topic surface, without prompting.

**Required test design:** Novel categorization task (not one already built in Helix). Provide raw unsorted material. Ask for groupings. Ask for explicit rationale. Have rationale evaluated for boundary-vs-topic structure. No cueing of boundary framing.

---

## Edge Case 4 — Teleporter Intuition Must Be Tested Without Theoretical Priming

**Test:** TEST 6 — Consciousness Bridge
**Status:** Unresolved — unprimed verification required

**The issue:** Claim cl_007 (teleporter duplicate is a new entity, not the same self) is classified as a philosophical primitive in CLAIM_LEDGER.yaml. The theory's primary test for a philosophical primitive is whether it predicts the operator's considered intuitions. THEORY.md explicitly states this position — so the model run confirmed agreement between THEORY.md and the claim.

But THEORY.md was written by the same operator who holds the theory. A self-referential document cannot independently verify intuitions about the self. The only genuine test is: can the operator produce the same intuition from scratch, without the theoretical frame active, in response to the bare thought experiment?

This is not a trivial concern. It is possible the operator's "intuition" that the copy is not them is the theoretical conclusion reasoning its way backward to phenomenology rather than a pre-theoretical response.

**What the test requires:** Present the teleporter thought experiment without any theoretical context. Ask for the pre-reflective intuition first: "Is the copy you, or not?" Then allow reflection. Record both. The pre-reflective intuition is the data point; the reflective answer may simply report the theory.

**Important:** If the operator's pre-reflective intuition is that the copy IS them, cl_007 fails its primary test. The theory must accommodate this, not explain it away.

---

## Edge Case 5 — Social Collapse and Artifact Collapse Should Not Be Averaged

**Test:** TEST 3 — Inspection Deepening / Collapse
**Status:** Confirmed finding, not unresolved — but requires explicit scoring protocol

**The issue:** Run 01 confirmed that collapse events differ by domain. Social collapse (articulate NPC: initial 4 → post-inspection 0, active contempt) and artifact collapse (generic ambient track: initial 3 → post-inspection 1, inertness) are not equivalent even when scored as the same result type ("collapsed").

The response character differs significantly. Social collapse produces active aversion — the exposed NPC is not inert, it triggers a recognition of deliberate concealment that generates contempt. Artifact collapse produces inertness — the track is simply demoted, with no active response component. The delta is large in both cases, but the phenomenology differs.

**Why averaging is wrong:** If you compute an average collapse delta across items, you flatten a mechanistically important difference. The theory predicts that false-boundary cases (social: the NPC performed an interior that wasn't there) produce stronger aversion than absent-interior cases (artifact: the track had nothing underneath). This asymmetry is itself a prediction — it would be falsified by an artifact collapse that generates contempt at social-collapse intensity, or a social collapse that produces mere inertness.

**Required protocol update:** When recording collapse events in live Test 3 runs, note domain and response character separately. Do not aggregate collapse deltas across domains without first checking whether the response characters are comparable. See scoring sheet: `live_test_003_scoring_sheet.md`.
