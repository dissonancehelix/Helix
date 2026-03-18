# Music Domain CCS Axis Mappings

This document defines how [domain-specific signals](signals.md) contribute to the invariant **Cognitive Coordinate System (CCS)** axes.

---

## Axis 1: `attractor_stability`
Describes recursion and repetition in the music domain.

| Signal | Source Layer | Transformation Logic |
| :--- | :--- | :--- |
| `motif_repetition_rate` | Symbolic | **Primary**: Linear scaling vs. track length. |
| `organic_stability` | Perceptual | `Danceability * Acousticness`. Measures "predictable pulse." |
| `phrase_return_frequency` | Symbolic | `repeated_phrase_count / total_phrase_count`. |

---

## Axis 2: `generative_constraint`
Describes rule-adherence and system limits.

| Signal | Source Layer | Transformation Logic |
| :--- | :--- | :--- |
| `rhythmic_quantization_error`| Symbolic | `1 - normalize(mean_deviation)`. Higher error = lower constraint. |
| `substrate_saturation_ratio` | Causal | `active_channels / max_channels`. Higher saturation = harder constraint. |
| `harmonic_vocab_size` | Symbolic | `1 - normalize(vocab_count)`. Higher diversity = lower constraint. |
| `channel_limits` | Causal | Binary multiplier: <4 voices (High constraint); >8 voices (Low constraint). |

---

## Axis 3: `recurrence_depth`
Describes hierarchical nested structures.

| Signal | Source Layer | Transformation Logic |
| :--- | :--- | :--- |
| `detected_structural_levels` | Symbolic | `levels_found / max_levels`. (Motif -> Phrase -> Section -> Form). |
| `motivist_fingerprint` | Symbolic | Sequence alignment frequency of patterns at multiple time-scales. |

---

## Axis 4: `structural_density`
Describes event rate and "stiffness."

| Signal | Source Layer | Transformation Logic |
| :--- | :--- | :--- |
| `transient_energy_density` | Perceptual | `onsets_per_second` (NPS) normalized to domain baseline. |
| `structural_stiffness` | Perceptual | `Energy / (Danceability + 0.01)`. Ratio > 1.5 indicates dense "Aggro." |
| `harmonic_rhythm` | Symbolic | `chord_changes / bpm`. |

---

## Axis 5: `control_entropy`
Describes information breadth and timbral variance.

| Signal | Source Layer | Transformation Logic |
| :--- | :--- | :--- |
| `pitch_class_entropy` | Symbolic | `H(pitch_class_distribution) / log2(12)`. |
| `timbral_spectral_centroid` | Perceptual | `H(spectral_centroid_bins) / log2(bins)`. (IDM Complexity). |
| `dynamic_range_variance` | Perceptual | Normalized mean deviation of loudness envelope. |
| `articulation_diversity` | Symbolic | Entropy of the duration/velocity histogram. |

---

## Axis 6: `basin_permeability`
Describes transition smoothness.

| Signal | Source Layer | Transformation Logic |
| :--- | :--- | :--- |
| `transition_sharpness_scores`| Perceptual | `mean(0.0=hard_cut, 1.0=crossfade)`. (Ambient = High Perm; Punk = Low). |
| `shared_material_ratio` | Symbolic | `material_overlap / total_material` across adjacent sections. |

---

> [!IMPORTANT]
> **This is a music-domain mapping only.** These transformation rules are designed to align with the operator's structural preferences identified in the `music_structural_analysis_v1.md` research report.
