# Music Domain Specific Signals

Catalog of domain-specific observables extractable by the **Music Substrate** for mapping to **Substrate Capability Vector Axis**.

---

## 1. Causal Signals (Hardware & Driver Layer)

Derived from register-write logs (VGM/ControlSequence) and sound-chip specifications.

| Signal Name | Description | Measurement Method | Platform (e.g.) |
| :--- | :--- | :--- | :--- |
| `substrate_saturation_ratio` | Percentage of hardware channels/polyphony currently active. | `active_channels / max_channels` per scan-line or frame. | YM2612, NES APU |
| `operator_topology_complexity`| The richness of FM algorithm/feedback configurations. | Normalization of carrier/modulator ratio vs total possible algorithms. | YM2151 (OPM) |
| `driver_vblank_interrupt` | Frequency of the driver's task-scheduler (Timing stability). | Measures frequency of register-write batches (e.g. 50Hz, 60Hz, 100Hz). | SMPS, GEMS |
| `channel_limits` | Binary/categorical constraint of available hardware voices. | Lookup from `core/adapters/SOUNDCHIPS.md`. | All chips |

---

## 2. Perceptual Signals (MIR Layer)

Derived from audio signal analysis (PCM/WAV/FLAC) via `librosa`, `essentia`, or Spotify features.

| Signal Name | Description | Measurement Method | Source Layer |
| :--- | :--- | :--- | :--- |
| `structural_stiffness` | Ratio of spectral energy to rhythmic predictability. | `Energy / (Danceability + 0.01)`. Ratio > 1.5 indicates "Stiff Aggro." | Spotify / Essentia |
| `timbral_spectral_centroid` | Information-theoretic entropy of the spectral centroid distribution over time. | `H(spectral_centroid_bins) / log2(bins)`. | librosa |
| `dynamic_range_variance` | Mean variance of the loudness/amplitude envelope. | Standard deviation of `loudness` bins over a 500ms window. | Essentia |
| `transient_energy_density` | Density of onset detections per unit time. | `onsets_per_second` (NPS) normalized against domain baseline. | librosa |

---

## 3. Symbolic Signals (Representation Layer)

Derived from MIDI, score notation, or reconstructed `ControlSequence` patterns.

| Signal Name | Description | Measurement Method | Source Layer |
| :--- | :--- | :--- | :--- |
| `rhythmic_quantization_error` | Mean deviation of note onsets from the inferred metrical grid. | `sum(abs(onset - grid_pos)) / total_notes`. | MIDI / music21 |
| `harmonic_vocab_size` | Count of distinct vertical pitch-class sets (chords) used. | `len(unique_chords) / domain_max`. | music21 |
| `pitch_class_entropy` | Shannon entropy of the 12 pitch classes. | `H(pitch_class_distribution) / log2(12)`. | MIDI / HSL |
| `articulation_diversity` | Number of distinct articulation types detectable over time. | Histogram entropy of note duration/velocity relationship. | MIDI |
| `motif_repetition_rate` | Frequency of repeating symbolic patterns (3-4 note fragments). | Sequence alignment frequency of detected n-grams. | MotifFeatures |

---

## 4. Hardware Constraints (from SOUNDCHIPS.md)

| Constraint Factor | Structural Relevance |
| :--- | :--- |
| **Voice Polyphony** | Limits `recurrence_depth` and `structural_density` by capping concurrent events. |
| **Operator Topology** | FM feedback/routing constraints limit `control_entropy` of timbral shifts. |
| **Timer Precision** | Clock-divider limits define the "grid hardness" in `generative_constraint`. |
