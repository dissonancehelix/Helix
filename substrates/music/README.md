# HELIX MUSIC SUBSTRATE SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal substrate specification
**Authority:** This document is the implementation contract for the Helix Music Substrate.
**Purpose:** Enable reconstruction of the Music Substrate without architectural invention. If code conflicts with this document, this document takes precedence until intentionally revised.

---

## 0. WHY THIS DOCUMENT EXISTS

This document is not a casual README.

It is the formal design specification for the Helix Music Substrate.

Its purpose:
- An LLM can rebuild the substrate without inventing architecture
- Existing scripts are not duplicated under new names
- Responsibilities are not placed into the wrong module
- Future planned components follow the same structural DNA
- Helix remains what it is, not a pile of unrelated music scripts

Redundancy in this document is intentional. Explicit beats implicit.

---

## 1. SUBSTRATE IDENTITY

### 1.1 What the Music Substrate is

The Music Substrate is the Helix environment responsible for transforming music libraries into structured computational datasets.

It analyzes music as a layered structural system spanning:
- synthesis mechanisms (chip register events, FM operator graphs)
- audio perception (signal features, spectral analysis)
- symbolic composition (notes, harmony, phrases, motifs)
- metadata identity (composer, platform, game, era)
- graph relationships (composer → track → game → platform → chip)

It converts music artifacts into:

```
raw files
→ decoded representations (chip events / rendered waveforms)
→ feature layers (MIR / symbolic / synthesis)
→ fused style vectors (per-track and per-composer)
→ embeddings and clusters
→ Atlas entities (via compiler only)
```

The Music Substrate is a translation and extraction layer. It converts music into structured data that Helix can reason over.

### 1.2 What the Music Substrate is not

The Music Substrate is not:
- a DAW or audio player
- a generic music streaming app
- an all-purpose tag editor
- a pure MIR-only toolkit
- a pure symbolic musicology toolkit
- a pure VGM utility pack
- a dumping ground for unrelated game-audio experiments

It exists to convert music into structured, comparable Helix representations. Not to "do anything music-related."

### 1.3 Core identity statement

The Music Substrate studies both:
- how sound is generated (causal synthesis)
- how sound is perceived (perceptual signal analysis)

And links both to:
- compositional structure (symbolic analysis)
- metadata identity (who, what, when, where)
- graph-level knowledge (entity relationships)

Any implementation that loses one of these layers is incomplete.

---

## 2. CLOSED SYSTEM LAW

The Music Substrate operates under Helix's Closed System Law.

**Substrates never write to Atlas directly.**

The substrate produces artifacts. The Atlas Compiler converts artifacts into Atlas entities.

**No substrate module may call `atlas_commit()` directly.**

The only Atlas write path is:

```
RUN operator:COMPILE_ATLAS
    → AtlasCompiler.compile_all()
    → normalize → semantic_validate → compile_entity → atlas_commit
```

### 2.1 Operator-only execution

The substrate's pipeline stages are invoked by operators, not by direct script execution.

- `INGEST_TRACK` → routes to `pipeline_core.py` stages
- `ANALYZE_TRACK` → routes to `pipeline_core.py` stages
- `STYLE_VECTOR` → routes to `substrates/music/style_vector/style_vector.py`
- `COMPILE_ATLAS` → routes to `core/compiler/atlas_compiler.py`

Scripts in `substrates/music/` must not be invoked directly in runtime mode.

### 2.2 Artifact pipeline

All substrate outputs are written to:

```
artifacts/music/<track_id>/
```

Never to `atlas/`. Artifacts accumulate. The Atlas Compiler batch-processes them.

---

## 3. HELIX LAYER POSITION

```
HIL
→ Normalization
→ Semantics
→ Operator Runtime
→ Atlas Compiler
→ Atlas

               Operators
                  │
                  ▼
           pipeline_core.py          ← substrates/music/pipeline_core.py
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
   Adapters    Substrate   Style
  core/adapters/  modules  Vector
        │         │         │
        └─────────┼─────────┘
                  ▼
            artifacts/music/
                  │
                  ▼
         Atlas Compiler (COMPILE_ATLAS)
                  │
                  ▼
              atlas/music/
```

### 3.1 Substrate responsibility

The Music Substrate is responsible for:
- file ingestion and format routing
- metadata normalization
- chip/event parsing
- waveform decoding and analysis
- symbolic reconstruction
- musicological feature extraction
- style vector computation
- artifact generation
- providing data to the Atlas Compiler

### 3.2 Music Lab responsibility

Music Lab (`labs/music_lab/`) is responsible for higher-level exploration:
- clustering experiments
- comparative style-space studies
- composer attribution experiments
- longitudinal corpus experiments
- research notebooks and scripts
- visualization experiments
- anything exploratory or replaceable

### 3.3 Boundary rule

If a component is required for deterministic ingestion and canonical artifact production → substrate.

If a component is exploratory, comparative, or replaceable without affecting canonical artifacts → Music Lab.

---

## 4. OPERATOR ARCHITECTURE

### 4.1 Music operators

Four operators are registered for the Music Substrate:

#### INGEST_TRACK

Ingests a music file and produces a ControlSequence artifact.

```
RUN operator:INGEST_TRACK track:music.track:<id>
```

**Pipeline stages:**
1. `validate_source` — confirm file exists, detect format
2. `route_to_adapter` — select appropriate adapter (libvgm / gme / vgmstream / fallback)
3. `render_control_sequence` — parse chip events or decode audio
4. `write_artifact` — write ControlSequence JSON to `artifacts/music/<track_id>/control_sequence.json`

**Accepted input types:** Track, SourcePath, FileHash

**Output:** ControlSequence artifact

#### ANALYZE_TRACK

Runs full analysis on an ingested track: symbolic, signal, and synthesis topology.

```
RUN operator:ANALYZE_TRACK track:music.track:<id>
```

**Pipeline stages:**
1. `load_control_sequence` — read ControlSequence artifact
2. `symbolic_analysis` — extract notes, harmony, motifs via music21/pretty_midi adapter
3. `signal_analysis` — extract MIR features via librosa/essentia adapter
4. `nuked_opn2_topology` — extract YM2612 operator topology if chip present
5. `write_symbolic_artifact` — write SymbolicScore JSON
6. `write_signal_artifact` — write SignalProfile JSON

**Accepted input types:** Track, ControlSequence

**Output:** SymbolicScore artifact + SignalProfile artifact

#### STYLE_VECTOR

Computes an ArtistStyleVector for a composer by aggregating across all their tracks.

```
RUN operator:STYLE_VECTOR composer:music.composer:<slug>
```

**Pipeline stages:**
1. `load_composer_tracks` — find all tracks attributed to composer
2. `compute_melodic` — interval distributions, leap frequency, melodic contour
3. `compute_harmonic` — chord type distribution, modulation frequency, chromaticism
4. `compute_rhythmic` — note density, tempo, syncopation
5. `compute_structural` — track length, phrase count, section transitions
6. `compute_timbral` — spectral centroid, brightness, dynamic range
7. `compute_motivic` — motif trigrams, motif entropy, repetition frequency
8. `aggregate_context_metadata` — platforms, chips, era range (hardware context, not identity)
9. `write_style_vector_artifact` — write ArtistStyleVector JSON

**Accepted input types:** Composer

**Output:** ArtistStyleVector artifact

#### COMPILE_ATLAS

Compiles all music artifacts into Atlas entities via the compiler pipeline.

```
RUN operator:COMPILE_ATLAS
```

**Pipeline stages:**
1. `discover_music_artifacts` — find all JSON artifacts in `artifacts/music/`
2. `normalize` — run normalization gate
3. `semantic_validate` — validate against SemanticSignature
4. `compile_to_substrate_dir` — route to `atlas/music/{type_plural}/`
5. `atlas_commit` — write entity JSON
6. `update_registry` — update `atlas/entities/registry.json`

**Only this operator may write to `atlas/`.**

---

## 5. ADAPTER LAYER

The adapter layer (`core/adapters/`) provides pure translation between external toolkits and Helix data structures.

Adapters:
- contain no Helix logic
- return graceful `available=False` if the toolkit is missing
- never raise unhandled exceptions
- always return typed dicts matching Helix artifact schemas

### 5.1 Adapter inventory

| Adapter | Toolkit | Output Type | Tier |
|---------|---------|-------------|------|
| `adapter_libvgm.py` | libvgm C library | ControlSequence | B |
| `adapter_gme.py` | game-music-emu | ControlSequence | B |
| `adapter_vgmstream.py` | vgmstream C library | ControlSequence | B |
| `adapter_nuked_opn2.py` | Static YM2612 constants | Topology dict | A |
| `adapter_librosa.py` | librosa | SignalProfile | D |
| `adapter_essentia.py` | essentia | SignalProfile extension | D |
| `adapter_music21.py` | music21 | SymbolicScore | C |
| `adapter_pretty_midi.py` | pretty_midi | SymbolicScore | C |

### 5.2 Format tiers

| Tier | Description | Requires |
|------|-------------|----------|
| A | Static parse, pure Python, always available | Nothing |
| B | Emulated chip rendering, compiled C libraries | libvgm / gme / vgmstream compiled |
| C | Symbolic / MIDI analysis | music21, pretty_midi |
| D | MIR / advanced signal analysis | librosa, essentia |

The substrate operates at the highest available tier. If Tier B libraries are not compiled, the system falls back to Tier A (static parse). It does not fail.

### 5.3 Adapter location

```
core/adapters/
├── __init__.py
├── adapter_libvgm.py
├── adapter_gme.py
├── adapter_vgmstream.py
├── adapter_nuked_opn2.py
├── adapter_librosa.py
├── adapter_essentia.py
├── adapter_music21.py
└── adapter_pretty_midi.py
```

---

## 6. PIPELINE CORE

**File:** `substrates/music/pipeline_core.py`

`PipelineCore` is the operator-callable substrate orchestrator. Operators invoke it instead of calling substrate modules directly.

### 6.1 Interface

```python
class PipelineCore:
    def run_stages(self, stage_nums: list[int], context: dict) -> dict:
        """Execute numbered pipeline stages, return aggregated results."""

    def write_track_artifact(self, track_id: str, artifact_name: str, data: dict) -> Path:
        """Write artifact to artifacts/music/<track_id>/<artifact_name>.json"""

    def read_track_artifact(self, track_id: str, artifact_name: str) -> dict:
        """Read artifact from artifacts/music/<track_id>/<artifact_name>.json"""

    def list_track_artifacts(self, track_id: str) -> list[str]:
        """List all artifacts for a track."""
```

### 6.2 Stage map

| Stage | Function | Module |
|-------|----------|--------|
| 1 | Library scan and index | `music_ingestion` |
| 2 | Chip register parsing | `vgm_parser` |
| 3 | Synthesis architecture analysis | `synthesis_analysis` |
| 4 | Symbolic music extraction | `symbolic_extraction` |
| 5 | Computational musicology | `musicology` |
| 6 | MIR audio analysis | `mir_analysis` |
| 7 | Feature synthesis | `feature_fusion` |
| 8 | Style-space embedding | `style_embedding` |
| 9 | Knowledge graph prep | `knowledge_engine` |
| 10 | LLM interpretation | `interpretation` |

### 6.3 master_pipeline.py status

`core/kernel/runtime/orchestration/master_pipeline.py` is now a legacy shim.

It must not be invoked directly. Operators call `pipeline_core.py` stages.

---

## 7. MUSIC ENTITY TYPES

### 7.1 Core music entities

These entities live in `atlas/music/`:

| Entity Type | ID Format | Description |
|-------------|-----------|-------------|
| `Composer` | `music.composer:<slug>` | Composer identity |
| `Track` | `music.track:<slug>` | Individual musical work |
| `Album` | `music.album:<slug>` | Collection of tracks |
| `Game` | `music.game:<slug>` | Video game |
| `Platform` | `music.platform:<slug>` | Hardware platform |
| `SoundChip` | `music.sound_chip:<slug>` | Audio synthesis chip |
| `SoundTeam` | `music.sound_team:<slug>` | Composer group / studio |

### 7.2 Music analysis entities

Produced by operators, compiled to Atlas:

| Entity Type | ID Format | Description |
|-------------|-----------|-------------|
| `ControlSequence` | `music.control_seq:<slug>` | Chip register event sequence derived from chip-native format |
| `SymbolicScore` | `music.symbolic:<slug>` | Notes, harmony, phrases derived from symbolic formats |
| `SignalProfile` | `music.signal:<slug>` | MIR features derived from rendered audio |
| `ArtistStyleVector` | `music.style_vec:<slug>` | Composer fingerprint aggregated across works |

### 7.3 Entity relationships

```
Composer → COMPOSED → Track
Track → APPEARS_IN → Game
Game → RUNS_ON → Platform
Track → USES_CHIP → SoundChip
Track → PERFORMED_BY → SoundTeam
ControlSequence → DERIVED_FROM → Track
ControlSequence → TARGETS_CHIP → SoundChip
SymbolicScore → DERIVED_FROM → Track
SignalProfile → DERIVED_FROM → Track
ArtistStyleVector → ATTRIBUTED_TO → Composer
ArtistStyleVector → SIMILAR_TO → ArtistStyleVector
ArtistStyleVector → DIVERGES_FROM → ArtistStyleVector
```

---

## 8. STYLE VECTOR SYSTEM

### 8.1 Design law

**Musical cognition features identify the composer. Hardware context is metadata only.**

This is a binding design rule. A composer's style must be recognizable across hardware eras.

Motoi Sakuraba on YM2612 (1991) must be recognizable as the same composer on orchestral PSO2 instrumentation (2012), despite completely different timbral profiles.

### 8.2 Feature categories

**Identity features (80% weight in cross-era similarity):**

| Category | Features |
|----------|---------|
| Melodic | interval_distribution, leap_frequency, step_frequency, phrase_length_mean/std, melodic_contour_bias, register_preference |
| Harmonic | chord_type_distribution, key_distribution, modulation_frequency, chromaticism_index, tonal_centroid_mean |
| Rhythmic | note_density_mean/std, tempo_mean, tempo_variance, syncopation_score, onset_density_mean |
| Structural | track_length_mean, phrase_count_mean, section_transition_freq, loop_length_estimate |
| Motivic | motif_repetition_frequency, motif_entropy, common_motifs (top-5 trigrams) |

**Hardware context features (20% weight in cross-era similarity):**

| Category | Features |
|----------|---------|
| Timbral | spectral_centroid_mean/std, brightness_mean, brightness_distribution (5-bin), mfcc_centroid, dynamic_range_mean |

**Context metadata (0% weight — informational only):**

| Field | Description |
|-------|-------------|
| `platforms_used` | Platforms the composer worked on |
| `chips_used` | Chips used across corpus |
| `era_range` | Earliest to latest year in corpus |

Context metadata never enters similarity computation. It explains timbral divergence; it does not define identity.

### 8.3 StyleVectorComputer

**File:** `substrates/music/style_vector/style_vector.py`

```python
class StyleVectorComputer:
    def compute(
        self,
        composer_id: str,
        symbolic_scores: list[dict],
        signal_profiles: list[dict],
        context_metadata: dict,
        track_ids: list[str],
    ) -> dict:
        """Returns ArtistStyleVector artifact dict."""
```

### 8.4 CrossEraAnalyzer

**File:** `substrates/music/style_vector/cross_era.py`

Compares two ArtistStyleVector snapshots across hardware eras.

```python
class CrossEraAnalyzer:
    SIMILAR_THRESHOLD  = 0.75   # cosine similarity ≥ 0.75 → SIMILAR_TO
    DIVERGENT_THRESHOLD = 0.40  # cosine similarity < 0.40 → DIVERGES_FROM

    def compare(
        self,
        vector_a: dict,
        vector_b: dict,
        composer_id: str | None = None,
        label_a: str = "era_a",
        label_b: str = "era_b",
    ) -> dict:
        """
        Returns:
        {
            composer_id, similarity_scores, overall_similarity,
            cognition_similarity, hardware_divergence,
            findings, relationship, attribution_note
        }
        """
```

**Weighting:** 80% cognition (melodic + harmonic + rhythmic + structural + motivic), 20% timbral.

**Relationship output:**
- `SIMILAR_TO` — cognition_similarity ≥ 0.75
- `DIVERGES_FROM` — cognition_similarity < 0.40
- `MIXED` — between thresholds

**Hardware attribution note:** When timbral divergence > 40%, the analyzer generates a natural-language note attributing the difference to hardware constraints rather than compositional intent.

---

## 9. SUPPORTED INPUT FORMATS

### 9.1 Format capability table

| Format | Tier | Adapter | ControlSequence | SymbolicScore | SignalProfile |
|--------|------|---------|----------------|---------------|--------------|
| .vgm / .vgz | B | libvgm | ✓ | — | — |
| .spc | B | gme | ✓ | — | — |
| .nsf | B | gme | ✓ | — | — |
| .gbs | B | gme | ✓ | — | — |
| .hes | B | gme | ✓ | — | — |
| .kss | B | gme | ✓ | — | — |
| .gym | B | gme | ✓ | — | — |
| .s98 | B | gme | ✓ | — | — |
| .sid | B | gme | ✓ | — | — |
| .psf / .psf2 | B | vgmstream | ✓ | — | — |
| .2sf / .gsf | B | vgmstream | ✓ | — | — |
| .dsf / .ncsf | B | vgmstream | ✓ | — | — |
| .flac / .wav | D | librosa/essentia | — | — | ✓ |
| .mp3 / .ogg | D | librosa/essentia | — | — | ✓ |
| .mid / .midi | C | music21/pretty_midi | — | ✓ | — |
| .musicxml | C | music21 | — | ✓ | — |

### 9.2 Chip family mapping (gme adapter)

| Extension | Chip | Platform |
|-----------|------|---------|
| `.spc` | SPC700 | SNES |
| `.nsf` | 2A03 | NES |
| `.gbs` | DMG | Game Boy |
| `.hes` | HuC6280 | PC Engine |
| `.kss` | AY-3-8910 | MSX |
| `.gym` | YM2612 | Sega Genesis |

### 9.3 YM2612 topology (nuked_opn2 adapter)

The nuked_opn2 adapter is always available (no compiled library required). It provides static YM2612 carrier slot constants for FM algorithm topology analysis.

| Algorithm | Carrier Slots |
|-----------|---------------|
| 0 | {3} |
| 1 | {3} |
| 2 | {3} |
| 3 | {3} |
| 4 | {1, 3} |
| 5 | {1, 2, 3} |
| 6 | {1, 2, 3} |
| 7 | {0, 1, 2, 3} |

`analyze_patch(algorithm, operator_total_levels) → topology dict with brightness_proxy`

### 9.4 Capability ladder rule

The substrate must use the deepest available representation.

Priority:
1. chip/event-native causal data (Tier B)
2. symbolic/performance data (Tier C)
3. rendered audio data (Tier D)
4. metadata-only fallback (Tier A)

If multiple representations exist for the same work, merge them. The Dual Timeline Model requires preserving both causal and perceptual views.

---

## 10. DUAL TIMELINE MODEL

Chip-native music exposes two timelines. The substrate must preserve both.

### 10.1 Causal timeline

Control instructions that generate the sound:
- register writes, operator parameter changes, algorithm switches
- voice allocation, sample triggers, envelope phase transitions

```
t=0.00 channel1 key_on
t=0.02 operator3 attack
t=0.05 algorithm switch
t=0.20 feedback increase
t=0.50 key_off
```

### 10.2 Perceptual timeline

Listener-facing sound result:
- spectral centroid, loudness envelope, harmonic density
- onset transients, timbral shifts

```
0.00 attack transient
0.10 brightness spike
0.25 harmonic saturation
0.50 decay
```

### 10.3 Cause–effect mapping

Helix must preserve the relationship between these two timelines:
- register write → spectral centroid shift
- algorithm change → timbre cluster change
- envelope change → amplitude contour change

Traditional MIR-only systems do not preserve this distinction. Helix must.

### 10.4 Missing causal data

If a format lacks chip/event-level information, the causal timeline is null. This is acceptable. Audio-only tracks remain valid substrate objects. The system degrades gracefully.

---

## 11. ARTIFACT SCHEMA

All artifacts are written to `artifacts/music/<track_id>/`.

### 11.1 ControlSequence artifact

```json
{
  "track_id": "music.track:angel_island_zone_act_1",
  "format": "vgm",
  "chip_target": "YM2612",
  "event_count": 14823,
  "events": [...],
  "timing_data": {...},
  "register_writes": [...],
  "sample_rate": 44100,
  "adapter": "libvgm",
  "source_file": "...",
  "bridge_mode": "libvgm"
}
```

### 11.2 SymbolicScore artifact

```json
{
  "track_id": "music.track:angel_island_zone_act_1",
  "source_track": "music.track:angel_island_zone_act_1",
  "notes": [...],
  "duration_total": 120.5,
  "tempo_map": [...],
  "key_estimates": [...],
  "chord_progression": [...],
  "phrase_segmentation": [...],
  "interval_histogram": {...},
  "melodic_contour": [...],
  "time_signatures": [...],
  "adapter": "music21"
}
```

### 11.3 SignalProfile artifact

```json
{
  "track_id": "music.track:angel_island_zone_act_1",
  "source_track": "music.track:angel_island_zone_act_1",
  "spectral_centroid_mean": 2800.3,
  "spectral_centroid_std": 420.1,
  "brightness_mean": 0.73,
  "mfcc_means": [...],
  "chroma_means": [...],
  "onset_density": 4.2,
  "tempo": 142.0,
  "dynamic_range_mean": 18.4,
  "adapter": "librosa"
}
```

### 11.4 ArtistStyleVector artifact

```json
{
  "composer_id": "music.composer:yuzo_koshiro",
  "melodic_features": {
    "interval_distribution": {...},
    "leap_frequency": 0.31,
    "melodic_contour_bias": 0.12
  },
  "harmonic_features": {
    "chord_type_distribution": {...},
    "modulation_frequency": 0.08
  },
  "rhythmic_features": {
    "note_density_mean": 6.2,
    "tempo_mean": 156.4,
    "syncopation_score": 0.44
  },
  "structural_features": {...},
  "timbral_features": {...},
  "motivic_features": {...},
  "context_metadata": {
    "platforms_used": ["Sega Genesis", "PC-88"],
    "chips_used": ["YM2612", "OPN"],
    "era_range": [1988, 1993]
  },
  "track_count": 47,
  "track_ids": [...]
}
```

### 11.5 TrackStyleVector (legacy, per-track)

The canonical per-track representation produced by the feature fusion stage:

```json
{
  "track_id": "...",
  "synthesis_features": {
    "fm_algorithm_distribution": [...],
    "operator_feedback_mean": 0.0,
    "noise_channel_density": 0.0
  },
  "symbolic_features": {
    "tempo_bpm": 0.0,
    "key_estimate": "",
    "note_density": 0.0,
    "chord_change_rate": 0.0,
    "motif_repetition_score": 0.0
  },
  "mir_features": {
    "spectral_centroid_mean": 0.0,
    "mfcc_mean": [...],
    "chroma_vector": [...],
    "onset_density": 0.0
  },
  "structural_features": {
    "phrase_length_mean": 0.0,
    "rhythmic_complexity": 0.0
  },
  "metadata_features": {
    "release_year": 0,
    "game_franchise": "",
    "composer_team": ""
  }
}
```

---

## 12. METADATA MODEL

### 12.1 Sources

Metadata may be gathered from:
- Internal file tags (ID3, Ogg Vorbis comment)
- APEv2 `.tag` sidecar files (highest priority for chip formats)
- Local library databases
- External metadata APIs (MusicBrainz, Last.fm)
- Reference datasets (VGMDB, Wikidata, Wikipedia)

### 12.2 APEv2 sidecar priority rule

For chip-native formats (.vgz, .spc, .nsf, etc.), APEv2 sidecar files take priority over embedded headers.

Sidecar naming: `filename.ext.tag`

Supported sidecar fields:
- `Sound chip`
- `Platform`
- `Franchise`
- `Sound team`
- `Featuring`

### 12.3 Conceptual-work model

Multiple file representations may map to one conceptual track entity.

```
Angel Island Zone Act 1.vgz       ─┐
Angel Island Zone Act 1.flac       ├─→ music.track:angel_island_zone_act_1
Angel Island Zone Act 1.mid        ─┘
```

The substrate must distinguish between:
- file instance (physical path + hash)
- representation type (vgz / flac / mid)
- conceptual track entity (`music.track:slug`)

### 12.4 Local-library-first rule

The local library is the corpus anchor. External metadata enriches local entities. External metadata does not bloat the graph with objects unrelated to the local corpus unless explicitly authorized.

---

## 13. LIBRARY INDEX

The substrate maintains a persistent library index.

Each indexed file stores:
- absolute file path + relative corpus path
- file hash (SHA-256)
- detected format
- file size
- metadata source availability
- analysis status by stage (staged bitmask)
- last analyzed timestamp
- linked entity candidate(s)

---

## 14. LEGACY EXPERIMENTS

Scripts previously in `atlas/experiments/` are now archived in `labs/legacy_experiments/`.

The `AUDIT.md` in that directory classifies them:

| Status | Count | Action |
|--------|-------|--------|
| REFACTOR CANDIDATES | 16 | Logic superseded by operators; do not invoke directly |
| ARCHIVE — NO REFACTOR | 3 | Superseded utilities; keep for reference |
| RESEARCH DOCUMENTS | 2 | Markdown research notes; keep as-is |

**Refactor candidates must not be invoked directly.** Their functionality is now available via HIL operators.

```
# Ingest tracks
RUN operator:INGEST_TRACK track:music.track:<id>

# Analyze tracks
RUN operator:ANALYZE_TRACK track:music.track:<id>

# Compute style vector
RUN operator:STYLE_VECTOR composer:music.composer:<slug>

# Compile to Atlas
RUN operator:COMPILE_ATLAS
```

---

## 15. HIL CONTRACT

All automated orchestration occurs through HIL.

Examples:
```
RUN operator:INGEST_TRACK track:music.track:angel_island_zone_act_1
RUN operator:ANALYZE_TRACK track:music.track:angel_island_zone_act_1
RUN operator:STYLE_VECTOR composer:music.composer:yuzo_koshiro
RUN operator:COMPILE_ATLAS
ATLAS list domain:music
ENTITY get music.composer:jun_senoue
GRAPH neighbors music.composer:hiroshi_kawaguchi
ATLAS lookup music.track:angel_island_zone_act_1
```

The substrate must not invent alternative orchestration patterns. HIL is the only official automation interface.

---

## 16. CONFIGURATION CONTRACT

The substrate must define explicit configuration defaults.

Minimum configurable:
- supported formats (by tier)
- style vector feature weights (cognition 80%, timbral 20%)
- motif trigram window size
- timbral histogram bin count
- random seed
- metadata source priorities
- artifact output paths
- runtime toggles for optional stages (Tier B, C, D)

Silent config drift is forbidden.

---

## 17. DETERMINISM REQUIREMENT

Given identical inputs and identical config, the Music Substrate must produce identical artifact structures.

- Randomized algorithms must use fixed seeds
- Nondeterministic external dependencies must be normalized or isolated
- Adapter calls are deterministic by contract

Reproducibility is mandatory.

---

## 18. ANTI-DRIFT RULES

### 18.1 No duplicate script rule

Do not create a new script if an existing script already owns that responsibility. Extend, refactor intentionally, or document the change in the spec.

### 18.2 No direct Atlas write rule

No substrate module calls `atlas_commit()` directly. This is a hard architectural constraint, not a suggestion.

### 18.3 No misplaced responsibility rule

- Substrate logic belongs in `substrates/music/`
- Lab logic belongs in `labs/music_lab/`
- No domain-specific logic in `core/`

### 18.4 No silent renaming rule

Stable concepts that must not be renamed without spec revision:
- TrackStyleVector
- ArtistStyleVector
- causal timeline / perceptual timeline
- CrossEraAnalyzer
- SIMILAR_THRESHOLD / DIVERGENT_THRESHOLD

### 18.5 No speculative expansion rule

Every addition must answer: **How does this help convert music into structured Helix representations?**

### 18.6 No architecture invention rule

If a behavior is not defined in this spec, extend this document rather than improvising hidden architecture.

---

## 19. MODULE OWNERSHIP

### 19.1 Substrate-owned modules (`substrates/music/`)

| Module | Responsibility |
|--------|---------------|
| `pipeline_core.py` | Operator-callable 10-stage pipeline orchestrator |
| `config.py` | Substrate configuration and defaults |
| `tag_reader.py` | Internal tags and APEv2 sidecar reader |
| `vgm_parser.py` | Chip/event-native format parser |
| `smps_reconstructor.py` | Symbolic reconstruction from event streams |
| `channel_profiler.py` | Channel-level usage metrics |
| `patch_fingerprinter.py` | Patch and timbral fingerprints |
| `feature_extractor.py` | Feature layer computation |
| `measurement_engine.py` | Structural metrics |
| `style_signal_generator.py` | Feature fusion into style signals |
| `knowledge_engine.py` | Atlas entity/relationship prep |
| `run_context.py` | Runtime execution context |
| `style_vector/style_vector.py` | StyleVectorComputer |
| `style_vector/cross_era.py` | CrossEraAnalyzer |

### 19.2 Adapter-owned modules (`core/adapters/`)

| Module | Responsibility |
|--------|---------------|
| `adapter_libvgm.py` | libvgm bridge → ControlSequence |
| `adapter_gme.py` | gme bridge → ControlSequence |
| `adapter_vgmstream.py` | vgmstream bridge → ControlSequence |
| `adapter_nuked_opn2.py` | YM2612 topology constants |
| `adapter_librosa.py` | librosa → SignalProfile |
| `adapter_essentia.py` | essentia → SignalProfile extension |
| `adapter_music21.py` | music21 → SymbolicScore |
| `adapter_pretty_midi.py` | pretty_midi → SymbolicScore |

### 19.3 Lab-owned modules (`labs/music_lab/`)

- clustering experiments
- style-space experiments
- composer attribution experiments
- corpus-level comparative studies
- research notebooks and visualization scripts
- legacy experiment archive (`labs/legacy_experiments/`)

---

## 20. PLANNED COMPONENTS

These are part of the intended long-term DNA. Future implementations must extend this lineage, not replace it.

- Full local music corpus ingestion (all supported formats)
- Rich entity seeding from local library + VGMDB/MusicBrainz
- Causal/perceptual comparative modeling (timeline linking)
- Cross-format track unification (same work across VGM/FLAC/MIDI)
- Style-space and composer fingerprinting at corpus scale
- Multi-chip synthesis evolution studies across hardware generations
- Cross-era composer analysis using CrossEraAnalyzer at scale

---

## 21. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the Music Substrate from this document. Required components:

- [ ] `pipeline_core.py` with 10 stages, artifact write methods
- [ ] 8 adapters in `core/adapters/` matching the adapter inventory table
- [ ] `StyleVectorComputer` with 6 feature category methods + context normalization
- [ ] `CrossEraAnalyzer` with cosine similarity, 80/20 weighting, SIMILAR_TO/DIVERGES_FROM/MIXED output
- [ ] 4 music operator specs registered in `core/operators/builtin_operators.py`
- [ ] 4 SemanticSignatures in `core/semantics/entity_registry/entity_types.py`
- [ ] Artifact schemas matching §11 above
- [ ] All artifacts write to `artifacts/music/<track_id>/`, never to `atlas/`
- [ ] No substrate module calls `atlas_commit()` directly
- [ ] `HELIX_MODE=runtime` blocks direct Atlas writes

---

*This document is the authoritative specification for the Helix Music Substrate.*
*Version 2.0 — 2026-03-17*
