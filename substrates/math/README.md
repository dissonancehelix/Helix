# HELIX MATHEMATICS SUBSTRATE SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal substrate specification
**Authority:** This document is the implementation contract for the Helix Mathematics Substrate.
**Purpose:** Enable reconstruction of the Mathematics Substrate without architectural invention. If code conflicts with this document, this document takes precedence until intentionally revised.

---

## 0. WHY THIS DOCUMENT EXISTS

This document is the formal design specification for the Helix Mathematics Substrate.

Its purpose:
- An LLM can rebuild the substrate without inventing architecture
- Theoretical work is not misplaced into Core or Labs
- Future implementations follow the same structural DNA

---

## 1. SUBSTRATE IDENTITY

### 1.1 What the Mathematics Substrate is

The Mathematics Substrate is the theoretical research arm of Helix.

It investigates the formal structure underlying patterns observed across other substrates.

Other substrates observe phenomena. Mathematics attempts to formalize them.

The substrate studies:
- decision geometry and collapse topology
- dynamical systems and phase transitions
- network stability and synchronization theory
- information-theoretic compression bounds
- formal proofs of invariants conjectured from empirical observation

### 1.2 What the Mathematics Substrate is not

The Mathematics Substrate is not:
- a general-purpose computational mathematics library
- a numerical analysis toolkit
- a statistics package
- a machine learning research framework

It exists to provide theoretical grounding for Helix invariants — not to do arbitrary mathematical computation.

### 1.3 Core identity statement

The Mathematics Substrate exists to answer: **Why does this invariant hold?**

When `decision_compression` is observed empirically in games, music, and language, the Mathematics Substrate asks: what formal structure guarantees this behavior? Can it be proven? Under what conditions does it break down?

---

## 2. CLOSED SYSTEM LAW

The Mathematics Substrate operates under Helix's Closed System Law.

**Substrates never write to Atlas directly.**

The substrate produces artifacts. The Atlas Compiler converts artifacts into Atlas entities.

**Pipeline:**
```
RUN operator:SCAN substrate:math
    → discover theoretical models
    → write model entity artifacts to artifacts/math/

RUN operator:ANALYZE entity:math.model:<id>
    → analyze formal structure
    → write proof and derivation artifacts to artifacts/math/

RUN operator:COMPILE_ATLAS
    → compile artifacts to atlas/mathematics/
```

---

## 3. RESEARCH AREAS

| Area | Description |
|------|-------------|
| Dynamical systems | Phase transitions, attractors, bifurcations |
| Network theory | Synchronization, stability, topology |
| Information theory | Compression bounds, entropy, mutual information |
| Decision geometry | Collapse geometry, irreversibility topology |
| Collective behavior | Emergence, oscillator coupling, coordination theory |

---

## 4. ACTIVE THEORETICAL PROGRAMS

### 4.1 Decision Compression Principle (DCP)

**Claim:** When an agent approaches an irreversible decision point, the cardinality of its available decision space decreases monotonically as a function of time-to-decision.

**Status:** Empirically verified (games 86%, music and language consistent with DCP)

**Formal conjecture:**
```
Let S(t) = decision space cardinality at time t before decision point.
DCP: dS/dt < 0 for t ∈ (-ε, 0), where t=0 is the decision point.
```

**Open questions:**
- Rate of compression — is it always monotone or can it oscillate?
- Minimum cardinality — is there a lower bound above 1?
- Domain universality — what conditions are sufficient for DCP to hold?

### 4.2 Epistemic Irreversibility Principle (EIP)

**Claim:** Once a decision collapses into an outcome, the pre-collapse epistemic state is not recoverable from the post-collapse observable state alone.

**Status:** Formal result established in `interpretation/`

**Relationship to DCP:** EIP is the information-theoretic complement of DCP. DCP describes the compression. EIP describes the irreversibility of that compression.

### 4.3 Oscillator Locking

**Claim:** Coupled oscillators with sufficient coupling strength converge to synchronized phase regardless of initial phase difference.

**Status:** Proven (Kuramoto model). Empirically verified in Helix substrates (100% pass rate).

**Formal basis:** Kuramoto model, mean-field synchronization, Lyapunov stability analysis.

### 4.4 Map8 Permutation Structure

**Status:** Legacy research. Artifacts preserved in `interpretation/`.

Formal topological analysis of 8-element permutation structure. Relevant to decision space geometry.

---

## 5. ANALYSIS PIPELINE

The Mathematics Substrate uses a deterministic, stage-based pipeline.

### 5.1 Stage sequence

```
1. INGESTION
   theoretical model definitions
   conjecture statements
   empirical observation data from other substrates

2. PARSING
   formalization of models into computable representations
   parameter identification
   state space definition

3. STRUCTURAL ANALYSIS
   phase transition analysis
   stability analysis (Lyapunov, eigenvalue)
   topological analysis

4. FEATURE EXTRACTION
   critical threshold identification
   bifurcation points
   invariant set characterization

5. DOMAIN ANALYSIS
   topological structure
   geometric analysis of collapse paths
   formal proof derivation attempts

6. MEASUREMENT SYNTHESIS
   metric synthesis across models
   cross-model invariant detection

7. EMBEDDING GENERATION
   latent structural representation
   embedding in formal proof space

8. PATTERN DETECTION
   cross-model invariant detection (Map8 mappings)
   unifying structural principles

9. ATLAS INTEGRATION
   formal registration of proven invariants
   proof artifact compilation

10. INTERPRETATION
    theoretical formulation and hypothesis generation
    formal statements for experimental validation
```

### 5.2 Artifact outputs

All artifacts written to `artifacts/math/<model_id>/`:

| Artifact | Description |
|----------|-------------|
| `model_spec.json` | Formal model definition |
| `phase_diagram.json` | Phase transition structure |
| `stability_analysis.json` | Lyapunov/eigenvalue results |
| `proof_sketch.json` | Formal proof or proof sketch |
| `critical_thresholds.json` | Identified critical parameter values |
| `invariant_candidate.json` | Proposed invariant for empirical testing |

---

## 6. ENTITY TYPES

### 6.1 Mathematics entities

| Entity Type | ID Format | Description |
|-------------|-----------|-------------|
| `MathModel` | `math.model:<slug>` | Formal mathematical model |
| `Conjecture` | `math.conjecture:<slug>` | Formal conjecture statement |
| `Proof` | `math.proof:<slug>` | Proof artifact |
| `CriticalThreshold` | `math.threshold:<slug>` | Critical parameter value |
| `PhaseTransition` | `math.phase:<slug>` | Identified phase transition |
| `InvariantCandidate` | `math.candidate:<slug>` | Proposed invariant from theory |

### 6.2 Relationships

```
Proof → PROVES → Conjecture
Conjecture → PREDICTS → Invariant
PhaseTransition → IDENTIFIED_IN → MathModel
CriticalThreshold → CHARACTERIZES → PhaseTransition
InvariantCandidate → FORMALIZES → Invariant
MathModel → EXPLAINS → Invariant
```

---

## 7. RELATIONSHIP TO HELIX INVARIANTS

The Mathematics Substrate provides theoretical explanations for empirically observed invariants.

| Invariant | Mathematical basis |
|-----------|-------------------|
| `decision_compression` | Decision space topology; DCP formal conjecture |
| `oscillator_locking` | Kuramoto model; mean-field synchronization theory |

**Validation flow:**
```
Math Substrate (theory) → conjecture
    → Games/Music/Language Substrate (empirics) → observation
    → probe confirms / disconfirms conjecture
    → Math Substrate refines theory
```

The Mathematics Substrate does not generate empirical data. It generates theoretical structure that predicts what empirical data should look like.

---

## 8. REPOSITORY STRUCTURE

```
substrates/math/
├── README.md                      ← this document
├── ingestion/                     ← stage 1: model definitions, conjecture import
├── parsing/                       ← stage 2: formalization into computable form
├── structural_analysis/           ← stage 3: phase transitions, stability
├── feature_extraction/            ← stage 4: thresholds, bifurcations
├── domain_analysis/               ← stage 5: topology, geometry, proof attempts
├── measurement_synthesis/         ← stage 6: cross-model metrics
├── embedding_generation/          ← stage 7: latent structural representations
├── pattern_detection/             ← stage 8: cross-model invariants (Map8)
├── atlas_integration/             ← stage 9: artifact prep for compiler
└── interpretation/                ← stage 10: theory and hypothesis documents
    ├── map8/                      ← Map8 permutation structure artifacts
    ├── dcp/                       ← Decision Compression Principle formalization
    ├── eip/                       ← Epistemic Irreversibility Principle formalization
    └── oscillator_locking/        ← Kuramoto-based synchronization theory
```

---

## 9. HIL CONTRACT

All orchestration occurs through HIL.

Examples:
```
RUN operator:SCAN substrate:math
RUN operator:ANALYZE entity:math.model:kuramoto_oscillator
PROBE invariant:decision_compression lab:math
ATLAS list domain:mathematics
ENTITY get math.conjecture:decision_compression_principle
GRAPH support invariant:decision_compression
```

---

## 10. ANTI-DRIFT RULES

- Do not write mathematical analysis directly to `atlas/` — use the artifact pipeline
- Do not invent general-purpose mathematical tooling — scope is Helix invariant theory only
- Do not conflate theoretical analysis with empirical observation — that belongs in other substrates
- Formal proof attempts must document assumptions explicitly

---

## 11. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the Mathematics Substrate from this document.

Required components:
- [ ] 10-stage analysis pipeline (ingestion through interpretation)
- [ ] Artifact schemas matching §5.2
- [ ] Entity types matching §6.1 with correct ID format
- [ ] Active theoretical programs for DCP, EIP, oscillator locking
- [ ] All artifacts written to `artifacts/math/`, never to `atlas/`
- [ ] HIL-only orchestration interface
- [ ] Interpretation directory with DCP, EIP, oscillator locking, Map8 subdirectories

---

*This document is the authoritative specification for the Helix Mathematics Substrate.*
*Version 2.0 — 2026-03-17*


---

## Architecture Guardrail

**Helix Architecture Law**
`HIL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler`

* Operators orchestrate
* Adapters translate
* Toolkits execute
* Artifacts store results
* Atlas compiler creates entities

**Prohibited Patterns**
- `master_pipeline.py`
- Direct toolkit calls from operators
- Toolkits writing artifacts
- Toolkits writing Atlas entities
- Operators writing Atlas entities
- Monolithic pipelines

*All new modules must follow the template registry located in `runtime/templates/`.*
