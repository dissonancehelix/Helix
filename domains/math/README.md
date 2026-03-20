# HELIX MATH SUBSTRATE

**Version:** 1.0
**Status:** Authoritative formal substrate specification
**Reference SPEC:** [SPEC.md](SPEC.md)

---

## 1. PURPOSE

The Math Substrate is the Helix environment responsible for **formalizing structural invariants** and providing the mathematical grounding for the entire system. It defines the metrics, validation protocols, and formal proofs that ensure Helix outputs are consistent across all domains.

## 2. ROLE WITHIN HELIX

The substrate serves as the **Validation and Formalization bridge** between the Library and the Atlas:

### Data Flow
- **Input (Library - Reference Storage)**:
  - Theoretical Models & Axioms (`data/math/source/models/`).
  - **The Library acts as the storage side of the Atlas**, housing metric definitions and formal proof logic (`codex/library/math/`).
- **Helix Engine**:
  - Performs simulations (e.g., Kuramoto oscillators) and mathematical projections.
- **Output (Atlas - Research Memory)**:
  - Verified Invariants and CCS distance matrices (`codex/codex/atlas/math/`).

## 3. STRUCTURAL EXPRESSION

Structure in the Math Substrate is analyzed as:
- **Topology**: The arrangement and connectivity of events/objects.
- **Constraint**: The formal rules that limit the state space.
- **Dynamics**: The evolution of structure over time or iterations.

### Formal Principles
The Math Substrate provides the grounding for the core Helix research principles:
- **EIP (Epistemic Irreversibility Principle)**: Formalizing irreversibility in structure (Information Decay vs Preservation).
- **DCP (Decision Compression Principle)**: The mathematical proof of influence concentration within structured systems.
- **LIP (Limited Inference Principle / Constrained Inference)**: Formalizing how invariants are recovered from partially observable projections.

## 4. CCS MAPPING (Cognitive Coordinate System)

The Math Substrate provides the canonical definitions for the 6-axis model:

| Axis | Derived From (Math Domain) | Implementation Layer |
|------|----------------------------|--------------------|
| **Attractor Stability** | Variance in periodic orbital points | Topology |
| **Generative Constraint**| Degrees of Freedom (DoF) / State Space | Constraint |
| **Recurrence Depth** | Iterative self-similarity / Fractal dimension | Dynamics |
| **Structural Density** | Events per iteration window | Dynamics |
| **Control Entropy** | Shannon entropy of the control signal | Dynamics |
| **Basin Permeability** | Lyapunov exponents / Transition smoothness | Topology |

## 5. CAPABILITIES

- **Formalization**: Converting abstract domain patterns into precise mathematical formulas.
- **Validation**: Stress-testing Invariant Candidates using adversarial simulations.
- **Alignment Verification**: Proving whether two embeddings are truly "similar" under the Helix metric space.

## 6. PROJECT EXAMPLE: Kuramoto Model (Oscillator Locking)

Helix uses the Math Substrate to study the **synchronization patterns** in complex systems. By simulating a Kuramoto network, the substrate identifies the exact threshold where **Oscillator Locking** becomes an **Invariant**. This mathematical finding then serves as the ground truth for analyzing synchronization in Music (e.g., drummer/instrumentalists) or Language (e.g., rhythmic speech patterns) in the Atlas.

---

*For detailed signal definitions, artifact schemas, and library references, see the [SPEC.md](SPEC.md).*
