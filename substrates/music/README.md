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

## §0.5 — Unified Musical Object (UMO) Model

### Musical Object, Not File

The Music Substrate does not treat tracks as files. Each ingested work is a **Unified Musical Object (UMO)** — a structured entity defined by `core/kernel/schema/umo_schema.json` with the following top-level fields:

| UMO Field | Schema Key | Source |
|-----------|-----------|--------|
| Causal layer | `representations.causal` | Register event timelines (VGM, NSF, SPC, S98, GBS, ...) |
| Symbolic layer | `representations.symbolic` | MIDI, MusicXML, music21 score objects |
| Perceptual layer | `representations.perceptual` | librosa/essentia feature vectors |
| Metadata | `representations.metadata` | Tag files, foobar2000 dialect (recorded + normalized) |
| Alignment map | `alignment_map` | Cross-layer links: causal ⇄ symbolic ⇄ perceptual |
| Conflicts | `conflicts` | Cross-layer disagreements (first-class data, never discarded) |
| Invariants | `invariants` | Patterns surviving across ≥2 dialect layers |
| Identity | `identity` | Inferred composer profile + evidence tracks |

All dialect layers under `representations` are optional — a UMO may be populated with one, two, or all three. `alignment_map`, `conflicts`, and `invariants` are required arrays (may be empty). The pipeline's job is to extract and align as many layers as the source format permits.

### Observability Depth by Format Family

| Format Family | Example Formats | Observability Depth |
|---------------|----------------|---------------------|
| VGM/VGZ | `.vgm`, `.vgz` | **Causal** — full register timeline, deterministic |
| NSF/NSFE | `.nsf`, `.nsfe` | **Causal** — NES APU register writes via emulation |
| SPC | `.spc` | **Causal** — SNES S-DSP register writes + SPC700 CPU state |
| GBS | `.gbs` | **Causal** — Game Boy APU register writes |
| HES | `.hes` | **Causal** — PC-Engine HuC6280 audio registers |
| KSS | `.kss` | **Causal** — MSX / SMS register writes |
| S98 | `.s98` | **Causal** — Japanese arcade FM register dumps |
| AY | `.ay` | **Causal** — AY-3-8910 register writes |
| PSF / PSF2 | `.psf`, `.psf2` | **Hybrid** — PlayStation SPU; full CPU execution, partial register visibility |
| 2SF | `.2sf` | **Hybrid** — Nintendo DS; ARM9/7 execution, DSP events extractable |
| USF | `.usf` | **Hybrid** — Nintendo 64; RSP microcode, partial audio pipeline visibility |
| GSF | `.gsf` | **Hybrid** — GBA; ARM7 execution, partial channel register visibility |
| DSF / NCSF | `.dsf`, `.ncsf` | **Hybrid** — DS/3DS; partial synthesis register visibility |
| MIDI / MusicXML | `.mid`, `.xml` | **Symbolic** — pitch/rhythm/harmony; no hardware detail |
| FLAC / WAV | `.flac`, `.wav` | **Perceptual** — full audio; generation logic not recoverable |
| MP3 / OGG / OPUS | `.mp3`, `.ogg`, `.opus` | **Perceptual** — compressed audio; feature extraction only |

Observability depth determines which pipeline stages are available and which views can be populated in the UMO.

### Perceptual Reasoning Without Hearing

The Music Substrate is designed for LLM reasoning about musical structure — not audio playback. LLMs reason over:
1. **Causal views** — register writes that deterministically explain every sonic event
2. **Symbolic views** — pitch/rhythm/harmony sequences that encode compositional intent
3. **Perceptual feature views** — numerical summaries of audible outcomes (MFCCs, chroma, spectral centroid, onset density)

In chip-native formats, causal observability can exceed compressed audio in structural information content: the register timeline explains every timbral and temporal event completely. In rendered audio formats, features capture expression, mixing, performance, and perceptual realization that chip/symbolic representations cannot encode.

Both directions of advantage are real. The substrate must populate as many views as available and make the observability depth explicit in artifact metadata.

### Composer Identity Principle

The Music Substrate's primary research goal is identifying **persistent compositional identity** across representations. A composer fingerprint consists of:

- **Structural habits**: Harmonic motion, interval sequences, rhythmic density
- **Decision patterns**: How constraints are navigated (hardware limits, driver idioms)
- **Motif behavior**: Recurring melodic/rhythmic fragments and their evolution
- **Control idioms**: Timbre shaping, envelope choices, channel allocation patterns
- **Perceptual signatures**: Spectral habits, dynamic range preferences, tonal center tendencies

This identity must be discoverable across format families. A composer whose works exist as VGM register dumps, SPC files, MIDI exports, and rendered FLAC files should yield consistent fingerprint measurements regardless of source format. Format and hardware are constraints on expression; compositional identity is what persists through those constraints.

---

## 1. SUBSTRATE IDENTITY

### 1.1 What the Music Substrate is

The Music Substrate is the Helix environment responsible for transforming music libraries into structured computational datasets.

## Core Capabilities
* **Hardware Invariant Extraction**: Direct structural modeling of vintage sound chips (YM2612, SN76489, YM2151, etc.) from reference emulator code (Nuked, libvgm).
* **Driver Layer Analysis**: Disentangling software-driver implementations (GEMS, SMPS, MCD DRM) from hardware capabilities using formal driver ontology.
* **Silicon-Level Logic Calibration**: Capturing undocumented hardware behaviors (e.g. YM2612 "Ladder Effect", SSG-EG logic).
* **Control Sequence Ingestion**: High-fidelity rendering of VGM/VGZ/SPC/NSF data.
* **Cognition Discovery**: Detection of cross-platform melodic fingerprints.
* **Style Vector Computation**: Construction of artist identities from structural data.

It analyzes music as a layered structural system spanning:
- synthesis mechanisms (chip register events, FM operator graphs)
- audio perception (signal features, spectral analysis)
- symbolic composition (notes, harmony, phrases, motifs)
- metadata identity (composer, platform, game, era)
- graph relationships (composer → track → game → platform → chip)

It converts music artifacts into:

```
raw files (data/music/source/)
→ decoded representations (chip events / rendered waveforms)
→ hardware architecture extraction (the 6-stage Ingestion Contract)
→ feature layers (MIR / symbolic / synthesis)
→ fused style vectors (per-track and per-composer)
→ embeddings and clusters
→ Atlas entities (via compiler only)
```

The Music Substrate is a translation and extraction layer. It converts music into structured data that Helix can reason over.

### 1.2 Language-Based Hierarchy (HSL Alignment)

As a **SubstrateLanguage** derived from HSL, the Music Substrate defines the following architectural layers:

#### Languages
The domain is partitioned into three specialized languages describing how structure exists:
*   **chip-level control language**: Structural description of hardware state and register transitions.
*   **symbolic music language**: High-level compositional structure (notes, harmony, motifs).
*   **perceptual audio language**: Measurable properties of the sonic result (timbre, dynamics, spectral flow).

#### Dialects (Representations)
Each language is expressed through specific dialects:
*   `chip_control` Dialects: **VGM**, **VGZ**, **SPC**, **NSF**, raw register write streams.
*   `symbolic_music` Dialects: **MIDI**, **MusicXML**, **music21** stream objects.
*   `perceptual_audio` Dialects: **waveform** (WAV, FLAC), **spectral features** (spectrograms, MFCCs).

#### Translation Paths
Processing in the Music Substrate is a formal translation between these dialects:
1.  **chip → symbolic**: Decoding hardware events into musical notes and score structures.
2.  **symbolic → perceptual**: Mapping compositional intent to predicted or measured sonic characteristics.
3.  **chip → perceptual**: Direct rendering of hardware instructions into audio features (skipping symbolic representation where appropriate).

Each stage of the pipeline transforms representation while preserving structural invariants.

### 1.3 What the Music Substrate is not

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
data/music/processed/
```

Never to `atlas/`. Artifacts correspond to specific **dialect translation stages** and accumulate in the **Execution Layer** before being persisted to the **Root Data Layer** under `data/music/processed/`.

### 2.3 Data Structure Alignment
The Music Substrate enforces a strict directory structure within `data/music/`:
*   `source/`: Raw dialect inputs (e.g., PDFs, manuals, VGM/MIDI files, raw audio).
*   `processed/`: Structured outputs of dialect translation stages (e.g., parsed events, extracted features, symbolic scores).
*   `metadata/`: Curated annotations, tags, and structured descriptors.

The `derived/` directory is prohibited; all non-source data must be mapped to specific dialect translation artifacts in `processed/`.

### 2.3 Hardware Ingestion Contract

The Music Substrate is responsible for ingesting technical documentation (PDFs, manuals) to seed hardware entities. This MUST follow the **6-stage pipeline**:
1. `parsed.json` (Document sections)
2. `features.json` (Measurable hardware properties)
3. `structure.json` (Signal flow / Topology graphs)
4. `patterns.json` (Motific extraction)
5. `measurements.json` (Quantified parameters/limits)
6. `atlas_candidates.json` (Proposed entities/relationships)

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
                  │
                  ▼
           execution/runs/           ← Intermediate Traces
                  │
                  ▼
        data/music/processed/        ← Persistent Derived Data
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

| Adapter | Toolkit / Source | Output Type | Tier |
|---------|-----------------|-------------|------|
| `adapter_nuked_opn2.py` | `code/Nuked-OPN2` (ym3438.h) | YM2612 carrier topology dict | A |
| `adapter_nuked_opm.py` | `code/Nuked-OPM` (opm.c) | YM2151 carrier topology dict | A |
| `adapter_nuked_opl3.py` | `code/Nuked-OPL3` (opl3.c) | OPL3 CON topology dict (2-op/4-op) | A |
| `adapter_nuked_opll.py` | `code/Nuked-OPLL` (opll.h) | YM2413/OPLL carrier constant + patch ROM names | A |
| `adapter_nuked_opl2.py` | `code/Nuked-OPL2-Lite` (opl2.h) | YM3812 CON topology dict + waveforms | A |
| `adapter_nuked_psg.py` | `code/Nuked-PSG` (ympsg.h) | YM7101/SN76489 PSG channel + volume table | A |
| `adapter_smps.py` | `code/SMPS` source | SMPS timing + opcode constants | A |
| `adapter_gems.py` | `code/GEMS`, `code/GEMSPlay`, `code/MidiConverters` | GEMS patch constants + MIDI bridge | A/B |
| `adapter_vgmfile.py` | `toolkits/vgmtools/VGMFile.h` | VGM header + GD3 + tag priority merge | A |
| `adapter_chiptext.py` | `toolkits/vgmtools/chiptext.c` | NES APU, GB DMG, Pokey regs; OPN/OPL flags; waveform tables | A |
| `adapter_vgm_system.py` | `toolkits/vgmtools/vgm_tag.c` | Platform taxonomy (70+ system codes → names) | A |
| `adapter_libvgm.py` | `toolkits/libvgm` C library | ControlSequence | B |
| `adapter_gme.py` | `toolkits/game-music-emu` | ControlSequence | B |
| `adapter_vgmstream.py` | `toolkits/vgmstream` C library | ControlSequence | B |
| `adapter_vgm2txt.py` | `toolkits/vgmtools/vgm2txt` binary | causal.temporal_trajectories (full register timeline) | B |
| `adapter_vgm_cnt.py` | `toolkits/vgmtools/vgm_cnt` binary | chip_command_counts + channel_stats | B |
| `adapter_vgm_stat.py` | `toolkits/vgmtools/vgm_stat` binary | duration_sec, loop points, GD3 fallback | B |
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
| `SoundChip` | `music.sound_chip:<slug>` | Audio synthesis chip (channels, topologies, DAC resolution) |
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
  "commitment_density": 0.82,  # EIP Metric: decision collapse strength
  "entropy_collapse_rate": 0.15,
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
  "research_features": {
    "commitment_density_mean": 0.76,
    "entropy_collapse_variance": 0.04
  },
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

## 14. OPERATOR APPLICATIONS
The functionality of legacy scripts is now available via HIL operators.

```hil
# Ingest tracks
RUN operator:INGEST_TRACK track:music.track:<id>

# Analyze tracks (Produces MIR, Motif, Geometry, Causal, and Style artifacts)
RUN operator:ANALYZE_TRACK track:music.track:<id>

# Research Loop: Falsification and Topology
RUN operator:FALSIFY_INVARIANT invariant:decision_compression
RUN operator:TOPOLOGY_MAP entity:music.track:<id> entity:games.experiment:<id>

# Knowledge Gain Monitoring
RUN operator:MEASURE_KNOWLEDGE_GAIN substrate:music

# Pattern Search
RUN operator:DISCOVER
RUN operator:DISCOVER target:attribution track:music.track:<id>
RUN operator:DISCOVER_INVARIANTS

# Compile to Atlas
RUN operator:COMPILE_ATLAS
```

---

## 15. MULTI-ARTIST ATTRIBUTION RULES

Tracks with multiple artists are treated as latent mixtures to prevent style vector corruption.

1.  **Delimiters**: Use `;` or `,` in `artist` field for parsing (Helix treats both as identical delimiters).
2.  **Attribution Persistence**:
    - `solo`: Verified single author. Weight = 1.0.
    - `multi`: Multiple credits, equal distribution placeholder. Weight = 0.25 (Low baseline).
    - `inferred`: Authorship refined via structural analysis. Weight = 0.5 - 1.0.
3.  **Refinement Pipeline**: Use `DISCOVER target:attribution` to generate an `attribution_inference.json`. If confidence is high, `COMPILE_ATLAS` promotes this to an `inferred` status.
4.  **Style Fingerprinting**: Only `solo` and `verified inferred` tracks are used for ground-truth style vector formation. `multi` tracks are deprioritized.


---

## 15. HSL CONTRACT

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

The substrate must not invent alternative orchestration patterns. HSL is the only official automation interface.

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

| Module | Tier | Responsibility |
|--------|------|---------------|
| `adapter_nuked_opn2.py` | A | YM2612 (OPN2) algorithm → carrier slots, brightness proxy |
| `adapter_nuked_opm.py` | A | YM2151 (OPM) algorithm → carrier slots |
| `adapter_nuked_opl3.py` | A | YMF262 (OPL3) 2-op and 4-op CON → carrier slots |
| `adapter_nuked_opll.py` | A | YM2413/OPLL carrier constant, patch ROM names, chip variants |
| `adapter_nuked_opl2.py` | A | YM3812 (OPL2) CON → carrier slots, waveform table |
| `adapter_nuked_psg.py` | A | YM7101/SN76489 PSG channel constants, volume table, freq formula |
| `adapter_smps.py` | A | SMPS driver timing, opcode table, channel allocation |
| `adapter_gems.py` | A/B | GEMS patch format constants (A); gems2mid MIDI bridge (B) |
| `adapter_vgmfile.py` | A | VGM binary header parser; GD3 reader; external .tag priority merge |
| `adapter_chiptext.py` | A | NES APU / GB DMG / Pokey register maps; OPN/OPL type flags; waveform tables |
| `adapter_vgm_system.py` | A | 70+ platform taxonomy (vgm_tag.c SYSTEM_NAMES) |
| `adapter_libvgm.py` | B | libvgm ctypes bridge → ControlSequence |
| `adapter_gme.py` | B | Game_Music_Emu bridge → ControlSequence |
| `adapter_vgm2txt.py` | B | vgm2txt binary → causal.temporal_trajectories |
| `adapter_vgm_cnt.py` | B | vgm_cnt binary → chip command counts + channel stats |
| `adapter_vgm_stat.py` | B | vgm_stat binary → duration, loop points, GD3 fallback |
| `adapter_vgmstream.py` | B | vgmstream CLI bridge → ControlSequence |
| `adapter_music21.py` | C | music21 → SymbolicScore |
| `adapter_pretty_midi.py` | C | pretty_midi → SymbolicScore |
| `adapter_librosa.py` | D | librosa → SignalProfile |
| `adapter_essentia.py` | D | essentia → SignalProfile extension |

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

---

## 22. TOOLKITS AND EXTERNAL DEPENDENCIES

The Music Substrate integrates a wide array of specialized toolkits for synthesis tracing, audio analysis, and symbolic musicology. Each is integrated via the **Adapter** layer to ensure modularity.

### 22.1 Synthesis & Emulation (C-Layer)
These toolkits reside in `substrates/music/toolkits/` and provide the **Causal Timeline** (register-level accuracy).

| Toolkit | Location | Usage in Helix |
|---------|----------|----------------|
| **libvgm** | `toolkits/libvgm` | Primary VGM/VGZ emulator. Used via `libvgm_bridge` for YM2612/SN76489 register-write tracing. |
| **game-music-emu** | `toolkits/game-music-emu` | Multi-chip emulator for SPC, NSF, GBS, HES, KSS, AY. Used for 8/16-bit console formats. |
| **vgmstream** | `toolkits/vgmstream` | Comprehensive audio decoder. Used for PSF, 2SF, and modern streaming formats. |
| **Nuked-OPN2** | `toolkits/Nuked-OPN2` | Cycle-accurate OPN2 (YM2612) reference. Carrier slot constants for FM topology analysis. |
| **vgmtools** | `toolkits/vgmtools` | VGM utilities. `vgm2txt` compiled via `tool_bridge.compile_tools()` for register dump validation. |

### 22.2 Chip Reference Models (Tier A — Static Constants)
Extracted from source code in `data/music/source/code/`. No compilation required. Always available.

| Toolkit | Source | Adapter | What it provides |
|---------|--------|---------|-----------------|
| **Nuked-OPN2** | `code/Nuked-OPN2` | `adapter_nuked_opn2.py` | YM2612 algorithm → carrier slots, brightness proxy |
| **Nuked-OPM** | `code/Nuked-OPM` | `adapter_nuked_opm.py` | YM2151 algorithm → carrier slots, brightness proxy |
| **Nuked-OPL3** | `code/Nuked-OPL3` | `adapter_nuked_opl3.py` | OPL3 CON-bit topology (2-op and 4-op modes) |
| **Nuked-OPLL** | `code/Nuked-OPLL` | `adapter_nuked_opll.py` | YM2413/OPLL fixed carrier topology, patch ROM names, chip variants |
| **Nuked-OPL2-Lite** | `code/Nuked-OPL2-Lite` | `adapter_nuked_opl2.py` | YM3812 (OPL2) CON-bit topology, waveform table, rhythm voices |
| **Nuked-PSG** | `code/Nuked-PSG` | `adapter_nuked_psg.py` | YM7101/SN76489 PSG channel structure, volume table, noise register |

### 22.3 Driver-Level Analysis (Tier A/B)
Source in `data/music/source/code/`. Constants available at Tier A; binary tools compiled on demand via `tool_bridge.compile_tools()`.

| Toolkit | Source | Adapter | Usage |
|---------|--------|---------|-------|
| **SMPS** | `code/SMPS` | `adapter_smps.py` | Tick rates, Tempo1Tick jitter, opcode table, volume steps |
| **GEMS / GEMSPlay** | `code/GEMS`, `code/GEMSPlay` | `adapter_gems.py` | Patch byte format, field offsets |
| **gems2mid** | `code/MidiConverters/gems2mid.c` | `adapter_gems.py` (via `tool_bridge`) | GEMS sequence → MIDI (Tier B binary) |
| **vgm2txt** | `toolkits/vgmtools/vgm2txt.c` | `tool_bridge.vgm2txt()` | VGM register dump for parser validation |

### 22.4 Format Converters (Tier B — Subprocess)
Compiled from `data/music/source/code/` via `tool_bridge.compile_tools()`. Convert formats into VGM for the libvgm pipeline.

| Tool | Source | Bridge function | What it enables |
|------|--------|----------------|-----------------|
| **s98tovgm** | `code/S98toVGM` | `tool_bridge.s98_to_vgm()` | S98 arcade recordings → VGM → register analysis |
| **nsf2vgm** | `code/nsf2vgm` | `tool_bridge.nsf_to_vgm()` | NES NSF files → VGM → causal timeline analysis |

### 22.4b SPC Observability Depth Note

The SNESAPU/spcplay component (where referenced in the SPC pipeline) contains the S-DSP register model used for SPC observability depth analysis. Its structural knowledge of the SNES S-DSP register architecture — not its playback capability — is relevant to PSF/SPC pipeline depth assessment when determining how much causal information can be extracted versus inferred from these Hybrid and Causal format families.

### 22.5 Signal & MIR Analysis (Python-Layer)
Provides the **Perceptual Timeline** (how the listener hears the sound).

| Toolkit | Key Capabilities | Usage |
|---------|------------------|-------|
| **Librosa** | Spectral features, MFCC, Chroma, Onset detection. | Primary signal profile extractor in `LibrosaAdapter`. |
| **Essentia** | Tonal Centroid, Chord segmentation, Rhythm features. | Advanced descriptors used by `EssentiaAdapter`. |

### 22.6 Symbolic Musicology
Handles the **Compositional Representation** (notes and structure).

| Toolkit | Purpose | Usage |
|---------|---------|-------|
| **Music21** | Music XML, Score-level analysis, Parallel phrase detection. | Musicological research and score modeling in `Music21Adapter`. |
| **PrettyMidi** | MIDI manipulation, Note density, Pitch histograms. | Efficient symbolic feature extraction in `PrettyMidiAdapter`. |

### 22.7 Cross-Substrate Pattern Libraries
- **FAISS**: Vector similarity search for motif and style clustering.
- **NetworkX**: Relationship graph modeling and traversal.

---

## 4. SOUND HARDWARE & DRIVER ONTOLOGY

Helix treats sound chips and drivers as **Invariants**. A chip's architecture defines the physical constraint space, while a driver's code defines the musical interface for the composer.

### **SoundChip**
Physical hardware entity (e.g. YM2612, SN76489).
- **Identity**: `family` (e.g. OPN, OPL, PSG), `internal_name` (e.g. OPN2, OPM), `platforms` (e.g. Sega Genesis, FM Towns).
- **Physical Invariants**: `dac_resolution` (9-bit truncation), `sampling_rate` (55.5kHz), `lfsr_feedback`.
- **Logic Invariants**: `ssg_eg_support`, `phase_wrapping`, `oscillator_topologies`.

### **SoundDriver**
Software layer orchestrating the hardware (e.g. GEMS, SMPS).
- **Rhythmic Invariants**: `tempo_jitter` (SMPS Tempo1Tick), `tick_quantization`.
- **Command Ontology**: Macro-based instruction sets (`FEVE`, `pan_macros`).

### Technical Calibration (Truth Values)

#### **Yamaha Chip Lineage (Family Mapping)**
- **OPN Series (Operator Type-N)**: YM2203 (OPN), YM2608 (OPNA), YM2610 (OPNB), YM2612 (OPN2), YM3438 (OPN2C), YMF288 (OPN3).
- **OPL Series (Operator Type-L)**: YM3526 (OPL), YM2413 (OPLL), YM3812 (OPL2), YMF262 (OPL3), YMF278 (OPL4).
- **OPM/OPP/OPZ Series**: YM2151 (OPM), YM2164 (OPP), YM2414 (OPZ).
- **PSG (SSG) Series**: YM2149F (SSG).
- **Next-Gen/Misc**: YMF292 (SCSP), YMZ280B (PCMD8).

#### **YM2612 (OPN2)**
- **Platforms**: Sega Genesis (Mega Drive), FM Towns, various Arcades (Sega System 18/32).
- **DAC Resolution**: 9-bit truncation (Root of "Ladder Effect").
- **SSG-EG**: Supported; enables non-linear envelope loops.
- **Sampling Rate**: 55.5kHz native output.
- **Clock**: 7.67MHz (NTSC Sega Genesis).

#### **SN76489 (PSG)**
- **Platforms**: Sega Master System, Game Gear, Sega Genesis (Mega Drive), ColecoVision, BBC Micro, TI-99/4A, IBM PCjr.
- **LFSR Pattern**: 16-bit shift register with specific white/periodic noise feedback taps.
- **Volume**: 4-bit attenuation (16 steps, -2dB intervals).

#### **SMPS Driver**
- **Tempo Jitter**: "Tempo1Tick" invariant caused by Z80 sub-engine mailbox latency.
- **Command Set**: 1-byte opcode structure (Notes: 0x00-0x7F; Commands: 0x80-0xFF).
- **Rhythmic Quantization**: 60Hz or 50Hz tick rate depending on regional vertical interrupt.

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

*All new modules must follow the template registry located in `runtime/templates/`.*
