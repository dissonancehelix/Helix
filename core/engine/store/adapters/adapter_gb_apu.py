"""
adapter_gb_apu.py — Helix adapter for Game Boy DMG / CGB APU
=============================================================
Source references:
    pandocs — gbdev.io/pandocs/Sound_Controller.html
    furnace src/engine/platform/gb.cpp/.h
    MAME src/devices/sound/gb.cpp/.h

Purpose:
    Complete structural constants for the Game Boy Audio Processing Unit.
    Present in all Game Boy variants: DMG (original), MGB (Pocket),
    SGB, CGB (Color), GBA (with minor differences).

    Four channels:
        CH1  Pulse + Sweep  — variable duty, frequency sweep, envelope, length
        CH2  Pulse          — same as CH1 without frequency sweep
        CH3  Wave           — 32 4-bit samples from wave RAM
        CH4  Noise          — LFSR, envelope, length counter

    All registers are memory-mapped at $FF10–$FF3F plus $FF76/$FF77 (CGB PCM).

Input:
    query (str) — one of:
        "clock"     — master clock, frequency derivation
        "registers" — complete register map with bit field descriptions
        "ch1"       — Pulse+Sweep channel: duty, sweep, envelope
        "ch2"       — Pulse channel: duty, envelope
        "ch3"       — Wave channel: wave RAM, output levels
        "ch4"       — Noise channel: LFSR, period table
        "control"   — NR50/NR51/NR52 master control registers
        "all"       — everything

Adapter rules:
    • No Helix logic. Static constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Clock constants
# ---------------------------------------------------------------------------

# DMG master clock: 4.194304 MHz (4 × 1.048576 MHz)
# CGB can run in double-speed (8.388608 MHz CPU) but APU clock stays at 4.194304 MHz.
APU_MASTER_CLOCK_HZ = 4_194_304     # Hz — DMG/CGB APU master clock

# Channel frequency formula (CH1, CH2, CH3):
#   f = 131072 / (2048 - X)  Hz   where X is the 11-bit period value
# Rewritten: X = 2048 - 131072 / f
FREQ_FORMULA      = "f_hz = 131072 / (2048 - period)"
FREQ_PERIOD_MAX   = 2047   # 11-bit period maximum (stored as ~period, so lower = higher pitch)
FREQ_PERIOD_WRITE = "period written as two parts: NRx3 (low 8 bits) + NRx4 (high 3 bits)"

# Wave channel (CH3) frequency is one octave lower than the formula above
# because its 32-step sequencer runs at half the rate of the 8-step pulse sequencers.
# Effective formula is still f = 131072 / (2048 - X) because the wave step
# rate is 2 MHz / (2048 - X) which with 32 steps → f = 2097152 / (32 × (2048 - X)) = 65536 / (2048 - X)
# Note: many sources give CH3 freq as 65536 / (2048 - X). Pandocs is authoritative:
#   "The wave channel's frequency timer period is 4 × (2048 - period)"
#   wave step rate = CPU_CLOCK / (4 × (2048 - period)) / 32 steps
#   → output freq = APU_CLOCK / (128 × (2048 - period))  ← 32 steps × 4 multiplier
# In practice output fundamental = f_pulse / 2 for same period value.
WAVE_FREQ_FORMULA = "f_hz = 65536 / (2048 - period)   (one octave below pulse formula)"

# CH4 noise frequency formula:
#   f = 524288 / r / 2^(s+1)
#   where r = noise divisor from NOISE_DIVISORS table, s = clock shift (0-13)
NOISE_FREQ_FORMULA = "f_hz = 524288 / r / 2^(s+1)"
NOISE_DIVISORS: list[int] = [8, 16, 32, 48, 64, 80, 96, 112]
# Index 0 is special: r=0.5 on hardware (equivalent to r=8 with doubled numerator)
# Common representation: treat index 0 as if 524288 × 2 / 2^(s+1)
NOISE_DIVISOR_ZERO_FACTOR = 2   # multiply 524288 by 2 when divisor code = 0

# ---------------------------------------------------------------------------
# Register map — all APU registers ($FF10–$FF3F)
# ---------------------------------------------------------------------------

APU_REGISTERS: dict[int, dict] = {
    # --- CH1: Pulse + Sweep ---
    0xFF10: {
        "name": "NR10", "channel": "ch1",
        "bits": {
            "6-4": "sweep_period — sweep timer period (0=sweep disabled)",
            "3":   "sweep_negate — 0=increase frequency, 1=decrease",
            "2-0": "sweep_shift  — frequency change per step: Δ = freq >> shift",
        },
    },
    0xFF11: {
        "name": "NR11", "channel": "ch1",
        "bits": {
            "7-6": "duty   — duty cycle (0=12.5%, 1=25%, 2=50%, 3=75%)",
            "5-0": "length — initial length timer (64 - length ticks before auto-stop)",
        },
    },
    0xFF12: {
        "name": "NR12", "channel": "ch1",
        "bits": {
            "7-4": "init_vol  — initial volume (0=no sound, 15=max)",
            "3":   "env_dir   — envelope direction (0=decrease, 1=increase)",
            "2-0": "env_sweep — envelope sweep period (0=disabled); steps in 1/64s units",
        },
    },
    0xFF13: {
        "name": "NR13", "channel": "ch1", "write_only": True,
        "bits": {"7-0": "freq_lo — low 8 bits of 11-bit period"},
    },
    0xFF14: {
        "name": "NR14", "channel": "ch1",
        "bits": {
            "7":   "trigger      — write 1 to restart channel",
            "6":   "length_enable — stop when length counter expires",
            "2-0": "freq_hi      — high 3 bits of 11-bit period",
        },
    },
    # --- CH2: Pulse (no sweep) ---
    0xFF16: {
        "name": "NR21", "channel": "ch2",
        "bits": {
            "7-6": "duty",
            "5-0": "length",
        },
    },
    0xFF17: {
        "name": "NR22", "channel": "ch2",
        "bits": {"7-4": "init_vol", "3": "env_dir", "2-0": "env_sweep"},
    },
    0xFF18: {"name": "NR23", "channel": "ch2", "write_only": True,
             "bits": {"7-0": "freq_lo"}},
    0xFF19: {
        "name": "NR24", "channel": "ch2",
        "bits": {"7": "trigger", "6": "length_enable", "2-0": "freq_hi"},
    },
    # --- CH3: Wave ---
    0xFF1A: {
        "name": "NR30", "channel": "ch3",
        "bits": {"7": "dac_power — 0=channel off, 1=DAC on"},
    },
    0xFF1B: {
        "name": "NR31", "channel": "ch3",
        "bits": {"7-0": "length — length timer (256 - length ticks before stop)"},
    },
    0xFF1C: {
        "name": "NR32", "channel": "ch3",
        "bits": {
            "6-5": "output_level — 0=mute, 1=100%, 2=50% (>>1), 3=25% (>>2)",
        },
    },
    0xFF1D: {"name": "NR33", "channel": "ch3", "write_only": True,
             "bits": {"7-0": "freq_lo"}},
    0xFF1E: {
        "name": "NR34", "channel": "ch3",
        "bits": {"7": "trigger", "6": "length_enable", "2-0": "freq_hi"},
    },
    # --- CH4: Noise ---
    0xFF20: {
        "name": "NR41", "channel": "ch4",
        "bits": {"5-0": "length — length timer (64 - length ticks before stop)"},
    },
    0xFF21: {
        "name": "NR42", "channel": "ch4",
        "bits": {"7-4": "init_vol", "3": "env_dir", "2-0": "env_sweep"},
    },
    0xFF22: {
        "name": "NR43", "channel": "ch4",
        "bits": {
            "7-4": "clock_shift  — s in frequency formula (0-13 effective)",
            "3":   "lfsr_width   — 0=15-bit LFSR (long), 1=7-bit LFSR (short)",
            "2-0": "divisor_code — r index into NOISE_DIVISORS table",
        },
    },
    0xFF23: {
        "name": "NR44", "channel": "ch4",
        "bits": {"7": "trigger", "6": "length_enable"},
    },
    # --- Master control ---
    0xFF24: {
        "name": "NR50", "channel": "control",
        "bits": {
            "7":   "vin_left   — mix VIN signal into left output",
            "6-4": "vol_left   — master volume left (0=mute, 7=max)",
            "3":   "vin_right  — mix VIN signal into right output",
            "2-0": "vol_right  — master volume right",
        },
    },
    0xFF25: {
        "name": "NR51", "channel": "control",
        "bits": {
            "7": "ch4_left", "6": "ch3_left", "5": "ch2_left", "4": "ch1_left",
            "3": "ch4_right","2": "ch3_right","1": "ch2_right","0": "ch1_right",
        },
    },
    0xFF26: {
        "name": "NR52", "channel": "control",
        "bits": {
            "7":   "apu_power  — 0=all APU off and registers cleared",
            "3":   "ch4_active — read-only: 1 if CH4 length counter > 0",
            "2":   "ch3_active — read-only",
            "1":   "ch2_active — read-only",
            "0":   "ch1_active — read-only",
        },
    },
}

# Wave RAM: 16 bytes at $FF30–$FF3F = 32 4-bit samples packed high-nibble first
WAVE_RAM_START      = 0xFF30
WAVE_RAM_END        = 0xFF3F
WAVE_RAM_BYTES      = 16
WAVE_SAMPLES        = 32   # two 4-bit samples per byte; high nibble plays first
WAVE_SAMPLE_BITS    = 4
WAVE_SAMPLE_MAX     = 15

# ---------------------------------------------------------------------------
# CH1 / CH2 — duty cycles
# ---------------------------------------------------------------------------

# Duty cycle waveforms — 8 steps, 1=high output, 0=low
# Source: pandocs APU Duty Cycle
DUTY_SEQUENCES: dict[int, list[int]] = {
    0: [0, 0, 0, 0, 0, 0, 0, 1],   # 12.5%
    1: [1, 0, 0, 0, 0, 0, 0, 1],   # 25%
    2: [1, 0, 0, 0, 0, 1, 1, 1],   # 50%
    3: [0, 1, 1, 1, 1, 1, 1, 0],   # 75%
}
DUTY_PERCENT: dict[int, str] = {0: "12.5%", 1: "25%", 2: "50%", 3: "75%"}

# ---------------------------------------------------------------------------
# CH1 — frequency sweep
# ---------------------------------------------------------------------------

# Sweep timer: clocked at 128Hz (APU_CLOCK / 32768)
# Each clock: new_freq = freq ± (freq >> shift)
# If new_freq > 2047 → channel is disabled (overflow)
# negate=1: new_freq = freq - (freq >> shift)  (decrease)
# negate=0: new_freq = freq + (freq >> shift)  (increase)
SWEEP_CLOCK_HZ      = 128    # Hz (APU_CLOCK / 32768)
SWEEP_PERIOD_MAX    = 7      # 3-bit field; 0 disables sweep timer
SWEEP_SHIFT_MAX     = 7      # 3-bit field
SWEEP_FREQ_MAX      = 2047   # overflow limit: disables channel

# ---------------------------------------------------------------------------
# Envelope system (CH1, CH2, CH4)
# ---------------------------------------------------------------------------

# Envelope clocked at 64Hz (APU_CLOCK / 65536)
# Volume increments or decrements by 1 each period tick
# Clamped at [0, 15]; stops when it hits a boundary
ENVELOPE_CLOCK_HZ   = 64     # Hz
ENVELOPE_STEPS      = 16     # 0–15
ENVELOPE_PERIOD_MAX = 7      # 3-bit field; 0 disables envelope clock

# DAC enable rule: if init_vol=0 AND env_dir=0 → DAC is off (channel silenced)
# This is why many GB composers set env_dir=1 for constant-volume sounds:
# it prevents the DAC-off behaviour.
DAC_ENABLE_NOTE = (
    "DAC is off when init_vol=0 AND env_dir=decrease (0). "
    "Set env_dir=1 (increase) with init_vol=0 for a DAC-on zero-volume state."
)

# ---------------------------------------------------------------------------
# CH3 — wave output levels
# ---------------------------------------------------------------------------

# Output level register NR32 bits 6-5:
WAVE_OUTPUT_LEVELS: dict[int, str] = {
    0: "mute (0%)",
    1: "100% — samples played as-is",
    2: "50%  — samples right-shifted 1 bit",
    3: "25%  — samples right-shifted 2 bits",
}

# Length counter maximum for CH3 is 256 (8-bit), unlike other channels (64)
WAVE_LENGTH_MAX     = 256
PULSE_LENGTH_MAX    = 64
NOISE_LENGTH_MAX    = 64

# ---------------------------------------------------------------------------
# CH4 — noise LFSR
# ---------------------------------------------------------------------------

# LFSR feedback taps:
#   15-bit mode: bit14 XOR bit13 → fed back to bit14 (long period: 32767 steps)
#    7-bit mode: bit6  XOR bit5  → fed back to bit6  (short period: 127 steps)
NOISE_LFSR_BITS_LONG     = 15
NOISE_LFSR_BITS_SHORT    = 7
NOISE_LFSR_PERIOD_LONG   = 32767
NOISE_LFSR_PERIOD_SHORT  = 127

# ---------------------------------------------------------------------------
# Frame sequencer — clocked at 512Hz (APU_CLOCK / 8192)
# ---------------------------------------------------------------------------

FRAME_SEQ_CLOCK_HZ   = 512    # Hz — frame sequencer master rate
FRAME_SEQ_DIVIDER    = 8192   # APU_CLOCK / 8192 = 512 Hz

# Which subsystem clocks at which frame step (step 0–7, 8-frame cycle = 512Hz / 8)
# length  = 256Hz (every other step)
# sweep   = 128Hz (steps 2 and 6)
# envelope = 64Hz (step 7)
FRAME_SEQ_STEPS: list[dict] = [
    {"step": 0, "length": True,  "sweep": False, "envelope": False},
    {"step": 1, "length": False, "sweep": False, "envelope": False},
    {"step": 2, "length": True,  "sweep": True,  "envelope": False},
    {"step": 3, "length": False, "sweep": False, "envelope": False},
    {"step": 4, "length": True,  "sweep": False, "envelope": False},
    {"step": 5, "length": False, "sweep": False, "envelope": False},
    {"step": 6, "length": True,  "sweep": True,  "envelope": False},
    {"step": 7, "length": False, "sweep": False, "envelope": True},
]
FRAME_SEQ_LENGTH_HZ  = 256    # length counter decrement rate
FRAME_SEQ_SWEEP_HZ   = 128    # sweep unit clock rate
FRAME_SEQ_ENVELOPE_HZ = 64    # envelope clock rate


class Adapter:
    """
    Adapter exposing complete Game Boy DMG/CGB APU structural constants.

    Covers: master clock, full register map with bit fields, pulse duty cycles,
    CH1 frequency sweep behaviour, envelope system (CH1/CH2/CH4), wave channel
    sample RAM layout and output levels, noise LFSR modes and divisor table,
    frame sequencer step table.

    Correct call path:
        HSL → ANALYZE_TRACK operator → Adapter → GB APU constants
    """
    toolkit   = "gb_apu"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.query(payload.get("query", "all"))

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return Game Boy APU structural constants.

        Args:
            what: "clock" | "registers" | "ch1" | "ch2" | "ch3" | "ch4" |
                  "control" | "all"
        """
        base: dict[str, Any] = {"chip": "GB_APU_DMG", "adapter": "gb_apu"}

        if what in ("clock", "all"):
            base.update({
                "apu_master_clock_hz": APU_MASTER_CLOCK_HZ,
                "freq_formula":        FREQ_FORMULA,
                "wave_freq_formula":   WAVE_FREQ_FORMULA,
                "noise_freq_formula":  NOISE_FREQ_FORMULA,
                "freq_period_max":     FREQ_PERIOD_MAX,
            })

        if what in ("registers", "all"):
            base.update({
                "registers":     APU_REGISTERS,
                "wave_ram_start": WAVE_RAM_START,
                "wave_ram_end":   WAVE_RAM_END,
                "wave_ram_bytes": WAVE_RAM_BYTES,
                "wave_samples":   WAVE_SAMPLES,
            })

        if what in ("ch1", "all"):
            base.update({
                "duty_sequences":     DUTY_SEQUENCES,
                "duty_percent":       DUTY_PERCENT,
                "sweep_clock_hz":     SWEEP_CLOCK_HZ,
                "sweep_period_max":   SWEEP_PERIOD_MAX,
                "sweep_shift_max":    SWEEP_SHIFT_MAX,
                "sweep_freq_max":     SWEEP_FREQ_MAX,
                "envelope_clock_hz":  ENVELOPE_CLOCK_HZ,
                "envelope_steps":     ENVELOPE_STEPS,
                "envelope_period_max": ENVELOPE_PERIOD_MAX,
                "dac_enable_note":    DAC_ENABLE_NOTE,
            })

        if what in ("ch2", "all"):
            base.update({
                "duty_sequences":     DUTY_SEQUENCES,
                "duty_percent":       DUTY_PERCENT,
                "envelope_clock_hz":  ENVELOPE_CLOCK_HZ,
                "envelope_steps":     ENVELOPE_STEPS,
                "envelope_period_max": ENVELOPE_PERIOD_MAX,
                "dac_enable_note":    DAC_ENABLE_NOTE,
            })

        if what in ("ch3", "all"):
            base.update({
                "wave_output_levels": WAVE_OUTPUT_LEVELS,
                "wave_length_max":    WAVE_LENGTH_MAX,
                "wave_ram_start":     WAVE_RAM_START,
                "wave_ram_bytes":     WAVE_RAM_BYTES,
                "wave_samples":       WAVE_SAMPLES,
                "wave_sample_bits":   WAVE_SAMPLE_BITS,
                "wave_sample_max":    WAVE_SAMPLE_MAX,
                "wave_freq_formula":  WAVE_FREQ_FORMULA,
            })

        if what in ("ch4", "all"):
            base.update({
                "noise_divisors":          NOISE_DIVISORS,
                "noise_divisor_zero_factor": NOISE_DIVISOR_ZERO_FACTOR,
                "noise_freq_formula":      NOISE_FREQ_FORMULA,
                "noise_lfsr_bits_long":    NOISE_LFSR_BITS_LONG,
                "noise_lfsr_bits_short":   NOISE_LFSR_BITS_SHORT,
                "noise_lfsr_period_long":  NOISE_LFSR_PERIOD_LONG,
                "noise_lfsr_period_short": NOISE_LFSR_PERIOD_SHORT,
                "noise_length_max":        NOISE_LENGTH_MAX,
            })

        if what in ("control", "all"):
            base.update({
                "frame_seq_clock_hz":   FRAME_SEQ_CLOCK_HZ,
                "frame_seq_divider":    FRAME_SEQ_DIVIDER,
                "frame_seq_steps":      FRAME_SEQ_STEPS,
                "frame_seq_length_hz":  FRAME_SEQ_LENGTH_HZ,
                "frame_seq_sweep_hz":   FRAME_SEQ_SWEEP_HZ,
                "frame_seq_envelope_hz": FRAME_SEQ_ENVELOPE_HZ,
                "pulse_length_max":     PULSE_LENGTH_MAX,
                "wave_length_max":      WAVE_LENGTH_MAX,
                "noise_length_max":     NOISE_LENGTH_MAX,
            })

        return base

    def channel_frequency(self, period: int) -> float:
        """Compute CH1/CH2/CH3 output frequency from 11-bit period value."""
        if period >= 2048:
            raise AdapterError(f"period must be 0–2047, got {period}")
        denom = 2048 - period
        if denom <= 0:
            return 0.0
        return 131072.0 / denom

    def noise_frequency(self, divisor_code: int, clock_shift: int) -> float:
        """Compute CH4 noise LFSR clock frequency."""
        if not 0 <= divisor_code <= 7:
            raise AdapterError(f"divisor_code must be 0–7, got {divisor_code}")
        if not 0 <= clock_shift <= 13:
            raise AdapterError(f"clock_shift must be 0–13, got {clock_shift}")
        r = NOISE_DIVISORS[divisor_code] if divisor_code > 0 else NOISE_DIVISORS[0] / 2
        return 524288.0 / r / (2 ** (clock_shift + 1))

    def period_from_frequency(self, freq_hz: float) -> int:
        """Compute 11-bit period register value from desired output frequency."""
        if freq_hz <= 0:
            return 2047
        raw = 2048 - (131072.0 / freq_hz)
        return max(0, min(2047, round(raw)))

    def is_available(self) -> bool:
        return True
