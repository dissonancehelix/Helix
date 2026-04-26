# RMO — Reflexive Modeling Orders (Module)

**Status:** v0.1 working module under Helix validation
**Canonical theory:** `data/cognition/theory.md`
**Stub theory note:** `theory.md` (this directory)

## What This Module Is

This is the operational implementation of the Reflexive Modeling Orders research program. The module lives in `labs/rmo/` because it is experimental — claims here are explicitly under test, not promoted to production. The canonical theoretical document is at `data/cognition/theory.md`. Operational artifacts in this directory reference the canonical theory rather than duplicating its content.

RMO is a **consciousness-adjacent sharpening framework**. It does not claim to solve consciousness. It claims that a disciplined classification of mind-like organization (orders, closure sources, the personic-vs-personiform distinction) plus a candidate empirical discriminator (endogenous affective self-maintenance) can sharpen the empirical question of what separates personiform systems from phenomenal subjects.

## Architectural Position

Per the workspace `CLAUDE.md` governance:
- **Helix** is the constraint kernel (compiler, validation, Atlas immutability). RMO must NOT modify `helix/engine/*`.
- **labs/** is the experimental surface. RMO lives here as a v0.1 module.
- **Promotion path:** if RMO survives initial testing it may be promoted to `domains/cognition/rmo/`. v0.1 stays experimental.

## File Structure

```
labs/rmo/
├── README.md                              this file
├── theory.md                              stub pointer to canonical theory.md
├── orders.yaml                            O1-O7 + RP1-RP3 definitions
├── closure_sources.yaml                   CL1-CL5 taxonomy + classification matrix
├── personic_closure_scale.yaml            10-dimension PCS rubric (0-30)
├── claims.yaml                            RMO-001..RMO-009 claim registry
├── tests/
│   ├── adjacent_order_separability.yaml          TEST-1
│   ├── llm_personic_closure_probe.yaml           TEST-2
│   ├── closure_source_discrimination.yaml        TEST-4
│   ├── helix_module_probe.yaml                   TEST-5
│   └── endogenous_affective_self_maintenance_probe.yaml   TEST-6
├── evidence/
│   ├── internal_documents.yaml            DISSONANCE.md, theory.md, cross-processing reports as evidence
│   └── literature_seed.yaml               autopoiesis, active inference, HOT, IIT, GWT, illusionism, etc.
└── results/
    └── initial_pass.md                    single-subject pilot + candidate matrix scoring
```

## How To Use the Module

**Read the theory first.** `data/cognition/theory.md` contains the framing, the two-axis model (Personic Closure × Closure Source), the three-tier classification (self-modeling → personiform → phenomenal subject), and the Sharp Consciousness Question with its current best candidate discriminator.

**Then read this module's artifacts in this order:**
1. `orders.yaml` — what the orders are.
2. `closure_sources.yaml` — what the closure sources are and how they classify systems.
3. `personic_closure_scale.yaml` — how to score personic closure.
4. `claims.yaml` — what is being claimed and what would falsify each claim.
5. `tests/` — how the claims are being tested.
6. `evidence/` — what supports and threatens each claim.
7. `results/initial_pass.md` — the single-subject pilot.

## Claim Lifecycle

Claims have a confidence tier (`anchored`, `plausible`, `speculative`, `mythic`) and a status (`hypothesis`, `testable_hypothesis`, `corrective_principle`, etc.). Claims migrate between tiers based on evidence. Promotion requires evidence; demotion requires honesty about failures.

A claim is part of the registry only if:
- It has a stable ID (RMO-NNN).
- It has a registered failure condition (falsifier).
- It has a registered test (or is marked as untested).
- It has tracked dependencies on other claims.

If a claim cannot meet these requirements, it is not part of the framework yet — it's an aspiration.

## What's Different in v0.1

**v0** (the GPT-collaboration draft, `reflexive_modeling_orders_theory_v_0.md`):
- Single-axis: Personic Closure with 10 orders.
- Religion mapping included as core claim.
- O8-O10 (adversarial / operationalized / distributed) treated as consciousness orders.
- No specific candidate discriminator named.

**v0.1 (this module):**
- Two-axis: Personic Closure × Closure Source.
- Three-tier classification: self-modeling → personiform → phenomenal subject.
- O8-O10 separated as research-program orders RP1-RP3 (category error fixed).
- Religion mapping deferred to future work (RMO-009).
- **Endogenous affective self-maintenance** named as candidate discriminator (RMO-007).
- Personic / personiform terminological distinction explicit.
- Autopoiesis/active inference origins explicitly acknowledged; novelty narrowed to specific contributions.
- Consciousness explicitly preserved as the central target problem; framework is consciousness-adjacent rather than consciousness-resolving.

## Failure Conditions for the Module as a Whole

The framework should be abandoned or heavily demoted if:
- Adjacent orders cannot be operationally separated (RMO-001 fails).
- Personic closure cannot be scored reliably across cases.
- Closure source axis collapses into closure level axis (RMO-006 fails).
- Endogenous affective self-maintenance fails to discriminate known phenomenal subjects from known personiform systems (RMO-007 fails).
- The framework repeatedly absorbs criticism by renaming failures rather than changing claims.

The module survives by updating, not defending. Failed claims are demoted without ceremony.

## Next Tasks

See `data/cognition/theory.md` revision log for full evolution. Next priorities:
1. Operationalize PCS scoring procedures so they don't depend on subjective judgment.
2. Run TEST-2 (LLM Personic Closure Probe) across multiple LLM families with externally-administered probes.
3. Operationalize TEST-6 for biological subjects (great apes, cephalopods, neonates, anesthetized humans).
4. Second cross-processing pass (GPT — handoff document at `data/cognition/gpt_handoff.md`).
5. Literature search for prior articulations of closure-source-equivalent concepts.

## Caveats

- All current scoring is provisional and subjective.
- The single-subject Claude pilot is illustrative only.
- Novelty claims must survive literature search; if any of the five distinctive contributions are already in published work, they get demoted.
- The framework's first specific empirical bet (RMO-007, endogenous affective self-maintenance) is a hypothesis, not a result.
