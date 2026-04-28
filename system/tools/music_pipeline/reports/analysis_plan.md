# deep Analysis Processing Priority Plan

To optimize the extraction of structural and synthesis data, deep analysis should proceed in the following order:

1. **VGM / VGZ**: Canonical chip instruction logs. Best for FM patch reconstruction and cycle-accurate behavior.
2. **SPC**: SNES memory/DSP dumps. High priority for sample library extraction and rhythm analysis.
3. **2SF / NCSF**: DS/3DS sequence formats. Rich in instrument and MIDI-like command data.
4. **USF / GSF**: N64/GBA memory traces.
5. **PSF / PSF2**: PlayStation sequence/driver bundles.
6. **S98**: PC-98 and other Japanese computer formats.
7. **Rendered Audio (Opus / MP3 / FLAC)**: Use for acoustic profiling, genre classification, and audio-based similarity when instructions are unavailable.

## Next Step
- Initialize Deep Extraction for VGM corpus (Sonic 3 & Knuckles focus).
