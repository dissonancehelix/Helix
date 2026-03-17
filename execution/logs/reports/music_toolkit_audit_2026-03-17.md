# Helix Music Toolkit Audit
**Date:** 2026-03-17
**Type:** Diagnostic — read-only pass. Repository not modified (except this file).
**Scope:** Music analysis, VGM, chip emulation, audio analysis, symbolic analysis toolkits.

---

## Executive Summary

Helix contains a comprehensive, well-stocked music analysis substrate. The physical toolkit coverage is strong: libvgm, vgmstream, Nuked-OPN2, Game_Music_Emu, Furnace, and Python libraries (librosa, music21, pretty_midi) are all present. An 18-stage Tier A–D analysis pipeline exists in `substrates/music/` and produces entity-compatible output.

**The critical gap is architectural:** the substrate operates as a self-contained legacy orchestrator. It bypasses every HIL gate, writes directly to internal databases, and has no operator wiring whatsoever. Zero of the 8 registered operators are called from the music substrate.

Operationalization requires wrapping the substrate's stages into INGEST → ANALYZE → COMPILE operators and materializing inter-stage data as formal artifact objects.

---

## 1. Tool Inventory

| Tool | Location | Language | Purpose | Operator | Adapter | Status |
|------|----------|----------|---------|----------|---------|--------|
| libvgm | `runtime/deps/libvgm/` | C | VGM emulation (YM2612, OPL, SN76489, YM2151, PSG) | None | `libvgm_bridge.py` (ctypes) | **PRESENT** |
| vgmstream | `runtime/deps/vgmstream/` | C | Game audio format decoding (SPC, NSF, PSF, USF) | None | subprocess fallback (planned) | **PRESENT** |
| Nuked-OPN2 | `runtime/deps/Nuked-OPN2/` | C | High-accuracy YM3438 emulation | None | Reference only | **PRESENT** |
| Game_Music_Emu | `runtime/deps/game-music-emu/` | C++ | Multi-format game music playback | None | `gme_bridge.py` (ctypes, partial) | **PRESENT** |
| vgmtools | `runtime/deps/vgmtools/` | C++ | VGM command-stream manipulation | None | None | **PRESENT, UNUSED** |
| Furnace | `runtime/deps/helix_sources/sound_drivers/furnace/` | C++ | Multi-chip tracker (emulation reference) | None | Reference only | **PRESENT, UNUSED** |
| libADLMIDI | `runtime/deps/helix_sources/sound_drivers/libADLMIDI/` | C++ | OPL MIDI synthesis | None | Reference only | **PRESENT, UNUSED** |
| SMPSPlay | `runtime/deps/helix_sources/sound_drivers/SMPSPlay/` | C++ | Sega SMPS playback reference | None | Reference only | **PRESENT, UNUSED** |
| MAME cores | `runtime/deps/helix_sources/sound_drivers/mame/` | C++ | Hardware emulation reference | None | Reference only | **PRESENT, UNUSED** |
| librosa | pyproject.toml / install_deps.py | Python | MIR: tempo, MFCC, chroma, spectral | None | `mir_extractor.py` (conditional import) | **INSTALLED (optional)** |
| music21 | pyproject.toml / install_deps.py | Python | Computational musicology: key, harmony, cadences | None | `symbolic_toolchain.py` (partial) | **INSTALLED (optional)** |
| pretty_midi | install_deps.py | Python | MIDI generation from symbolic data | None | `score_representation.py` (partial) | **INSTALLED (optional)** |
| muspy | install_deps.py | Python | Symbolic music I/O | None | None | **LISTED, NOT ACTIVE** |
| essentia | install_deps.py | Python | Spectral MIR features | None | Mentioned only | **LISTED, NOT ACTIVE** |
| FFmpeg/ffprobe | External binary | CLI | Audio metadata, format conversion | None | `FFmpegAdapter` (ingestion) | **ACTIVE (subprocess)** |
| scikit-learn | install_deps.py | Python | Clustering (k-means, HDBSCAN) | None | Used in feature_vec stage | **ACTIVE** |
| numpy / scipy | pyproject.toml | Python | Signal processing, feature arrays | None | Used throughout | **ACTIVE** |
| faiss-cpu | install_deps.py | Python | Similarity indexing | None | Used in faiss stage | **ACTIVE** |
| vgm2x | clone_tools.py | C | VGM command conversion | None | None | **NOT CLONED** |
| libfmvoice | clone_tools.py | C | FM operator data structures | None | None | **NOT CLONED** |
| libOPNMIDI | clone_tools.py | C | OPN2 FM→MIDI conversion | None | None | **NOT CLONED** |
| mdtools | clone_tools.py | Python/C | Mega Drive SMPS tools | None | None | **NOT CLONED** |

---

## 2. Dependency Manifest (Music/Audio Relevant)

### Core (`pyproject.toml`)
```
numpy, scipy, mutagen, pandas, networkx, beautifulsoup4
```

### Tier C — Symbolic Analysis (`install_deps.py`)
```
pretty_midi     MIDI generation
music21         Computational musicology (key, harmony, cadences)
symusic         Fast MIDI ingestion
musif           Research feature extraction
musicntwrk      Harmonic/motif network analysis
```

### Tier D — MIR and Advanced (`install_deps.py`)
```
librosa         Audio analysis (MFCC, chroma, spectral, tempo)
muspy           Symbolic music manipulation
partitura       Score parsing + onset detection
essentia        Spectral MIR features
faiss-cpu       Similarity indexing
scikit-learn    Clustering
umap-learn      Dimensionality reduction
hdbscan         Density-based clustering
anthropic       LLM interpretation (Claude API)
```

---

## 3. Adapter Inventory

### Existing Adapters

| Adapter | Path | Wraps | Operator | Complete |
|---------|------|-------|----------|----------|
| FFmpegAdapter | `substrates/music/ingestion/adapters/ffmpeg.py` | ffprobe subprocess | None | Partial |
| FoobarAdapter | `substrates/music/ingestion/adapters/foobar.py` | Foobar2000 DB | None | Partial |
| SpotifyAdapter | `substrates/music/ingestion/adapters/spotify.py` | Spotify API | None | Partial |
| libvgm_bridge | `substrates/music/measurement_synthesis/libvgm_bridge.py` | libvgm ctypes | None | Partial |
| gme_bridge | `substrates/music/measurement_synthesis/gme_bridge.py` | game-music-emu ctypes | None | Partial |
| chip_state_tracer | `substrates/music/measurement_synthesis/chip_state_tracer.py` | libvgm register trace | None | Partial |
| vgm_to_midi_adapter | `substrates/music/domain_analysis/vgm_to_midi_adapter.py` | VGM → MIDI struct | None | Active |

### Missing Adapters (required for operator integration)

| Adapter to Create | Wraps | Operator |
|-------------------|-------|----------|
| `core/adapters/libvgm_adapter.py` | libvgm_bridge → normalized output | ANALYZE |
| `core/adapters/gme_adapter.py` | gme_bridge → normalized output | ANALYZE |
| `core/adapters/vgmstream_adapter.py` | vgmstream subprocess | ANALYZE |
| `core/adapters/music21_adapter.py` | music21 theory analysis | ANALYZE |
| `core/adapters/librosa_adapter.py` | librosa MIR features | ANALYZE |
| `core/adapters/pretty_midi_adapter.py` | pretty_midi MIDI ops | ANALYZE |
| `core/adapters/ffmpeg_adapter.py` | FFmpegAdapter → normalized | INGEST |

Note: `core/adapters/` does not currently exist.

---

## 4. Legacy Scripts (Migrated to `labs/legacy_experiments/`)

All legacy scripts call `MasterPipeline` stages directly. None use the operator system.

| Script | Apparent Purpose | Pipeline Stage(s) | Recommended Path |
|--------|-----------------|-------------------|-----------------|
| `music_chip_analysis.py` | YM2612 operator/DAC feature extraction | 3–4 | `RUN operator:ANALYZE` with chip mode |
| `music_mir_analysis.py` | Audio MIR (tempo, spectral, brightness) | 8 | `RUN operator:ANALYZE` with mir mode |
| `music_symbolic_analysis.py` | Symbolic extraction + music theory | 6–7 | `RUN operator:ANALYZE` with symbolic mode |
| `music_library_index.py` | Library scanning and indexing | 1–2 | `RUN operator:SCAN` |
| `music_library_ingestion.py` | Metadata ingestion | 2 | `RUN operator:INGEST` |
| `music_ingestion.py` | Full ingestion pipeline | 1–2 | `RUN operator:INGEST` |
| `composer_attribution.py` | Probabilistic composer attribution | 12 | `RUN operator:ANALYZE` with attribution mode |
| `fingerprints.py` | Gaussian composer fingerprinting | 11 | `RUN operator:ANALYZE` with fingerprint mode |
| `motif_network_analysis.py` | Pattern/motif graph construction | 14 | `RUN operator:ANALYZE` with motif mode |
| `composer_style_space.py` | Style vector clustering | 9 | `RUN operator:ANALYZE` with style mode |
| `composer_similarity_graph.py` | Composer relationship graph | 11–12 | `RUN operator:ANALYZE` with graph mode |
| `s3k_analysis.py` | Sonic 3K specific analysis | 3–8 | `RUN operator:ANALYZE soundtrack:s3k` |
| `soundtrack_analysis.py` | Per-game soundtrack analysis | 9–12 | `RUN operator:ANALYZE` |
| `expand_composer_dataset.py` | Training set generation | 17 | `RUN operator:SCAN` |
| `composer_training_sets.py` | Training corpus selection | 17 | `RUN operator:INGEST` |
| `filesystem_scan.py` | File enumeration | 1 | `RUN operator:SCAN` |

All scripts are **archive candidates** — their logic should be absorbed into operators, not maintained as scripts.

---

## 5. Substrates/Music Pipeline Analysis

### Current Architecture

`substrates/music/` runs an 18-stage self-contained orchestrator (`master_pipeline.py`) in four tiers:

```
Tier A (Static Parse)   — VGM/SPC/NSF/SID structure, register extraction
Tier B (Emulation)      — libvgm/gme live chip emulation
Tier C (Symbolic)       — Note reconstruction, music theory (music21)
Tier D (MIR)            — librosa audio features, clustering, FAISS
```

Stage progression:
```
1  scan         → enumerate library files
2  ingest       → insert into TrackDB
3  tier_a_parse → static parsing (vgm_parser, spc_parser, nsf_parser, sid_parser)
4  chip_feat    → FM operator data, DAC patterns
5  tier_b_trace → libvgm register traces / gme playback
6  symbolic     → VGM→MIDI reconstruction (vgm_note_reconstructor)
7  theory       → music21: key, harmony, cadences, tempo
8  mir          → librosa MFCC/chroma/spectral OR chip-proxy fallback
9  feature_vec  → 64-dim fused feature vector
10 faiss        → similarity index + KDTree
11 composer_fp  → Gaussian fingerprint per composer
12 attribution  → probabilistic track→composer attribution
13 taste        → operator taste centroid
14 recommend    → near-core + frontier recommendations
15 graph        → entity builder (Track/Composer/Game/Platform/Chip)
16 ludo         → ludomusicology (gameplay role, energy curves)
17 training     → corpus selection
18 style_space  → style vector clustering
```

**None of these stages call into the HIL/Operator system.**

### Violation Summary

1. Direct DB writes — stages 2, 15 write directly to registry, no INGEST gate
2. No artifacts — inter-stage data is in-memory, never materialized
3. No operator manifests — no input/output type declarations
4. No provenance — data flows with no hil_command or run_id tracking
5. No COMPILE gate — entity_builder writes to Atlas without going through atlas_compiler

---

## 6. Operator Coverage Gaps

### Registered Operators vs. Music Substrate Needs

| Music Need | Correct Operator | Currently Wired | Gap |
|------------|-----------------|-----------------|-----|
| Library scan | SCAN | No | Create SCAN → music substrate stage 1 |
| Metadata ingest | INGEST | No | Create INGEST → stages 2 |
| Chip feature extraction | ANALYZE | No | Create ANALYZE chip mode → stages 3–4 |
| Emulation trace | ANALYZE | No | Create ANALYZE emulation mode → stage 5 |
| Symbolic analysis | ANALYZE | No | Create ANALYZE symbolic mode → stages 6–7 |
| MIR extraction | ANALYZE | No | Create ANALYZE mir mode → stage 8 |
| Composer attribution | ANALYZE | No | Create ANALYZE attribution mode → stage 12 |
| Entity building | COMPILE | No | Wire entity_builder → atlas_compiler |
| Style vector | ANALYZE | No | Create ANALYZE style mode → stage 18 |

**Total operator gaps: 9 of 9 music substrate functions are unconnected.**

### Music-Specific Operators to Add

```python
ANALYZE_CHIP      # Chip feature extraction (FM operators, PSG envelopes, DAC)
ANALYZE_SYMBOLIC  # Symbolic analysis (note reconstruction, music21 theory)
ANALYZE_MIR       # Audio MIR (librosa: tempo, MFCC, chroma, spectral)
ANALYZE_COMPOSER  # Attribution + fingerprinting + style clustering
```

These could alternatively be modes of the existing `ANALYZE` operator via a `mode:chip|symbolic|mir|composer` parameter.

---

## 7. Missing Critical Toolkits

### Present (confirmed)
| Toolkit | Status | Notes |
|---------|--------|-------|
| libvgm | ✓ PRESENT | `runtime/deps/libvgm/`, ctypes bridge exists |
| Nuked-OPN2 | ✓ PRESENT | `runtime/deps/Nuked-OPN2/`, reference only |
| Game_Music_Emu | ✓ PRESENT | `runtime/deps/game-music-emu/`, gme_bridge.py partial |
| vgmstream | ✓ PRESENT | `runtime/deps/vgmstream/`, subprocess fallback |
| librosa | ✓ INSTALLED | Conditional import in mir_extractor.py |
| music21 | ✓ INSTALLED | Conditional import in symbolic_toolchain.py |
| pretty_midi | ✓ INSTALLED | Partial use in score_representation.py |
| Furnace | ✓ PRESENT | `runtime/deps/helix_sources/furnace/`, reference only |
| Essentia | ✓ LISTED | Not actively used in code |

### Absent (not cloned, referenced in clone_tools.py)
| Toolkit | Priority | Purpose | Flag |
|---------|----------|---------|------|
| vgm2x | HIGH | VGM command-stream conversion | RECOMMENDED INSTALL |
| libfmvoice | HIGH | FM operator data structures | RECOMMENDED INSTALL |
| libOPNMIDI | MEDIUM | OPN2 FM→MIDI conversion | RECOMMENDED INSTALL |
| mdtools | MEDIUM | Mega Drive SMPS tools | RECOMMENDED INSTALL |

### Completely absent (not referenced anywhere)
| Toolkit | Purpose | Flag |
|---------|---------|------|
| highly-experimental | PSF/PS1 audio | RECOMMENDED INSTALL |
| vio2sf | Nintendo DS 2SF audio | OPTIONAL |
| lazyusf | Nintendo 64 USF audio | OPTIONAL |
| nsfplay | NES NSF reference player | OPTIONAL |

---

## 8. Atlas Compatibility

### Entity Schemas — Current Output

| Substrate Output | Atlas Type | Fields | Gaps |
|-----------------|------------|--------|------|
| TrackDB row | `Track` | id, title, artist, album, platform, audio_features | Missing `label`, `description` |
| ComposerNode | `Composer` | composer_id, full_name, aliases, fingerprint_vector | Missing `label`, `description` |
| SoundChipNode | `SoundChip` | chip_id, name, manufacturer | Missing `label`, `description` |
| GameNode | `Game` | game_id, title, platform | Missing `label`, `description` |
| PlatformNode | `Platform` | platform_id, name, manufacturer | Missing `label`, `description` |

### Missing Atlas Schemas (no entity type defined)

| Needed Schema | Contents | Maps To |
|---------------|----------|---------|
| `signal_profile` | MIR features, chip features, spectral | New atlas type needed |
| `symbolic_score` | Note sequences, key, harmony analysis | New atlas type needed |
| `style_vector` | 64-dim fused feature, cluster ID | New atlas type needed |
| `control_sequence` | FM register write trace | New atlas type needed |
| `artist_style_vector` | Gaussian fingerprint, HDBSCAN cluster | New atlas type needed |

### Relationship Coverage

| Relationship | Source → Target | In Registry | In Substrate |
|-------------|-----------------|-------------|--------------|
| COMPOSED | Composer → Track | ✓ defined | ✓ created |
| APPEARS_IN | Track → Game | ✓ defined | ✓ created |
| RUNS_ON | Game → Platform | ✓ defined | ✓ created |
| USES_CHIP | Game → SoundChip | ✓ defined | ✓ created |
| MEMBER_OF | Composer → SoundTeam | ✓ defined | Not used in substrate |
| COLLABORATED_WITH | Composer ↔ Composer | ✓ defined | Partially (via recommendations) |

---

## 9. Style Vector Pipeline Coverage

### Feature Classes and Tool Coverage

| Feature Class | Required Evidence | Tool Available | Wired to Operator |
|--------------|------------------|----------------|-------------------|
| Chip usage patterns | FM channel allocation, PSG ratios | libvgm (Tier B) | No |
| Envelope distributions | ADSR envelopes, FM operator params | libvgm_bridge (Tier A/B) | No |
| Melodic interval statistics | Note reconstruction, interval histogram | vgm_note_reconstructor (Tier C) | No |
| Rhythm density | Note onset density, syncopation | symbolic_toolchain + music21 (Tier C) | No |
| Harmonic features | Key, chord progressions, cadences | music21 (Tier C/D) | No |
| Spectral signatures | MFCC, chroma, brightness | librosa (Tier D) | No |
| Motif fingerprints | Recurring pattern detection | motif_detector (Tier C) | No |
| Cluster membership | HDBSCAN, UMAP | scikit-learn / hdbscan (Tier D) | No |

**Style vector computation is possible with current tools but entirely disconnected from the operator system.**

---

## Removal Candidates

None recommended for immediate deletion. The following are **archive candidates** once their logic is absorbed into operators:

- All 16 scripts in `labs/legacy_experiments/` (listed in §4)
- `substrates/music/` standalone analysis scripts (duplicated in legacy_experiments)

The following are **dead reference code** (no adapter, no operator, no build system integration):
- `runtime/deps/helix_sources/` subdirectories (Furnace, libADLMIDI, MAME, SMPSPlay) — keep as reference, do not build

---

## Recommended Tool Additions

| Tool | Priority | Source | Purpose |
|------|----------|--------|---------|
| vgm2x | HIGH | Listed in clone_tools.py | VGM command conversion for MIDI bridge |
| libfmvoice | HIGH | Listed in clone_tools.py | FM operator data structures |
| libOPNMIDI | MEDIUM | Listed in clone_tools.py | OPN2 FM→MIDI conversion |
| mdtools | MEDIUM | Listed in clone_tools.py | Mega Drive SMPS toolkit |
| highly-experimental | MEDIUM | PSF plugin project | PS1/PSF audio support |
| nsfplay | LOW | GitHub | NES audio reference player |

All are flagged as recommended — do not clone automatically.

---

## Summary

| Phase | Finding |
|-------|---------|
| Tool coverage | Strong — 9 of 9 priority toolkits present |
| Python libraries | Strong — librosa, music21, pretty_midi, essentia all available |
| Adapter layer | Partial — bridges exist in substrate but not in `core/adapters/` |
| Operator integration | None — 0 of 9 music functions wired to operators |
| Atlas output | Partial — entity types correct, missing signal_profile/style_vector schemas |
| Legacy scripts | 16 scripts in labs/legacy_experiments/ need operator migration |
| Architecture compliance | FAIL — substrate bypasses HIL, writes Atlas directly |
| helix verify | PASS (unrelated to substrate integration) |
