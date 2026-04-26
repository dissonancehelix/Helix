# HELIX LANGUAGE SUBSTRATE SPECIFICATION

**Version:** 1.2
**Status:** Authoritative target specification — implementation status tracked in README.md §11
**Relationship:** Extends `domains/language/README.md`

---

## 1. DOMAIN SCOPE

The Language Substrate operates across three primary layers:
- **Lexical**: Discrete tokens, morphemes, and their surface properties
- **Syntactic**: Phrasal arrangement rules, parse structure, dependency relations
- **Semantic**: Underlying conceptual structure, thematic roles, topic coherence

Its goal is to identify structural identity — recurring patterns of phrasal construction and conceptual mapping that define an author, dialect, or language family — and extract invariants that survive translation or register shift.

---

## 2. DOMAIN-LOCAL STRUCTURAL SIGNALS

These signals are extracted by the language pipeline and are domain-local. They are NOT the same as HelixEmbedding axes. They feed into the feature fusion stage which produces a shared embedding.

### 2.1 Lexical Signals
- **`morpheme_density`**: Atomic units of meaning per word
- **`lexical_diversity`**: Type-token ratio (TTR) within analysis window
- **`phonetic_entropy`**: Distribution variation of phonemes (spoken corpora only)

### 2.2 Syntactic Signals
- **`phrasal_depth`**: Maximum depth of the constituent parse tree
- **`dependency_length`**: Cumulative linear distance between governors and dependents
- **`inflectional_constraint`**: Density of morphosyntactic markers (gender, number, tense)
- **`phrasal_repetition_rate`**: Frequency of recurring phrasal patterns

### 2.3 Semantic Signals
- **`topic_cohesion`**: Semantically related vectors per unit text
- **`argument_structure_complexity`**: Count of thematic roles correctly filled
- **`topic_transition_smoothness`**: Cosine similarity between adjacent semantic windows

---

## 3. SHARED EMBEDDING PROJECTION

Language-domain signals are fused and projected into the shared `HelixEmbedding` format.

**Projection mapping** (signal → embedding axis):

| HelixEmbedding Axis | Primary Language Signal | Normalization Method |
|---------------------|-------------------------|----------------------|
| `structure` | `phrasal_repetition_rate` | Baseline: news corpus idiom density |
| `complexity` | `inflectional_constraint` | Scale of grammatical rule-boundness |
| `repetition` | `clausal_nesting_depth` | Max level of subordinate clauses |
| `density` | `morpheme_density` | Tokens/morphemes per semantic unit |
| `variation` | `lexical_diversity` | Author-specific vocabulary variance |
| `expression` | `topic_transition_smoothness` | Cosine similarity between adjacent windows |

**Non-equivalence rule**: HelixEmbedding axis names are system-wide. Language signal names are domain-local. The mapping is explicit and not a naming equivalence.

**Projection schema versioning**: Implemented as `language_v1` on runtime embedding artifacts.

---

## 4. PIPELINE STAGES

| Stage | Responsibility | Input | Output | Status |
|-------|----------------|-------|--------|--------|
| 1 | Ingestion | Raw text / fixture corpus | Language records | ✅ Implemented |
| 2 | Tokenization | Text stream | Tokens / morphemes | ✅ Heuristic |
| 3 | Syntax parse | Token stream | Surface structure stats / morphology | ✅ Heuristic |
| 4 | Semantic tagging | Fixture pairs / records | Frame hints / register labels | ⚠️ Fixture-backed |
| 5 | Feature fusion | All layers | `language_structural_vector` + substrate / DCP / semantic blocks | ✅ Implemented |
| 6 | Atlas compilation | Artifacts | Corpus-level Atlas entities with explicit Helix blocks | ⚠️ Optional / partial |

---

## 5. ARTIFACT SCHEMAS

### SyntacticProfile (`artifacts/language/<id>/syntax.json`)
```json
{
  "sentence_id": "...",
  "parse_tree_depth": 14,
  "dependency_graph": {},
  "constraint_indices": {}
}
```

### SemanticFrame (`artifacts/language/<id>/semantics.json`)
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

### HelixEmbedding (`artifacts/language/<id>/embedding.json`)
```json
{
  "complexity": 0.65,
  "structure": 0.82,
  "repetition": 0.44,
  "density": 0.31,
  "expression": 0.22,
  "variation": 0.76,
  "confidence": 0.61,
  "domain": "language",
  "source_vector": "language_style_vector",
  "projection_schema": "language_v1"
}
```

### Substrate Block (`artifacts/language/<id>/substrate_profile.json`)
```json
{
  "block": "substrate",
  "schema_version": "language_substrate_v1",
  "possibility_space": 0.91,
  "constraint": 0.22,
  "attractor_stability": 0.78,
  "basin_permeability": 0.63,
  "recurrence_depth": 0.41
}
```

### DCP Block (`artifacts/language/<id>/dcp_block.json`)
```json
{
  "block": "dcp",
  "schema_version": "language_dcp_block_v1",
  "source_boundary": "construction_family_transform",
  "possibility_space": 0.94,
  "constraint": 0.14,
  "tension": 0.15,
  "collapse": 0.37,
  "post_narrowing": 0.66,
  "composite": 0.46,
  "qualification": "FULL",
  "event_count": 8,
  "dominant_morphology": "CIRCULAR"
}
```

### Probe / Trajectory Artifacts

- `dcp_events.json` emits shared `DCPEvent` records for family-local transforms
- `dcp_probe_output.json` emits shared `DCPProbeOutput`
- `trajectory_dynamics.json` packages the corpus-level transform family map and morphology histogram
- `corpus_profile.json`, `structure_profile.json`, and `semantic_profile.json` expose the top-level Helix runtime blocks compiled into Atlas
- `parser_traces.json` emits one `language_parser_trace_v1` record per text fixture using the canonical `heuristic_surface_parser` backend

### Sentence-Level Atlas Entity Packaging

When Atlas compilation is enabled, the language runtime emits:

- one `Corpus` entity for the full lattice
- one `Text` entity per fixture record under `codex/atlas/language/texts/`

Each `Text` entity includes:
- shared Substrate Capability Vector embedding
- corpus link (`PART_OF`)
- variant relation (`VARIANT_OF`) when the record is a transform target
- sentence-local `structure` and `dcp` views derived from `parser_traces.json` and corpus DCP events

---

## 6. VALIDATION RULES

- **Translation preservation check**: Deterministic EN↔ES fixture must maintain alignment score > 0.80 for annotated invariants — implemented
- **Model invariance** (target): Syntactic depth measurements must be consistent across parser adapters (SpaCy vs NLTK) — not yet validated
- **Null model guard**: Randomized token sequences must not collapse into the same construction-space signature as the curated corpus — implemented heuristically
- **DCP block integrity**: Corpus runs must emit shared-schema `DCPEvent` artifacts and a non-empty corpus-level `dcp` block — implemented
- **Atlas block packaging**: Compiled corpus entities must expose `substrate`, `dcp`, `corpus`, `structure`, and `semantic` blocks at the top level — implemented
- **Sentence entity packaging**: Compiled `Text` entities must carry parser traces and `PART_OF` corpus relationships — implemented

Validation suites currently ship as:
- `test_language_contracts.py`
- `test_language_transforms.py`
- `test_language_controls.py`
- `test_language_stack.py` (aggregate runner)

---

## 7. METRIC SPACE / SIMILARITY / DISTANCE

The HelixEmbedding metric space uses Euclidean distance normalized by √6:

```
distance(a, b) = euclidean(a, b) / sqrt(6)          ∈ [0, 1]
similarity(a, b) = 1 - distance(a, b)               ∈ [0, 1]
```

**Triangle inequality** applies to **distance**, not similarity:
```
d(a, c) ≤ d(a, b) + d(b, c)
```

A violation is a `STRUCTURAL_FAILURE`.

---

## 8. ENTRY / HSL INTEGRATION STATE

**Target**: HSL commands `INGEST_TRACK language.<id>`, `ANALYZE_TRACK language.<id>`\
**Current**: Canonical runtime is `SUBSTRATE run name:language corpus:<fixture> lang:<language>`. `pipeline.py` is runnable and HSL-routed.

---

## 9. THRESHOLDS AND CALIBRATION

| Threshold | Value | Status |
|-----------|-------|--------|
| Minimum embedding confidence | 0.30 | Provisional — global default, not language-calibrated |
| Translation alignment floor | 0.80 | Defined; calibration basis unknown |

Calibration procedure for confidence floor: generate null corpus (random token sequences) → compute embedding distribution → set at `mean + 2 * std`. Not yet performed.

---

## 10. PROMOTION CONDITIONS

Invariant candidates must pass the global 6-criterion promotion gate (see `docs/GOVERNANCE.md`). No language-domain candidates have been promoted or are in active pipeline.

---

## 11. KNOWN ASSUMPTIONS / OPEN CONSTRAINTS

- Language domain assumes Unicode text input with sentence boundary detection
- Current runtime is heuristic and fixture-led rather than parser-backed
- Spanish and English construction maps are implemented; open-world corpora remain out of scope for now
- Translation invariant (0.80 floor) is currently grounded only in deterministic fixture data
- `projection_schema` versioning is fixed at `language_v1`
- Sentence-level Atlas entities are compiled, but cross-language `TRANSLATES_TO` links are not yet emitted
