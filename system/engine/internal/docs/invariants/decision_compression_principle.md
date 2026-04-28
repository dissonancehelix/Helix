# Decision Compression Principle (DCP)

**Version:** 1.1  
**Status:** CANDIDATE  
**Invariant Family:** `decision_compression`  
**Updated:** 2026-03-21  
**Machine-readable entry:** `codex/library/invariants/decision_compression_principle.yaml`  
**Domain hook:** `core/probes/math/analysis/dcp.py`  
**Morphology schema:** `system/engine/compute/invariants/dcp/morphology.py`  
**Event schema:** `core/invariants/dcp/event.py`  
**Research notes:** `docs/research/dcp_trajectory_open_questions.md`

---

## 1. Definition

The Decision Compression Principle (DCP) is the hypothesis that constrained systems generate structure by collapsing multiple possible futures into a smaller set of realized trajectories through commitment or effectively irreversible narrowing.

Stated formally:

```
possibility space → constraint → tension → compression event → reduced trajectory set
```

A **compression event** is the identifiable moment or interval where the narrowing becomes sharp enough to produce a new structural trajectory.

DCP is a candidate invariant for a **specific class of event**: the collapse. It is not a theory of all state-space dynamics, and is not the same as ordinary trajectory movement.

---

## 2. Core Event Signature

A DCP-like event has five detectable components:

| Component | Description | Observable Proxy |
|-----------|-------------|-----------------|
| **Possibility space** | The breadth of reachable futures before constraint acts | State entropy, policy entropy, trajectory spread |
| **Constraint** | Limits that shape and focus that space | Resource depletion, coupling strength, rule density, adversarial action |
| **Tension** | Unresolved competition among continuations | Entropy plateau or rise before collapse, phase variance, prediction uncertainty |
| **Compression event** | Sharp narrowing of the trajectory set | Entropy drop rate, order-parameter jump, commitment density spike |
| **Post-collapse state** | Reduced, stabilized trajectory narrower than before | Sustained low entropy, locked sync, strategy convergence |

The compression event is the diagnostic unit. All five components must be identifiable for a DCP claim to be made.

---

## 3. Constraint as Focusing Principle

Constraint is not merely one component in the DCP chain. It is what gives the possibility space its **shape** and makes narrowing events **meaningful**.

Without constraint:
- Possibility-space reduction is often just noise or ordinary drift
- Tension cannot accumulate in a structured way — there is nothing to resolve
- A compression event, even if detectable, carries no structural significance

With meaningful constraint:
- The possibility space is actively shaped — some futures are bounded out, others are weighted
- Tension accumulates because the system is being pushed toward commitment
- The collapse event narrows a constrained space into an even smaller realized set
- Structure-generating commitment depends on constraint, not merely on change

**Constraint classes (current working split):**

| Class | Description | Examples |
|-------|-------------|---------|
| `internal` | Structural or self-imposed limits arising from within the system | Resource limits, internal rule sets, bounded operator capacity |
| `external` | Applied from outside the system boundary | Adversarial action, coupling from other agents, regulatory pressure |
| `mixed` | Both internal and external constraints active simultaneously | Most real DCP events involve both |

> *Informational and resource-scarcity constraint are further distinctions within these classes — relevant for future probe design, but not yet separately operationalized.*

This classification is provisional. Its value is for structuring probe design and for determining whether a DCP signal generalizes across constraint types. Whether internal and external constraints produce structurally different compression events is an open question (see `docs/research/dcp_trajectory_open_questions.md §8`).

---

## 4. What Counts as a Compression Event

A compression event qualifies if:

1. A measurable proxy for possibility-space breadth **decreases sharply** over a bounded interval
2. The decrease is **preceded by** a measurable constraint signal (not coincidental with noise)
3. **Tension accumulates** prior to the decrease (entropy does not drop monotonically from the start)
4. The post-collapse state is **distinguishable** from the initial state by reduced future-trajectory diversity
5. The event is **reproducible** under similar initial+constraint conditions

Partial qualification: if (1), (2), and (5) are met but (3) is not clearly observable, the event is an **unconfirmed compression candidate** — still of interest, but cannot be claimed as DCP.

---

## 5. What Does Not Count

| Situation | Reason |
|-----------|--------|
| Monotonic entropy decrease from the start | No tension accumulation — just decay |
| Random fluctuation producing a temporary low | Not reproducible; no constraint cause |
| Ordinary state transition without space narrowing | Movement through state space ≠ compression of it |
| Gradual constraint tightening without detectable collapse | May be relevant context, but lacks the compression event |
| Null/noise controls producing similar signatures | Would falsify DCP for that domain |

---

## 6. Domain Interpretations

DCP is a cross-domain hypothesis. Each domain expresses the same underlying event structure in domain-specific signals.

### Mathematics (Kuramoto model)
- Possibility space: variance in phase trajectory angles before synchronization
- Constraint: coupling strength K approaching K_c
- Tension: oscillation in order parameter R near critical coupling
- Compression: sharp rise in R from disordered to synchronized state
- Post-collapse: locked synchronized trajectory; phase variance near zero

### Games
- Possibility space: policy entropy — number of viable strategies at a decision point
- Constraint: resource depletion, irreversible moves, adversarial actions
- Tension: decision branch competition near critical game state
- Compression: sharp policy entropy drop before/at irreversible commitment
- Post-collapse: reduced viable strategy space; new trajectory locked in

Signal: `decision_entropy_slope` — rate of entropy reduction approaching decision point. Current probe pass rate: **86%** (3 domains).

### Music
- Possibility space: harmonic vocabulary size, interval entropy before structural commitment
- Constraint: chip register limits, phrase loop density, compositional rules
- Tension: competing harmonic possibilities near formal resolution
- Compression: the phrase or motif resolution event — the moment harmonic tension collapses to a fixed structure
- Post-collapse: recurring motif locked in; recurrence depth rises

### Cognition (agent systems)
- Possibility space: branching factor / available state transitions from current position
- Constraint: internal cognitive limits, external task constraints, time pressure
- Tension: sustained competition among continuation modes before commitment
- Compression: commitment / decision event with sharp trajectory narrowing
- Post-collapse: post-commitment trajectory with reduced alternative diversity

See `model/domains/cognition/` for the operational probe framework.

---

## 7. Collapse Morphology

Not all compression events terminate the same way. **Collapse morphology** classifies the structure of the trajectory *after* a compression event.

These categories are provisional, operational, and useful for probe design and cross-domain comparison. They are not settled laws.

| Morphology | Post-Collapse Tendency | Coherence Effect |
|------------|----------------------|-----------------|
| `TRANSFORMATIVE` | New stable attractor; trajectory structurally distinct from pre-collapse | Coherence **increases** across the event |
| `DISSOLUTIVE` | Trajectory destabilizes or disperses; no new coherent structure | Coherence **decreases** across the event |
| `CIRCULAR` | Return to prior attractor or near-prior state | Coherence restored to prior level; no net structural change |
| `DEFERRED_SUSPENDED` | Sustained high-tension state; no sharp collapse crossing | Coherence held at unstable intermediate level |

**Machine-readable definitions:** `system/engine/compute/invariants/dcp/morphology.py` — `CollapseMorphology` enum + `MORPHOLOGY_PROFILES` interpretation table.

**Classification basis:** trajectory similarity before/after candidate collapse event. Classification is not yet implemented in any domain pipeline; the schema exists for future probe use.

**Open questions on morphology:** Does morphology predict downstream trajectory stability? Can morphology be detected pre-collapse rather than only post-collapse? See `docs/research/dcp_trajectory_open_questions.md §7`.

---

## 8. Candidate Metrics

These are measurement proxies, not the invariant itself. Different domains will use different proxies. Cross-domain validity is the testable claim.

| Metric | Proxy For | Domain Examples |
|--------|-----------|-----------------|
| `possibility_space_entropy` | Breadth of reachable futures | Policy entropy (games), phase variance (math), interval entropy (music) |
| `constraint_intensity` | Strength of acting constraint | K/K_c ratio (math), resource utilization rate (games), chip register saturation (music) |
| `tension_accumulation_index` | Pre-collapse competition | Entropy plateau duration, phase variance peak |
| `collapse_sharpness` | Steepness of the compression event | dH/dt (entropy rate), dR/dt (order parameter rate) |
| `post_collapse_trajectory_width` | Narrowing of realized futures | Post-collapse entropy, locked-state diversity |
| `irreversibility_proxy` | Non-recoverability of collapse | Lyapunov exponent sign change, commitment density threshold |

Metric formulas are domain-local at this stage. A cross-domain normalization procedure does not yet exist and is a known open question.

---

## 9. Falsification Criteria

DCP is falsifiable. Any of the following would count as evidence against the principle:

1. **Control collapse**: A null/randomized version of the constraint (no coupling, random actions, no compositional rules) produces compression signatures indistinguishable from claimed DCP events → DCP signal is artifact of measurement

2. **Tension-free compression**: Measurable entity space narrows without any detectable tension accumulation in the approach → DCP's "tension → collapse" mechanism is not required

3. **Non-reproducible collapse events**: Under fixed initial conditions + fixed constraint, compression events occur at inconsistent locations or not at all → DCP is not a structural invariant, just coincidental narrowing

4. **Domain specificity**: Compression events in math, games, and music cannot be made structurally comparable under any metric translation → DCP is domain-local noise, not a cross-domain principle

5. **Constrained systems without compression**: A class of clearly constrained systems shows trajectory narrowing without identifiable collapse events → DCP's collapse-event framing is wrong; the dynamics are gradual

Active falsification tests should be run against null models before any Helix promotion above CANDIDATE.

---

## 10. Relationship to Trajectory Dynamics

DCP is an **event-level principle**. It describes a class of collapse events.

Trajectory dynamics — the broader process model of how systems move through constrained state spaces — describe movement over time:

```
possibility space → constraint → tension → collapse/commitment → new trajectory
```

The relationship is:

```
[trajectory dynamics]   →  describes the full process (motion, constraint, accumulation)
[DCP]                   →  identifies a specific class of collapse within that process
[compression event]     →  the detectable unit DCP predicts
[collapse morphology]   →  classifies what kind of outcome the compression produces
```

DCP does not replace dynamical systems modeling. It makes a narrower, more falsifiable claim: that within such dynamics, there exists a recurring event-structure characterized by possibility-space compression under meaningful constraint.

A system can be fully described by a dynamical model and still have DCP be wrong (if compression events don't generalize) or right (if they do).

### Historical precursor

An earlier Helix formulation attempted to describe this general dynamic in a single blended equation derived from music analysis:

```
dC/dt = −∇C + Ψ(C) + ∇V + ∂P/∂x + φ·D
```

with terms labeled: **resolve**, **depth**, **coherence**, **drift**, **diversity**.

This did not survive as a canonical Helix equation. Its semantic content has since been distributed more cleanly across:

- trajectory dynamics (the motion layer)
- coherence / attractor behavior (resolve, depth)
- drift / transition movement (drift term)
- possibility-space breadth (diversity)
- DCP as the collapse/compression event (what the equation could not isolate)

Preserved here as a historical marker.

---

## 11. Trajectory Modes

DCP trajectories exhibit distinct qualitative patterns. What was previously theorized as separate principles (EIP, LIP) has been dissolved and reclassified as DCP trajectory modes based on empirical probe results (2026-03-25):

| Mode | Signature | Example |
|------|-----------|---------|
| **Collapse** (was EIP) | Breadth → near-zero; irreversible by construction | Tamam Shud (k=20, solved 2022), Fermat's Last Theorem |
| **Floor / Stall** (was LIP) | Plateau at non-zero; structurally blocked | D.B. Cooper (~50K suspects), P vs NP (3 proven barriers), Ramsey R(5,5) |
| **Oscillating** | Direction changes ≥ 3; k≈1, R²<0.1 | Wow! Signal (5 reversals), abc conjecture (2), 'Oumuamua |
| **Anti-convergent** | Hypothesis space expands over time | Voynich Manuscript (+5 hypotheses over 112 years) |
| **Latent collapse** | Long plateau then rapid collapse via new tool | Tamam Shud pre-2019, technology-gated cold cases |

Irreversibility is a structural consequence of DCP compression — a collapsed possibility space cannot be reconstructed by construction. The floor mode explains structural stalls without requiring a separate mechanism. Both are trajectory outcomes, not independent laws.

---

## 12. Relationship to the Cognition Domain

The cognition domain (`model/domains/cognition/`) is the domain within Helix explicitly designed to study DCP-like collapse events in agent systems — human participants, AI systems, and simulated agents.

The relationship:

| Layer | What |
|-------|------|
| **DCP** | The event-level principle — defines what a compression event is and what it requires |
| **Trajectory dynamics** | The process model — describes the full motion from possibility space through collapse |
| **Collapse morphology** | The classification layer — describes what kind of outcome the collapse produces |
| **Cognition domain** | The operational test domain — applies the above framework to agent state trajectories |

The cognition domain is not a proof of DCP. It is a test environment for it. Cross-agent comparison data from the cognition domain, once available, would contribute evidence for or against DCP's cross-domain generality.

**Consciousness-adjacent research** sits above the cognition domain as a speculative/interpretive layer. DCP events in agent systems are measurable dynamics; whether there is phenomenal experience associated with collapse boundaries is not a testable Helix claim.

---

## 13. Current Helix Status

| Component | Status |
|-----------|--------|
| Named in INVARIANTS.md | ✅ |
| Machine-readable library entry | ✅ `codex/library/invariants/decision_compression_principle.yaml` |
| Authoritative doc | ✅ This file (v1.1) |
| Morphology schema | ✅ `system/engine/compute/invariants/dcp/morphology.py` |
| Event schema | ✅ `core/invariants/dcp/event.py` (v2) |
| Probe output schema | ✅ `core/invariants/dcp/event.py::DCPProbeOutput` |
| Domain hook: math | ✅ `core/probes/math/analysis/dcp.py` |
| Domain hook: games | ✅ GWT probes (gwt_*.py) — topology floor, k_eff, EEG alignment, adversarial, chess |
| Domain hook: music | ⚠️ Conceptually mapped; library pipeline running |
| Domain hook: cognition | ✅ GWT/LLM probes confirm Bayesian accumulator profile; DCP visible within-trace only |
| Domain hook: language | ⚠️ Wikipedia probe run; density confound identified |
| Domain hook: math | ✅ Mystery probes (7) + open problem probes (Ramsey, prime gaps, P vs NP, abc) |
| Cross-domain metric normalization | ❌ Open question |
| Null-baseline falsification run | ❌ Not yet performed |
| Morphology classifier | ❌ Schema exists; no detection logic |
| Lifecycle tier | `CANDIDATE` |

---

## 14. Initial Domains of Interest

Priority order for DCP probing:

1. **Math** — Kuramoto model provides controlled, deterministic collapse events. First integration hook is implemented.
2. **Games** — Existing probe infrastructure; 86% pass rate already exists. Formal harness and null model needed.
3. **Music** — Harmonic resolution as compression event. Signal mapping defined; probe not yet built.
4. **Cognition** — Toy branching agent fixture target. DCP event-level + morphology classification together.
5. **Language** — Syntactic commitment events (pronoun reference resolution, garden-path sentences). Long-range target.

---

## 15. Known Open Questions

- Can `collapse_sharpness` be normalized across domains to enable cross-domain structural comparison?
- What is the minimal observable evidence for tension accumulation vs. monotonic decay?
- Does DCP generalize to continuous systems, or only to systems with identifiable discrete decision/locked states?
- What is the relationship between DCP collapse sharpness and Lyapunov exponent sign changes?
- Is the games probe (86%) passing because DCP is real, or because the measurement is underspecified?
- At what coupling strength does the Kuramoto compression event reliably occur relative to K_c?
- Can collapse morphology be predicted pre-collapse, or only classified post-collapse?
- Does constraint class (internal vs external) affect tension accumulation rate or morphology outcome?

