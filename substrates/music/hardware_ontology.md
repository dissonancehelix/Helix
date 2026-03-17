# Sound Hardware & Driver Ontology

Helix treats sound chips and drivers as **Invariants**. A chip's architecture defines the physical constraint space, while a driver's code defines the musical interface for the composer.

## 1. Entity: `SoundChip`

### Core Properties
- `id`: Unique identifier (e.g., `music.sound_chip:ym2612`).
- `name`: Human-readable name (e.g., "Yamaha YM2612").
- `substrate`: Domain (always `music`).
- `synthesis_type`: `FM`, `PSG`, `PCM`, `Wavetable`, `Hybrid`.
- `clock_speed`: Native frequency (e.g., `7.67MHz`).
- `aliasing_invariant`: Characteristic distortion/artifacts (e.g., "9-bit DAC truncation").

### Components
A chip is a collection of components:
- `channels`: Total logical polyphony.
- `component_map`: Internal units (e.g., `8 LFOs`, `2 timers`, `1 noise generator`).
- `operator_structure`: For FM, the stack height (e.g., `4-op`).

## 2. Entity: `SoundDriver`

A software layer (usually Z80 or 68k code) that orchestrates the hardware. Drivers define the "Musical Interface" for the composer.

### Core Properties
- `id`: Unique identifier (e.g., `music.sound_driver:smps`).
- `name`: Human-readable name (e.g., "Sega Music Pre-processor System").
- `platform`: Primary platform (e.g., `Sega Genesis`).
- `language`: Code language (e.g., `Z80 Assembly`).
- `capabilities`: Features (e.g., `PCM playback`, `Dynamic FM patching`, `Stereo Panning`).

### Components
- `command_set`: List of macros/opcodes (e.g., `SetTempo`, `JumpLoop`).
- `envelope_logic`: How the driver handles software-level volume envelopes (if any).
- `pitch_tables`: Native frequency lookup tables (for tuning bias mapping).

## 3. Entity: `HardwareTopology`

A configuration of internal components. For FM, this is an "Algorithm".
- `id`: `music.topology:ym2151_alg0`.
- `description`: Signal flow description (e.g., "Linear stack").
- `carriers`: Slot indices outputting to audio.
- `modulators`: Slot indices modulating other operators.
- `feedback_path`: Index of operator with feedback.

## 4. Invariants

### Structural Invariants (Hardware)
- **Phase Wrapping**: How the phase accumulator resets.
- **Envelope Stepping**: The resolution of the ADSR curve.
- **Rate Scaling**: How frequency affects envelope speed.

### Behavioral Invariants (Hardware)
- **Register Write Lag**: Minimum time between commands before corruption.
- **Channel Pairing**: (e.g., YM2612 Channel 3 special mode).

### Driver Invariants (Software)
- **Vibrato LFO Depth**: Driver-level modulation vs hardware-level LFO.
- **Macro Sequence Pattern**: Rhythmic biases (e.g., SMPS rhythmic swing logic).
- **Patch Reuse Signature**: How the driver clusters FM patches globally.

## 5. Derived Measurements
- **Algorithm Complexity**: Weighted sum of modulators per carrier.
- **Carrier/Modulator Ratio**: Indicator of spectrum density.
- **Envelope Precision**: Measure of transient resolution.
- **Driver Overhead**: Cycles required per note-on (affects timing jitter).
