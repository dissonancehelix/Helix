"""
adapter_ay8910.py — Helix adapter for AY-3-8910 / YM2149 PSG
=============================================================
Source references:
    General Instrument AY-3-8910/8912 datasheet
    Yamaha YM2149 datasheet
    furnace src/engine/platform/ay.cpp/.h  (AY8914RegRemap, PSGMode bits)
    MAME src/devices/sound/ay8910.cpp/.h

Purpose:
    Complete structural constants for the AY-3-8910 Programmable Sound
    Generator and its pin-compatible equivalent the Yamaha YM2149.

    The chip provides:
        3 tone channels (A, B, C) — 12-bit square wave period dividers
        1 noise generator         — 5-bit period divider, LFSR output
        1 envelope generator      — 16-bit period, 10 distinct shapes
        2 I/O ports               — not audio; ignored here

    Used in: ZX Spectrum 128k, Atari ST, MSX (many), Amstrad CPC, Vectrex,
    Intellivision, arcade boards (Konami, Taito), Famicom (AY via mapper),
    and dozens of other platforms. The YM2149 variant is used in the Atari
    ST and some arcade boards; it is functionally identical but with a
    different pin mapping and optional clock divider (/2 mode).

Input:
    query (str) — one of:
        "clock"     — platform clock variants, frequency derivation
        "registers" — complete 16-register map with bit field descriptions
        "tone"      — tone channel period/frequency, mixer control
        "noise"     — noise generator period, LFSR
        "envelope"  — envelope generator: shapes, period, volume interaction
        "volume"    — 4-bit volume table, amplitude modes
        "ym2149"    — YM2149-specific differences (AY8914 remap, /2 mode)
        "all"       — everything

Adapter rules:
    • No Helix logic. Static constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Clock constants — platform-specific variants
# ---------------------------------------------------------------------------

# The AY-3-8910 and YM2149 accept a wide range of input clocks.
# All frequency calculations below use clock_hz as a parameter.
# Common platform clocks:
CLOCK_VARIANTS: dict[str, dict] = {
    "zx_spectrum_128k":  {"clock_hz": 1_773_400,  "platform": "ZX Spectrum 128k / +2 / +3"},
    "atari_st":          {"clock_hz": 2_000_000,  "platform": "Atari ST (YM2149, /2 mode off → effective 2 MHz)"},
    "msx":               {"clock_hz": 1_789_772,  "platform": "MSX (derived from NTSC 3.579545 MHz ÷ 2)"},
    "amstrad_cpc":       {"clock_hz": 1_000_000,  "platform": "Amstrad CPC (1 MHz from 4 MHz ÷ 4)"},
    "vectrex":           {"clock_hz": 1_500_000,  "platform": "Vectrex (1.5 MHz)"},
    "intellivision":     {"clock_hz": 894_886,    "platform": "Intellivision (AY-3-8914 variant, ~895 kHz)"},
    "arcade_konami":     {"clock_hz": 1_789_772,  "platform": "Konami arcade boards"},
    "ym2149_genesis":    {"clock_hz": 3_579_545,  "platform": "YM2149 in Mega Drive (315-5246, driven at full NTSC rate)"},
    "pc98":              {"clock_hz": 2_457_600,  "platform": "NEC PC-98 (2.4576 MHz)"},
}

# Tone frequency formula:
#   f_tone  = clock_hz / (16 × period)   [period is 12-bit; 0 treated as 4096]
# Noise frequency formula:
#   f_noise = clock_hz / (16 × noise_period)  [noise_period is 5-bit]
# Envelope frequency formula:
#   f_env   = clock_hz / (256 × env_period)   [env_period is 16-bit]

TONE_FREQ_FORMULA  = "f_hz = clock_hz / (16 × period)    [period 1–4095; 0 = 4096]"
NOISE_FREQ_FORMULA = "f_hz = clock_hz / (16 × noise_period)  [noise_period 1–31; 0 = 32]"
ENV_FREQ_FORMULA   = "f_hz = clock_hz / (256 × env_period)   [env_period 1–65535; 0 = 65536]"

# ---------------------------------------------------------------------------
# Register map — 16 registers (R0–R15)
# ---------------------------------------------------------------------------

AY_REGISTERS: dict[int, dict] = {
    0x00: {
        "name": "R0 — Channel A Tone Period Fine",
        "bits": {"7-0": "tone_a_fine — low 8 bits of 12-bit tone period for channel A"},
    },
    0x01: {
        "name": "R1 — Channel A Tone Period Coarse",
        "bits": {"3-0": "tone_a_coarse — high 4 bits of 12-bit tone period for channel A"},
    },
    0x02: {
        "name": "R2 — Channel B Tone Period Fine",
        "bits": {"7-0": "tone_b_fine"},
    },
    0x03: {
        "name": "R3 — Channel B Tone Period Coarse",
        "bits": {"3-0": "tone_b_coarse"},
    },
    0x04: {
        "name": "R4 — Channel C Tone Period Fine",
        "bits": {"7-0": "tone_c_fine"},
    },
    0x05: {
        "name": "R5 — Channel C Tone Period Coarse",
        "bits": {"3-0": "tone_c_coarse"},
    },
    0x06: {
        "name": "R6 — Noise Period",
        "bits": {"4-0": "noise_period — 5-bit noise period divider"},
    },
    0x07: {
        "name": "R7 — Mixer Control / I/O Enable",
        "bits": {
            "7":   "io_b_dir  — I/O port B direction (0=input, 1=output)",
            "6":   "io_a_dir  — I/O port A direction",
            "5":   "noise_c   — 1=disable noise on channel C",
            "4":   "noise_b   — 1=disable noise on channel B",
            "3":   "noise_a   — 1=disable noise on channel A",
            "2":   "tone_c    — 1=disable tone on channel C",
            "1":   "tone_b    — 1=disable tone on channel B",
            "0":   "tone_a    — 1=disable tone on channel A",
        },
        "note": "Mixer bits are DISABLE flags (1=off). Both tone and noise can be "
                "active simultaneously — their outputs are ORed before volume scaling.",
    },
    0x08: {
        "name": "R8 — Channel A Amplitude",
        "bits": {
            "4":   "env_mode — 1=use envelope generator output instead of fixed volume",
            "3-0": "amplitude — fixed volume level (0=silent, 15=maximum)",
        },
    },
    0x09: {
        "name": "R9 — Channel B Amplitude",
        "bits": {"4": "env_mode", "3-0": "amplitude"},
    },
    0x0A: {
        "name": "R10 — Channel C Amplitude",
        "bits": {"4": "env_mode", "3-0": "amplitude"},
    },
    0x0B: {
        "name": "R11 — Envelope Period Fine",
        "bits": {"7-0": "env_period_fine — low 8 bits of 16-bit envelope period"},
    },
    0x0C: {
        "name": "R12 — Envelope Period Coarse",
        "bits": {"7-0": "env_period_coarse — high 8 bits of 16-bit envelope period"},
    },
    0x0D: {
        "name": "R13 — Envelope Shape",
        "bits": {
            "3": "continue — 0=envelope runs once then holds 0 (shapes 0-7 behaviour)",
            "2": "attack   — 0=start high (decay), 1=start low (attack)",
            "1": "alternate — invert direction on each envelope period",
            "0": "hold     — stop after first period",
        },
        "note": "Only shapes 8–15 (continue=1) produce looping envelopes. "
                "Shapes 0–7 (continue=0) all resolve to either single-shot decay or single-shot attack.",
    },
    0x0E: {
        "name": "R14 — I/O Port A Data",
        "bits": {"7-0": "port_a — I/O port A data (not audio)"},
    },
    0x0F: {
        "name": "R15 — I/O Port B Data",
        "bits": {"7-0": "port_b — I/O port B data (not audio)"},
    },
}

# Tone period register assembly:
#   period = (R_coarse & 0x0F) << 8 | R_fine
TONE_PERIOD_BITS   = 12    # 12-bit tone period (R_fine[7:0] + R_coarse[3:0])
TONE_PERIOD_MAX    = 4095  # 0xFFF
NOISE_PERIOD_BITS  = 5     # 5-bit noise period (R6[4:0])
NOISE_PERIOD_MAX   = 31
ENV_PERIOD_BITS    = 16    # 16-bit envelope period (R12[7:0] << 8 | R11[7:0])
ENV_PERIOD_MAX     = 65535

# ---------------------------------------------------------------------------
# Noise generator — LFSR
# ---------------------------------------------------------------------------

# 17-bit LFSR with feedback taps at bits 0 and 3 (XOR):
#   feedback = bit[0] XOR bit[3]
#   shift right by 1, insert feedback at bit 16
# Output is the current bit 0 value (1 or 0)
NOISE_LFSR_BITS   = 17
NOISE_LFSR_TAPS   = (0, 3)     # feedback: bit0 XOR bit3
NOISE_LFSR_PERIOD = 131071     # 2^17 - 1 steps before repeating

# ---------------------------------------------------------------------------
# Envelope generator — 10 distinct shapes
# ---------------------------------------------------------------------------

# Envelope shapes are determined by R13 bits 3-0.
# Despite 4 bits (16 combinations), shapes 0-3 and 4-7 each behave identically
# within their groups, giving 10 effective patterns:
#   Shapes 0-3:  \_ (single decay, hold at 0)
#   Shapes 4-7:  /_ ... actually 4-7: all decay once then hold 0
#   Wait — let me be precise:

# R13 shape behaviour:
#   Bit 3 (CONTINUE): if 0, after first envelope period output holds at boundary value
#   Bit 2 (ATTACK):   if 0, start high (decay); if 1, start low (attack)
#   Bit 1 (ALTERNATE): if 1, reverse direction at each period boundary
#   Bit 0 (HOLD):     if 1, stop after reaching end of first period

ENVELOPE_SHAPES: dict[int, dict] = {
    0:  {"pattern": "\\_ (decay, hold at 0)",    "continue": 0, "attack": 0, "alternate": 0, "hold": 0},
    1:  {"pattern": "\\_ (decay, hold at 0)",    "continue": 0, "attack": 0, "alternate": 0, "hold": 1},
    2:  {"pattern": "\\_ (decay, hold at 0)",    "continue": 0, "attack": 0, "alternate": 1, "hold": 0},
    3:  {"pattern": "\\_ (decay, hold at 0)",    "continue": 0, "attack": 0, "alternate": 1, "hold": 1},
    4:  {"pattern": "/_ (attack, hold at 0)",    "continue": 0, "attack": 1, "alternate": 0, "hold": 0},
    5:  {"pattern": "/_ (attack, hold at 0)",    "continue": 0, "attack": 1, "alternate": 0, "hold": 1},
    6:  {"pattern": "/_ (attack, hold at 0)",    "continue": 0, "attack": 1, "alternate": 1, "hold": 0},
    7:  {"pattern": "/_ (attack, hold at 0)",    "continue": 0, "attack": 1, "alternate": 1, "hold": 1},
    8:  {"pattern": "\\\\ (decay loop)",         "continue": 1, "attack": 0, "alternate": 0, "hold": 0},
    9:  {"pattern": "\\_ (decay, hold at 0)",    "continue": 1, "attack": 0, "alternate": 0, "hold": 1},
    10: {"pattern": "\\/\\ (decay-attack zigzag)","continue": 1, "attack": 0, "alternate": 1, "hold": 0},
    11: {"pattern": "\\¯ (decay, hold at max)",  "continue": 1, "attack": 0, "alternate": 1, "hold": 1},
    12: {"pattern": "// (attack loop)",          "continue": 1, "attack": 1, "alternate": 0, "hold": 0},
    13: {"pattern": "/¯ (attack, hold at max)",  "continue": 1, "attack": 1, "alternate": 0, "hold": 1},
    14: {"pattern": "/\\/ (attack-decay zigzag)","continue": 1, "attack": 1, "alternate": 1, "hold": 0},
    15: {"pattern": "/_ (attack, hold at 0)",    "continue": 1, "attack": 1, "alternate": 1, "hold": 1},
}

# Envelope output range: 0–15 (4-bit, same as fixed amplitude steps)
ENVELOPE_STEPS = 16   # 0–15

# Analogue amplitude table — output voltage is NOT linear.
# Volume steps follow an approximate square-root (logarithmic perceived) curve.
# AY-3-8910 hardware output levels (normalised to max=1.0), 16 steps:
AY_VOLUME_TABLE_NORMALIZED: list[float] = [
    0.000, 0.010, 0.015, 0.022,
    0.031, 0.046, 0.064, 0.090,
    0.127, 0.180, 0.254, 0.358,
    0.506, 0.715, 1.000, 1.000,  # steps 14 and 15 are identical on some chip revisions
]
# YM2149 volume table differs slightly — some implementations use this table:
YM2149_VOLUME_TABLE_NORMALIZED: list[float] = [
    0.000, 0.010, 0.013, 0.018,
    0.027, 0.038, 0.054, 0.076,
    0.107, 0.152, 0.214, 0.303,
    0.428, 0.605, 0.855, 1.000,
]
VOLUME_BITS  = 4    # 4-bit volume register
VOLUME_STEPS = 16

# ---------------------------------------------------------------------------
# YM2149 — differences from AY-3-8910
# ---------------------------------------------------------------------------

# The YM2149 is pin-compatible with AY-3-8910 but has two notable differences:

# 1. AY8914 register remap (furnace source: AY8914RegRemap[16])
#    On the AY-3-8914 (Intellivision variant), register addresses are remapped.
#    This remap table converts AY8914 address → standard AY8910 address:
AY8914_REG_REMAP: list[int] = [0, 4, 1, 5, 2, 6, 9, 8, 11, 12, 13, 3, 7, 10, 14, 15]
# AY8914_REG_REMAP[i] = standard AY8910 register index for AY8914 register i

# 2. Internal clock divider (/2 mode) on YM2149
#    The YM2149 has an internal ÷2 prescaler selectable by the /SEL pin.
#    When /SEL is tied low (common in Atari ST): effective clock = input_clock / 2
#    When /SEL is high: chip runs at full input clock (same as AY-3-8910)
#    Atari ST uses 2 MHz input clock with /SEL high → 2 MHz effective
YM2149_SEL_DIVIDE_BY_2 = True   # /SEL pin tied low → divide by 2 (some platforms)
YM2149_SEL_NOTE = (
    "Atari ST: 2 MHz input, /SEL=HIGH → runs at 2 MHz (no division). "
    "YM2149 in /SEL=LOW mode: input ÷ 2 — use half the clock_hz for frequency calculations."
)

# ---------------------------------------------------------------------------
# Mixer combinations and structural fingerprinting
# ---------------------------------------------------------------------------

# R7 mixer byte encodes tone+noise enable/disable per channel.
# Common patterns used as structural fingerprints:
MIXER_PATTERNS: dict[str, int] = {
    "all_tone":         0b11111000,  # only tones, all three channels
    "all_noise":        0b11000111,  # only noise, all three channels
    "ch_a_tone_only":   0b11111110,  # channel A tone only, everything else silent
    "ch_a_noise_only":  0b11111011,  # channel A noise only
    "all_silent":       0b11111111,  # all disabled
    "all_active":       0b11000000,  # all tone AND noise active (rare — creates harsh texture)
}
MIXER_TONE_DISABLE_BITS  = [0, 1, 2]   # bits that disable tone (1=disable)
MIXER_NOISE_DISABLE_BITS = [3, 4, 5]   # bits that disable noise


class Adapter:
    """
    Adapter exposing complete AY-3-8910 / YM2149 structural constants.

    Covers: platform clock variants and frequency derivation, all 16 registers
    with bit field descriptions, 12-bit tone period assembly, 5-bit noise LFSR
    (17-bit, taps 0&3), 16-bit envelope generator with all 10 effective shapes,
    non-linear 4-bit volume table (both AY8910 and YM2149 curves), YM2149
    AY8914 register remap and /SEL clock divider.

    Correct call path:
        HSL → ANALYZE_TRACK operator → Adapter → AY8910 constants
    """
    toolkit   = "ay8910"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.query(payload.get("query", "all"))

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return AY-3-8910 / YM2149 structural constants.

        Args:
            what: "clock" | "registers" | "tone" | "noise" | "envelope" |
                  "volume" | "ym2149" | "all"
        """
        base: dict[str, Any] = {"chip": "AY-3-8910/YM2149", "adapter": "ay8910"}

        if what in ("clock", "all"):
            base.update({
                "clock_variants":    CLOCK_VARIANTS,
                "tone_freq_formula": TONE_FREQ_FORMULA,
                "noise_freq_formula":NOISE_FREQ_FORMULA,
                "env_freq_formula":  ENV_FREQ_FORMULA,
            })

        if what in ("registers", "all"):
            base.update({
                "registers":        AY_REGISTERS,
                "tone_period_bits": TONE_PERIOD_BITS,
                "tone_period_max":  TONE_PERIOD_MAX,
                "noise_period_bits":NOISE_PERIOD_BITS,
                "noise_period_max": NOISE_PERIOD_MAX,
                "env_period_bits":  ENV_PERIOD_BITS,
                "env_period_max":   ENV_PERIOD_MAX,
            })

        if what in ("tone", "all"):
            base.update({
                "tone_freq_formula": TONE_FREQ_FORMULA,
                "tone_period_bits":  TONE_PERIOD_BITS,
                "tone_period_max":   TONE_PERIOD_MAX,
                "mixer_patterns":    MIXER_PATTERNS,
                "mixer_tone_disable_bits":  MIXER_TONE_DISABLE_BITS,
                "mixer_noise_disable_bits": MIXER_NOISE_DISABLE_BITS,
            })

        if what in ("noise", "all"):
            base.update({
                "noise_freq_formula": NOISE_FREQ_FORMULA,
                "noise_period_bits":  NOISE_PERIOD_BITS,
                "noise_period_max":   NOISE_PERIOD_MAX,
                "noise_lfsr_bits":    NOISE_LFSR_BITS,
                "noise_lfsr_taps":    NOISE_LFSR_TAPS,
                "noise_lfsr_period":  NOISE_LFSR_PERIOD,
            })

        if what in ("envelope", "all"):
            base.update({
                "envelope_shapes":    ENVELOPE_SHAPES,
                "envelope_steps":     ENVELOPE_STEPS,
                "env_freq_formula":   ENV_FREQ_FORMULA,
                "env_period_bits":    ENV_PERIOD_BITS,
                "env_period_max":     ENV_PERIOD_MAX,
            })

        if what in ("volume", "all"):
            base.update({
                "volume_bits":                   VOLUME_BITS,
                "volume_steps":                  VOLUME_STEPS,
                "ay_volume_table_normalized":    AY_VOLUME_TABLE_NORMALIZED,
                "ym2149_volume_table_normalized": YM2149_VOLUME_TABLE_NORMALIZED,
            })

        if what in ("ym2149", "all"):
            base.update({
                "ay8914_reg_remap":      AY8914_REG_REMAP,
                "ym2149_sel_divide_by_2": YM2149_SEL_DIVIDE_BY_2,
                "ym2149_sel_note":       YM2149_SEL_NOTE,
            })

        return base

    def tone_frequency(self, period: int, clock_hz: float) -> float:
        """Compute tone channel output frequency from 12-bit period and platform clock."""
        p = period if period > 0 else 4096  # 0 treated as 4096 on hardware
        return clock_hz / (16.0 * p)

    def noise_frequency(self, noise_period: int, clock_hz: float) -> float:
        """Compute noise generator clock frequency from 5-bit period and platform clock."""
        p = noise_period if noise_period > 0 else 32
        return clock_hz / (16.0 * p)

    def envelope_frequency(self, env_period: int, clock_hz: float) -> float:
        """Compute envelope generator frequency from 16-bit period and platform clock."""
        p = env_period if env_period > 0 else 65536
        return clock_hz / (256.0 * p)

    def tone_period_from_registers(self, fine: int, coarse: int) -> int:
        """Assemble 12-bit tone period from fine (R0/R2/R4) and coarse (R1/R3/R5) register values."""
        return ((coarse & 0x0F) << 8) | (fine & 0xFF)

    def remap_ay8914(self, address: int) -> int:
        """Remap an AY-3-8914 (Intellivision) register address to standard AY-3-8910 address."""
        if not 0 <= address < len(AY8914_REG_REMAP):
            raise AdapterError(f"AY8914 address must be 0–15, got {address}")
        return AY8914_REG_REMAP[address]

    def is_available(self) -> bool:
        return True
