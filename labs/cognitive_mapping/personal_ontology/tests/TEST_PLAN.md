# Personal Ontology Test Plan

**Purpose:** Falsify, sharpen, and validate the Dissonance personal ontology. Each test targets a specific mechanistic claim. The goal is not to protect the theory — it is to find what survives pressure.

**Scoring:** All dimensions use 0–5. See `scoring_schema.json` for full scale definitions.

**Registry:** `test_registry.yaml` — machine-readable index of all tests.

**Template:** `system/engine/run/templates/test_report_template.md` — use for all run reports.

**Run outputs:** Write to `labs/research/personal_ontology/tests/runs/` (gitignored).

---

## TEST 1 — Useful Friction vs Waste Friction
**ID:** `ont_001_friction`

**Core Question:** Does the operator prefer low friction generally, or specifically low waste friction with tolerance for high useful friction?

**Hypothesis:** The operator values load-bearing difficulty (useful friction) that reveals structure, teaches mastery, or generates discovery payoff. He rejects energy-leaking difficulty (waste friction) caused by poor design, arbitrary obstruction, or social noise. The distinction is not about degree of resistance but about whether the resistance resolves into something.

**Null Hypothesis:** The operator prefers low friction overall. The useful/waste distinction is an ex-post-facto rationalization for simple laziness or inconsistent thresholds. If true, both useful and waste friction should correlate negatively with engagement.

**Required Data:** Comparative pairs drawn from music, games, workspace, and social domains — matched for surface-level difficulty but divergent on whether the friction is load-bearing or leaking. Pairs must include: (a) low friction, (b) high useful friction, (c) high waste friction.

**Scoring Dimensions:**
- `useful_friction` (0–5): load-bearing resistance present in the stimulus
- `waste_friction` (0–5): energy-leaking resistance present in the stimulus
- `overall_response` (0–5): net engagement/attraction

**Predicted Result:** High useful friction → overall_response 4–5 with persistence. Low friction → overall_response 3–4 with decay over time. High waste friction → overall_response 0–1, immediate rejection, no persistence regardless of surface quality.

**Falsifying Result:** High waste friction paired with sustained engagement (e.g., sticking with a laggy UI because the "vibe" is good). Or: aversion to all resistance — useful and waste alike — indicating no real distinction in practice.

**Ambiguous Result:** Operator tolerates moderate waste friction in a domain where the useful friction is extremely high (e.g., EFT's poor netcode but genuine mastery depth). This would suggest waste friction tolerance is domain-gated by useful friction ceiling, not a flat rule. Requires sharpening rather than falsification.

**Implementation Notes:** Pair selection is critical. The strongest test pairs useful and waste friction at similar resistance magnitudes. Don't use "hard" vs "easy" — use "hard but fair" vs "hard but broken." Music pairs: dense coherent IDM (useful) vs muddy poor-mix garage rock (waste). Game pairs: EFT mastery curve (useful) vs unskippable cutscenes in a mediocre game (waste).

**Run 01 finding — waste friction tolerance is not flat:** Waste friction degrades overall_response only when useful friction cannot compensate. The EFT case confirmed this: waste_friction: 1 produced no degradation when useful_friction: 5. The tolerance band for waste friction widens proportionally to the useful friction ceiling. A simple net-subtraction model (overall = useful − waste) is wrong. When scoring ambiguous items, check whether the useful friction ceiling is high enough to absorb the waste before calling a result anomalous.

---

## TEST 2 — Channel Convergence
**ID:** `ont_002_convergence`

**Core Question:** Are strongest positive responses better predicted by multi-channel convergence than by any single dominant channel?

**Hypothesis:** Peak attraction occurs when multiple channels (facial architecture, tonal depth, body structure, presentation/styling, environmental enclosure, ambient texture) align without requiring the system to reconcile contradictory signals. A single outstanding channel cannot compensate for contradiction across others. Convergence produces a gestalt rating that exceeds the average of individual channel scores.

**Null Hypothesis:** Positive response is driven by one dominant channel. Convergence is a post-hoc explanation for the channel that happened to be strongest. If true, a single 5/5 channel should predict peak response regardless of other channels.

**Required Data:** Stimulus sets (attraction, environments, objects) where channels vary independently. Need: (a) single high channel + contradicted others, (b) moderate all channels converging, (c) high all channels converging, (d) moderate single channel + high contradiction. Gestalt rating must be collected separately from individual channel ratings.

**Scoring Dimensions:**
- `channel_convergence` (0–5): degree of cross-channel alignment
- `artificiality_penalty` (0–5): penalty if a channel signals performative/scripted construction
- `overall_response` (0–5): gestalt rating

**Predicted Result:** Gestalt rating exceeds channel average when channels converge (channel_convergence 4–5). Gestalt rating collapses below average when channels contradict — especially when high-signal channel is paired with artificiality in another (e.g., architectural face + influencer styling → artificiality_penalty fires and pulls gestalt down).

**Falsifying Result:** An item scores 5 on one channel and contradicts all others but still receives overall_response 4–5. This would mean a single channel can dominate convergence, falsifying the multi-channel model.

**Ambiguous Result:** An item with partial convergence (3 of 5 channels aligned) receives a high gestalt rating. This could mean convergence threshold is lower than predicted, or that certain channels are weighted heavier than others. Requires channel weighting investigation rather than falsification.

**Implementation Notes:** For attraction testing, avoid explicit image dumps. Use descriptive structural labels: facial architecture type, tonal contrast level, styling register (natural/performative). For environments: enclosure, thermal register, ambient sound texture, visual noise level. Channels must be rated independently before gestalt is recorded.

---

## TEST 3 — Inspection Deepening / Collapse
**ID:** `ont_003_inspection`

**Core Question:** Does liking increase when closer inspection reveals more structure, and collapse when inspection reveals surface-only construction?

**Hypothesis:** The operator uses surfaces as portals, not destinations. Liked objects deepen — each inspection layer reveals more consistent interior. Surface-attractive but shallow objects collapse — inspection exposes the performance rather than confirming a real interior. The inspection result predicts long-term engagement more reliably than initial attraction.

**Null Hypothesis:** Liking is surface-level. Once an aesthetic is accepted, the presence or absence of "deeper structure" does not change valuation. If true, inspection_deepening and inspection_collapse scores should not correlate with long-term engagement or retention.

**Required Data:** Objects across at least three domains (music, games, people/social) where: (a) surface quality is held constant, (b) interior structure varies from rich/coherent to absent/performed. Inspection must be conducted at four layers: surface → context/metadata → mechanics → recursive interior.

**Scoring Dimensions:**
- `interior_signal` (0–5): recursive interiority signal strength
- `inspection_deepening` (0–5): reward density across inspection layers
- `inspection_collapse` (0–5): exposure of surface-only construction
- `artificiality_penalty` (0–5): penalty for detected performance or script
- `overall_response` (0–5): net response after full inspection

**Predicted Result:** Objects with rich interior (inspection_deepening 4–5) receive overall_response uplift after inspection, sometimes exceeding initial attraction. Objects with surface-only construction (inspection_collapse 4–5) receive dramatic overall_response drop — often to 0–1 — even if initial attraction was 3–4. The drop is not gradual: it tends to trigger at the moment of exposure.

**Falsifying Result:** Continued liking of a surface-only object after its emptiness is exposed (e.g., an AI-generated track that still rates 4 once the operator knows it's AI-generated and has confirmed no interesting construction underneath). Or: failure of a genuinely deep object to generate increased engagement on inspection.

**Ambiguous Result:** Initial rejection of a surface followed by upgraded assessment on inspection, where the surface quality was genuinely poor but the interior was rich. This would indicate the surface threshold is independent of inspection, requiring investigation of the entry gate vs interior reward distinction.

**Implementation Notes:** The strongest test objects are those where surface quality is deceptive in either direction: a modest surface hiding deep structure (underrated entry), or a polished surface hiding nothing (NPC face). Outer Wilds is the clearest archetype for deepening. A socially fluent NPC is the clearest archetype for collapse.

**Run 01 finding — collapse magnitude is domain-sensitive:** Social collapse (NPC: initial 4 → final 0, active aversion) is sharper and more aversive than artifact collapse (generic track: initial 3 → final 1, inertness). The theory predicts collapse in both domains but does not predict that social collapse is more complete. These are not equivalent events. When an exposed NPC scores 0 with active contempt and a generic track scores 1 with inertness, both are collapse — but the response character differs. Do not average them. Stimulus design should include domain labels and note expected collapse floor when scoring.

---

## TEST 4 — Boundary / Inside-Outside Mapping
**ID:** `ont_004_boundary`

**Core Question:** Is the operator's cognitive style primarily driven by boundary detection and inside/outside modeling rather than associative, trait-based, or topic-based organization?

**Hypothesis:** The operator perceives and structures domains as volumes with thresholds, gates, and safe interiors rather than as flat topic clusters or trait lists. When organizing information, he defaults to boundary-first categorization: what does this protect, what does it exclude, what behavior changes at the threshold? This spatial-boundary style generalizes across workspace, music, games, people, and theory.

**Null Hypothesis:** The cognitive style is associative or linear. "Inside/outside" is a metaphor he uses in post-hoc description, not an active organizational primitive. If true, his actual sorting behavior should produce flat topic clusters indistinguishable from a standard categorical organizer.

**Required Data:** Novel categorization tasks (not previously solved) in at least two domains: (a) workspace organization, (b) social/relational modeling. Tasks must allow either boundary-first or topic-first solutions without cueing one approach. Collect decision rationales, not just outcomes.

**Scoring Dimensions:**
- `boundary_clarity` (0–5): degree to which the operator identifies or creates clear inside/outside distinctions
- `overall_response` (0–5): engagement/satisfaction with the organizing task

**Predicted Result:** In free categorization, the operator groups by what a boundary protects rather than by topic surface. He will identify when an apparent category has no real inside (it's a bucket, not a room). He will create threshold objects (gates, validators) rather than just labels. In social modeling, he predicts behavior by state-transition (entry/exit from a mode) rather than trait inference.

**Falsifying Result:** Consistent preference for flat/open structures without detectable boundary logic. Inability to distinguish "inside" from "outside" in a novel domain not previously analyzed. Or: boundary language used only in verbal description but not in actual organizational choices.

**Ambiguous Result:** Boundary-first organization in known domains (workspace, music) but topic-first in unfamiliar domains. This would indicate the spatial boundary style is domain-trained rather than constitutive, requiring investigation of whether it transfers to genuinely novel territory.

**Implementation Notes:** Task design is sensitive. Do not give him a pre-structured taxonomy to sort — give him raw unsorted material. Ask for explicit rationale. The strongest test is novel domain categorization where he hasn't already built a map. Workspace cleanup tasks with an unfamiliar folder structure are a clean analog.

**Run 01 finding — two distinct boundary failure modes:** `boundary_absent` (e.g., outputs/ folder — no inside exists, everything enters) and `boundary_false` (e.g., hidden-decision institution — the stated inside is a performance) produce different response characters. Absent boundary → frustration, cognitive load, refactoring impulse. False boundary → contempt, active aversion. Both score boundary_clarity: 0–1 under the current schema, but they are mechanistically distinct. When scoring boundary failures, add a `failure_mode` note field with value `boundary_absent` or `boundary_false`. The majority of DISSONANCE.md threat-taxonomy items are false-boundary cases, not absent-boundary cases — the most acute aversion is to deliberate concealment, not disorganization.

---

## TEST 5 — Continuity Through Transformation
**ID:** `ont_005_continuity`

**Core Question:** What transformations preserve identity for the operator, and which break continuity?

**Hypothesis:** Identity is preserved by survival of identity-bearing structure (invariants), not by label, name, genre tag, or substrate continuity. The operator tolerates high surface mutation (stylistic shift, remaster, evolution) when invariants survive, and experiences zero tolerance for "breakage" — loss of internal logic, authorial betrayal, or replacement of core invariants with arbitrary substitutes.

**Null Hypothesis:** Identity judgments are label-anchored or substrate-anchored. An object renamed, re-skinned, or moved to a different medium is experienced as a different object regardless of whether structural invariants survive. If true, continuity_preservation scores should correlate with substrate/label stability, not invariant survival.

**Required Data:** Transformation sequences across at least three domains (games/franchise, music/remasters, workspace/refactors, self/self-model). Each sequence must define: what was the original invariant set, what the transformation changed, what it preserved. Operator must rate identity continuity without knowing the predicted outcome.

**Scoring Dimensions:**
- `continuity_preservation` (0–5): degree to which invariants survived
- `transformation_tolerance` (0–5): amount of change absorbed without identity loss
- `overall_response` (0–5): whether the result is experienced as the same object or a new one

**Predicted Result:** High continuity_preservation (invariants intact) → overall_response treated as "evolved same object" even when surface mutation is extreme. Low continuity_preservation (invariants replaced) → "breakage" — the result is experienced as a different object or betrayal, regardless of how much surface continuity is maintained (same name, same brand, same genre).

**Falsifying Result:** An object that preserves all structural invariants but is experienced as broken because a surface property changed (e.g., a faithful musical remaster that feels wrong due to a different mix texture, permanently). This would suggest substrate or surface sensitivity that overrides invariant analysis.

**Ambiguous Result:** Operator accepts a transformation that breaks one invariant if a stronger invariant is preserved or upgraded. This would suggest invariants have a priority ordering rather than being flat. Requires identification of the invariant hierarchy.

**Implementation Notes:** The clearest transformation cases are: (a) Trails series — world-memory continuity across games despite massive stylistic evolution; (b) EFT — server wipes reset state but the core skill-loop invariants survive; (c) music remasters — arrangement intact but production substrate changed; (d) Helix refactors — file structure changes but boundary contracts survive. Breakage archetypes: franchise entries that retain a name but abandon the internal logic of the world.

---

## TEST 6 — Consciousness Bridge / Owned Continuity
**ID:** `ont_006_bridge`

**Core Question:** Can the personal ontology generate useful, falsifiable hypotheses about consciousness without overclaiming? Which parts are empirical, philosophical, analogical, or speculative?

**Hypothesis:** "Owned Continuity" — a field that maps its own history without branching or interruption — is a necessary condition for the subjective experience of selfhood. Consciousness, modeled through this ontology, requires: (1) a bounded field, (2) non-branching continuity, (3) recursive self-mapping (interior signal), (4) transformation tolerance without breakage. These are bridge concepts from the personal ontology to formal consciousness theory.

**Null Hypothesis:** The "Owned Continuity" model is not a theory of consciousness; it is a description of the operator's personal experience of self-continuity projected onto a philosophical domain. The concepts (boundary, interior, continuity) have no specific predictive force beyond restating standard personal identity debates (Parfit, Locke) in different vocabulary.

**Required Data:** Consciousness thought experiments and empirical cases: (a) split-brain commissurotomy reports, (b) teleporter/duplication thought experiments, (c) LLM interaction as "NPC test," (d) gradual transformation cases (Ship of Theseus, slow neuron replacement). Operator must rate each case against the Owned Continuity model and note where the model succeeds or fails to predict intuitions.

**Scoring Dimensions:**
- `interior_signal` (0–5): strength of interiority indicator in the case
- `boundary_clarity` (0–5): whether a clear inside/outside exists in the case
- `continuity_preservation` (0–5): whether non-branching continuity is maintained
- `overall_response` (0–5): whether the Owned Continuity model correctly predicts intuitions about the case

**Predicted Result:** The model correctly predicts: (a) teleporter duplicate is a new entity, not the same self; (b) split-brain produces continuity break, not two full selves; (c) gradual replacement preserves continuity if the replacement process is continuous and non-branching; (d) an LLM with no persistent state has no self-continuity regardless of interior signal quality.

**Falsifying Result:** Discovery that "branching" produces two simultaneous, fully coherent interiors that both claim the same prior history as owned continuity — and that this is experimentally supportable (e.g., split-brain literature that cannot be accounted for by the non-branching requirement). Or: evidence that interiority can exist without any boundary or continuity (isolated experience without a self-boundary).

**Ambiguous Result:** A case where the model's predictions match the operator's intuitions but fail to match standard philosophical or neuroscientific accounts. This would suggest the model is capturing something real about the operator's cognitive style without necessarily being a general theory of consciousness. Would require demotion from "theory" to "personal primitive."

**Implementation Notes:** This test is primarily conceptual and cannot be fully empirically tested with available data. Rate each claim with its epistemic tier (see `consciousness_bridge_tests.md`). Prioritize identifying which parts of the theory are empirically falsifiable vs. which are philosophical primitives that organize intuitions without being falsifiable. The goal is not to prove the theory but to find its boundary.

---

## Cross-Test Questions

The full six-test suite is designed to answer:

1. Does "structural friction minimization" predict Dissonance's preferences better than simple liking, simplicity, or novelty?
2. Does "channel convergence" predict peak attraction and peak taste responses better than isolated traits?
3. Does inspection deepen liked objects and collapse disliked-but-surface-attractive objects?
4. Does boundary/inside-outside mapping explain his cognition across domains?
5. What transformations preserve identity for him, and which break continuity?
6. Which parts of the consciousness bridge are empirical, philosophical, analogical, or speculative?

These questions are independent and can be run in any order. Tests 1, 3, and 5 have the highest falsifiability. Tests 2 and 4 require the most careful stimulus design. Test 6 is primarily epistemic tier classification.

