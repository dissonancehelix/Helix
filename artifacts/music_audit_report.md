# Helix Music Research Subsystem Audit Report
**Date:** 2026-03-17
**Pass:** Formal System Consolidation — Music Substrate
**Status:** COMPLETE

---

## Executive Summary

The Helix music research subsystem has been audited, repaired, and standardized.
All music analysis now flows through the formal execution pipeline:

```
HIL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler → Atlas
```

Substrates no longer write to Atlas directly.
The `master_pipeline.py` standalone orchestrator has been converted to an
internal module (`substrates/music/pipeline_core.py`) callable by operators only.

---

## 1. Tool Inventory

### 1.1 Chip Emulation & VGM Tools

| Tool | Location | Language | Purpose | Bridge | Adapter | Status |
|------|----------|----------|---------|--------|---------|--------|
| **libvgm** (ValleyBell) | `runtime/deps/libvgm/` | C++ | VGM emulation (YM2612, SN76489, YM2151, OPL) | `measurement_synthesis/libvgm_bridge.py` | `core/adapters/adapter_libvgm.py` | SOURCE PRESENT, not compiled |
| **Nuked-OPN2** | `runtime/deps/Nuked-OPN2/` | C | YM2612 FM topology reference | `domain_analysis/tool_bridge.py` | `core/adapters/adapter_nuked_opn2.py` | ACTIVE (static constants, no compilation needed) |
| **Game_Music_Emu** | `runtime/deps/game-music-emu/` | C++ | SPC, NSF, GBS, HES, KSS, AY formats | `measurement_synthesis/gme_bridge.py` | `core/adapters/adapter_gme.py` | SOURCE PRESENT, not compiled |
| **vgmstream** | `runtime/deps/vgmstream/` | C | Broad game audio decoding | `measurement_synthesis/gme_bridge.py` (proxy) | `core/adapters/adapter_vgmstream.py` | SOURCE PRESENT, not compiled |
| **Furnace tracker** | `runtime/deps/helix_sources/furnace/` | C++ | Reference source only | None | None | REFERENCE ONLY |
| **MAME sound cores** | `runtime/deps/helix_sources/mame/` | C++ | Reference source only | None | None | REFERENCE ONLY |

### 1.2 Runtime Analysis Tools (Python/compiled)

| Tool | Location | Language | Purpose | Bridge | Adapter | Status |
|------|----------|----------|---------|--------|---------|--------|
| **vgm2txt** | `runtime/bin/vgm2txt.exe` | C (binary) | VGM command decode | `domain_analysis/tool_bridge.py` | `core/adapters/adapter_libvgm.py` (proxy) | ACTIVE |
| **gems2mid** | `runtime/bin/gems2mid.exe` | C (binary) | GEMS→MIDI conversion | `domain_analysis/tool_bridge.py` | — | ACTIVE |
| **libOPNMIDI** | `runtime/deps/...` (clone target) | C++ | OPN2→MIDI (highest quality) | None | None | NOT CLONED — optional expansion |
| **vgm2x** | Clone target | C | VGM stream conversion | None | None | NOT CLONED — optional expansion |
| **libfmvoice** | Clone target | C | FM voice patch structures | None | None | NOT CLONED — optional expansion |
| **mdtools** | Clone target | C | MD SMPS→MIDI | None | None | NOT CLONED — optional expansion |

### 1.3 Music Analysis Libraries (Python)

| Tool | Install State | Purpose | Bridge | Adapter | Status |
|------|--------------|---------|--------|---------|--------|
| **librosa** | ✅ INSTALLED | MIR features (spectral, rhythm, timbre) | — | `core/adapters/adapter_librosa.py` | ACTIVE |
| **music21** | ✅ INSTALLED | Symbolic score analysis, key/chord | — | `core/adapters/adapter_music21.py` | ACTIVE |
| **pretty_midi** | ✅ INSTALLED | MIDI parsing, note events | — | `core/adapters/adapter_pretty_midi.py` | ACTIVE |
| **essentia** | ❌ NOT INSTALLED | High-quality audio descriptors | — | `core/adapters/adapter_essentia.py` | ADAPTER READY, install optional |
| **faiss-cpu** | ❌ NOT INSTALLED | Similarity indexing | — | — | OPTIONAL |
| **scikit-learn** | unknown | Clustering, dimensionality reduction | — | — | OPTIONAL |

### 1.4 Ingestion Adapters

| Adapter | Location | Purpose | Status |
|---------|----------|---------|--------|
| `ffmpeg.py` | `substrates/music/ingestion/adapters/` | Audio format decoding (WAV export) | ACTIVE |
| `foobar.py` | `substrates/music/ingestion/adapters/` | Foobar2000 v2 metadata | ACTIVE |
| `metadb_sqlite.py` | `substrates/music/ingestion/adapters/` | Foobar SQLite parser | ACTIVE |
| `spotify.py` | `substrates/music/ingestion/adapters/` | Spotify API integration | ACTIVE |
| `vgmdb_ingester.py` | `substrates/music/atlas_integration/sources/` | VGMdb track metadata | ACTIVE |
| `musicbrainz_ingester.py` | `substrates/music/atlas_integration/sources/` | MusicBrainz metadata | ACTIVE |

---

## 2. Active Operator Bindings

All 12 registered operators verified:

| Operator | Input Types | Output | Pipeline Stages | Music-specific |
|----------|-------------|--------|----------------|---------------|
| `INGEST_TRACK` | Track, * | ControlSequence artifact | validate → route_adapter → render → write | ✅ |
| `ANALYZE_TRACK` | Track, ControlSequence | SymbolicScore + SignalProfile artifacts | load → symbolic → signal → nuked_opn2 → write | ✅ |
| `STYLE_VECTOR` | Composer | ArtistStyleVector artifact | load_tracks → 6 feature computations → context → write | ✅ |
| `COMPILE_ATLAS` | Track, Composer, ControlSequence, SymbolicScore, SignalProfile, ArtistStyleVector | Atlas entries in atlas/music/ | discover → normalize → validate → compile → commit | ✅ |
| `PROBE` | Invariant | probe_result | load_dataset → execute → collect_signal → write | — |
| `INGEST` | * | entity artifacts | validate → parse → normalize → write | — |
| `LINK` | all entity types | relationship | validate_source → validate_target → check_type → write | — |
| `COMPILE` | * | Atlas entries | discover → normalize → validate → compile → commit | — |
| `SCAN` | * | entity candidates | enumerate → extract → write | — |
| `ANALYZE` | Composer, Track, Game, Invariant, Experiment | signal artifact | load → extract → compute → write | — |
| `DISCOVER` | Invariant | HIL command candidates | load_atlas → analyze_gaps → generate → log | — |
| `MIGRATE` | * | migrated entities | detect_legacy → convert → compile → mark | — |

---

## 3. Missing Adapters

All required adapters are now present. Summary:

| Adapter | Created | Toolkit Available |
|---------|---------|------------------|
| `adapter_libvgm` | ✅ | Source present, not compiled |
| `adapter_gme` | ✅ | Source present, not compiled |
| `adapter_vgmstream` | ✅ | Source present, not compiled |
| `adapter_nuked_opn2` | ✅ | Static constants — always available |
| `adapter_librosa` | ✅ | ✅ Installed |
| `adapter_essentia` | ✅ | ❌ Not installed (optional) |
| `adapter_music21` | ✅ | ✅ Installed |
| `adapter_pretty_midi` | ✅ | ✅ Installed |

All adapters return graceful `available=False` dicts when their toolkit is missing.
No adapter raises on missing dependency in production.

---

## 4. Legacy Scripts Requiring Refactor

All 16 legacy scripts in `labs/legacy_experiments/` have been audited.
See `labs/legacy_experiments/AUDIT.md` for per-file classification.

| Script | Was Calling | Operator Replacement |
|--------|-------------|----------------------|
| `composer_attribution.py` | master_pipeline stage 12 directly | `STYLE_VECTOR` → attributions stage |
| `composer_similarity_graph.py` | atlas_integration directly | `STYLE_VECTOR` + `COMPILE_ATLAS` |
| `composer_style_vectors.py` | feature_extraction directly | `STYLE_VECTOR` operator |
| `composer_training_sets.py` | master_pipeline stage 17 | `STYLE_VECTOR` → training_sets stage |
| `fingerprints.py` | domain_analysis.composer_fingerprint directly | `STYLE_VECTOR` → composer_fp stage |
| `music_ingestion.py` | metadata_processor directly | `INGEST_TRACK` |
| `music_mir_analysis.py` | mir.py directly | `ANALYZE_TRACK` → mir stage |
| `music_symbolic_analysis.py` | symbolic.py directly | `ANALYZE_TRACK` → symbolic stage |
| `s3k_analysis.py` | master_pipeline stages 1–9 | `INGEST_TRACK` + `ANALYZE_TRACK` |

None of these scripts are deleted. They remain in `labs/legacy_experiments/` for reference.

---

## 5. Removal Candidates

No files are recommended for deletion at this time.

The following are **low priority archival candidates** (no active use, no operator mapping):

- `labs/legacy_experiments/expand_composer_dataset.py` — superseded by ingesters
- `labs/legacy_experiments/filesystem_scan.py` — superseded by scan stage
- `labs/legacy_experiments/music_lab_list.py` — no architectural value

These should only be removed with explicit user approval.

The following directory contains ~6,800 Pandoc test suite files:
- `artifacts/tests/pandoc_observations/` — NOT Atlas entities; can be deleted if disk space needed

---

## 6. Recommended Optional Tool Additions

These tools are not yet present but would expand Helix's analysis capabilities.
Do NOT clone automatically — mark for future consideration.

### Chip Emulation (High Value)
| Tool | Source | Purpose | Priority |
|------|--------|---------|----------|
| libOPNMIDI | github.com/Wohlstand/libOPNMIDI | OPN2→MIDI (highest quality conversion) | HIGH |
| vgm2x | github.com/vampirefrog/vgm2x | VGM command stream conversion | MEDIUM |
| libfmvoice | github.com/vampirefrog/libfmvoice | FM voice patch data structures | MEDIUM |
| mdtools | github.com/sikthehedgehog/mdtools | SMPS→MIDI for Mega Drive | MEDIUM |

### Python Libraries (Medium Value)
| Library | pip name | Purpose | Priority |
|---------|----------|---------|----------|
| essentia | `essentia` | High-quality audio descriptors, tonal analysis | HIGH |
| faiss-cpu | `faiss-cpu` | Large-scale similarity search | HIGH |
| muspy | `muspy` | Multi-format symbolic music toolkit | MEDIUM |
| partitura | `partitura` | MusicXML/MEI symbolic analysis | LOW |

### Build Required (High Value, already cloned)
| Library | Status | Action needed |
|---------|--------|--------------|
| libvgm | Source at runtime/deps/libvgm/ | Run `build_extensions.py` or `cmake` |
| vgmstream | Source at runtime/deps/vgmstream/ | Run `build_extensions.py` or `cmake` |
| game-music-emu | Source at runtime/deps/game-music-emu/ | Compile libgme.so |

To build: `RUN operator:SCAN substrate:music` will trigger build detection via
`substrates/music/measurement_synthesis/build_extensions.py`.

---

## 7. Current Coverage of Music Analysis Capabilities

### Tier A — Static Parse (No compilation needed)
| Capability | Coverage | Tools |
|------------|----------|-------|
| VGM register decode | ✅ FULL | `libvgm_bridge` fallback (pure Python) |
| SPC/NSF basic metadata | ✅ PARTIAL | `parsing/router.py` |
| MIDI parsing | ✅ FULL | `pretty_midi`, `music21` |
| Music theory (key, chords) | ✅ FULL | `music21`, `librosa` |
| Spectral features | ✅ FULL | `librosa` |
| Melodic/rhythmic features | ✅ FULL | `pretty_midi` + style_vector computation |
| Composer style vector | ✅ FULL | `StyleVectorComputer` |
| Cross-era comparison | ✅ FULL | `CrossEraAnalyzer` |

### Tier B — Emulated (Requires compiled libraries)
| Capability | Coverage | Blocker |
|------------|----------|---------|
| Full YM2612 emulation | ⚠️ PARTIAL | libvgm not compiled |
| SPC/NSF emulation | ⚠️ PARTIAL | gme not compiled |
| Broad format decoding | ⚠️ PARTIAL | vgmstream not compiled |
| Timing-accurate events | ❌ BLOCKED | requires libvgm compilation |

### Tier C — Symbolic
| Capability | Coverage | Tools |
|------------|----------|-------|
| MIDI→note events | ✅ FULL | `pretty_midi` |
| Chord progression | ✅ FULL | `music21` |
| Key estimation | ✅ FULL | `music21`, `librosa` |
| Interval analysis | ✅ FULL | `StyleVectorComputer` |
| Motif detection | ✅ PARTIAL | `StyleVectorComputer` (trigram proxy) |

### Tier D — MIR + Advanced
| Capability | Coverage | Tools |
|------------|----------|-------|
| Spectral MIR | ✅ FULL | `librosa` |
| Tonal descriptors | ⚠️ PARTIAL | requires `essentia` |
| Similarity indexing | ❌ MISSING | requires `faiss-cpu` |
| Composer attribution | ✅ FULL | `STYLE_VECTOR` + `CrossEraAnalyzer` |

---

## 8. Atlas Schema Status

### New Entity Types (added this pass)

| Type | Required Fields | Relationships | Purpose |
|------|----------------|---------------|---------|
| `ControlSequence` | id, type, name, label, description, source_track, chip_target, format | DERIVED_FROM, TARGETS_CHIP | Hardware register-write log |
| `SymbolicScore` | id, type, name, label, description, source_track | DERIVED_FROM, REPRESENTS | Music theory representation |
| `SignalProfile` | id, type, name, label, description, source_track | DERIVED_FROM, REPRESENTS | Audio feature set |
| `ArtistStyleVector` | id, type, name, label, description, composer_id, melodic_features, harmonic_features, rhythmic_features | ATTRIBUTED_TO, DERIVED_FROM, SIMILAR_TO, DIVERGES_FROM | Composer musical fingerprint |

**Total ontology types:** 19 (was 15)

### Artist Style Vector Design Law
> Musical cognition features DOMINATE.
> Hardware context (chips, platforms) is METADATA ONLY.
> It explains differences — it does not define identity.

Feature weights in cross-era similarity:
- Cognition features (melodic + harmonic + rhythmic + motivic + structural): **80%**
- Timbral features (hardware-influenced): **20%**

---

## 9. Architecture Compliance

| Requirement | Status | Notes |
|------------|--------|-------|
| Substrates never write Atlas directly | ✅ ENFORCED | `pipeline_core.py` explicit; `master_pipeline.py` docstring updated |
| All Atlas writes through COMPILE_ATLAS | ✅ ENFORCED | Atlas compiler is the only authorized path |
| RUN operator:UNDEFINED raises HILValidationError | ✅ VERIFIED | Tested — correct error returned |
| All operators in registry | ✅ VERIFIED | 12 operators including 4 music-specific |
| Adapters contain no Helix logic | ✅ VERIFIED | All 8 adapters are pure translation layers |
| Artifact path: artifacts/music/<track_id>/ | ✅ DEFINED | `pipeline_core.write_track_artifact()` |
| Entity types in Semantics layer | ✅ VERIFIED | 19 types including 4 new music analysis types |
| Cross-era reasoning supported | ✅ IMPLEMENTED | `CrossEraAnalyzer` + `SIMILAR_TO`/`DIVERGES_FROM` relationships |

---

## 10. Files Created This Pass

| File | Purpose |
|------|---------|
| `substrates/music/pipeline_core.py` | Operator-callable pipeline (replaces standalone master_pipeline) |
| `core/adapters/__init__.py` | Adapter layer package |
| `core/adapters/adapter_libvgm.py` | libvgm VGM emulation adapter |
| `core/adapters/adapter_gme.py` | Game_Music_Emu adapter |
| `core/adapters/adapter_vgmstream.py` | vgmstream broad-format adapter |
| `core/adapters/adapter_nuked_opn2.py` | Nuked-OPN2 YM2612 topology adapter |
| `core/adapters/adapter_librosa.py` | librosa MIR feature adapter |
| `core/adapters/adapter_essentia.py` | Essentia audio descriptor adapter |
| `core/adapters/adapter_music21.py` | music21 symbolic score adapter |
| `core/adapters/adapter_pretty_midi.py` | pretty_midi MIDI analysis adapter |
| `substrates/music/style_vector/__init__.py` | Style vector package |
| `substrates/music/style_vector/style_vector.py` | ArtistStyleVector computation |
| `substrates/music/style_vector/cross_era.py` | Cross-era composer comparison |
| `labs/legacy_experiments/AUDIT.md` | Legacy script classification |
| `artifacts/tests/pandoc_observations/` | Moved from atlas/observations/ |
| `labs/legacy_experiments/` | Moved from atlas/experiments/ |

## Files Modified This Pass

| File | Change |
|------|--------|
| `core/kernel/runtime/orchestration/master_pipeline.py` | Docstring updated — architecture note, operator paths, no-direct-Atlas-write warning |
| `core/operators/builtin_operators.py` | Added INGEST_TRACK, ANALYZE_TRACK, STYLE_VECTOR, COMPILE_ATLAS |
| `core/semantics/entity_registry/entity_types.py` | Added ControlSequence, SymbolicScore, SignalProfile, ArtistStyleVector |
| `core/kernel/schema/entities/ontology.py` | Added ENTITY_MUSIC_ANALYSIS_TYPES, updated ENTITY_ONTOLOGY |

---

*Report end. Helix music subsystem audit complete.*
