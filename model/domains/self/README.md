# Cognition Domain — Helix Analysis Pipeline

**Location**: `model/domains/cognition/`  
**Version**: 0.3  
**Status**: Operational — minimal fixture/probe/validation layer implemented  
**Updated**: 2026-03-21  
**Spec**: [`SPEC.md`](SPEC.md)

> **Maturity notice**: This domain has a minimal operational layer (pass 3).
> Two toy fixtures, domain-local probes, a heuristic morphology classifier,
> perturbation support, and domain-local validation are implemented.
> No real agent input, HSL integration, or Atlas persistence exists yet.
> Morphology labels are **provisional heuristics** — not calibrated findings.

---

## Vision

The cognition domain studies **trajectory dynamics** — how systems move through
constrained possibility spaces, accumulate tension, and narrow into committed
trajectories.

The **process model** for this domain is:

```
possibility space → constraint → tension → collapse/commitment → new trajectory
```

The primary objects of study are:

- **State trajectories** — how a system traces a path through its accessible state space
- **Possibility-space breadth** — how open or constrained that space is at each moment
- **Constraint** — what shapes the space and makes narrowing events meaningful
- **Tension accumulation** — how unresolved constraint builds before a transition
- **Collapse events** — moments of commitment where the accessible space narrows sharply (DCP events)
- **Collapse morphology** — what kind of trajectory the system enters after commitment

This is an operational research domain. It is not a consciousness domain, a
metaphysical layer, or a proof of qualia.

Consciousness-adjacent research is a *later, higher-speculative layer* above this
domain — not identical to it.

---

## Role Within Helix

The cognition domain provides:

1. **DCP test environment** — the cognition domain is the primary operational environment for testing DCP claims in agent systems. DCP is the *event-level principle* (collapse/commitment); trajectory dynamics is the *process model*; cognition provides the *observational substrate*.
2. **Cross-agent comparison** — the same trajectory/collapse framework applied to human participants, AI systems, and simulated toy agents
3. **Collapse morphology classification** — first-class classification of post-collapse outcome type, using the canonical `CollapseMorphology` enum (`system/engine/compute/invariants/dcp/morphology.py`)
4. **Perturbation and recovery probing** — measuring how systems respond to disruption of their possibility space

---

## Coordinate Separation

> **Domain-local cognition metrics are not the same as HelixEmbedding axes.**

| Layer | What | Status |
|-------|------|--------|
| Domain-local | `possibility_breadth`, `constraint_intensity`, `tension_level`, `collapse_magnitude`, `post_collapse_class`, `perturbation_response` | Defined; not yet computed |
| Shared embedding | `complexity`, `structure`, `repetition`, `density`, `expression`, `variation` | Standard Helix axes |
| Projection | `CognitionStateVector → HelixEmbedding` | Not yet implemented |

Domain-local variables are extracted from agent behavior data. They are not
HelixEmbedding axes. The projection that maps them into the shared embedding
space will be defined in `SPEC.md §3` and implemented separately.

---

## Domain-Local Variables

These are the initial operational variables for the domain. All are provisional —
they exist to structure probes and fixtures, and are subject to revision as
calibration data accumulates.

**Constraint is treated as a first-class operational concept here**, not just a
pipeline input. Without meaningful constraint — internal (rule sets, capacity limits)
or external (adversarial action, task pressure) — possibility-space reduction is often
ordinary drift rather than a structured collapse event. The domain-local variables
below operate within a constraint regime, not independently of one.

| Variable | Operational Definition | Status |
|----------|----------------------|--------|
| `constraint_class` | Whether acting constraint is `internal`, `external`, or `mixed` | Categorical placeholder |
| `constraint_intensity` | Normalized strength of the acting constraint | Placeholder |
| `possibility_breadth` | Cardinality or volume of accessible next-states from current state | Placeholder |
| `tension_level` | Accumulated unresolved constraint; proxy: decision latency or variance elevation | Placeholder |
| `collapse_threshold` | The `possibility_breadth` value at which a collapse event triggers | Not calibrated |
| `collapse_magnitude` | Fractional reduction in `possibility_breadth` across the collapse event | Placeholder |
| `post_collapse_class` | Trajectory morphology class after collapse (see §Collapse Morphology) | Categorical |
| `perturbation_response` | Change in trajectory after external disruption to possibility space | Placeholder |
| `self_boundary_stability` | Stability of agent's distinction between self-state and environment state | Research-stage only |

---

## Collapse Morphology

Four provisional collapse categories defined in the canonical morphology schema.
These are working classifications — not settled laws — meant to structure probes
and discriminate outcomes across agent types and domains.

**Canonical schema**: `system/engine/compute/invariants/dcp/morphology.py` — `CollapseMorphology` enum

| Class | Description |
|-------|-------------|
| `TRANSFORMATIVE` | Narrowing into stronger / more coherent structure. Post-collapse trajectory is qualitatively distinct from pre-collapse. |
| `DISSOLUTIVE` | Narrowing via thinning, dispersal, or coherence loss. The trajectory does not stabilize post-event. |
| `CIRCULAR` | Narrowing back toward the pre-collapse attractor. Commitment is partial or temporary. |
| `DEFERRED_SUSPENDED` | Sustained high-tension state without crossing the collapse boundary. Collapse is delayed or avoided. |

These categories are:
- Provisional — subject to revision as empirical data accumulates
- Operational — intended to be measurable from trajectory data
- Non-exhaustive — edge cases and overlapping morphologies are expected

---

## Directory Structure

```
model/domains/cognition/
  fixtures/
    branching.py          — toy branching decision fixture (4 schedules + perturbation)
    attractor.py          — recurrent basin fixture (entropy-based breadth + perturbation)
    README.md             — fixture specification
  analysis/
    trajectory.py         — TrajectoryEvent + TrajectoryLog schema
    probes.py             — proxy measurement functions (breadth, tension, collapse, etc.)
    morphology_classifier.py  — heuristic CollapseMorphology assignment
  validation/
    cognition_fixture.py  — domain-local validation harness (18/18 checks, 2026-03-21)
  e2e.py                  — end-to-end demo path (4 runs, structured result)
  README.md / SPEC.md / manifest.yaml
```

## Target Pipeline (Architecture)

The target analysis pipeline for a cognition probe session:

1. **Agent observation** — record agent state sequence (human, AI, or simulated)
2. **State-space estimation** — estimate or bound `possibility_breadth` at each step
3. **Tension proxy extraction** — derive `tension_level` from available signals
4. **Collapse detection** — identify collapse events by threshold crossing
5. **Morphology classification** — classify collapse type from post-event trajectory
6. **Perturbation probe** (optional) — inject disruption and measure recovery
7. **Embedding projection** — map `CognitionStateVector → HelixEmbedding`
8. **Atlas registration** — persist event entities for cross-domain comparison

**Current status**:

| Stage | Status |
|-------|--------|
| 1. Agent observation | ❌ not started — toy fixtures used instead |
| 2. State-space estimation | ✅ partial — branching + attractor fixtures |
| 3. Tension proxy extraction | ✅ partial — `estimate_tension()` |
| 4. Collapse detection | ✅ partial — `detect_collapse()` (heuristic threshold) |
| 5. Morphology classification | ✅ partial — heuristic classifier |
| 6. Perturbation probe | ✅ partial — both fixtures support perturbation |
| 7. Embedding projection | ❌ not started |
| 8. Atlas registration | ❌ not started |

> All partial stages are **heuristic first-pass implementations**, not calibrated pipelines.

---

## Entry Point / HSL Integration

**Target**: `HSL: PROBE cognition.<agent_id>`  
**Current**: Not implemented. No HSL command is wired.

---

## Confidence and Calibration

No calibration baseline has been established for this domain. There is no null
corpus and no validated threshold for any domain-local variable.

Target calibration procedure (not yet run):
1. Define null agent (random state transitions, no structural constraint)
2. Compute `possibility_breadth` and `tension_level` distributions over null corpus
3. Set collapse threshold at `mean + 2σ` of null distribution
4. Validate against known collapse events in test fixtures

---

## Canonical Fixtures

Two fixture families are implemented:

#### Branching Decision Fixture (`fixtures/branching.py`)
A toy system with a configurable number of initial branches + constraint schedule:
- **Schedules**: `linear`, `step`, `exponential`, `none` (null control)
- Perturbation: restores branches at a specified step
- Collapse detection: `detect_collapse()` at breadth threshold
- Morphology: heuristic assignment via `classify_morphology()`

#### Attractor Basin Fixture (`fixtures/attractor.py`)
A probability distribution over N discrete states pulled toward an attractor basin:
- Possibility breadth computed from Shannon entropy of state distribution
- Perturbation: mixes in uniform distribution at a specified step
- Supports circular, transformative, and deferred morphology under different configs

Both fixtures produce a `TrajectoryLog` (JSON-serializable, version-stamped).

End-to-end demo: `python -m domains.self.e2e`

---

## Known Gaps

- No real agent input — toy fixtures only (no human or AI session data)
- No HSL integration
- No Atlas registration or artifact persistence
- No calibration data for any domain-local variable — null corpus not yet run
- Collapse morphology classifier is heuristic — not calibrated against null baseline
- `self_boundary_stability` has no operationalization
- DCP probe output (`DCPProbeOutput`) not yet wired to fixture outputs
- `CognitionStateVector → HelixEmbedding` projection not defined

---

## Framework Layer Map

The cognition domain sits within a layered framework:

| Layer | What | Reference |
|-------|------|-----------|
| **Trajectory dynamics** | Process model — full motion from possibility space through collapse | This domain's framing |
| **DCP** | Event-level principle — defines what a compression/collapse event is | `docs/invariants/decision_compression_principle.md` |
| **Collapse morphology** | Classification layer — what kind of outcome the collapse produces | `system/engine/compute/invariants/dcp/morphology.py` |
| **Cognition domain** | Operational test environment — applies above to agent state trajectories | `model/domains/cognition/` |
| **Consciousness research** | Speculative/interpretive layer — above this domain, not inside it | Not a Helix claim |

DCP is the *event-level principle* within trajectory dynamics. The cognition domain
studies DCP events in agent systems. They are connected but not identical — do not
treat DCP as cognition-specific, or cognition as a proof of DCP.

