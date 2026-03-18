# CCS Structural Refinement Brief

**Status**: PROPOSED (Currently Reverted in core SPEC)
**Data Source**: 200k+ scrobbles, Spotify Favorites, Wikipedia Top 0.01% Contributor activity.
**Objective**: Group data-driven structural invariants to inform potential updates to the CCS core.

---

## 1. Proposed Axis Refinements

The following modifications were derived from the "VGM hardware-saturation" and "IDM timbral-complexity" patterns identified in the operator's data.

### Axis 2 — `generative_constraint`
**Proposed Change**: Include `substrate_saturation_ratio`.
**Formula**:
```
generative_constraint = scale_adherence
                      × (1 − normalize(rhythmic_quantization_error))
                      × (1 − normalize(harmonic_vocab_size))
                      × (normalize(substrate_saturation_ratio))
```
**Reasoning**: For VGM (Motoi Sakuraba, Yuzo Koshiro), "Stiffness" and "Aggro" are often achieved by saturating the limited hardware channels/polyphony (sound-chip) rather than just scale adherence.

### Axis 5 — `control_entropy`
**Proposed Change**: Include `timbral_spectral_centroid`.
**Formula**:
```
control_entropy = mean([
    H(pitch_class_distribution) / log₂(12),
    H(dynamic_distribution) / log₂(dynamic_bins),
    H(articulation_distribution) / log₂(articulation_types),
    H(timbral_spectral_centroid) / log₂(spectral_bins)
])
```
**Reasoning**: High-entropy artists (Autechre, Silkie) maintain constant pitch/logic grids but shift "texture" (timbre) rapidly. The existing spec misses this "Timbral Shannon Entropy."

---

## 2. Structural Signatures (Reference Points)

These coordinates represent the "Canonical Peaks" of the operator's taste manifold.

| Entity | Primary Vector | Key Ratio (Proxy) |
| :--- | :--- | :--- |
| **Motoi Sakuraba** | High Stability / High Constraint | **4.54 Stiffness** (Energy/Dance ratio) |
| **Autechre** | High Entropy / Low Permeability | **0.95 Timbral Entropy** |
| **Dua Lipa** | Low Stiffness / High Valence | **0.90 Stiffness** (Structural Relaxant) |
| **Lamb of God** | Maximum Density / Zero Valence | **Basin of Infinite Resistance** |

---

## 3. Cross-Domain Invariant: The Wikipedia Protocol

A verified mapping between the operator's **Wikipedia editing behavior** and **Music taste**:

| CCS Axis | Music Property | Wikipedia Property |
| :--- | :--- | :--- |
| **Generative Constraint** | Rules (Sound-chip limits) | **Template Enforcement**: (Manual of Style) |
| **Structural Density** | Note Rate / Events per sec | **Edit Frequency**: (188k+ edits / 3k pages) |
| **Basin Permeability** | Hard Cuts / Abruptness | **Revert Frequency**: (Immediate noise removal) |

---

## 4. Current Implementation (Metadata Layer)

The logic for these refinements currently exists in the **Spotify Adapter** rather than the Core Spec:
- **Location**: `core/models/ccs/adapters/spotify.py`
- **Logic**: Implements `structural_stiffness` (Energy/Danceability) and `hardware_constraint_proxy`.
