# Helix

**Closed semantic execution system for experimental invariant discovery.**

Helix is a constrained, deterministic research machine. It discovers structural invariants across complex systems by running experiments through a formal five-layer execution pipeline. Every input is normalized, every entity is semantically validated, every action is performed by a registered operator, and every piece of knowledge is compiled into a structured Atlas before it can be reasoned about.

This document is the authoritative system specification. A complete Helix instance can be regenerated from this file, `HIL.md`, and the substrate READMEs.

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
HIL → Normalization → Semantics → Operators → Atlas Compiler → Atlas
```

Substrates produce artifacts. The Atlas Compiler converts artifacts into Atlas entities. Nothing else writes to Atlas.

---

## Execution Pipeline

### Layer 1 — HIL (Syntax)

The Helix Interface Language. A strict formal DSL. The only valid way to express intent in Helix. See `HIL.md` for the complete language specification.

| Component | Location | Purpose |
|-----------|----------|---------|
| Grammar (EBNF) | `core/hil/grammar.ebnf` | Authoritative syntax definition |
| Parser | `core/hil/parser.py` | Tokenizer → typed AST |
| Validator | `core/hil/validator.py` | 10-stage semantic validation |
| Interpreter | `core/hil/interpreter.py` | Command execution dispatcher |
| Dispatcher | `core/hil/hil_dispatch.py` | Routes to interpreter or kernel |
| Normalizer | `core/hil/normalizer.py` | Shim → `core/normalization/` |
| Aliases | `core/hil/aliases.py` | Human shorthand → canonical HIL |
| Command registry | `core/hil/command_registry.py` | Formal spec of all 24 command families |
| AST nodes | `core/hil/ast_nodes.py` | `HILCommand`, `TypedRef`, `RangeExpr` |
| Errors | `core/hil/errors.py` | 6 typed error classes |
| Semantic roles | `core/hil/semantic_roles.py` | 11 relationship role types |
| Ontology | `core/hil/ontology.py` | 24 HIL object types, valid engines |

Non-HIL input is rejected. There is no fallback to Python or shell in runtime mode.

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
4. **Style Vector Weighting**: `STYLE_VECTOR` (via `ANALYZE_TRACK`) weights contributions: `effective_weight = confidence * attribution_weight`. Weights: `solo` (1.0), `inferred` (0.5–1.0), `multi` (0.25).
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
├── HIL.md                         ← HIL language specification
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

12 registered operators. `RUN operator:UNKNOWN` raises `HILValidationError` in all modes.

### Music Substrate Operators

| Operator | Accepted Input Types | Output Schema | Pipeline Stages |
|----------|---------------------|---------------|----------------|
| `INGEST_TRACK` | Track, * | `{track_id, control_sequence, artifact_path, bridge_used, bridge_mode}` | validate_source → route_to_adapter → render_control_sequence → write_artifact |
| `ANALYZE_TRACK` | Track, ControlSequence | `{track_id, symbolic_score, signal_profile, artifact_paths}` | load_control_sequence → symbolic_analysis → signal_analysis → nuked_opn2_topology → write_artifacts |
| `STYLE_VECTOR` | Composer | `{composer_id, artist_style_vector, track_count, artifact_path}` | load_composer_tracks → compute_melodic → compute_harmonic → compute_rhythmic → compute_structural → compute_timbral → compute_motivic → aggregate_context → write |
| `COMPILE_ATLAS` | Track, Composer, ControlSequence, SymbolicScore, SignalProfile, ArtistStyleVector, * | `{entities_compiled, entities_rejected, atlas_paths, substrate}` | discover_music_artifacts → normalize → semantic_validate → compile_to_substrate_dir → atlas_commit → update_registry |

### Core Operators

| Operator | Accepted Input Types | Output Schema | Pipeline Stages |
|----------|---------------------|---------------|----------------|
| `PROBE` | Invariant | `{probe_name, domain, signal, confidence, passed, run_id, artifact_dir}` | load_dataset → execute_probe → collect_signal → write_artifact → update_atlas |
| `INGEST` | * | `{entities_created, entities_updated, artifact_path}` | validate_source → parse_records → normalize_entities → write_artifacts |
| `LINK` | all entity types | `{source_id, relation, target_id, created}` | validate_source → validate_target → check_relationship_type → write_relationship |
| `COMPILE` | * | `{entities_compiled, entities_rejected, atlas_paths}` | discover_artifacts → normalize → semantic_validate → compile_entries → atlas_commit → update_index |
| `SCAN` | * | `{substrate, entities_found, artifact_path}` | enumerate_substrate → extract_entities → write_artifacts |
| `ANALYZE` | Composer, Track, Game, Invariant, Experiment | `{signals, artifact_path}` | load_entity → extract_features → compute_signals → write_artifact |
| `DISCOVER` | Invariant | `{candidate_commands, reasoning, log_path}` | load_atlas → analyze_gaps → generate_hil_candidates → log_session |
| `MIGRATE` | * | `{entities_migrated, entities_failed, migration_log}` | detect_legacy → convert_to_canonical → compile_entity → mark_migration_metadata |

---

## Adapter Layer

`core/adapters/` — Pure translation layers. No Helix logic. Every adapter strictly follows the `Adapter` template, providing a unified `execute(payload)` entry point and a `normalize(result)` stage.

Adapters are registered by their original names (e.g., `LibvgmAdapter`) but implement the standardized `Adapter` interface.

| Adapter | Toolkit | Purpose | Interface |
|---------|---------|---------|-----------|
| `adapter_libvgm.py` | libvgm (ValleyBell) | VGM/VGZ emulation | `execute(payload)` |
| `adapter_gme.py` | Game_Music_Emu | SPC, NSF, GBS, HES, KSS, AY | `execute(payload)` |
| `adapter_vgmstream.py` | vgmstream CLI | Audio decoding & envelope | `execute(payload)` |
| `adapter_nuked_opn2.py` | Nuked-OPN2 | FM Topology analysis | `execute(payload)` |
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
RUN operator:COMPILE

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
  → artifacts/music/<track_id>/symbolic_score.json
  → artifacts/music/<track_id>/signal_profile.json

RUN operator:STYLE_VECTOR composer:music.composer:<slug>
  → StyleVectorComputer (substrates/music/style_vector/style_vector.py)
  → 6 cognition feature computations + context metadata aggregation
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
helix "HIL COMMAND"             # single command
helix script.hil                # execute .hil script file
echo "VERB target" | helix      # piped input
```

### Operator Execution

```
RUN operator:PROBE invariant:games.invariant:decision_compression [lab:games]
RUN operator:INGEST_TRACK track:music.track:<id>
RUN operator:ANALYZE_TRACK track:music.track:<id>
RUN operator:STYLE_VECTOR composer:music.composer:<slug>
RUN operator:COMPILE_ATLAS
RUN operator:SCAN substrate:music
RUN operator:UNDEFINED              → HILValidationError (closed-world)

OPERATOR list
OPERATOR status operator:PROBE
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
7. No standalone pipeline scripts. All execution through HIL operators.
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
| 1 | HIL syntax layer | `core/hil/` | `HIL.md` |
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
| `HIL.md` | HIL language specification |
| `core/hil/grammar.ebnf` | Formal HIL grammar (EBNF) |
| `core/hil/interpreter.py` | HIL execution engine + execution modes |
| `core/hil/command_registry.py` | All 24 HIL command family specs |
| `core/normalization/normalizer.py` | Normalization pipeline |
| `core/normalization/id_enforcer.py` | ID pattern enforcement |
| `core/semantics/entity_registry/entity_types.py` | All 19 semantic signatures |
| `core/semantics/property_registry/property_types.py` | All 50+ property specs |
| `core/semantics/relationship_registry/relationship_types.py` | All 30+ relationship specs |
| `core/semantics/validator.py` | SemanticValidator |
| `core/operators/builtin_operators.py` | All 12 operator specs |
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
| `atlas/entities/registry.json` | Authoritative entity index |
| `artifacts/music_audit_report.md` | Music subsystem audit (2026-03-17) |
| `labs/legacy_experiments/AUDIT.md` | Legacy script classification |


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

Applies only to ANALYZE, not INGEST.

## Operator Constraint Rule

Do not add new operators beyond the defined core set.

## Helix Ingestion Contract Rule

All data ingestion MUST be deterministic, structural, and decomposed.

1.  **Source Constraint**: ONLY read from `data/<domain>/source/`.
2.  **6-Stage Pipeline**: Must execute `parsed`, `features`, `structure`, `patterns`, `measurements`, and `atlas_candidates`.
3.  **Entity Decomposition**: Systems MUST be decomposed into reusable entities (operators, topolgoies).
4.  **No True Invariants**: Forbidden to assert invariants; only `invariant_candidates` allowed.
5.  **Measurable Interpretation**: Use quantifiable metrics, not vague descriptors.
