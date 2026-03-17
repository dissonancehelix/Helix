# Legacy Experiments Audit
**Date:** 2026-03-17
**Audited by:** Helix Formal System Consolidation Pass

## Status

These files were moved from `atlas/experiments/` during Atlas housekeeping.
They represent ad-hoc research scripts written before the Helix formal operator architecture.

They must NOT be deleted automatically.
They may be refactored into operators or archived as needed.

---

## File Classification

### REFACTOR CANDIDATES
These scripts contain logic that should now live in a Helix operator or adapter.
The logic is preserved here; the operator path supersedes direct script execution.

| File | Current Function | Operator Replacement |
|------|-----------------|----------------------|
| `composer_attribution.py` | Probabilistic composer attribution via feature vectors | `STYLE_VECTOR` operator → `attributions` stage |
| `composer_report.py` | Atlas report generation for composer entities | `ANALYZE_TRACK` → `COMPILE_ATLAS` |
| `composer_similarity_graph.py` | Similarity graph construction between composers | `STYLE_VECTOR` → `COMPILE_ATLAS` + Atlas graph |
| `composer_style_space.py` | Style space embedding construction | `STYLE_VECTOR` → `style_space` stage |
| `composer_style_vectors.py` | Style vector computation (now superseded) | `STYLE_VECTOR` operator |
| `composer_training_sets.py` | Training corpus extraction | `STYLE_VECTOR` → `training_sets` stage |
| `fingerprints.py` | Gaussian fingerprinting of composer style | `STYLE_VECTOR` → `composer_fp` stage |
| `motif_network_analysis.py` | Motif co-occurrence network | `ANALYZE_TRACK` → `motivic_features` |
| `music_chip_analysis.py` | Chip-level feature analysis | `INGEST_TRACK` → `chip_features` stage |
| `music_ingestion.py` | Track metadata ingestion | `INGEST_TRACK` → `ingest` stage |
| `music_library_index.py` | Library indexing and cataloging | `INGEST_TRACK` → `scan` stage |
| `music_library_ingestion.py` | Full library ingestion pipeline | `INGEST_TRACK` operator |
| `music_mir_analysis.py` | MIR feature extraction | `ANALYZE_TRACK` → `mir` stage |
| `music_symbolic_analysis.py` | Symbolic reconstruction (MIDI) | `ANALYZE_TRACK` → `symbolic` stage |
| `s3k_analysis.py` | Sonic 3 & Knuckles specific analysis | `INGEST_TRACK` + `ANALYZE_TRACK` |
| `soundtrack_analysis.py` | Per-soundtrack feature analysis | `ANALYZE_TRACK` + `STYLE_VECTOR` |

### ARCHIVE — NO REFACTOR NEEDED
These scripts do not map to any operator. Keep for research reference only.

| File | Reason |
|------|--------|
| `expand_composer_dataset.py` | Dataset expansion utility; superseded by vgmdb/musicbrainz ingesters |
| `filesystem_scan.py` | Generic filesystem scanner; superseded by `INGEST_TRACK` scan stage |
| `music_lab_list.py` | Lab file listing utility; no architectural value |

### RESEARCH DOCUMENTS — KEEP AS-IS
These markdown files contain research notes or sweep results.

| File | Reason |
|------|--------|
| `composer_style_probe_sega_sound_team.md` | Research notes on Sega Sound Team style analysis |
| `decision_compression_sweep.md` | Decision compression probe sweep results |

---

## Migration Notes

Scripts marked REFACTOR CANDIDATES should NOT be invoked directly.
Their functionality is now available via HIL:

```
# Ingest tracks
RUN operator:INGEST_TRACK track:music.track:<id>

# Analyze tracks
RUN operator:ANALYZE_TRACK track:music.track:<id>

# Compute style vector for a composer
RUN operator:STYLE_VECTOR composer:music.composer:<slug>

# Compile to Atlas
RUN operator:COMPILE_ATLAS
```

Cross-era composer analysis is now available via:
```python
from substrates.music.style_vector import CrossEraAnalyzer
analyzer = CrossEraAnalyzer()
result = analyzer.compare(vector_ym2612, vector_orchestral, composer_id="music.composer:motoi_sakuraba")
```

---

## Do Not Delete Policy

These files are archived research artifacts.
Deletion requires explicit user approval.
They may contain edge-case logic or dataset knowledge not yet captured in operators.
