"""
adapter_nuked_psg.py — Helix adapter for Nuked-PSG (YM7101 PSG / SN76489) constants
======================================================================================
Source reference:
    domains/music/data/library/source/code/Nuked-PSG/ympsg.c
    domains/music/data/library/source/code/Nuked-PSG/ympsg.h

Chip coverage:
    YM7101 — Yamaha PSG core embedded in the Sega Mega Drive/Genesis VDP (315-5313)
    SN76489 — Texas Instruments PSG used in Sega Master System, BBC Micro, etc.
              (YM7101 is functionally SN76489-compatible with minor differences)

Architecture:
    The PSG is not an FM chip. It has no operators, no algorithms, and no carrier
    topology. Instead it has 4 independent sound generators:

      Channel 0 — Tone 0 (square wave, 10-bit frequency divider)
      Channel 1 — Tone 1 (square wave, 10-bit frequency divider)
      Channel 2 — Tone 2 (square wave, 10-bit frequency divider)
      Channel 3 — Noise (white or periodic, 3 control bits + volume)

    Each channel has:
      - A volume/attenuation register (4 bits, 0 = maximum output, 15 = silent)
      - A frequency register (tone channels: 10-bit divider; noise: 2-bit rate)

    All channels are independent. There is no modulation routing.
    The Nuked-PSG emulator also exposes a volume lookup table (ympsg_vol[17])
    for linear amplitude conversion.

Register encoding (SN76489 / YM7101 latch-based write protocol):
    All writes go through a single 8-bit data bus with a latch bit:
      Bit 7 = 1: LATCH byte — bits[5:4] = channel select, bits[3:2] = register
                              type (0=freq low, 1=volume), bits[1:0] = data
      Bit 7 = 0: DATA byte  — bits[5:0] = upper 6 bits of frequency (tone channels)

    Frequency calculation (tone channels):
      f_out = clock / (32 × N)    where N = 10-bit freq register value
      Genesis clock = 3.579545 MHz (NTSC) or 3.546893 MHz (PAL)

    Noise register bits:
      bit 0-1: noise rate (0=512 Hz, 1=1024 Hz, 2=2048 Hz, 3=tone2 rate)
      bit 2:   noise type (0=periodic, 1=white noise, LFSR tapped bits 0 and 3)

Input:
    query (str) — one of: "channels", "volume_table", "register_protocol",
                          "timing", "all"

Output (dict):
    {
        "chip":              str,
        "tone_channels":     int,
        "noise_channel":     int,
        "total_channels":    int,
        "volume_range":      dict,
        "volume_table":      list[float],
        "tone_freq_bits":    int,
        "noise_bits":        dict,
        "clock_ntsc_hz":     float,
        "clock_pal_hz":      float,
        "adapter":           "nuked_psg",
    }

Adapter rules:
    • Tier A — static constants only, no compilation, always available.
    • No Helix logic. Translation only.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Channel allocation
# ---------------------------------------------------------------------------

_TONE_CHANNELS  = 3   # Channels 0, 1, 2 — square wave tone generators
_NOISE_CHANNEL  = 3   # Channel 3 — noise generator
_TOTAL_CHANNELS = 4

CHANNEL_NAMES: dict[int, str] = {
    0: "Tone0",
    1: "Tone1",
    2: "Tone2",
    3: "Noise",
}

# ---------------------------------------------------------------------------
# Volume / attenuation table
# ympsg_vol[17] from ympsg.c — linear amplitude per attenuation step.
# Index 0 = max output (1.0), index 15 = near-silent, index 16 = 0.0 (mute).
# These are the actual float values from Nuked-PSG source.
# ---------------------------------------------------------------------------

VOLUME_TABLE: list[float] = [
    1.000000, 0.794328, 0.630957, 0.501187,
    0.398107, 0.316228, 0.251189, 0.199526,
    0.158489, 0.125893, 0.100000, 0.079433,
    0.063096, 0.050119, 0.039811, 0.031623,
    0.000000,
]
# Index 15 maps to 0.031623 (~-30dB), index 16 = full mute.
# Register value 15 → effectively silent in practice.

_VOLUME_BITS   = 4    # 4-bit volume register
_VOLUME_MAX    = 0    # 0 = maximum output
_VOLUME_SILENT = 15   # 15 = minimum output (near-silent)

# ---------------------------------------------------------------------------
# Frequency registers
# ---------------------------------------------------------------------------

_TONE_FREQ_BITS   = 10   # tone frequency: 10-bit divider (6 high + 4 low)
_TONE_FREQ_MAX    = 1023  # 0x3FF
_NOISE_RATE_BITS  = 2    # noise rate: bits 0–1
_NOISE_TYPE_BIT   = 2    # noise type: bit 2 (0=periodic, 1=white)

NOISE_RATE_DESCRIPTIONS: dict[int, str] = {
    0: "Divided by 512 (fixed rate)",
    1: "Divided by 1024 (fixed rate)",
    2: "Divided by 2048 (fixed rate)",
    3: "Tone2 rate (noise tracks channel 2 frequency)",
}

NOISE_TYPE_DESCRIPTIONS: dict[int, str] = {
    0: "Periodic (tonal buzz — LFSR repeats at fixed period)",
    1: "White noise (pseudo-random LFSR: taps at bits 0 and 3)",
}

# ---------------------------------------------------------------------------
# Clock rates and frequency formula
# ---------------------------------------------------------------------------

_CLOCK_NTSC_HZ = 3_579_545.0   # Genesis/SMS NTSC master clock to PSG
_CLOCK_PAL_HZ  = 3_546_893.0   # Genesis/SMS PAL master clock to PSG

# Tone output frequency: f = clock / (32 × N)
# Noise base rates: 512, 1024, 2048 Hz divisions (relative to clock)


def tone_frequency_hz(n: int, clock_hz: float = _CLOCK_NTSC_HZ) -> float:
    """
    Calculate tone output frequency from 10-bit divider register value N.

    Args:
        n:        10-bit frequency register value (1–1023; 0 = no output)
        clock_hz: PSG input clock (default NTSC Genesis)

    Returns:
        Output frequency in Hz, or 0.0 if n == 0.
    """
    if n <= 0:
        return 0.0
    return clock_hz / (32.0 * n)


def volume_linear(reg_value: int) -> float:
    """
    Convert 4-bit volume register to linear amplitude (0.0–1.0).

    Args:
        reg_value: Volume register value 0–15 (0=max, 15=near-silent)

    Returns:
        Linear amplitude from VOLUME_TABLE.
    """
    idx = max(0, min(reg_value, 15))
    return VOLUME_TABLE[idx]


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class Adapter:
    """
    Tier A adapter exposing Nuked-PSG (YM7101 / SN76489) structural constants.

    PSG analysis differs from FM analysis: there are no operators or algorithms.
    Each channel is characterized by:
      - frequency register → tone/pitch
      - volume register → amplitude
      - noise channel: noise type + rate

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → PSG constants
    """
    toolkit   = "nuked_psg"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """Return PSG structural constants."""
        base: dict[str, Any] = {
            "chip":    "YM7101 PSG / SN76489",
            "adapter": "nuked_psg",
        }
        if what in ("channels", "all"):
            base.update({
                "tone_channels":  _TONE_CHANNELS,
                "noise_channel":  _NOISE_CHANNEL,
                "total_channels": _TOTAL_CHANNELS,
                "channel_names":  CHANNEL_NAMES,
            })
        if what in ("volume_table", "all"):
            base.update({
                "volume_table":  VOLUME_TABLE,
                "volume_bits":   _VOLUME_BITS,
                "volume_max":    _VOLUME_MAX,
                "volume_silent": _VOLUME_SILENT,
            })
        if what in ("register_protocol", "all"):
            base.update({
                "tone_freq_bits":          _TONE_FREQ_BITS,
                "tone_freq_max":           _TONE_FREQ_MAX,
                "noise_rate_bits":         _NOISE_RATE_BITS,
                "noise_type_bit":          _NOISE_TYPE_BIT,
                "noise_rate_descriptions": NOISE_RATE_DESCRIPTIONS,
                "noise_type_descriptions": NOISE_TYPE_DESCRIPTIONS,
            })
        if what in ("timing", "all"):
            base.update({
                "clock_ntsc_hz":   _CLOCK_NTSC_HZ,
                "clock_pal_hz":    _CLOCK_PAL_HZ,
                "freq_formula":    "f_out = clock / (32 × N)",
            })
        return base

    def is_available(self) -> bool:
        """Static constants always available."""
        return True
