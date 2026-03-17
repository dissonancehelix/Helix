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

The only execution units in runtime mode. Operators are deterministic: fixed pipeline stages, declared input types, declared output schema.

| Component | Location | Purpose |
|-----------|----------|---------|
| Spec | `core/operators/operator_spec.py` | `OperatorSpec` dataclass |
| Registry | `core/operators/operator_registry.py` | Singleton, closed-world enforcement |
| Built-ins | `core/operators/builtin_operators.py` | 12 pre-registered operators |

No operator generates scripts at runtime. No operator writes to Atlas directly.

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
├── README.md                      ← This file — system specification
├── HIL.md                         ← HIL language specification
├── DISSONANCE.md                  ← Operator profile
├── pyproject.toml                 ← Python package definition
│
├── core/                          ← Execution infrastructure
│   ├── hil/                       ← HIL: parser, validator, interpreter
│   ├── normalization/             ← Normalization gate
│   ├── semantics/                 ← Semantic type/property/relationship registries
│   ├── operators/                 ← Operator registry and 12 built-ins
│   ├── adapters/                  ← Toolkit translation layers (8 adapters)
│   ├── compiler/                  ← Atlas compiler (sole authorized Atlas writer)
│   ├── kernel/
│   │   ├── schema/entities/       ← Entity dataclass, ontology, registry, resolver
│   │   ├── graph/                 ← EntityGraph, AtlasGraph, traversal
│   │   ├── dispatcher/            ← Probe runner, probe registry
│   │   └── runtime/orchestration/ ← master_pipeline.py (internal shim)
│   ├── discovery/                 ← Hypothesis engine, experiment generator
│   ├── integrity/                 ← Architecture integrity checks
│   ├── analysis/                  ← Feature extraction, pattern stores
│   ├── engines/                   ← Python and Godot runtime engines
│   └── cli/                       ← helix_cli.py, command_runner.py, repl.py
│
├── substrates/                    ← Domain analysis pipelines
│   ├── music/                     ← Game music / VGM / composer style
│   │   ├── pipeline_core.py       ← 18-stage operator-callable pipeline
│   │   ├── style_vector/          ← StyleVectorComputer, CrossEraAnalyzer
│   │   ├── measurement_synthesis/ ← libvgm_bridge, gme_bridge, build_extensions
│   │   ├── domain_analysis/       ← composer fingerprint, symbolic, MIR, theory
│   │   ├── feature_extraction/    ← feature extractor, channel profiler
│   │   ├── embedding_generation/  ← style embedding, signal generator
│   │   ├── pattern_detection/     ← FAISS index, similarity, attribution
│   │   ├── atlas_integration/     ← entity builder, graph integration, sources
│   │   ├── ingestion/             ← library scanner, metadata, adapters
│   │   └── parsing/               ← VGM, SPC, NSF, SID parsers
│   ├── games/                     ← Agent decision system analysis
│   ├── language/                  ← Symbolic communication analysis
│   ├── math/                      ← Formal structure and topology
│   └── agents/                    ← Multi-agent simulation
│
├── atlas/                         ← Compiled semantic knowledge
│   ├── entities/
│   │   └── registry.json          ← Authoritative entity index (98,313+ entities)
│   ├── music/
│   │   ├── composers/
│   │   ├── tracks/
│   │   ├── albums/
│   │   ├── games/
│   │   ├── platforms/
│   │   └── sound_chips/
│   ├── games/
│   ├── language/
│   ├── mathematics/
│   ├── invariants/                ← Verified structural invariants
│   ├── signals/                   ← Processed measurable signals
│   └── system_integrity/          ← Integrity audit logs
│
├── artifacts/                     ← Intermediate pipeline outputs
│   ├── music/
│   │   └── <track_id>/
│   │       ├── control_sequence.json
│   │       ├── symbolic_score.json
│   │       └── signal_profile.json
│   └── tests/                     ← Test data (not Atlas entities)
│
├── labs/
│   ├── experiments/               ← Active probes and experiments
│   └── legacy_experiments/        ← Archived scripts (see AUDIT.md)
│
├── datasets/                      ← Raw input data
├── governance/                    ← Validation and promotion rules
├── applications/                  ← Tools built on Helix invariants
└── runtime/
    └── deps/                      ← Cloned external tool source repos
        ├── libvgm/
        ├── vgmstream/
        ├── Nuked-OPN2/
        ├── game-music-emu/
        └── helix_sources/         ← Sound driver reference collection
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
|------|---------|----------------------|----------------------|
| `ControlSequence` | Hardware register-write log | `source_track`, `chip_target`, `format` | DERIVED_FROM, TARGETS_CHIP |
| `SymbolicScore` | Music theory representation | `source_track` | DERIVED_FROM, REPRESENTS |
| `SignalProfile` | Audio feature representation | `source_track` | DERIVED_FROM, REPRESENTS |
| `ArtistStyleVector` | Composer musical fingerprint | `composer_id`, `melodic_features`, `harmonic_features`, `rhythmic_features` | ATTRIBUTED_TO, SIMILAR_TO, DIVERGES_FROM, DERIVED_FROM |

**Reserved (planned substrates):**

| Type | Purpose |
|------|---------|
| `Soundtrack` | Game soundtrack collection |
| `Studio` | Development studio |

**Research domain:**

| Type | Purpose | Required Extra Fields |
|------|---------|----------------------|
| `Dataset` | Input data collection | `source`, `version` |
| `Experiment` | Falsification test | `source` |
| `Model` | Explanatory structure | — |
| `Invariant` | Cross-domain structural rule | `source` |
| `Operator` | Execution unit | `version` |
| `Driver` | Substrate driver | — |
| `Infrasubstrate` | Infrastructure layer | — |

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

`core/adapters/` — Pure translation layers. No Helix logic. Each adapter normalizes inputs, calls one external toolkit, and returns a structured JSON-compatible dict.

| Adapter | Toolkit | Purpose | Available |
|---------|---------|---------|-----------|
| `adapter_libvgm.py` | libvgm (ValleyBell) | VGM/VGZ emulation, YM2612/SN76489/OPL chip events | Source in `runtime/deps/libvgm/`; compile required |
| `adapter_gme.py` | Game_Music_Emu | SPC (SPC700), NSF (2A03), GBS (DMG), HES, KSS, AY | Source in `runtime/deps/game-music-emu/`; compile required |
| `adapter_vgmstream.py` | vgmstream CLI | FLAC, MP3, OGG, WAV, OPUS, PSF, 2SF, USF → amplitude envelope | Source in `runtime/deps/vgmstream/`; compile required |
| `adapter_nuked_opn2.py` | Nuked-OPN2 | YM2612 algorithm → carrier slot tables, brightness proxy | Always available (static constants, no compilation) |
| `adapter_librosa.py` | librosa | Spectral, rhythm, timbral MIR features from audio | pip installed |
| `adapter_essentia.py` | Essentia | High-quality descriptors: tonal centroid, chord histogram, HPCP | `pip install essentia` (optional) |
| `adapter_music21.py` | music21 | MIDI/MusicXML: key, chord progression, phrase segmentation | pip installed |
| `adapter_pretty_midi.py` | pretty_midi | MIDI: note events, pitch histogram, velocity, note density | pip installed |

**Adapter output schemas:**
- `adapter_libvgm`, `adapter_gme`, `adapter_vgmstream` → ControlSequence schema
- `adapter_librosa`, `adapter_essentia` → SignalProfile schema
- `adapter_music21`, `adapter_pretty_midi` → SymbolicScore schema
- `adapter_nuked_opn2` → topology dict `{algorithm, carrier_slots, modulator_slots, brightness_proxy}`

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
| Shell | bash (MSYS2 on Windows, native on Linux/WSL2) |
| Required pip | `mutagen pandas numpy beautifulsoup4 networkx librosa music21 pretty_midi` |
| Optional pip | `essentia faiss-cpu scikit-learn umap-learn hdbscan anthropic` |
| External (compile) | `libvgm vgmstream game-music-emu` (source in `runtime/deps/`) |

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
