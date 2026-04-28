# DCP / Trajectory Open Questions

**Type:** Research working note
**Status:** Active — not a specification, not a manifesto
**Created:** 2026-03-20

This document exists to keep DCP and the broader trajectory model from being absorbed into Helix as received wisdom. It is a handle on what is uncertain and what the next moves are.

**Layer distinctions used throughout this doc:**

| Layer | What it describes |
|-------|------------------|
| **Constrained state-transition dynamics** | The process: movement through a state space under active constraint over time |
| **DCP (Decision Compression Principle)** | A specific event class within that process: possibility-space collapses sharply at a commitment point |
| **Ontology / irreversibility** | The interpretive layer: why commitment might generate durable structure; what it means that some collapses are irreversible |

These are not the same thing. DCP can be real even if the ontological framing is wrong. The trajectory model can be useful even if DCP doesn't generalize across domains.

---

## 1. What Currently Seems True

- **Constrained systems produce structural trajectories.** This is not a hypothesis — it is an observational baseline. Systems under binding constraints exhibit non-random trajectory distributions.

- **Some transitions within those trajectories look like compression events.** In the Kuramoto model, the phase transition near K_c has measurable DCP-like signatures: possibility-space dispersion before coupling, tension near K_c, sharp order-parameter rise, post-lock stability. This is real and inspectable.

- **The games probe (86% pass rate, 3 domains) suggests decision_entropy_slope is a viable DCP signal.** This is the strongest current multi-domain evidence. It has not yet been run against a properly constructed null model.

- **The signal structure is similar across math and games at a descriptive level.** Both show: unconstrained breadth → constraint introduction → entropy drop → locked state. Whether this is the same structural phenomenon or two coincidentally similar patterns is not yet distinguishable.

- **Oscillator locking is one instance of DCP, not its proof.** The K_c transition is a clean natural experiment for DCP. It does not establish DCP as universal.

---

## 2. What Is Observable Now

| Observable | Domain | Tool |
|-----------|--------|------|
| Sync index as collapse proxy | Math | `core/probes/math/analysis/dcp.py` |
| K/K_c ratio as constraint proxy | Math | `core/probes/math/analysis/dcp.py` |
| Order-parameter variance near K_c | Math | ✅ `labs/dcp_null_tests.py` Test 2 |
| Decision entropy slope | Games | `data/games/decision_compression_dataset.json` |
| Policy entropy drop at commitment | Games | ✅ GWT probes `model/domains/games/probes/gwt_*.py` |
| Piece-count possibility breadth (chess) | Games | ✅ `gwt_decision_dcp.py` — k=7–20, R²=0.90 |
| Network consensus topology floor | Games/Cognition | ✅ `gwt_topology_floor.py` — floor=6.2L+46.8, R²=0.90 |
| Wikipedia thread density slope | Language | ✅ `gwt_network_consensus.py` — positive slope (confound found) |
| LLM confidence trajectory | Cognition | ✅ `gwt_llm_agent_profile.py` — Bayesian accumulator, not logistic |
| Mystery/open problem DCP trajectories | Math | ✅ `core/probes/math/probes/mystery_dcp_*.py` + `math_probe_*.py` |
| Regime transition step-ratio | Math | ✅ Prime gaps / Zhang 2013 — step_ratio=3.1× |
| Phrase recurrence rate change | Music | Signal defined; probe not built |
| Post-lock trajectory diversity | Math | `post_collapse_narrowing` in DCPEvent |
| Composite DCP score (provisional) | Any | `core/invariants/dcp/metrics.py::compute_dcp_score()` |

Not yet observable:
- Cross-domain metric normalization (no normalization procedure exists)
- Music phrase-level DCP signal (library pipeline running; probe not built yet)
- Sentence-position-resolved k_eff traces in language (static k_eff only so far)

---

## 3. What Would Count as Evidence

**Evidence for DCP at CANDIDATE → EMERGING level:**
- A formally constructed math fixture (Kuramoto time-series probe) produces tension-accumulation measurement that correlates with K/K_c across N ≥ 20 distinct K values
- The games probe passes null model test: randomized action sequences do NOT produce equivalent decision_entropy_slope signatures
- At least one music track produces a phrase-recurrence-rate compression event detectable by the DCP metric interface

**Evidence for DCP at EMERGING → STABLE level:**
- Math, games, and music all produce DCPEvents with `qualification_status == "FULL"` (all five components measurable)
- Cross-domain K_eq (equivalent coupling) analysis shows structural similarity in collapse sharpness across domains
- Null models fail to produce similar DCP signatures (F1 falsification criterion not triggered)
- Two independent runs with different system sizes / random seeds produce structurally similar DCP scores

---

## 4. What Would Count as Falsification

These are the actual disconfirmation conditions (also in `codex/library/invariants/decision_compression_principle.yaml`):

**F1 — Null control collapse (highest priority):**
K=0 Kuramoto, randomized game actions, or unconstrained music sequences produce compression signatures indistinguishable from the claimed DCP events. This would mean the signal is a measurement artifact, not a constraint-driven phenomenon.

**F2 — Tension-free compression:**
Possibility space narrows without any detectable tension accumulation in any domain. This would mean the three-stage sequence (tension → collapse) is not required — the narrowing just happens monotonically.

**F3 — Non-reproducible collapse:**
Fixed initial conditions + fixed constraint produce compression events at different locations or not at all across runs. This would mean DCP events are not deterministic outcomes of constraint — just coincidental local minima.

**F4 — Domain specificity:**
Math, games, and music compression events cannot be translated into structurally comparable DCP scores under any normalization. This would mean each domain just has its own local dynamics — DCP is not a cross-domain phenomenon.

**F5 — Ordinary transition indistinguishability:**
DCP events are not distinguishable from ordinary state transitions in any domain under available metrics. This would mean the "compression event" framing adds no predictive or structural value.

---

## 5. Immediate Next Tests

Priority order — do these before claiming any tier above CANDIDATE:

**Test 1: K=0 null model for math DCP (addresses F1)**
Run `extract_dcp_event()` on K=0 Kuramoto results (N ≥ 50 times, different seeds).
Expected: DCP scores should be consistently low (< 0.3).
If DCP scores are high under K=0: F1 is triggered.
Location: extend `core/probes/math/validation/kuramoto_fixture.py` with a DCP null section.
→ **RUN 2026-03-23** (`labs/dcp_null_tests.py`, Test 1): **PASS**
  K=0 mean DCP=0.175, max=0.188, std=0.004. F1 NOT triggered.
  TAI at K=0: mean=0.031 (consistent near-zero tension from null).
  Artifact: `artifacts/dcp_null_test_results.json`

**Test 2: Time-series tension probe for math (addresses tension_proxy accuracy)**
Run Kuramoto at K sweep (0.5 × K_c to 2.0 × K_c, 20 steps).
Record order-parameter R at each step.
Compute `tension_accumulation_index()` from the actual R time series, not the K/K_c approximation.
Expected: tension peaks near K_c; drops away from it.
→ **RUN 2026-03-23** (`labs/dcp_null_tests.py`, Test 2): **PASS**
  TAI peaks at K/K_c=1.211 (within expected [0.7, 1.5]). TS DCP peaks at K/K_c=1.00.
  Tension is a real time-series signal, not just a proxy artifact.
  K_c=0.484 (seed=42, N=50, std=1.0 Gaussian).

**Test 3: Games null model (addresses F1 for games)**
Run decision_entropy_slope on randomized game action sequences (no strategy).
Compare slope distribution to strategy-present distribution.
Expected: null distribution should have lower collapse_sharpness.
→ **RUN 2026-03-23** (`labs/dcp_null_tests.py`, Test 3): **FAIL — DATA GAP**
  The current games fixture (`agents/decision_compression_dataset.json`) is a static
  5-player weight scaffold. The weights barely change across rounds; k_eff trajectory
  shows no compression (slope=0.011, 48th percentile of null). The fixture does not
  contain the decision_entropy_slope signal referenced here.
  **Action required**: the games domain needs a richer dataset — actual game play sequences
  where decision entropy changes over time as strategy converges. The current fixture
  is structurally insufficient for this test. This is a data gap, not F1.

**Test 4: Cross-coupling comparison (addresses F4 partially)**
Compare `dcp_composite_score` at K = 0.5 K_c, 1.0 K_c, 1.5 K_c, 2.0 K_c.
Expected: score should peak near K_c and saturate above it.
This characterizes the math DCP curve before attempting cross-domain comparison.
→ **RUN 2026-03-23** (`labs/dcp_null_tests.py`, Test 4): **PASS**
  TS DCP peaks at K/K_c=1.00. Proxy DCP rises monotonically (correct: more coupling
  = stronger locking). Both measures agree on K_c as the transition point.
  Cross-domain comparison is now meaningful for the math domain.

**Status (2026-03-23):** Tests 1, 2, 4 PASS. Test 3 is blocked by a data gap in the
games domain. DCP remains at CANDIDATE pending a real games dataset with entropy-slope
dynamics, plus the language and music domain DCP hooks.

**Pass-4 update (2026-03-23):**
Games domain rebuilt — Test 3 is now runnable.
New fixtures: `model/domains/games/fixtures/sequential_decision.py` (pursuit + resource + null).
These produce genuine sequential narrowing with temporal DCP structure. The static
`decision_compression_dataset.json` scaffold was the identified root cause of the
Test 3 failure. New validation harness: `model/domains/games/validation/games_fixture.py`.
Cross-domain comparison layer: `labs/dcp_cross_domain.py`.
Synthetic calibration baselines: `labs/dcp_synthetic_fixtures.py`.

---

## 6. Open Questions / Unknowns

**On metrics:**
- Can `collapse_sharpness` be normalized across domains to allow structural comparison, or is it irreducibly domain-dependent?
- What is the right tension accumulation metric for systems with continuous (not discrete) decision points?
- Is the K/K_c ratio a valid constraint_proxy proxy, or does it assume mean-field coupling in a way that doesn't generalize?

**On DCP scope:**
- Does DCP apply to continuous systems only, or also to discrete decision/commitment systems (games)?
- Is the "compression event" a physical phenomenon or a description of a measurement protocol?
- If DCP events are real, are they the cause of post-event structure or just correlated with it?

**On trajectory dynamics:**
- The broader constrained state-transition model describes motion through state space. DCP describes collapses within that motion. Are there constrained systems where DCP collapse events DO NOT occur — where the narrowing is always gradual? If yes, what distinguishes those systems?

**On ontology:**
- The ontological framing (commitment generates structure, irreversibility is primary) is not directly testable by any current Helix metric. It may be interpretively correct even if DCP metrics fail to generalize. These are separate questions.
- The cognitive profile describes DCP-like dynamics at the level of a specific subject. This is consistent with DCP but is not a domain-independent validation.

**On cross-domain comparison:**
- The `compute_dcp_score()` composite is weighted equally by default. There is no principled basis for these weights yet. They are provisional heuristics.
- Until Test 1 and Test 3 (null model tests) are run, no DCP score from any domain should be used in Atlas promotion arguments.

---

## 7. Collapse Morphology — Open Questions

The four morphology categories (TRANSFORMATIVE, DISSOLUTIVE, CIRCULAR, DEFERRED_SUSPENDED) are working classifications defined in `system/engine/compute/invariants/dcp/morphology.py`. The following questions are open:

- **Discriminability**: What trajectory features reliably distinguish morphology classes post-collapse? Is cosine similarity of pre/post feature vectors sufficient, or does it require domain-specific metrics?
- **Predictability**: Can morphology be predicted *before* collapse, not just classified after? What pre-collapse signals correlate with outcome class?
- **Cross-domain transfer**: Does a TRANSFORMATIVE collapse in a math system look structurally similar to a TRANSFORMATIVE collapse in a games or agent system? Or is morphology class domain-local?
- **Edge cases**: Mixed or sequential morphologies (e.g., CIRCULAR leading to TRANSFORMATIVE on second cycle) — are these a distinct category or combinations of the base four?
- **Falsifiability**: Under what conditions would the four-category taxonomy be empirically inadequate? What would force a revision?

---

## 8. Constraint Classes — Open Questions

The current constraint class split (internal / external / mixed) is a provisional working taxonomy. Open questions:

- **Differential effects**: Do internal and external constraints produce structurally different tension accumulation patterns? Testable in math (coupling K is internal; adversarial injection is external) and games.
- **Class transitions**: Can constraint class shift during a trajectory? If yes, how should class transitions be tracked in DCPEvent artifacts?
- **Interaction effects**: When both internal and external constraints are active simultaneously (mixed), do they produce superadditive or subadditive tension?
- **Resource vs. informational constraint**: Are resource-depletion and information-asymmetry constraints measurably distinct in their DCP signatures? Not yet operationalized.

---

## 9. Pre-Collapse Indicators

What signals reliably *precede* a collapse event and could serve as early-warning indicators?

Current candidates (not yet formalized as metrics):
- Sustained `tension_level` above threshold for ≥ N time steps
- Rising `constraint_intensity` rate (second derivative of breadth reduction)
- Increasing variance in trajectory direction (approaching bifurcation)
- Entropy *plateau* followed by sharp drop — plateau duration may predict morphology class

Empirical target: build a pre-collapse detection window → validate on toy branching agent fixture → transfer to math and games domains.

False-positive rate from null controls must be established before any pre-collapse indicator is used in an Atlas promotion argument.

---

## 10. Cognition Domain Applications

The cognition domain (`model/domains/cognition/`) is the primary operational test environment for DCP in agent systems. Open questions:

- **Toy branching agent feasibility**: Does a controlled branching-factor reduction schedule produce `DCPEvent` instances with `qualification_status == "FULL"` (all 5 components)?
- **AI token entropy as proxy**: Does token probability entropy over a constrained generation task produce a DCP event signature near constraint completion? What morphology?
- **Cross-agent morphology comparison**: Do human and AI systems facing the same constraint schedule produce the same morphology class? Or is morphology class agent-type-dependent?
- **Perturbation recovery and morphology**: Does the pre-perturbation morphology class predict the recovery shape?
- **Constraint class and architecture**: For AI systems, is constraint internal (bounded context, fixed vocabulary) or external (adversarial prompting, strict schema)? Does agent architecture determine constraint class?

---

## 11. Consciousness-Boundary Notes

This note exists to maintain an explicit boundary between what Helix studies and what it does not claim.

**What the cognition domain studies:**
- Observable trajectory dynamics in agent systems
- Measurable DCP events (possibility-space compression under constraint)
- Morphology classification of observed post-collapse trajectories
- Cross-agent structural comparison

**What the cognition domain does NOT claim:**
- Whether agents have phenomenal experience at or near collapse events
- Whether DCP events correlate with subjective experience of any kind
- Proof of qualia, self-awareness, or sentience in any system

Consciousness-adjacent research is a **speculative / interpretive layer above the cognition domain**, not inside it. If future work attempts to probe consciousness-adjacent hypotheses, it must provide:
1. An operationalized, falsifiable definition of what is being measured
2. A clear demarcation from the cognition domain's observational claims
3. Its own promotion criteria separate from DCP evidence

The DCP/trajectory/morphology framework is neutral on consciousness. Its value stands or falls on whether compression events generalize across domains — independent of any consciousness claim.

---

## 12. Pass-4 Cross-Domain Evidence Summary (2026-03-23)

This section documents the empirical state after the pass-4 DCP validation work.

### What changed in pass-4

| Item | Before | After |
|------|--------|-------|
| Games domain | Static 5-agent weight scaffold; Test 3 blocked | Sequential decision fixtures (pursuit, resource, null); Test 3 now runnable |
| Cross-domain comparison | No shared layer | `labs/dcp_cross_domain.py` |
| Synthetic baselines | None | 3 calibration fixtures in `dcp_synthetic_fixtures.py` |

### Current evidence by domain

| Domain | Evidence Quality | Qualification Ceiling | Status |
|--------|-----------------|----------------------|--------|
| Math | STRONGEST | FULL | Tests 1, 2, 4 passed; K_c confirmed; mystery probes (7) + open problem probes (4); regime transition (prime gaps) first evidence |
| Games | STRONG | FULL | GWT probes complete: topology floor, k_eff formalization, EEG alignment, adversarial, chess DCP |
| Language | PARTIAL | INCOMPLETE | Wikipedia density probe run; confound (voting vs debate threads) identified; k=7–12 confirmed in chess |
| Music | WEAK | INCOMPLETE | Library pipeline running (full 122k); phrase-level DCP probe not yet built |
| Cognition | REAL DATA | PARTIAL | LLM confirmed as Bayesian accumulator (not logistic); DCP visible within-trace only, not across turns |
| Synthetic | CALIBRATION BASELINE | FULL | Confirms probe functions; no domain semantics |

### What still blocks promotion beyond CANDIDATE

1. **Games null model** (Test 3): new fixtures make this runnable but it has not been run yet.
   Run `model/domains/games/validation/games_fixture.py` section B first, then run
   the null model against `run_null()` at scale (≥50 seeds).

2. **Music collapse_proxy**: requires audio-level loop-seam detection.
   `model/domains/music/analysis/loop_seam.py` has candidacy scoring but is not wired to
   produce a `collapse_proxy` in DCPEvent. This blocks music from FULL qualification.

3. **Language temporal probe**: grammar_resolution gives static k_eff (constraint level)
   but not a temporal collapse event. The sentence trajectory probe
   (`labs/sentence_trajectory_probe.py`) tested this on short texts —
   needs longer UD treebank sentences for meaningful timing shapes.

4. **Cognition real data**: branching fixture is a toy. Real agent data (AI generation
   under constraint, human decision sequences) would provide genuine cognition evidence.

5. **Cross-domain K_eq analysis**: `dcp_cross_domain.py` now collects comparable
   signals but does not yet compute structural similarity in collapse sharpness
   across domains. This is the next metric to implement.

### What DCP now means empirically

> DCP is a cross-domain CANDIDATE supported by strong math evidence (Kuramoto transition),
> improved games evidence (new sequential fixtures, not yet null-calibrated), weak
> music/language evidence (proxies only), and synthetic calibration showing probe
> functions behave correctly in stripped-down cases.
>
> The claim "possibility-space compression events occur across multiple domains with
> structurally comparable signatures" is now INVESTIGABLE across math, games, and
> synthetic domains. It is not yet established.
>
> DCP is not promoted to EMERGING until Test 3 passes at scale and at least one
> additional domain achieves FULL qualification.

### Next empirical priorities (in order)

1. Run games null model at scale (≥50 seeds, pursuit + resource + null)
2. Wire music loop-seam detection to produce `collapse_proxy`
3. Run sentence trajectory probe on UD treebank sentences (not construction maps)
4. Find correct UD repository URLs for Swahili and Bengali (both returned 404)
5. Implement cross-domain K_eq structural similarity comparison in `dcp_cross_domain.py`

