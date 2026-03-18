# Helix

**Closed semantic execution system for experimental invariant discovery.**

Helix is a constrained, deterministic research machine. It discovers structural invariants across complex systems by running experiments through a formal five-layer execution pipeline. Every input is normalized, every entity is semantically validated, every action is performed by a registered operator, and every piece of knowledge is compiled into a structured Atlas before it can be reasoned about.

The system is built on **HSL (Helix Structural Language)**, the root abstraction from which all domain-specific languages (substrates) are derived.

This document is the authoritative system specification. A complete Helix instance can be regenerated from this file, `HSL.md`, and the substrate READMEs.

---

## Closed System Law

```
No untyped input.
No undefined meaning.
No unregistered execution.
No unvalidated output.
No direct Atlas writes.
```

All execution passes through:

```
HSL → Normalization → Semantics → Operators → Atlas Compiler → Atlas
```

Substrates produce artifacts. The Atlas Compiler converts artifacts into Atlas entities. Nothing else writes to Atlas.

---

## Execution Pipeline

### Layer 1 — HSL (Syntax)

The Helix Structural Language. A strict formal DSL. The only valid way to express intent and structure in Helix. See `HSL.md` for the complete language specification.

| Component | Location | Purpose |
|-----------|----------|---------|
| Grammar (EBNF) | `core/hil/grammar.ebnf` | Authoritative syntax definition |
| Parser | `core/hil/parser.py` | Tokenizer → typed AST |
| Validator | `core/hil/validator.py` | 10-stage semantic validation |
| Interpreter | `core/hil/interpreter.py` | Command execution dispatcher |
| Dispatcher | `core/hil/hil_dispatch.py` | Routes to interpreter or kernel |
| Normalizer | `core/hil/normalizer.py` | Shim → `core/normalization/` |
| Aliases | `core/hil/aliases.py` | Human shorthand → canonical HSL |
| Command registry | `core/hil/command_registry.py` | Formal spec of all 24 command families |
| AST nodes | `core/hil/ast_nodes.py` | `HSLCommand`, `TypedRef`, `RangeExpr` |
| Errors | `core/hil/errors.py` | 6 typed error classes |
| Semantic roles | `core/hil/semantic_roles.py` | 11 relationship role types |
| Ontology | `core/hil/ontology.py` | 24 HSL object types, valid engines |

Non-HSL input is rejected. There is no fallback to Python or shell in runtime mode.

### Layer 2 — Normalization

Before semantic validation, all inputs are normalized to canonical form.

| Component | Location | Purpose |
|-----------|----------|---------|
| Normalizer | `core/normalization/normalizer.py` | Alias resolution, casing, typed ref resolution |
| ID enforcer | `core/normalization/id_enforcer.py` | Pattern validation, namespace check |
| Errors | `core/normalization/errors.py` | `NormalizationError`, `InvalidIDError`, `DuplicateEntityError` |

**Normalization pipeline:**
1. Alias resolution (`"Jun Senoue"` → `music.composer:jun_senoue`)
2. Casing normalization (verbs/types upper, slugs lower)
3. ID pattern enforcement: must match `^[a-z_]+\.[a-z_]+:[a-z0-9_]+$`
4. Typed reference resolution: `prefix:name` → registry entity lookup
5. Deduplication detection: warn if entity ID already registered

### Layer 3 — Semantics

Defines all valid meaning. Every entity type has a `SemanticSignature` declaring required fields, optional fields, and allowed relationships.

| Component | Location | Purpose |
|-----------|----------|---------|
| Entity registry | `core/semantics/entity_registry/entity_types.py` | `SemanticSignature` for all 19 types |
| Property registry | `core/semantics/property_registry/property_types.py` | 50+ typed `PropertySpec` definitions |
| Relationship registry | `core/semantics/relationship_registry/relationship_types.py` | 30+ typed `RelationshipSpec` definitions |
| Validator | `core/semantics/validator.py` | `SemanticValidator.validate()` → `ValidationResult` |

No entity may exist without a registered type. No property may be unknown. No relationship may connect incompatible types.

### Layer 4 — Operators

The only execution units in runtime mode. Operators are functional units that orchestrate adapters and toolkits. Each operator declares exactly what it accepts, what it produces, and its fixed pipeline stages.

**Core System Operators:**
- `INGEST_TRACK`: Ingest music file to ControlSequence.
- `ANALYZE_TRACK`: Full structural analysis (MIR, Motifs, Geometry, Causal).
- `DISCOVER`: Pattern/Theory search (data-driven or target:model).
- `DISCOVER_INVARIANTS`: Autonomously propose new hypotheses.
- `FALSIFY_INVARIANT`: Search for counterexamples to update confidence.
- `TOPOLOGY_MAP`: Compare structural behavior across domains.
- `MEASURE_KNOWLEDGE_GAIN`: Monitor semantic saturation.
- `COMPILE_ATLAS`: The ONLY authorized path for writing to Atlas.

Operators follow the `run(payload)` pattern, performing validation before dispatching to the adapter layer. No operator generates scripts at runtime or writes to Atlas directly.

### Section X — Multi-Artist Attribution Handling

Helix handles tracks with multiple credited artists by treating them as latent mixture models.

1. **Artist Parsing**: `INGEST_TRACK` parses multiple artists using the `;` delimiter.
2. **Attribution Type**: Tracks are tagged as `solo`, `multi`, or `inferred`.
3. **Contribution Structure**: `artist_contributions` stores a list of `{artist_id, confidence, source}`.
4. **Style Vector Weighting**: `ANALYZE_TRACK` (compute_style_vector stage) weights contributions: `effective_weight = confidence * attribution_weight`. Weights: `solo` (1.0), `inferred` (0.5–1.0), `multi` (0.25).
5. **Attribution Inference**: `DISCOVER target:attribution track:<id>` compares track features against artist style vectors to predict authorship.
6. **Refinement**: Verified inferences update `attribution_type` to `inferred` and refine contribution weights.

---

### Layer 5 — Atlas Compiler → Atlas

The only authorized path for writing to Atlas. Enforces normalize → validate → compile → commit.

| Component | Location | Purpose |
|-----------|----------|---------|
| Compiler | `core/compiler/atlas_compiler.py` | Full compilation pipeline (700+ lines) |
| Output root | `atlas/` | Organized by substrate |
| Entity index | `atlas/entities/registry.json` | Authoritative entity index |

---

## Execution Modes

Controlled by the `HELIX_MODE` environment variable (default: `runtime`).

| Mode | Operators | Schemas | Atlas writes | Script execution |
|------|-----------|---------|--------------|-----------------|
| `runtime` | registered only | immutable | compiler only | blocked |
| `dev` | register new | evolvable | compiler only | allowed |

```bash
HELIX_MODE=dev helix ...
```

---

## Repository Structure

```
Helix/
│
├── helix                          ← CLI entry point (bash wrapper)
├── README.md                      ← System Overview
├── SPEC.md                        ← Detailed technical specification
├── HSL.md                         ← HSL language specification
├── DISSONANCE.md                  ← Operator profile
├── pyproject.toml                 ← Python package definition
│
├── core/                          ← Execution infrastructure
│
├── substrates/                    ← Domain analysis pipelines
│
├── atlas/                         ← Compiled semantic knowledge
│
├── data/                          ← Root Data Layer (Immutable + Processed)
│   ├── music/
│   │   ├── source/                ← Raw knowledge (manuals, source, audio)
│   │   ├── processed/             ← Structured extraction (parsed, features)
│   │   └── metadata/              ← Curated tags and annotations
│   ├── agents/
│   └── language/
│
├── execution/                     ← Runtime Execution Layer
│   ├── runs/                      ← Command history and results
│   ├── logs/                      ← Detailed trace logs
│   └── integrity/                 ← Validation and audit logs
│
├── labs/                          ← Active research probes
├── governance/                    ← Validation and promotion rules
└── applications/                  ← Tools built on Helix invariants
```

---

## Entity System

### Canonical ID Format

```
namespace.type:slug
```

| Part | Description | Pattern |
|------|-------------|---------|
| `namespace` | substrate or domain | `music`, `games`, `language`, `mathematics`, `system` |
| `type` | entity type (lowercase) | matches `ENTITY_ONTOLOGY` slug |
| `slug` | unique identifier | lowercase, underscores, digits |

Examples:
```
music.composer:jun_senoue
music.track:8aa0534f...
games.invariant:decision_compression
music.controlsequence:8aa0534f_cs
```

### Entity Schema (all entities)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | canonical `namespace.type:slug` |
| `type` | string | yes | must be in `ENTITY_ONTOLOGY` |
| `name` | string | yes | human-readable display name |
| `label` | string | yes | short display label; defaults to `name` on load |
| `description` | string | required in runtime | one-sentence description |
| `metadata` | dict | no | domain extras + provenance keys |
| `external_ids` | dict | no | references to external knowledge bases |
| `relationships` | list | no | `[{relation, target_id, confidence}]` |

**Provenance keys (required for pipeline-generated entities):**
`source`, `source_stage`, `source_artifact`, `extraction_method`

### Entity Types (19 total)

**Core music domain:**

| Type | Purpose | Required Extra Fields | Allowed Relationships |
|------|---------|----------------------|----------------------|
| `Composer` | Music creator | — | COMPOSED, MEMBER_OF, COLLABORATED_WITH |
| `Track` | Musical work | — | APPEARS_IN, COMPOSED_BY |
| `Game` | Videogame title | — | RUNS_ON, USES_CHIP, HAS_SOUNDTRACK |
| `Platform` | Hardware platform | — | HOSTS, USES_CHIP |
| `SoundChip` | Audio hardware | — | USED_BY |
| `SoundTeam` | Composer group | — | MEMBER_OF |

**Music analysis artifacts (produced by operators):**

| Type | Purpose | Required Extra Fields | Allowed Relationships |
|------|---------|----------------------|-----------------------|
| `ControlSequence` | Hardware register-write log | `source_track`, `chip_target` | DERIVED_FROM |
| `MirFeatures` | Audio signal features | `source_track` | DERIVED_FROM |
| `MotifFeatures` | Symbolic music theory | `source_track` | DERIVED_FROM |
| `ArtistStyleVector` | Composer musical fingerprint| `composer_id` | ATTRIBUTED_TO, SIMILAR_TO |
| `CollapseGeometry` | Entropy funnel (DCP) | `source_track` | DERIVED_FROM |
| `CausalMap` | Synthesis → Signal link | `source_track` | DERIVED_FROM |

**Reserved (planned substrates):**

| Type | Purpose |
|------|---------|
| `Soundtrack` | Game soundtrack collection |
| `Studio` | Development studio |

**Research domain:**

| Type | Purpose | Required Extra Fields | Allowed Relationships |
|------|---------|----------------------|-----------------------|
| `Dataset` | Input data collection | `source`, `version` | USED_BY, DERIVED_FROM |
| `Experiment` | Falsification test | `source` | TESTS, SUPPORTS, CONTRADICTS, DERIVED_FROM |
| `Model` | Explanatory structure | — | IMPLEMENTS, TRAINED_ON, EVALUATED_BY |
| `Invariant` | Cross-domain structural rule | `source` | SUPPORTED_BY, CONTRADICTED_BY, TESTED_BY, RELATES_TO, FORMALIZED_BY |
| `MathModel` | Formal mathematical model | `formal_definition` | EXPLAINS, FORMALIZES, APPLIED_TO |
| `Conjecture` | Formal conjecture | `statement` | PREDICTS, PROVEN_BY |
| `Proof` | Math proof/derivation | — | PROVES, DERIVED_FROM |
| `ResearchReport`| Falsification/Map details | `report_type`, `findings` | DOCUMENTS, FALSIFIES, MAPS |
| `Operator` | Execution unit | `version` | IMPLEMENTS, USES, PRODUCES |
| `Driver` | Substrate driver | — | DRIVES, USED_BY |
| `Infrasubstrate` | Infrastructure layer | — | DEPENDS_ON, PROVIDES |

---

## HSL Architecture Schemas

### HSL (Root Language)
```json
{
  "language": "HSL",
  "version": "2.0.0",
  "capabilities": ["representation", "translation", "alignment", "invariant_discovery"],
  "root_abstraction": true
}
```

### SubstrateLanguage
```json
{
  "type": "SubstrateLanguage",
  "derived_from": "HSL",
  "id": "substrate.language:slug",
  "domain": "string",
  "dialects": ["list of dialect slugs"]
}
```

### Dialect
```json
{
  "type": "Dialect",
  "id": "substrate.dialect:slug",
  "substrate": "substrate.language:slug",
  "representation_format": "string",
  "structural_rules": "list"
}
```

### TranslationMapping
```json
{
  "type": "TranslationMapping",
  "id": "translation.map:slug",
  "source_dialect": "substrate.dialect:slug",
  "target_dialect": "substrate.dialect:slug",
  "transformation_logic": "operator_id",
  "lossless": true
}
```

---

## Invariant Definition Constraints

Invariants must be defined independent of any single dialect. Dialects are partial observations of the same underlying structure — a VGM register stream, a MIDI score, and a rendered audio file may all express the same compositional object through different observability windows. An invariant that can only be measured in one dialect is not a structural invariant; it is a format artifact.

Helix models structure under partial observability, reconstructing invariants from available representations.

Required properties for a valid invariant definition:
- Measurable from at least one dialect (perceptual_audio is the minimum baseline)
- Not invalidated by the absence of any single dialect
- Confidence score must reflect observability depth of supporting evidence
- Missing dialect fields are recorded as absent, not as zero or default

---

## Invariant Lifecycle System

Invariants are hypotheses describing recurring structural patterns (Decision Compression, Epistemic Irreversibility, etc.).

**Lifecycle States:**
`proposed → measured → tested → falsified → refined → verified → retired`

**Core Invariant Fields:**
- `status`: Lifecycle state.
- `confidence_score`: Probability the pattern is a universal law (0.0 - 1.0).
- `dissonance_score`: Ratio of counterexamples to total evidence.
- `evidence_entities`: Supporting Atlas objects.
- `counterexamples`: Contradicting Atlas objects.

---

## Closed Semantic Research Loop

Helix operates as a self-correcting research system:
1. **Measure Structure**: Substrates extract features (MIR, Symbolic, Causal).
2. **Store Artifacts**: results written to `artifacts/`.
3. **Compile Atlas**: `COMPILE_ATLAS` creates formal entities.
4. **Apply Math Models**: Use mathematical substrate to formalize patterns.
5. **Discover & Test**: Propose invariants and test them via `PROBE`.
6. **Falsify & Refine**: Use `FALSIFY_INVARIANT` to hunt for counterexamples and update confidence.
---

## Operator Registry

9 registered operators. `RUN operator:UNKNOWN` raises `HSLValidationError` in all modes.

### Music Substrate Operators

| Operator | Accepted Input Types | Output Schema | Pipeline Stages |
|----------|---------------------|---------------|----------------|
| `INGEST_TRACK` | Track, * | `{track_id, control_sequence, artifact_path}` | validate_source → route_to_adapter → translate_to_chip_control → write_artifact |
| `ANALYZE_TRACK` | Track, ControlSequence, Composer | `{track_id, mir_features, motif_features, collapse_geometry, cause_effect_map, artist_style_vector}` | load_artifacts → translate_to_perceptual_audio → translate_to_symbolic_music → generate_collapse_geometry → generate_causal_map → compute_style_vector → write_research_artifacts |
| `COMPILE_ATLAS` | * | `{entities_compiled, atlas_paths}` | discover_artifacts → normalize → semantic_validate → atlas_commit |

### Research / Discovery Operators

| Operator | Accepted Input Types | Output Schema | Pipeline Stages |
|----------|---------------------|---------------|----------------|
| `DISCOVER` | Invariant, MathModel, * | `{candidate_commands, model_match_report, invariant_candidates}` | load_context → pattern_search → theory_search → generate_output |
| `DISCOVER_INVARIANTS` | * | `{invariant_candidates, compression_score}` | extract_patterns → detect_compression → validate_consistency → align_with_math → write_candidate_artifact |
| `FALSIFY_INVARIANT` | Invariant | `{falsification_report, confidence_score, dissonance_score}` | load_invariant → detect_deviations → calculate_scores → write_report |
| `TOPOLOGY_MAP` | * | `{topology_mapping, alignment_score}` | extract_descriptors → compare_structural_behavior → write_mapping_artifact |
| `MEASURE_KNOWLEDGE_GAIN` | * | `{knowledge_gain_report, dataset_status}` | measure_variance_shift → check_motif_expansion → check_invariant_shift → write_gain_report |
| `QUERY` | * | `{matching_entities, entity_type}` | load_atlas_index → apply_filters → return_results |

---

## Adapter Layer

`core/adapters/` — Pure translation layers. No Helix logic. Every adapter strictly follows the `Adapter` template, providing a unified `execute(payload)` entry point and a `normalize(result)` stage.

Adapters are registered by their original names (e.g., `LibvgmAdapter`) but implement the standardized `Adapter` interface.

| Adapter | Toolkit | Purpose | Interface |
|---------|---------|---------|-----------|
| `adapter_libvgm.py` | libvgm (ValleyBell) | VGM/VGZ emulation | `execute(payload)` |
| `adapter_gme.py` | Game_Music_Emu | SPC, NSF, GBS, HES, KSS, AY | `execute(payload)` |
| `adapter_vgmstream.py` | vgmstream CLI | Audio decoding & envelope | `execute(payload)` |
| `adapter_nuked_opn2.py` | Nuked-OPN2 | YM2612 FM topology (Tier A) | `execute(payload)` |
| `adapter_nuked_opm.py` | Nuked-OPM | YM2151 FM topology (Tier A) | `execute(payload)` |
| `adapter_nuked_opl3.py` | Nuked-OPL3 | OPL3 FM topology (Tier A) | `execute(payload)` |
| `adapter_nuked_opll.py` | Nuked-OPLL | YM2413 fixed-patch topology (Tier A) | `execute(payload)` |
| `adapter_nuked_opl2.py` | Nuked-OPL2-Lite | YM3812 2-op FM topology (Tier A) | `execute(payload)` |
| `adapter_nuked_psg.py` | Nuked-PSG | SN76489/YM7101 PSG channels (Tier A) | `execute(payload)` |
| `adapter_smps.py` | SMPS | Sega SMPS driver constants (Tier A) | `execute(payload)` |
| `adapter_gems.py` | GEMS | GEMS driver constants (Tier A) | `execute(payload)` |
| `adapter_librosa.py` | librosa | Spectral/MIR features | `execute(payload)` |
| `adapter_essentia.py` | Essentia | High-end MIR descriptors | `execute(payload)` |
| `adapter_music21.py` | music21 | Symbolic/MusicXML analysis | `execute(payload)` |
| `adapter_pretty_midi.py` | pretty_midi | MIDI/Representation analysis | `execute(payload)` |

**Adapter Workflow:**
1. `execute(payload)` extracts parameters (file_path, etc.)
2. Dispatch to `ToolkitBridge` or external library.
3. `normalize(raw_result)` formats output to Helix schema.
4. Return structured artifact dict.

---

## Atlas Architecture

### Definition
The **Atlas** is a graph of structures expressed across languages and dialects. It functions as the structural memory of Helix, storing entities and invariants in a way that supports:
*   **Cross-Dialect Mapping**: Linking equivalent structures across different representations.
*   **Invariant Detection**: Identifying patterns that persist across multiple dialects and substrates.
*   **Structural Equivalence**: Comparing data independent of its original format.

### Directory Layout

```
atlas/
├── entities/
│   └── registry.json          ← authoritative entity index (primary source of truth)
├── music/
│   ├── composers/             ← one JSON per compiled Composer entity
│   ├── tracks/                ← one JSON per compiled Track entity
│   ├── albums/
│   ├── games/
│   ├── platforms/
│   └── sound_chips/
├── games/
├── language/
├── mathematics/
├── invariants/                ← verified structural invariants (markdown + JSON)
├── signals/                   ← per-track signal extracts
└── system_integrity/          ← timestamped integrity audit logs
```

**`registry.json`** is the authoritative source. Filesystem entity files are compiled projections.

### Compilation Law

No file may be written to `atlas/` except by the Atlas Compiler gate.

```
# CORRECT
RUN operator:COMPILE_ATLAS

# WRONG — direct write (blocked in runtime mode)
with open("atlas/music/composers/foo.json", "w") as f: ...
```

### Compilation Pipeline

```
artifacts/music/<track_id>/control_sequence.json
  ↓
normalize(entity_dict)           # ID pattern, casing, alias resolution
  ↓
SemanticValidator.validate()     # type check, required fields, relationship validity
  ↓
compile_entity()                 # resolve substrate path → atlas/music/composers/
  ↓
atlas_commit()                   # write JSON (ONLY authorized path)
  ↓
registry.json updated
```

### Entity File Format

```json
{
  "id":            "music.composer:jun_senoue",
  "type":          "Composer",
  "name":          "Jun Senoue",
  "label":         "Jun Senoue",
  "description":   "Sonic Team lead guitarist and composer.",
  "metadata": {
    "source":           "vgmdb_ingester",
    "source_stage":     "knowledge_graph_integration",
    "source_artifact":  "track_db",
    "extraction_method": "vgmdb_scraper"
  },
  "external_ids":  {"vgmdb_id": "..."},
  "relationships": [
    {"relation": "MEMBER_OF", "target_id": "music.soundteam:sonic_team", "confidence": 1.0}
  ]
}
```

---

## Music Research System

### Objective

Discover structural properties of a composer's musical identity that persist across hardware eras and platform constraints.

**Target capability example:**
Motoi Sakuraba's early YM2612 work (El Viento, Genesis, 1991) should be analyzable alongside later orchestral work (Dark Souls, PS3, 2011). Atlas must recognize them as the same composer entity while explaining timbral differences as platform constraints — not identity drift.

### Style Vector Design Law

```
Musical cognition features DOMINATE (80% weight in cross-era similarity).
Hardware context is METADATA (20% weight).
Context explains differences. It does not define identity.
```

### ArtistStyleVector Feature Categories

| Category | Features | Identity Role |
|----------|---------|--------------|
| **Melodic** | interval_distribution, leap_frequency, step_frequency, phrase_length_mean/std, melodic_contour_bias, register_preference | Defines identity |
| **Harmonic** | chord_type_distribution, key_distribution, modulation_frequency, chromaticism_index, tonal_centroid_mean | Defines identity |
| **Rhythmic** | note_density_mean/std, tempo_mean/variance, syncopation_score, onset_density_mean | Defines identity |
| **Structural** | track_length_mean, phrase_count_mean, section_transition_freq, loop_length_estimate | Defines identity |
| **Timbral** | spectral_centroid_mean/std, brightness_mean/distribution, mfcc_centroid, dynamic_range_mean | Partially hardware-influenced |
| **Motivic** | motif_repetition_frequency, motif_entropy, common_motifs | Defines identity |
| **Context metadata** | platforms_used, chips_used, era_range | Context only — never overrides musical fingerprint |

### Music Pipeline (operator sequence)

```
RUN operator:INGEST_TRACK track:music.track:<id>
  → adapter_libvgm (VGM/VGZ) | adapter_gme (SPC/NSF/GBS) | adapter_vgmstream (audio)
  → artifacts/music/<track_id>/control_sequence.json

RUN operator:ANALYZE_TRACK track:music.track:<id>
  → adapter_pretty_midi | adapter_music21    (symbolic analysis)
  → adapter_librosa | adapter_essentia       (signal analysis)
  → adapter_nuked_opn2                       (YM2612 brightness, if applicable)
  → artifacts/music/<track_id>/mir_features.json
  → artifacts/music/<track_id>/motif_features.json
  → artifacts/music/<track_id>/collapse_geometry.json

RUN operator:ANALYZE_TRACK composer:music.composer:<slug>
  → compute_style_vector stage (ArtistStyleVector, included in ANALYZE_TRACK pipeline)
  → artifacts/music/<composer_id>/artist_style_vector.json

RUN operator:COMPILE_ATLAS
  → Atlas Compiler gate (normalize → validate → compile → commit)
  → atlas/music/composers/, atlas/music/tracks/, etc.
```

### Cross-Era Reasoning

```python
from substrates.music.style_vector import CrossEraAnalyzer
analyzer = CrossEraAnalyzer()
result = analyzer.compare(
    vector_ym2612,
    vector_orchestral,
    composer_id="music.composer:motoi_sakuraba",
    label_a="YM2612 era (1991)",
    label_b="orchestral era (2011)",
)
# result.relationship:         "SIMILAR_TO"
# result.cognition_similarity: 0.87
# result.hardware_divergence:  0.08
# result.attribution_note:     "Motoi Sakuraba shows highly similar musical cognition..."
```

Atlas relationship types for cross-era:
- `SIMILAR_TO` — cognition similarity ≥ 0.75
- `DIVERGES_FROM` — cognition similarity < 0.40 (hardware era divergence)
- `ATTRIBUTED_TO` — ArtistStyleVector → Composer

### Format Support

| Format | Tier | Adapter | Fallback |
|--------|------|---------|---------|
| VGM/VGZ | B (emulated) | `adapter_libvgm` | Static register parse |
| SPC | B (emulated) | `adapter_gme` | Empty ControlSequence |
| NSF/NSFE | B (emulated) | `adapter_gme` | Empty ControlSequence |
| GBS, HES, KSS, AY, SGC | B (emulated) | `adapter_gme` | Empty ControlSequence |
| GYM | B (emulated) | `adapter_gme` | — |
| FLAC, MP3, OGG, WAV, OPUS | A (rendered) | `adapter_vgmstream` | Amplitude envelope proxy |
| PSF, PSF2, SSF, DSF | A (rendered) | `adapter_vgmstream` | — |
| 2SF, NCSF, USF, GSF | A (rendered) | `adapter_vgmstream` | — |
| MIDI | C (symbolic) | `adapter_pretty_midi`, `adapter_music21` | — |

---

## Active Invariants

| Invariant | Confidence | Domains | Pass Rate | Location |
|-----------|-----------|---------|-----------|---------|
| `decision_compression` | Verified | games, music, language | 86% | `atlas/invariants/decision_compression/` |
| `oscillator_locking` | Verified | games, language, music | 100% | `atlas/invariants/oscillator_sync/` |
| `epistemic_irreversibility` | Candidate | multiple | 82% | `atlas/invariants/epistemic_irreversibility/` |

**Confidence tiers:**
| Threshold | Class |
|-----------|-------|
| ≥ 4 domains + ≥ 90% pass rate | Structural |
| ≥ 3 domains + ≥ 75% pass rate | Verified |
| ≥ 2 domains + ≥ 50% pass rate | Candidate |
| ≥ 1 domain | Exploratory |

---

## CLI Reference

```bash
helix                           # interactive REPL
helix "HSL COMMAND"             # single command
helix script.hil                # execute .hil script file
echo "VERB target" | helix      # piped input
```

### Operator Execution

```
RUN operator:INGEST_TRACK track:music.track:<id>
RUN operator:ANALYZE_TRACK track:music.track:<id>
RUN operator:ANALYZE_TRACK composer:music.composer:<slug>
RUN operator:DISCOVER_INVARIANTS
RUN operator:FALSIFY_INVARIANT invariant:music.invariant:<name>
RUN operator:TOPOLOGY_MAP
RUN operator:MEASURE_KNOWLEDGE_GAIN
RUN operator:QUERY type:Composer namespace:music
RUN operator:COMPILE_ATLAS
RUN operator:UNDEFINED              → HSLValidationError (closed-world)

OPERATOR list
OPERATOR status operator:ANALYZE_TRACK
```

### Entity Management

```
ENTITY add music.composer:<slug> name:"Name" description:"One sentence."
ENTITY get music.composer:jun_senoue
ENTITY list type:Composer namespace:music limit:50
ENTITY list name:senoue
ENTITY link music.composer:jun_senoue relation:COLLABORATED_WITH target:music.composer:...
ENTITY export
```

### Atlas & Compilation

```
ATLAS lookup invariant:games.invariant:decision_compression
ATLAS list
ATLAS verify
COMPILE atlas
```

### Discovery

```
DISCOVER experiments invariant:games.invariant:decision_compression
DISCOVER invariants
DISCOVER execute invariant:games.invariant:decision_compression
```

### Substrate

```
SUBSTRATE list
SUBSTRATE info name:music
SUBSTRATE run name:music stages:1,2,3
SUBSTRATE run name:music stages:1,2,3 limit:100 dry-run:true
```

### Graph

```
GRAPH neighbors music.composer:jun_senoue
GRAPH path music.composer:jun_senoue music.composer:yuzo_koshiro
GRAPH edges music.composer:jun_senoue
```

### Integrity & System

```
INTEGRITY check
SYSTEM sync
```

---

## Governance

### Anti-Drift Rules

1. Never modify `core/hil/`, `core/semantics/`, or `core/normalization/` without updating this README.
2. Every new entity type requires: `SemanticSignature` in `entity_types.py` + entry in `ENTITY_ONTOLOGY`.
3. Every new operator requires: `OperatorSpec` in `builtin_operators.py`.
4. Substrate code must not import from `core/operators/`, `core/semantics/`, or `core/compiler/`.
5. No substrate may write to `atlas/` directly. All Atlas writes through `COMPILE` or `COMPILE_ATLAS`.
6. No new pip dependency without a corresponding adapter in `core/adapters/`.
7. No standalone pipeline scripts. All execution through HSL operators.
8. `INTEGRITY check` must pass clean before any commit to main.

### Promotion Gate (invariants)

```
helix "ATLAS verify"
```

---

## Environment

| Requirement | Value |
|-------------|-------|
| Python | ≥ 3.10 |
| Shell | bash (MSYS2 on Windows, native on Linux/WSL2, git-bash) |
| Required pip | `mutagen pandas numpy beautifulsoup4 networkx librosa music21 pretty_midi faiss-cpu` |
| Optional pip | `essentia scikit-learn umap-learn hdbscan anthropic` |
| External (Repo) | `libvgm vgmstream game-music-emu Nuked-OPN2` (source in `runtime/deps/`) |
| Driver Source | `SMPS`, `GEMS`, `AddmusicK`, `FamiTracker` (in `runtime/deps/helix_sources/`) |

**Core Toolkits:**
- **Libvgm**: VGM emulation and register tracing.
- **GME**: Multi-format game music emulation (SPC, NSF, etc.).
- **Vgmstream**: Non-chip audio decoding and envelope extraction.
- **Nuked-OPN2**: Cycle-accurate YM2612 topology modeling.
- **SMPS/GEMS**: Driver-level reconstruction and patch benchmarking.
- **Librosa/Essentia**: MIR signal analysis.
- **Music21/PrettyMidi**: Symbolic score reconstruction.

```bash
# Setup
python -m venv .venv
source .venv/Scripts/activate      # Windows/MSYS2
source .venv/bin/activate          # Linux/WSL2
pip install -e .
pip install mutagen pandas numpy beautifulsoup4 networkx librosa music21 pretty_midi

# Run
helix                              # REPL
helix "OPERATOR list"              # verify system
helix "INTEGRITY check"            # verify architecture
```

---

## Regeneration Specification

To regenerate a complete Helix instance from scratch, implement in this order:

| Priority | Component | Key Files | Spec Source |
|----------|-----------|-----------|-------------|
| 1 | HSL syntax layer | `core/hil/` | `HSL.md` |
| 2 | Normalization gate | `core/normalization/` | This README, Layer 2 |
| 3 | Semantics layer | `core/semantics/` | This README, Entity Types |
| 4 | Entity schema | `core/kernel/schema/entities/` | This README, Entity Schema |
| 5 | Operator registry | `core/operators/` | This README, Operator Registry |
| 6 | Adapter layer | `core/adapters/` | This README, Adapter Layer |
| 7 | Atlas compiler | `core/compiler/` | This README, Atlas Architecture |
| 8 | Entity graph | `core/kernel/graph/` | SPEC-03 (graph storage) |
| 9 | Music substrate | `substrates/music/` | `substrates/music/README.md` |
| 10 | Style vector | `substrates/music/style_vector/` | This README, Music Research System |
| 11 | Discovery system | `core/discovery/` | This README, DISCOVER operator |
| 12 | Atlas structure | `atlas/` | This README, Atlas Architecture |
| 13 | CLI | `core/cli/`, `helix` | This README, CLI Reference |
| 14 | Integrity | `core/integrity/` | INTEGRITY check section |

---

## Key File Index

| File | Purpose |
|------|---------|
| `helix` | Bash CLI entry point |
| `HSL.md` | HSL language specification |
| `core/hil/grammar.ebnf` | Formal HSL grammar (EBNF) |
| `core/hil/interpreter.py` | HSL execution engine + execution modes |
| `core/hil/command_registry.py` | All 24 HSL command family specs |
| `core/normalization/normalizer.py` | Normalization pipeline |
| `core/normalization/id_enforcer.py` | ID pattern enforcement |
| `core/semantics/entity_registry/entity_types.py` | All 19 semantic signatures |
| `core/semantics/property_registry/property_types.py` | All 50+ property specs |
| `core/semantics/relationship_registry/relationship_types.py` | All 30+ relationship specs |
| `core/semantics/validator.py` | SemanticValidator |
| `core/operators/builtin_operators.py` | All 9 operator specs |
| `core/operators/operator_registry.py` | Singleton registry, require() |
| `core/adapters/__init__.py` | Adapter layer public API |
| `core/compiler/atlas_compiler.py` | Atlas compilation pipeline |
| `core/kernel/schema/entities/schema.py` | Entity dataclass |
| `core/kernel/schema/entities/ontology.py` | ENTITY_ONTOLOGY (19 types) |
| `core/kernel/schema/entities/registry.py` | EntityRegistry |
| `substrates/music/pipeline_core.py` | 18-stage operator-callable pipeline |
| `substrates/music/style_vector/style_vector.py` | ArtistStyleVector computation |
| `substrates/music/style_vector/cross_era.py` | CrossEraAnalyzer |
| `substrates/music/measurement_synthesis/libvgm_bridge.py` | libvgm ctypes bridge |
| `substrates/music/measurement_synthesis/gme_bridge.py` | gme + vgmstream bridge |
| `substrates/music/domain_analysis/tool_bridge.py` | vgm2txt, gems2mid, Nuked-OPN2 |
| `atlas/entities/registry.json` | Authoritative entity index (generated by COMPILE_ATLAS) |


---

## Architecture Guardrail

**Helix Architecture Law**
`HSL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler`

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

**All new modules must follow the template registry located in `runtime/templates/`.**

---

# System Constraints

The following rules are mandatory.

## Atlas Resolution Rule

All queries must resolve through atlas entities after indexing.

## Phase Separation Rule

INDEX must not trigger analysis.
ANALYZE must not modify metadata.

## Partial Entity Rule

Entities may exist with:
analysis_status: pending

## Attribution Integrity Rule

Original metadata must never be overwritten.
Use:

* inferred_attribution
* attribution_history

## Knowledge Gain Scope Rule

Applies only to `ANALYZE_TRACK`, not `INGEST_TRACK`.

## Operator Constraint Rule

Do not add new operators beyond the defined core set.

## Helix Ingestion Contract Rule

All data ingestion MUST be deterministic, structural, and decomposed.

1.  **Source Constraint**: ONLY read from `data/<domain>/source/`.
2.  **6-Stage Pipeline**: Must execute `parsed`, `features`, `structure`, `patterns`, `measurements`, and `atlas_candidates`.
3.  **Entity Decomposition**: Systems MUST be decomposed into reusable entities (operators, topolgoies).
4.  **No True Invariants**: Forbidden to assert invariants; only `invariant_candidates` allowed.
5.  **Measurable Interpretation**: Use quantifiable metrics, not vague descriptors.

---

---

# Unified Musical Object Specification

## §UMO-1 — Musical Object Model

A track or work processed by Helix is not represented as a single file. It is a **Unified Musical Object (UMO)**: a structural entity that may simultaneously have multiple aligned dialect views:

| View | Dialect | What it contains |
|------|---------|-----------------|
| `control_view` | `chip_control` | Register writes, hardware instructions, causal event timeline |
| `symbolic_view` | `symbolic_music` | Pitch sequences, rhythm, harmony, form (MIDI, music21, MusicXML) |
| `perceptual_view` | `perceptual_audio` | Spectral features, MFCCs, chroma, onset/tempo summaries |
| `structural_view` | (cross-dialect) | Motifs, patterns, invariants, form detected across views |

Canonical schema (`core/kernel/schema/umo_schema.json`):

```json
{
  "entity_id": "music.track:<slug>",
  "representations": {
    "causal":     { "operator_topology": {}, "carrier_slots": [], "temporal_trajectories": [] },
    "symbolic":   { "melody": {}, "harmony": {}, "rhythm": {}, "voice_structure": {} },
    "perceptual": { "timbre_descriptors": {}, "spectral_profile": {}, "brightness": 0.0, "roughness": 0.0 },
    "metadata": {
      "recorded":   { "title": "...", "artist": "...", "sound_chip": "..." },
      "normalized": {}
    }
  },
  "alignment_map": [
    {
      "causal": "dual_carriers_ch0",
      "perceptual": "layered_timbre",
      "symbolic": "parallel_voices",
      "temporal_scope": "0.0-4.2s",
      "granularity": "phrase",
      "confidence": 0.87
    }
  ],
  "conflicts": [
    {
      "type": "causal_symbolic_mismatch",
      "temporal_scope": "verse_1",
      "confidence": 0.72,
      "causal": {},
      "symbolic": {}
    }
  ],
  "invariants": [
    {
      "name": "dual_carrier_layering",
      "evidence": {
        "causal":     { "carrier_slots": [0, 1] },
        "perceptual": { "polyphony_estimate": 2.0 }
      },
      "evidence_dialects": ["causal", "perceptual"],
      "confidence": 0.91
    }
  ],
  "identity": {
    "inferred_profile": { "topology_preference": "dual_carrier", "feedback_tendency": "high" },
    "evidence_tracks": []
  }
}
```

All dialect views under `representations` are optional — a UMO may be fully populated, partially populated, or contain a single view. `alignment_map`, `conflicts`, and `invariants` are required arrays (may be empty). Invariants require evidence from ≥2 dialects (`evidence_dialects` enforces this structurally). Helix must never treat a single-view UMO as structurally complete.

## §UMO-2 — Observability Depth

Each format family exposes a different level of structural access. Helix assigns **observability depth** per format:

| Depth | Description | Example formats |
|-------|-------------|-----------------|
| **Causal** | Full register-write timeline; complete generation logic visible | VGM, VGZ, NSF, SPC, S98, GBS, HES, KSS, AY |
| **Symbolic** | Compositional intent (pitch/rhythm/harmony); hardware detail absent | MIDI, MusicXML, ABC notation |
| **Perceptual** | Listener-facing features only; generation logic not recoverable | MP3, WAV, FLAC, OGG, OPUS |
| **Hybrid** | Partial causal + partial perceptual; generation partially reconstructable | PSF/PSF2, 2SF, USF, GSF, DSF/NCSF |

The pipeline records observability depth per artifact. Cross-view alignment is only possible when at least two views are populated.

## §UMO-3 — Perceptual Inference Principle

LLMs do not hear rendered audio. LLMs reason over structured representations derived from sound. Helix provides these representations explicitly:

1. Causal data (register writes) determines sound with hardware precision.
2. Symbolic data (note/chord sequences) encodes compositional intent.
3. Perceptual features (MFCCs, chroma, spectral envelope) summarize audible outcome.

In chip-native formats, causal observability can exceed raw audio in information content: the register timeline is deterministic and explains every audible event. In rendered audio formats, perceptual features capture expression, performance nuance, mixing, and timbral realizations that symbolic/causal representations cannot reconstruct.

Neither representation is universally superior. Helix must maintain all available views and make their differences explicit.

## §UMO-4 — Composer Identity Principle

Helix is not classifying formats or chips. The primary structural target is **compositional identity** — the persistent fingerprint of a composer that survives translation, platform shifts, and hardware constraints.

A composer fingerprint is defined by:
- Structural habits (harmonic motion, interval preferences, rhythmic tendencies)
- Decision patterns (compression under hardware constraint)
- Motif behavior (recurring melodic/rhythmic fragments)
- Control idioms (timbral choices, envelope shaping, driver-level techniques)

This identity is **representation-invariant**. It must be discoverable whether the source is:
- A VGM register dump (Genesis, Master System)
- An SPC file (SNES)
- A MIDI or MusicXML score
- A rendered FLAC or MP3 recording

Attribution inference is always a falsifiable hypothesis. Helix separates recorded credit from structurally inferred attribution.

## §UMO-5 — Translation, Not Conversion

All pipeline operations are framed as **translation between dialects**, not format conversion. Translation may be:
- **Lossless**: When full causal information is preserved (e.g., VGM → register event list)
- **Lossy downward**: When moving to a lower observability depth (e.g., symbolic → perceptual feature)
- **Lossy upward** (inference): When moving to a higher depth requires reconstruction (e.g., MIDI → estimated register writes)

Loss must be explicit in artifact metadata. Helix never implies a translation is lossless unless it is verified to be.

## §UMO-6 — Partial Observability and Graceful Degradation

Helix is not dependent on chip-level data. It supports analysis of any musical work regardless of available representation.

### Representation Availability Cases

| Case | Available Dialects | System Behavior |
|------|--------------------|-----------------|
| Full stack | chip_control + symbolic_music + perceptual_audio | All pipeline stages active; full UMO populated |
| Partial stack | symbolic_music + perceptual_audio | Control-layer stages skipped; symbolic + perceptual stages active |
| Minimal stack | perceptual_audio only | Symbolic inference attempted; perceptual features always extracted |
| Symbolic only | symbolic_music only | Perceptual estimation attempted; control-layer skipped |

Missing dialects must not block analysis. Every case must produce a valid, atlas-compatible UMO with the available views populated and missing views marked as absent (not errored).

### Dialect Field Optionality

The UMO schema treats all dialect views as optional fields:
- `control_view`: present if and only if a causal format (VGM, NSF, SPC, etc.) is available
- `symbolic_view`: present if directly available (MIDI, MusicXML) or successfully inferred
- `perceptual_view`: present whenever any audio or renderable source is available
- `structural_view`: derived from any combination of available views

Inferred views (e.g., pitch/chord structure estimated from audio via MIR) must be flagged with `"inferred": true` and `"confidence": <float>` in artifact metadata. They are hypotheses, not measurements.

### Invariant Independence from Dialect

Invariant definitions must not depend on any single dialect. The composer fingerprint invariant must be:
- Computable from perceptual_audio alone (minimal baseline)
- Enriched, not replaced, when additional dialects are available
- Structurally consistent across all stack levels

A modern band representable only through audio recordings must exist in the same atlas structural space as a chip composer with full register-write access. Their fingerprints are measured with different precision, but they occupy the same invariant space and their structural similarity is computable.

### Atlas Uniformity Requirement

All entities in the atlas — regardless of data richness — must be represented with a uniform schema. This requires:
- All entity types support optional dialect view fields
- Relationship types (SIMILAR_TO, SHARES_MOTIF, DIVERGES_FROM) must be computable from minimum available features
- Missing dialect information must be recorded as absent, not as zero or default

Helix does not require perfect information to model structure. It operates under partial observability and reconstructs invariants from whatever representations are available.

---

## LLM Governance Contract

Helix is a **closed structural system**. All large language models (LLMs) interacting with Helix are **execution agents**, not architects. LLMs must operate strictly within the Helix Structural Language (HSL) and repository specifications. They are not permitted to reinterpret, extend, or redefine the system.

### 1. Authority Hierarchy

The source of truth in Helix is:

1. HSL (Helix Structural Language)
2. SPEC (machine-enforceable architecture)
3. Substrate specifications
4. Repository structure

LLM outputs are **never authoritative**. They must conform to the above hierarchy.

### 2. Prohibited Actions

LLMs must NOT:

- Rename core concepts (HSL, Substrate, Dialect, Atlas, Translation)
- Introduce new architectural layers or abstractions
- Merge distinct layers (structure, execution, data)
- Reinterpret substrate boundaries
- Invent alternative pipelines or workflows
- Modify naming conventions without explicit instruction
- Replace deterministic structure with heuristic descriptions

Any of the above constitutes **architectural drift**.

### 3. Required Behavior

LLMs must:

- Treat substrates as **languages**
- Treat dialects as **equivalent structural representations**
- Treat all processing as **translation between dialects**
- Preserve strict separation:
  - `data/` (storage)
  - `execution/` (runtime)
  - system code (structure)

If ambiguity exists: → preserve structure rather than invent new interpretation

### 4. Structural Validation Requirement

All LLM outputs must internally satisfy:

- HSL hierarchy is preserved
- No new abstractions are introduced
- Translation pathways remain explicit
- Data is not embedded into structural layers
- Outputs remain reconstructable

If any condition is violated: → output must be corrected before completion

### 5. Multi-Model Consistency

Different LLMs may produce different outputs. Helix treats LLM disagreement as a **signal**, not authority.

- Agreement across models increases confidence
- Disagreement requires inspection
- No single model defines truth

Structural correctness is determined by alignment with HSL and SPEC, not by model output.

### 6. Role of LLMs in Helix

LLMs function as:

- Executors of defined transformations
- Translators between representations
- Assistants for structural reasoning

LLMs are NOT:

- System designers
- Architectural authorities
- Sources of truth

### 7. Architectural Drift Definition

Architectural drift occurs when:

- System structure changes without specification updates
- Concepts are renamed or merged implicitly
- Data and structure boundaries are violated
- New abstractions appear without formal definition

All drift must be corrected immediately.

### 8. Enforcement Philosophy

Helix prioritizes:

> structural integrity over convenience

Correct structure must be preserved even if it requires:

- rejecting LLM output
- re-running tasks
- manual correction

No output is accepted if it violates system architecture.

---

*This contract applies to all current and future LLM interactions with Helix.*
