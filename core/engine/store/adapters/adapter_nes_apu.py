"""
adapter_nes_apu.py — Helix adapter for NES APU (Ricoh 2A03 / 2A07)
====================================================================
Source references:
    NesDev wiki — wiki.nesdev.org/w/index.php/APU
    furnace src/engine/platform/nes.cpp/.h
    MAME src/devices/sound/nes_apu.cpp/.h

Purpose:
    Complete structural constants for the NES Audio Processing Unit.
    The APU is embedded in the Ricoh 2A03 (NTSC) and 2A07 (PAL) CPU
    packages. It provides 5 channels:

        CH1  Pulse 1   — variable duty, sweep, envelope, length counter
        CH2  Pulse 2   — same as Pulse 1 but no sweep hardware
        CH3  Triangle  — fixed 15-step waveform, linear + length counter
        CH4  Noise     — LFSR, envelope, length counter
        CH5  DMC       — delta-modulation PCM playback (7-bit, 1-bit deltas)

    These constants let Helix parse NSF/NES register streams at driver
    level — separating hardware synthesis parameters from composer intent.

Input:
    query (str) — one of:
        "clock"     — master clock constants, channel frequencies
        "registers" — complete register map with bit field descriptions
        "pulse"     — duty cycle table, sweep, envelope system
        "triangle"  — linear counter, length counter, frequency
        "noise"     — LFSR period tables (NTSC + PAL), mode
        "dmc"       — DMC rate tables, addressing, IRQ flags
        "length"    — length counter lookup table (32 entries)
        "frame"     — frame counter sequencer (4-step / 5-step)
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

# Ricoh 2A03 (NTSC) / 2A07 (PAL) CPU + APU clock
APU_CLOCK_NTSC   = 1_789_773    # Hz — NTSC (derived from 21.477272 MHz / 12)
APU_CLOCK_PAL    = 1_662_607    # Hz — PAL  (derived from 26.601712 MHz / 16)

# Pulse channel frequency formula:
#   f = APU_CLOCK / (16 × (period + 1))
# Triangle channel frequency formula:
#   f = APU_CLOCK / (32 × (period + 1))
# (Triangle runs at half the pulse rate because its sequencer has 32 steps)

PULSE_FREQ_FORMULA    = "f_hz = APU_CLOCK / (16 × (period + 1))"
TRIANGLE_FREQ_FORMULA = "f_hz = APU_CLOCK / (32 × (period + 1))"

# Minimum safe period (periods below this cause ultrasonic frequencies
# and are muted by the sweep unit on hardware):
PULSE_PERIOD_MIN  = 8    # periods ≤ 7 are muted by hardware
PULSE_PERIOD_MAX  = 0x7FF  # 11-bit timer

# ---------------------------------------------------------------------------
# Register map — all APU I/O registers ($4000–$4017)
# ---------------------------------------------------------------------------

# Format: address -> {name, bits, desc}
APU_REGISTERS: dict[int, dict] = {
    # --- Pulse 1 ($4000–$4003) ---
    0x4000: {
        "name": "SQ1_VOL",
        "channel": "pulse1",
        "bits": {
            "7-6": "duty    — duty cycle select (0=12.5%, 1=25%, 2=50%, 3=75% inverted)",
            "5":   "lc_halt — length counter halt / envelope loop flag",
            "4":   "const_v — constant volume flag (1=use bits 3-0 directly)",
            "3-0": "vol_env — volume (const_v=1) or envelope decay rate (const_v=0)",
        },
    },
    0x4001: {
        "name": "SQ1_SWEEP",
        "channel": "pulse1",
        "bits": {
            "7":   "enabled — sweep unit enable",
            "6-4": "period  — sweep divider period (P); sweep rate = P+1 half-frames",
            "3":   "negate  — negate flag (1=subtract; Pulse1 uses one's complement)",
            "2-0": "shift   — shift count (S); target = period >> S",
        },
    },
    0x4002: {
        "name": "SQ1_LO",
        "channel": "pulse1",
        "bits": {"7-0": "timer_lo — low 8 bits of 11-bit timer period"},
    },
    0x4003: {
        "name": "SQ1_HI",
        "channel": "pulse1",
        "bits": {
            "7-3": "lc_load  — length counter load index (5 bits → table lookup)",
            "2-0": "timer_hi — high 3 bits of 11-bit timer period; also resets phase",
        },
    },
    # --- Pulse 2 ($4004–$4007) — identical to Pulse 1 except sweep negate ---
    0x4004: {"name": "SQ2_VOL",   "channel": "pulse2",
             "bits": {"7-6": "duty", "5": "lc_halt", "4": "const_v", "3-0": "vol_env"}},
    0x4005: {"name": "SQ2_SWEEP", "channel": "pulse2",
             "bits": {"7": "enabled", "6-4": "period", "3": "negate (two's complement)", "2-0": "shift"}},
    0x4006: {"name": "SQ2_LO",    "channel": "pulse2", "bits": {"7-0": "timer_lo"}},
    0x4007: {"name": "SQ2_HI",    "channel": "pulse2",
             "bits": {"7-3": "lc_load", "2-0": "timer_hi"}},
    # --- Triangle ($4008–$400B) ---
    0x4008: {
        "name": "TRI_LINEAR",
        "channel": "triangle",
        "bits": {
            "7":   "ctrl_flag — length counter halt / linear counter control",
            "6-0": "lin_load  — linear counter reload value (7-bit)",
        },
    },
    0x4009: {"name": "TRI_UNUSED", "channel": "triangle", "bits": {"7-0": "unused"}},
    0x400A: {
        "name": "TRI_LO",
        "channel": "triangle",
        "bits": {"7-0": "timer_lo — low 8 bits of 11-bit timer period"},
    },
    0x400B: {
        "name": "TRI_HI",
        "channel": "triangle",
        "bits": {
            "7-3": "lc_load  — length counter load index",
            "2-0": "timer_hi — high 3 bits of timer; also triggers linear counter reload",
        },
    },
    # --- Noise ($400C–$400F) ---
    0x400C: {
        "name": "NOISE_VOL",
        "channel": "noise",
        "bits": {
            "5":   "lc_halt  — length counter halt / envelope loop",
            "4":   "const_v  — constant volume flag",
            "3-0": "vol_env  — volume or envelope decay rate",
        },
    },
    0x400D: {"name": "NOISE_UNUSED", "channel": "noise", "bits": {"7-0": "unused"}},
    0x400E: {
        "name": "NOISE_LO",
        "channel": "noise",
        "bits": {
            "7":   "loop_noise — noise mode: 0=long LFSR (32767-step), 1=short (93-step)",
            "3-0": "period     — period index into NOISE_PERIOD_TABLE",
        },
    },
    0x400F: {
        "name": "NOISE_HI",
        "channel": "noise",
        "bits": {"7-3": "lc_load — length counter load index"},
    },
    # --- DMC ($4010–$4013) ---
    0x4010: {
        "name": "DMC_FREQ",
        "channel": "dmc",
        "bits": {
            "7":   "irq_enable — DMC IRQ enable",
            "6":   "loop       — loop sample",
            "3-0": "rate_index — rate index into DMC_RATE_TABLE",
        },
    },
    0x4011: {
        "name": "DMC_RAW",
        "channel": "dmc",
        "bits": {"6-0": "direct_load — directly set output level (0–127)"},
    },
    0x4012: {
        "name": "DMC_START",
        "channel": "dmc",
        "bits": {"7-0": "addr_offset — sample address = 0xC000 + (addr_offset × 0x40)"},
    },
    0x4013: {
        "name": "DMC_LEN",
        "channel": "dmc",
        "bits": {"7-0": "length — sample length = (length × 0x10) + 1 bytes"},
    },
    # --- Control / Status ---
    0x4015: {
        "name": "SND_CHN",
        "channel": "control",
        "bits": {
            "4": "dmc_enable   — DMC enable (write) / DMC active (read)",
            "3": "noise_enable — Noise length counter enable",
            "2": "tri_enable   — Triangle length counter enable",
            "1": "sq2_enable   — Pulse 2 length counter enable",
            "0": "sq1_enable   — Pulse 1 length counter enable",
        },
    },
    0x4017: {
        "name": "FRAME_CNT",
        "channel": "control",
        "bits": {
            "7": "mode       — 0=4-step (60Hz IRQ), 1=5-step (no IRQ)",
            "6": "irq_inhibit — inhibit frame IRQ (mode=0 only)",
        },
    },
}

# ---------------------------------------------------------------------------
# Pulse channel — duty cycle waveforms
# ---------------------------------------------------------------------------

# Duty cycle sequences (8-step, MSB-first). 1 = high output, 0 = low.
# Source: NesDev wiki APU Pulse
PULSE_DUTY_SEQUENCES: dict[int, list[int]] = {
    0: [0, 0, 0, 0, 0, 0, 0, 1],   # 12.5%
    1: [0, 0, 0, 0, 0, 0, 1, 1],   # 25%
    2: [0, 0, 0, 0, 1, 1, 1, 1],   # 50%
    3: [1, 1, 1, 1, 1, 1, 0, 0],   # 75% (25% inverted)
}
PULSE_DUTY_PERCENT: dict[int, str] = {0: "12.5%", 1: "25%", 2: "50%", 3: "75%"}

# Sweep negate difference between Pulse 1 and Pulse 2:
# Pulse 1: target = current - (current >> shift) - 1  (one's complement, always -1 extra)
# Pulse 2: target = current - (current >> shift)       (two's complement)
PULSE1_SWEEP_NEGATE = "ones_complement"   # always 1 less than Pulse 2 in negate mode
PULSE2_SWEEP_NEGATE = "twos_complement"

# Envelope system — 4-bit decay counter (15 down to 0), reset by write to $4003/$4007
ENVELOPE_STEPS      = 16   # 0–15 (15 = loudest, 0 = silent)
ENVELOPE_DIVIDER_MAX = 15  # decay rate is 1/(rate+1) of frame counter period

# ---------------------------------------------------------------------------
# Triangle channel — fixed 32-step waveform
# ---------------------------------------------------------------------------

# Triangle waveform — 32 samples, output 0–15 then 15–0
TRIANGLE_SEQUENCE: list[int] = [
    15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0,
     0,  1,  2,  3,  4,  5, 6, 7, 8, 9,10,11,12,13,14,15,
]
TRIANGLE_STEPS      = 32
TRIANGLE_VOLUME     = 15    # fixed output level — no envelope on triangle
# Triangle is silenced when period < 2 (ultrasonic / popping prevention)
TRIANGLE_PERIOD_MIN = 2

# Linear counter: 7-bit down counter, reloaded from $4008 bits 6-0 on write to $400B.
# Counts down every frame tick; when it hits 0 the channel is silenced.
# ctrl_flag ($4008 bit 7) = 1 → counter is not decremented (halt)
LINEAR_COUNTER_BITS = 7
LINEAR_COUNTER_MAX  = 127  # 0x7F

# ---------------------------------------------------------------------------
# Noise channel — LFSR
# ---------------------------------------------------------------------------

# LFSR feedback:
#   Long mode  (bit 7=0): feedback = bit14 XOR bit13  → period 32767 steps
#   Short mode (bit 7=1): feedback = bit14 XOR bit6   → period 93 steps
NOISE_LFSR_BITS_LONG  = 15   # 15-bit LFSR
NOISE_LFSR_PERIOD_LONG  = 32767
NOISE_LFSR_PERIOD_SHORT = 93

# Noise period tables — timer period values for indices 0–15
# Frequency: f = APU_CLOCK / period
# Source: NesDev wiki APU Noise
NOISE_PERIOD_TABLE_NTSC: list[int] = [
    4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068
]
NOISE_PERIOD_TABLE_PAL: list[int] = [
    4, 8, 14, 30, 60, 88, 118, 148, 188, 236, 354, 472, 708, 944, 1890, 3778
]

# ---------------------------------------------------------------------------
# DMC channel — delta-modulation PCM
# ---------------------------------------------------------------------------

# DMC rate tables — timer period in CPU cycles between output bits
# Frequency: f = APU_CLOCK / rate  (effective sample rate per output bit)
# Source: NesDev wiki APU DMC
DMC_RATE_TABLE_NTSC: list[int] = [
    428, 380, 340, 320, 286, 254, 226, 214,
    190, 160, 142, 128, 106,  84,  72,  54
]
DMC_RATE_TABLE_PAL: list[int] = [
    398, 354, 316, 298, 276, 236, 210, 198,
    176, 148, 132, 118,  98,  78,  66,  50
]

# DMC output — 7-bit delta accumulator (0–127)
# Each sample bit: 1 = add 2 to output, 0 = subtract 2, clamped to [0, 127]
DMC_OUTPUT_BITS   = 7
DMC_OUTPUT_MAX    = 127
DMC_DELTA_STEP    = 2     # ± per bit
DMC_ADDR_BASE     = 0xC000  # base address for sample data
DMC_ADDR_SHIFT    = 6       # address = 0xC000 + (reg × 64)
DMC_LEN_MULTIPLIER = 16    # sample length = (reg × 16) + 1 bytes
DMC_LEN_ADDEND    = 1

# ---------------------------------------------------------------------------
# Length counter — 32-entry lookup table
# ---------------------------------------------------------------------------

# Write to $4003/$4007/$400B/$400F bits 7-3 loads this index.
# The length counter then decrements by 1 each half-frame (120Hz NTSC).
# When it reaches 0 the channel is silenced.
# Source: NesDev wiki APU Length Counter
LENGTH_COUNTER_TABLE: list[int] = [
    10, 254, 20,  2, 40,  4, 80,  6,
   160,   8, 60, 10, 14, 12, 26, 14,
    12,  16, 24, 18, 48, 20, 96, 22,
   192,  24, 72, 26, 16, 28, 32, 30,
]
LENGTH_COUNTER_ENTRIES = 32

# ---------------------------------------------------------------------------
# Frame counter sequencer
# ---------------------------------------------------------------------------

# Two sequencer modes selected by $4017 bit 7.
# Each step generates clocks for: envelope / linear counter (E) and/or length / sweep (L).
# Source: NesDev wiki APU Frame Counter

# 4-step mode: 4 steps at 240Hz (NTSC), generates frame IRQ at step 4
FRAME_4STEP_NTSC_HZ  = 240.0     # approximate; each step = 7457 CPU cycles
FRAME_4STEP_CYCLES: list[int] = [7457, 14913, 22371, 29829]   # cycle counts per step
FRAME_4STEP_CLOCKS: list[dict] = [
    {"step": 1, "cycles": 7457,  "envelope": True,  "length_sweep": False},
    {"step": 2, "cycles": 14913, "envelope": True,  "length_sweep": True},
    {"step": 3, "cycles": 22371, "envelope": True,  "length_sweep": False},
    {"step": 4, "cycles": 29829, "envelope": True,  "length_sweep": True, "irq": True},
]

# 5-step mode: 5 steps, no IRQ, first step of each pair is silent (no clocks)
FRAME_5STEP_CLOCKS: list[dict] = [
    {"step": 1, "cycles": 7457,  "envelope": True,  "length_sweep": False},
    {"step": 2, "cycles": 14913, "envelope": True,  "length_sweep": True},
    {"step": 3, "cycles": 22371, "envelope": True,  "length_sweep": False},
    {"step": 4, "cycles": 29829, "envelope": False, "length_sweep": False},  # silent
    {"step": 5, "cycles": 37281, "envelope": True,  "length_sweep": True},
]

# ---------------------------------------------------------------------------
# Channel output mixing
# ---------------------------------------------------------------------------

# APU mixing is non-linear (lookup table on hardware).
# Pulse channels share one table; triangle/noise/DMC share another.
# Approximation: mixed = pulse_out + tnd_out where:
#   pulse_out = 95.88 / (8128 / (pulse1 + pulse2) + 100)
#   tnd_out   = 159.79 / (1 / (tri/8227 + noise/12241 + dmc/22638) + 100)
# Source: NesDev wiki APU Mixer
APU_PULSE_MIX_NUMERATOR    = 95.88
APU_PULSE_MIX_DENOMINATOR  = 8128
APU_PULSE_MIX_OFFSET       = 100
APU_TND_MIX_NUMERATOR      = 159.79
APU_TRI_DIVISOR            = 8227
APU_NOISE_DIVISOR          = 12241
APU_DMC_DIVISOR            = 22638
APU_TND_MIX_OFFSET         = 100


class Adapter:
    """
    Adapter exposing complete NES APU (2A03/2A07) structural constants.

    Covers: clock derivation, full register map with bit fields, pulse duty
    cycles and sweep behaviour, triangle 32-step sequence and linear counter,
    noise LFSR modes and period tables (NTSC + PAL), DMC rate tables and delta
    encoding, length counter lookup table, frame counter sequencer (4/5-step),
    and non-linear mixing approximation constants.

    Correct call path:
        HSL → ANALYZE_TRACK operator → Adapter → NES APU constants
    """
    toolkit   = "nes_apu"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.query(payload.get("query", "all"))

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return NES APU structural constants.

        Args:
            what: "clock" | "registers" | "pulse" | "triangle" | "noise" |
                  "dmc" | "length" | "frame" | "all"
        """
        base: dict[str, Any] = {"chip": "NES_APU_2A03", "adapter": "nes_apu"}

        if what in ("clock", "all"):
            base.update({
                "apu_clock_ntsc":        APU_CLOCK_NTSC,
                "apu_clock_pal":         APU_CLOCK_PAL,
                "pulse_freq_formula":    PULSE_FREQ_FORMULA,
                "triangle_freq_formula": TRIANGLE_FREQ_FORMULA,
                "pulse_period_min":      PULSE_PERIOD_MIN,
                "pulse_period_max":      PULSE_PERIOD_MAX,
            })

        if what in ("registers", "all"):
            base.update({"registers": APU_REGISTERS})

        if what in ("pulse", "all"):
            base.update({
                "duty_sequences":       PULSE_DUTY_SEQUENCES,
                "duty_percent":         PULSE_DUTY_PERCENT,
                "pulse1_sweep_negate":  PULSE1_SWEEP_NEGATE,
                "pulse2_sweep_negate":  PULSE2_SWEEP_NEGATE,
                "envelope_steps":       ENVELOPE_STEPS,
                "envelope_divider_max": ENVELOPE_DIVIDER_MAX,
            })

        if what in ("triangle", "all"):
            base.update({
                "triangle_sequence":  TRIANGLE_SEQUENCE,
                "triangle_steps":     TRIANGLE_STEPS,
                "triangle_volume":    TRIANGLE_VOLUME,
                "triangle_period_min": TRIANGLE_PERIOD_MIN,
                "linear_counter_bits": LINEAR_COUNTER_BITS,
                "linear_counter_max":  LINEAR_COUNTER_MAX,
            })

        if what in ("noise", "all"):
            base.update({
                "noise_lfsr_bits":         NOISE_LFSR_BITS_LONG,
                "noise_lfsr_period_long":  NOISE_LFSR_PERIOD_LONG,
                "noise_lfsr_period_short": NOISE_LFSR_PERIOD_SHORT,
                "noise_period_ntsc":       NOISE_PERIOD_TABLE_NTSC,
                "noise_period_pal":        NOISE_PERIOD_TABLE_PAL,
            })

        if what in ("dmc", "all"):
            base.update({
                "dmc_rate_ntsc":       DMC_RATE_TABLE_NTSC,
                "dmc_rate_pal":        DMC_RATE_TABLE_PAL,
                "dmc_output_bits":     DMC_OUTPUT_BITS,
                "dmc_output_max":      DMC_OUTPUT_MAX,
                "dmc_delta_step":      DMC_DELTA_STEP,
                "dmc_addr_base":       DMC_ADDR_BASE,
                "dmc_addr_shift":      DMC_ADDR_SHIFT,
                "dmc_len_multiplier":  DMC_LEN_MULTIPLIER,
                "dmc_len_addend":      DMC_LEN_ADDEND,
            })

        if what in ("length", "all"):
            base.update({
                "length_counter_table":   LENGTH_COUNTER_TABLE,
                "length_counter_entries": LENGTH_COUNTER_ENTRIES,
            })

        if what in ("frame", "all"):
            base.update({
                "frame_4step_hz":     FRAME_4STEP_NTSC_HZ,
                "frame_4step_cycles": FRAME_4STEP_CYCLES,
                "frame_4step_clocks": FRAME_4STEP_CLOCKS,
                "frame_5step_clocks": FRAME_5STEP_CLOCKS,
            })

        return base

    def pulse_frequency(self, period: int, region: str = "ntsc") -> float:
        """Compute pulse channel output frequency from 11-bit timer period."""
        if period < PULSE_PERIOD_MIN:
            return 0.0   # hardware mutes below minimum
        clock = APU_CLOCK_NTSC if region == "ntsc" else APU_CLOCK_PAL
        return clock / (16.0 * (period + 1))

    def triangle_frequency(self, period: int, region: str = "ntsc") -> float:
        """Compute triangle channel output frequency from 11-bit timer period."""
        if period < TRIANGLE_PERIOD_MIN:
            return 0.0
        clock = APU_CLOCK_NTSC if region == "ntsc" else APU_CLOCK_PAL
        return clock / (32.0 * (period + 1))

    def noise_frequency(self, rate_index: int, region: str = "ntsc") -> float:
        """Compute noise LFSR clock frequency from period table index."""
        table = NOISE_PERIOD_TABLE_NTSC if region == "ntsc" else NOISE_PERIOD_TABLE_PAL
        if not 0 <= rate_index < len(table):
            raise AdapterError(f"noise rate_index must be 0–15, got {rate_index}")
        clock = APU_CLOCK_NTSC if region == "ntsc" else APU_CLOCK_PAL
        return clock / table[rate_index]

    def dmc_sample_rate(self, rate_index: int, region: str = "ntsc") -> float:
        """Compute DMC output sample rate from rate table index."""
        table = DMC_RATE_TABLE_NTSC if region == "ntsc" else DMC_RATE_TABLE_PAL
        if not 0 <= rate_index < len(table):
            raise AdapterError(f"DMC rate_index must be 0–15, got {rate_index}")
        clock = APU_CLOCK_NTSC if region == "ntsc" else APU_CLOCK_PAL
        return clock / table[rate_index]

    def dmc_sample_address(self, reg_value: int) -> int:
        """Compute DMC sample start address from $4012 register value."""
        return DMC_ADDR_BASE + (reg_value * (1 << DMC_ADDR_SHIFT))

    def dmc_sample_length(self, reg_value: int) -> int:
        """Compute DMC sample byte length from $4013 register value."""
        return (reg_value * DMC_LEN_MULTIPLIER) + DMC_LEN_ADDEND

    def length_counter_value(self, index: int) -> int:
        """Look up length counter from 5-bit write index."""
        if not 0 <= index < LENGTH_COUNTER_ENTRIES:
            raise AdapterError(f"length counter index must be 0–31, got {index}")
        return LENGTH_COUNTER_TABLE[index]

    def is_available(self) -> bool:
        return True
