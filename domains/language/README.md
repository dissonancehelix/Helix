# HELIX LANGUAGE SUBSTRATE

**Version:** 1.0
**Status:** Authoritative formal substrate specification
**Reference SPEC:** [SPEC.md](SPEC.md)

---

## 1. PURPOSE

The Language Substrate is the Helix environment responsible for decomposing **linguistic communication** into its underlying structural invariants. It treats language not as a sequence of strings, but as a hierarchical system of syntax, semantics, and constraints.

## 2. ROLE WITHIN HELIX

The substrate serves as the **Hierarchical Decomposition bridge** between the Library and the Atlas:

### Data Flow
- **Input (Library - Reference Storage)**:
  - Textual datasets (`labs/datasets/language/source/`).
  - **The Library acts as the storage side of the Atlas**, housing lexicons, grammars, and Part-of-Speech invariants (`codex/library/language/`).
- **Helix Engine**:
  - Performs 6-stage extraction (Tokenization → Syntax → Semantics).
  - Normalizes signals under **Partial Observability**.
- **Output (Atlas - Research Memory)**:
  - Sentence/Concept entities and CCS Embeddings (`codex/codex/atlas/language/`).

## 3. STRUCTURAL EXPRESSION

Language is analyzed as a layered symbolic system:
- **Lexical**: Discrete tokens and their properties.
- **Syntactic**: The rules of phrasal arrangement (tree-depth).
- **Semantic**: The underlying conceptual invariants.

The substrate’s goal is to identify **Structural Identity**—the recurring patterns of phrasal construction and conceptual mapping that define an author or a dialect.

## 4. CCS MAPPING (Cognitive Coordinate System)

The substrate maps linguistic features into the standardized 6-axis CCS model:

| Axis | Derived From (Language Domain) | Implementation Layer |
|------|--------------------------------|--------------------|
| **Attractor Stability** | Phrasal repetition / Idiom frequency | Syntactic |
| **Generative Constraint**| Grammatical rule density / Inflection | Syntactic |
| **Recurrence Depth** | Nested clausal hierarchy | Syntactic |
| **Structural Density** | Morphemes/Tokens per semantic unit | Lexical |
| **Control Entropy** | Lexical diversity / Vocabulary | Lexical |
| **Basin Permeability** | Smoothness of topic transitions | Semantic |

## 5. CAPABILITIES

- **Decomposition**: Splitting sentences into parse trees and semantic frames.
- **Mapping**: Projecting syntactic complexity into a single coordinate point.
- **Structural Preservation**: Identifying when different languages (projections) express the same underlying structure (invariant).

## 6. PROJECT EXAMPLE: English vs Spanish (Structural Alignment)

When translating:
*"The quick brown fox jumps over the lazy dog"* (English) ⇄ *"El veloz zorro marrón salta sobre el perro perezoso"* (Spanish)

Helix uses the Language Substrate to prove that while the **Dialects** (Lexical/Syntactic) differ, the **Structural Invariant** (the agent-action-target relationship and the phrasal rhythm) remains comparable in the Atlas. The substrate identifies how Spanish's higher **Generative Constraint** (gender/number agreement) affects its **Structural Density** while preserving the **Attractor Stability** of the core proposition.

---

*For detailed signal definitions, artifact schemas, and library references, see the [SPEC.md](SPEC.md).*
