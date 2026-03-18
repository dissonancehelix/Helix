"""
adapter_smps.py — Helix adapter for SMPS driver constants
==========================================================
Source reference:
    data/music/source/code/SMPS/

Purpose:
    Provide structural constants from the Sega Music Processor System (SMPS)
    driver source code. SMPS is the primary sound driver for Sega Genesis
    (Mega Drive) first-party and many third-party titles.

    These constants are used to interpret VGM register-write streams in
    the context of driver-level behaviour, separating hardware capability
    (YM2612/SN76489) from software orchestration (SMPS).

SMPS structural invariants (from spec §22.2 and SMPS source):
    - Tempo is quantized to 60Hz (NTSC) or 50Hz (PAL) vertical interrupt ticks
    - "Tempo1Tick" jitter: Z80 sub-engine mailbox latency adds ±1 tick variance
    - Note opcodes: 0x00–0x7F (128 note values, mapped to YM2612 key codes)
    - Command opcodes: 0x80–0xFF (driver macros, channel control, FM writes)
    - Volume attenuation: 16-step table (driver-level, above chip-level TL)

Input:
    query (str)  — one of: "timing", "opcodes", "volume", "all"

Output (dict):
    {
        "driver":           "SMPS",
        "tick_rate_ntsc":   int,      # Hz
        "tick_rate_pal":    int,      # Hz
        "tempo_jitter_ticks": int,    # ±N ticks variance from Tempo1Tick
        "note_range":       [int, int],  # [min_opcode, max_opcode]
        "command_range":    [int, int],  # [min_opcode, max_opcode]
        "volume_steps":     int,
        "fm_channels":      int,
        "psg_channels":     int,
        "dac_channel":      int,
        "adapter":          "smps",
    }

Adapter rules:
    • No Helix logic.
    • Static constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# SMPS timing constants
# Source: SMPS Z80 and 68000 source code tick interrupt handlers
_TICK_RATE_NTSC = 60   # Hz — NTSC vertical interrupt (60.098 Hz, rounded)
_TICK_RATE_PAL  = 50   # Hz — PAL vertical interrupt (50.000 Hz)
_TEMPO1TICK_JITTER = 1  # ±1 tick variance from Z80 mailbox polling latency

# SMPS opcode ranges (1-byte opcode structure)
# Notes: 0x00–0x7F map to YM2612 key codes via driver lookup table
# Commands: 0x80–0xFF are driver macros (pan, volume, portamento, etc.)
_NOTE_MIN     = 0x00
_NOTE_MAX     = 0x7F
_COMMAND_MIN  = 0x80
_COMMAND_MAX  = 0xFF

# Well-known SMPS command opcodes (from 68000 source, ver11 mdbse11.s)
COMMAND_OPCODES: dict[str, int] = {
    "stop":            0xF2,  # stop channel
    "loop":            0xF3,  # loop to offset
    "goto":            0xF4,  # jump to offset
    "pan_center":      0xE0,  # pan: center
    "pan_left":        0xE1,  # pan: left
    "pan_right":       0xE2,  # pan: right
    "volume_up":       0xE4,  # master volume increase
    "volume_down":     0xE5,  # master volume decrease
    "set_volume":      0xE6,  # set absolute volume
    "portamento":      0xEC,  # portamento slide
    "detune":          0xED,  # detune (fine tune)
    "fm_patch_change": 0xF0,  # load FM patch from table
    "tempo_set":       0xF1,  # set tempo (ticks per beat)
    "rest":            0x80,  # rest (silence for N ticks)
    "tie":             0x81,  # tie / extend previous note
    "note_off":        0x82,  # key off
}

# SMPS volume attenuation table (driver-level, 16 steps above chip TL)
# Each step maps to a TL offset applied to the YM2612 carrier operators
# Step 0 = loudest, step 15 = silent
_VOLUME_STEPS = 16
_VOLUME_TL_OFFSETS: list[int] = [
    0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 96, 127
]

# SMPS channel allocation on Sega Genesis
_FM_CHANNELS  = 6   # YM2612 channels 1-6 (channel 6 doubles as DAC)
_PSG_CHANNELS = 4   # SN76489: 3 tone + 1 noise
_DAC_CHANNEL  = 6   # YM2612 channel 6, DAC mode for PCM samples


class Adapter:
    """
    Adapter exposing SMPS driver structural constants.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → SMPS constants
    """
    toolkit = "smps"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return SMPS structural constants.

        Args:
            what: "timing" | "opcodes" | "volume" | "all"
        """
        base: dict[str, Any] = {
            "driver":  "SMPS",
            "adapter": "smps",
        }
        if what in ("timing", "all"):
            base.update({
                "tick_rate_ntsc":      _TICK_RATE_NTSC,
                "tick_rate_pal":       _TICK_RATE_PAL,
                "tempo_jitter_ticks":  _TEMPO1TICK_JITTER,
                "fm_channels":         _FM_CHANNELS,
                "psg_channels":        _PSG_CHANNELS,
                "dac_channel":         _DAC_CHANNEL,
            })
        if what in ("opcodes", "all"):
            base.update({
                "note_range":     [_NOTE_MIN, _NOTE_MAX],
                "command_range":  [_COMMAND_MIN, _COMMAND_MAX],
                "command_opcodes": COMMAND_OPCODES,
            })
        if what in ("volume", "all"):
            base.update({
                "volume_steps":      _VOLUME_STEPS,
                "volume_tl_offsets": _VOLUME_TL_OFFSETS,
            })
        return base

    def classify_opcode(self, opcode: int) -> dict[str, Any]:
        """
        Classify a single SMPS opcode byte.

        Returns:
            {"type": "note" | "command", "opcode": int, "name": str | None}
        """
        if _NOTE_MIN <= opcode <= _NOTE_MAX:
            return {"type": "note", "opcode": opcode, "name": None}
        name = next(
            (k for k, v in COMMAND_OPCODES.items() if v == opcode), None
        )
        return {"type": "command", "opcode": opcode, "name": name}

    def ticks_to_seconds(self, ticks: int, region: str = "ntsc") -> float:
        """Convert SMPS tick count to seconds. region: 'ntsc' or 'pal'."""
        rate = _TICK_RATE_NTSC if region == "ntsc" else _TICK_RATE_PAL
        return ticks / rate

    def is_available(self) -> bool:
        """SMPS adapter is always available — uses static constants."""
        return True
