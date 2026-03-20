# HELIX MUSIC SUBSTRATE SPECIFICATION (SPEC)

**Version:** 2.1
**Status:** Authoritative technical specification
**Relationship:** Implementation partner to `domains/music/README.md`

---

## 1. FORMAL SIGNAL DEFINITIONS

The Music Substrate extracts measurable signals from three observability layers:

### 1.1 Causal Signals (Hardware/Driver)
- **`register_write_density`**: Number of chip register writes per second.
- **`operator_topology_complexity`**: Graph complexity of FM algorithms (source: `adapter_nuked_opn2`).
- **`driver_tick_jitter`**: Temporal variance in command dispatch (source: `adapter_smps`).
- **`lfsr_noise_entropy`**: Entropy of noise channel bitstreams (source: `adapter_nuked_psg`).

### 1.2 Symbolic Signals (Compositional)
- **`interval_entropy`**: Shannon entropy of melodic intervals.
- **`rhythmic_quantization_error`**: Deviation from absolute grid centers.
- **`harmonic_vocab_size`**: Number of unique chord types used.
- **`phrase_recurrence_ratio`**: Percentage of phrases that repeat with >90% similarity.

### 1.3 Perceptual Signals (Audio)
- **`spectral_centroid_drift`**: Variance in brightness over time.
- **`onset_density`**: Perceived rhythmic events per second (source: `adapter_librosa`).
- **`timbre_cluster_count`**: Number of distinct MFCC clusters detected.

---

## 2. CCS AXIS DERIVATION

The 6 CCS axes are derived from the above signals using the following normalization methods:

| CCS Axis | Primary Music Signal | Helix Normalization Method |
|----------|----------------------|----------------------------|
| `attractor_stability` | `phrase_recurrence_ratio` | Domain baseline: VGM loop-density |
| `generative_constraint` | `rhythmic_quantization_error` | Inverse of deviation from grid |
| `recurrence_depth` | `hierarchical_motif_depth` | Normalized count of nested repeats |
| `structural_density` | `register_write_density` | Log-normalized per-chip event rate |
| `control_entropy` | `interval_entropy` | Percentile of composer-specific variance |
| `basin_permeability` | `spectral_transition_slope` | Sigmoid-mapped slope of timbral shifts |

---

## 3. EXTRACTION PIPELINE (10 STAGES)

| Stage | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| 1 | Ingestion | Source Path | Library Index Entry |
| 2 | Decoding | VGM/FLAC/MIDI | ControlSequence / Audio Stream / Symbolic Object |
| 3 | Static Parse | Header Data | Metadata Artifact |
| 4 | Causal Trace | Register Log | Timeline Trace Artifact |
| 5 | Symbolic Extr. | Event Stream | SymbolicScore Artifact |
| 6 | MIR Analysis | Rendered Audio | SignalProfile Artifact |
| 7 | Motif Detection | Phrasal Data | Motif Entity Candidates |
| 8 | Feature Fusion | All Artifacts | Unified Style Vector |
| 9 | CCS Embedding | Style Vector | CCS Embedding Artifact |
| 10 | Atlas Compilation| All Artifacts | Atlas Entities |

---

## 4. ARTIFACT SCHEMAS

### 4.1 ControlSequence (`artifacts/music/<id>/control_seq.json`)
```json
{
  "track_id": "...",
  "chip_target": "YM2612",
  "events": [...],
  "timing_vblank": true
}
```

### 4.2 SymbolicScore (`artifacts/music/<id>/symbolic.json`)
```json
{
  "track_id": "...",
  "notes": [...],
  "interval_histogram": {...}
}
```

### 4.3 SignalProfile (`artifacts/music/<id>/signal.json`)
```json
{
  "track_id": "...",
  "spectral_centroid": 2800.3,
  "onset_density": 4.2
}
```

---

## 5. VALIDATION

- **Deterministic Check**: Re-running the pipeline on a fixed hash must yield identical CCS coordinates.
- **Cross-Layer Alignment**: Symbolic score durations must match perceptual waveform durations within 5ms.
- **Library Reference Compliance**: Any chip-level measurement must be validated against `codex/library/audio/chips/` specifications.
