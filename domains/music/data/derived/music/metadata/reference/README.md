# Reference Tools

These repositories are checked out in `runtime/deps/helix_sources/sound_drivers/`
and serve as **source study material only** — chip behavior documentation,
register maps, format specs, and driver internals.

They are never imported at runtime.

| Repo | Location | Purpose |
|------|----------|---------|
| furnace | `runtime/deps/helix_sources/sound_drivers/furnace/` | Multi-chip tracker — chip emulation reference |
| mame | `runtime/deps/helix_sources/sound_drivers/mame/` | YM2612, SN76489, SPC700 cores |
| Dn-FamiTracker | `runtime/deps/helix_sources/sound_drivers/Dn-FamiTracker/` | NES APU reference |
| AddmusicK | `runtime/deps/helix_sources/sound_drivers/AddmusicK/` | SNES N-SPC engine reference |
| Echo | `runtime/deps/helix_sources/sound_drivers/Echo/` | Genesis SMPS-class driver |
| SMPSPlay | `runtime/deps/helix_sources/sound_drivers/SMPSPlay/` | SMPS format player |
| s2-sound-driver-plus | `runtime/deps/helix_sources/sound_drivers/s2-sound-driver-plus/` | Sonic 2 driver reference |
| MidiConverters | `runtime/deps/helix_sources/sound_drivers/MidiConverters/` | Format → MIDI conversion reference |
| ExtractorsDecoders | `runtime/deps/helix_sources/sound_drivers/ExtractorsDecoders/` | Proprietary format decoders |
| libADLMIDI | `runtime/deps/helix_sources/sound_drivers/libADLMIDI/` | OPL FM synthesis reference |


---

## Architecture Guardrail

**Helix Architecture Law**
`HSL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler`

* Operators orchestrate
* Adapters translate
* Toolkits execute
* Artifacts store results
* Atlas compiler creates entities

**Prohibited Patterns**
- `master_pipeline.py`
- Direct toolkit calls from operators
- Toolkits writing artifacts
- Toolkits writing Atlas entities
- Operators writing Atlas entities
- Monolithic pipelines

*All new modules must follow the template registry located in `runtime/templates/`.*
