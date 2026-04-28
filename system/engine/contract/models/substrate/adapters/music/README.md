# Substrate Capability Vector Music Domain Adapter

This directory defines the music-specific signal extraction and mapping logic for the **Substrate Capability Vector**.

## Separation of Concerns

1. **Substrate Capability Vector Core (`system/engine/contract/models/substrate/SPEC.md`)**: Defines the invariant 6-axis coordinate system. It is domain-agnostic and mathematical.
2. **Music Adapter (`system/engine/contract/models/substrate/adapters/music/`)**: Translates music-specific observables (sound chip registers, MIDI intervals, spectral features) into the abstract signals required by the Substrate Capability Vector axes.

This structural separation ensures that the core specification remains stable while allowing the system to be expanded to new music substrates (e.g., specific sound chips or new MIR descriptors) without modifying the invariant model.

## Contents

- **[signals.md](signals.md)**: Catalog of all music-specific signals, including their source layer (Causal, Perceptual, or Symbolic).
- **[mappings.md](mappings.md)**: Domain-specific mapping rules that connect extracted signals to the 6 Substrate Capability Vector axes.

## Principles

- **Determinism**: All signal extractions must be reproducible and deterministic.
- **Signal-to-Axis Integrity**: Each domain signal must map to exactly one primary Substrate Capability Vector axis to maintain axis independence.
- **Substrate Awareness**: Signals may be derived from different layers (e.g., a "stiffness" ratio from perceptual audio or a "channel saturation" from causal chip register logs).

