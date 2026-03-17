# REGIME: VGM LOOP STRUCTURES

**Type**: Regime  
**Status**: Exploratory  
**Origin**: Helix Music Lab  
**Domain Coverage**: Ludomusicology (VGM Substrate Focus)  

## Description

VGM Loop Structures describe the identified phases of interactive music behavior, specifically how tracks handle the transition from the **Intro** section to the **Loop** section.

## Mechanism

Analysis identifies transition points in VGM file streams:
- **Intro Phase**: High energy, establishment of melodic motifs.
- **Loop Phase**: Harmonic stability, repetitive rhythmic density.
- **Transition Point**: Often marked by a specific register reset or jump command in the sound driver (e.g., SMPS $E0 jump).

## Indicators

- `loop_length`
- `intro_vs_loop_contrast`
- `arrangement_density_stability`

## Falsifiers

- Music that does not use loops (e.g., cinematic cutscene scores with linear progression).
- Generative music where boundaries are fluid rather than fixed commands.

## Linked Experiments

- [music_symbolic_analysis](file:///c:/Users/dissonance/Desktop/Helix/labs/music_lab/experiments/music_symbolic_analysis.py)
- [motif_network_analysis](file:///c:/Users/dissonance/Desktop/Helix/labs/music_lab/experiments/motif_network_analysis.py)
