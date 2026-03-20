# HELIX LANGUAGE SUBSTRATE SPECIFICATION (SPEC)

**Version:** 1.0
**Status:** Authoritative technical specification
**Relationship:** Implementation partner to `domains/language/README.md`

---

## 1. FORMAL SIGNAL DEFINITIONS

The Language Substrate extracts measurable signals from three primary layers:

### 1.1 Lexical Signals (Token/Morpheme)
- **`morpheme_density`**: Atomic units of meaning per word.
- **`lexical_diversity`**: Type-token ratio (TTR) within a window.
- **`phonetic_entropy`**: Distribution variation of phonemes (for spoken subsets).

### 1.2 Syntactic Signals (Grammar)
- **`phrasal_depth`**: Maximum depth of the constituent parse tree.
- **`dependency_length`**: Cumulative linear distance between governors and dependents.
- **`inflectional_constraint`**: Density of morphosyntactic markers (gender, number, tense).

### 1.3 Semantic Signals (Meaning)
- **`topic_cohesion`**: Semantically related vectors per unit text.
- **`argument_structure_complexity`**: Count of thematic roles correctly filled (Agent, Patient, Instrument).

---

## 2. CCS AXIS DERIVATION

The 6 CCS axes are derived from the above signals using the following normalization methods:

| CCS Axis | Primary Language Signal | Helix Normalization Method |
|----------|-------------------------|----------------------------|
| `attractor_stability` | `phrasal_repetition_rate` | Baseline: News corpus idiom density |
| `generative_constraint` | `inflectional_constraint` | Scale of grammatical rule-boundness |
| `recurrence_depth` | `clausal_nesting_depth` | Max level of subordinate clauses |
| `structural_density` | `morpheme_density` | Tokens/Morphemes per semantic unit |
| `control_entropy` | `lexical_diversity` | Author-specific vocabulary variance |
| `basin_permeability` | `topic_transition_smoothness` | Cosine similarity between adjacent windows |

---

## 3. EXTRACTION PIPELINE (6 STAGES)

| Stage | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| 1 | Ingestion | Raw Text | Language Index Entry |
| 2 | Tokenization | Text Stream | Tokens / Morphemes |
| 3 | Syntax Parse | Token Stream | Parse Tree / Dep. Graph |
| 4 | Semantic Tagging | Parse Tree | Semantic Roles / Frames |
| 5 | Feature Fusion | All Layers | Author/Dialect Style Vector |
| 6 | Atlas Compilation| Artifacts | Atlas Entities |

---

## 4. ARTIFACT SCHEMAS

### 4.1 SyntacticProfile (`artifacts/language/<id>/syntax.json`)
```json
{
  "sentence_id": "...",
  "parse_tree_depth": 14,
  "dependency_graph": {...},
  "constraint_indices": {...}
}
```

### 4.2 SemanticFrame (`artifacts/language/<id>/semantics.json`)
```json
{
  "sentence_id": "...",
  "thematic_roles": {
    "agent": "fox",
    "action": "jumps",
    "target": "dog"
  }
}
```

### 4.3 StructuralEmbedding (`artifacts/language/<id>/embedding.json`)
```json
{
  "id": "...",
  "ccs_v1_coordinates": [0.65, 0.82, 0.44, 0.31, 0.76, 0.22]
}
```

---

## 5. VALIDATION

- **Translation Preservation Check**: A sentence translated into a different language must maintain a cross-substrate **Alignment Score > 0.80** for its semantic invariants.
- **Model Invariance**: Syntactic depth measurements must be consistent across different parser adapters (e.g., SpaCy vs NLTK).
