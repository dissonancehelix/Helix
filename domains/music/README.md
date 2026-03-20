# HELIX MUSIC SUBSTRATE

**Version:** 2.1
**Authority:** Authoritative formal substrate specification
**Reference SPEC:** [SPEC.md](SPEC.md)

---

## 1. PURPOSE

The Music Substrate is the Helix environment responsible for transforming music libraries into **structured computational datasets**. It enables the discovery of structural invariants across different representations of music—from hardware register writes to rendered spectral features.

## 2. ROLE WITHIN HELIX

The substrate serves as the **Translation and Extraction bridge** between the Library and the Atlas:

### Data Flow
- **Input (Library - Reference Storage)**:
  - Raw Audio/VGM/MIDI files (`codex/library/music/source/`).
  - **The Library acts as the storage side of the Atlas**, housing reference chip models (`codex/library/audio/chips/`) and driver ontologies (`codex/library/audio/drivers/`).
- **Helix Engine**:
  - Performs 10-stage extraction (Decoding → Analysis → Fusion).
  - Normalizes signals under **Partial Observability** constraints.
- **Output (Atlas - Research Memory)**:
  - Unified Musical Objects (UMO) and CCS Embeddings (`codex/codex/atlas/music/`).

## 3. STRUCTURAL EXPRESSION

Music is analyzed as a multi-layered linguistic system:
- **Causal**: Synthesis logic (What the hardware does).
- **Symbolic**: Compositional intent (What the composer writes).
- **Perceptual**: Psychoacoustic outcome (What the listener hears).

The substrate's primary goal is to extract the **Invariants** that survive when format, hardware, or era changes.

## 4. CCS MAPPING (Cognitive Coordinate System)

The substrate maps its high-dimensional feature space into the standardized 6-axis CCS model:

| Axis | Derived From (Music Domain) | Implementation Layer |
|------|-----------------------------|--------------------|
| **Attractor Stability** | Loop recurrence / Motif repetition | Symbolic |
| **Generative Constraint**| Grid adherence / Key consistency | Symbolic |
| **Recurrence Depth** | Nested phrasal hierarchy | Symbolic/Causal |
| **Structural Density** | Note/Event rate per unit time | Causal/Perceptual |
| **Control Entropy** | Timbral/Interval variance | Perceptual/Symbolic |
| **Basin Permeability** | Timbral transition smoothness | Perceptual |

## 5. CAPABILITIES

- **Decomposition**: Splitting work into its synthesis and score components.
- **Mapping**: Projecting multi-dialect features into a single coordinate point.
- **Reconstruction**: Inferring missing layers (e.g., predicting score from audio alone) under **Partial Observability**.

## 6. PROJECT EXAMPLE: Final Fantasy VI (SPC → MIDI → CD)

The **Final Fantasy VI (Terra's Theme)** exists as multiple dialect projections:
1. **SPC700 Register Writes (SPC/VGM)**: The hardware-native causal representation (SNES).
2. **Standard MIDI File (Symbolic)**: The high-level compositional score (Note events, No hardware detail).
3. **Orchestral Rendition (WAV/FLAC)**: The rendered perceptual audio (Timbre and Expression).

Helix uses the Music Substrate to align these dialects, extracting the **Composer Identity** (structural invariants) that remained stable across all three layers despite shifting from 16-bit sound-chip constraints to full orchestral expression.

---

*For detailed signal definitions, artifact schemas, and library references, see the [SPEC.md](SPEC.md).*
