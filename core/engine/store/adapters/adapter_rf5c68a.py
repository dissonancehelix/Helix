"""
adapter_rf5c68a.py — Helix adapter for Ricoh RF5C68A PCM sound source
======================================================================
Tier A: Static constants. No compilation required.
Source references:
    domains/music/data/output/library/source/chip_docs/RF5C68A.pdf
    domains/music/data/output/library/source/chip_docs/MCDHardware_Manual_PCM_Sound_Source.pdf

Chip coverage:
    RF5C68A  — Ricoh PCM sound source (Sega CD / Mega CD)
    RF5C164  — Ricoh extended PCM (Sega Saturn; same architecture, wider samples)

Architecture:
    The RF5C68A is an 8-channel PCM playback chip with bank-switched sample RAM.
    It is NOT an FM synthesizer. There are no operators, algorithms, or envelopes.
    Each channel streams a waveform from a configurable start address in sample RAM.

    Key architectural features:
      - 8 independent PCM channels
      - 8 sample RAM banks, 64 KB per bank (512 KB total addressable)
      - Per-channel: start address, step (pitch), loop start/end, left/right volume
      - Sample format: 8-bit signed PCM (RF5C68A) or 16-bit (RF5C164)
      - Output sample rate: input_clock / 384
      - Sega CD clock: 12.5 MHz → sample rate ≈ 32,552 Hz

Register map (RF5C68A):
    Control register (0xFF00):
      bit 7: SPRAM bank select bit 2
      bit 6: SPRAM bank select bit 1
      bit 5: SPRAM bank select bit 0
      bit 4: RF5C68 enable (1 = active, 0 = stop all)

    Per-channel registers (channel N at base 0xFF01 + N*8):
      Offset 0: ENV_L   — left volume  (0x00 = full, 0xFF = silent)
      Offset 1: ENV_R   — right volume (0x00 = full, 0xFF = silent)
      Offset 2: STEP_H  — pitch step high byte (16.16 fixed point, high)
      Offset 3: STEP_L  — pitch step low byte
      Offset 4: LOOP_H  — loop start address high byte
      Offset 5: LOOP_L  — loop start address low byte
      Offset 6: START   — sample start address (bank-relative, right-shifted 8)
      Offset 7: CTRL    — channel control (bit 0: key-on, bit 4: loop enable)

    RAM bank register (0xFF09 or via control register bank bits):
      Selects which of 8 sample RAM banks is mapped to the CPU/DMA window.

Input:
    query (str) — one of: "channels", "registers", "clock", "banks", "all"

Output (dict):
    {
        "chip":              str,
        "pcm_channels":      int,
        "sample_ram_banks":  int,
        "bytes_per_bank":    int,
        "sample_format":     str,
        "clock_hz":          float,
        "sample_rate_hz":    float,
        "clock_divisor":     int,
        "register_map":      dict,
        "channel_registers": dict,
        "adapter":           "rf5c68a",
    }

Adapter rules:
    • Tier A — static constants only, no compilation, always available.
    • No Helix logic. Translation only.
    • VGM header field: hz_rf5c68 at offset 0x40
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Architecture constants
# ---------------------------------------------------------------------------

_PCM_CHANNELS     = 8
_SAMPLE_RAM_BANKS = 8
_BYTES_PER_BANK   = 65536  # 64 KB
_SAMPLE_FORMAT    = "8-bit signed PCM"

# ---------------------------------------------------------------------------
# Clock and sample rate
# ---------------------------------------------------------------------------

# Sega CD (Mega CD) provides 12.5 MHz to the RF5C68A
_CLOCK_SEGA_CD_HZ = 12_500_000.0
_CLOCK_DIVISOR    = 384
_SAMPLE_RATE_HZ   = _CLOCK_SEGA_CD_HZ / _CLOCK_DIVISOR  # ≈ 32,552 Hz

# ---------------------------------------------------------------------------
# Register map
# ---------------------------------------------------------------------------

CONTROL_REGISTERS: dict[str, dict] = {
    "CTRL": {
        "address": 0xFF00,
        "description": "Global control register",
        "bits": {
            "7:5": "Sample RAM bank select (bits 2:0)",
            "4":   "Chip enable (1=active, 0=all channels silent)",
            "3:0": "Reserved",
        },
    },
    "WBANK": {
        "address": 0xFF09,
        "description": "Write bank select for CPU/DMA access to sample RAM",
    },
}

# Per-channel register block layout (8 bytes per channel, starting at 0xFF01 + N*8)
CHANNEL_REGISTER_OFFSETS: dict[str, dict] = {
    "ENV_L":  {"offset": 0, "description": "Left channel volume (0=full, 0xFF=silent)"},
    "ENV_R":  {"offset": 1, "description": "Right channel volume (0=full, 0xFF=silent)"},
    "STEP_H": {"offset": 2, "description": "Pitch step high byte (16.16 fixed point)"},
    "STEP_L": {"offset": 3, "description": "Pitch step low byte"},
    "LOOP_H": {"offset": 4, "description": "Loop start address high byte (bank-relative)"},
    "LOOP_L": {"offset": 5, "description": "Loop start address low byte"},
    "START":  {"offset": 6, "description": "Sample start address (bank-relative, >>8)"},
    "CTRL":   {
        "offset": 7,
        "description": "Channel control",
        "bits": {
            "0": "Key-on (1=playing, 0=stopped)",
            "4": "Loop enable (1=loop, 0=one-shot)",
        },
    },
}


def channel_base_address(channel: int) -> int:
    """
    Return the base register address for a given PCM channel (0–7).

    Args:
        channel: Channel index 0–7.

    Returns:
        Base address for this channel's 8-byte register block.
    """
    if not (0 <= channel < _PCM_CHANNELS):
        raise AdapterError(
            f"Invalid RF5C68A channel {channel!r}. Valid range: 0–7."
        )
    return 0xFF01 + channel * 8


def pitch_step_to_hz(
    step: int,
    clock_hz: float = _CLOCK_SEGA_CD_HZ,
) -> float:
    """
    Convert RF5C68A pitch step value to output sample rate multiplier.

    The step register encodes pitch as a 16.8 fixed-point value.
    Step = 0x0100 plays back at the native sample rate.
    Step = 0x0200 plays back at 2× (one octave up).

    Args:
        step:     Raw 16-bit step register value.
        clock_hz: Input clock (default Sega CD 12.5 MHz).

    Returns:
        Effective playback sample rate in Hz.
    """
    base_rate = clock_hz / _CLOCK_DIVISOR
    return base_rate * (step / 256.0)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class Adapter:
    """
    Tier A adapter exposing RF5C68A PCM sound source structural constants.

    The RF5C68A is the Sega CD/Mega CD PCM chip. Unlike FM chips, it has
    no operators or synthesis parameters — only sample playback with
    pitch (step), volume (ENV_L/R), and looping.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → PCM constants
    """
    toolkit  = "rf5c68a"
    substrate = "music"

    SUPPORTED_CHIPS: frozenset[str] = frozenset({"RF5C68", "RF5C68A", "RF5C164"})

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """Return RF5C68A structural constants."""
        base: dict[str, Any] = {
            "chip":    "RF5C68A",
            "adapter": "rf5c68a",
        }
        if what in ("channels", "all"):
            base.update({
                "pcm_channels":   _PCM_CHANNELS,
                "sample_format":  _SAMPLE_FORMAT,
            })
        if what in ("banks", "all"):
            base.update({
                "sample_ram_banks": _SAMPLE_RAM_BANKS,
                "bytes_per_bank":   _BYTES_PER_BANK,
                "total_ram_bytes":  _SAMPLE_RAM_BANKS * _BYTES_PER_BANK,
            })
        if what in ("clock", "all"):
            base.update({
                "clock_hz":      _CLOCK_SEGA_CD_HZ,
                "clock_divisor": _CLOCK_DIVISOR,
                "sample_rate_hz": round(_SAMPLE_RATE_HZ, 2),
                "note": "step=0x0100 → native rate; step=0x0200 → 2× (octave up)",
            })
        if what in ("registers", "all"):
            base.update({
                "control_registers":      CONTROL_REGISTERS,
                "channel_register_offsets": CHANNEL_REGISTER_OFFSETS,
                "channel_base_formula":   "0xFF01 + channel × 8",
            })
        return base

    def get_channel_addresses(self) -> list[dict[str, Any]]:
        """Return register base addresses for all 8 channels."""
        return [
            {"channel": ch, "base_address": hex(channel_base_address(ch))}
            for ch in range(_PCM_CHANNELS)
        ]

    def is_available(self) -> bool:
        """Static constants always available."""
        return True
