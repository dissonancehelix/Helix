"""
adapter_nuked_opl2.py — Helix adapter for Nuked-OPL2-Lite (YM3812/OPL2) constants
====================================================================================
Source reference:
    domains/music/data/derived/music/source/code/Nuked-OPL2-Lite/opl2.c
    domains/music/data/derived/music/source/code/Nuked-OPL2-Lite/opl2.h

Chip coverage:
    YM3812 — Yamaha OPL2, used in Sound Blaster 1.0–2.0, AdLib card
    YM3526 — Yamaha OPL (predecessor, similar register set, no waveform select)

Architecture:
    OPL2 has 9 FM channels, each with 2 operator slots (slotz[0] and slotz[1]).
    Unlike OPL3, OPL2 only supports 2-op mode (no 4-op pairing).

    The CON register bit per channel determines carrier topology:
      CON = 0: FM mode    → slot 0 = modulator (feeds slot 1), slot 1 = carrier
      CON = 1: Additive   → both slots output independently (both are carriers)

    OPL2 also supports a rhythm mode (5 percussion voices) using channels 6–8.

    Slot numbering:
      slotz[0] = operator 0 (modulator in FM mode)
      slotz[1] = operator 1 (carrier in FM mode)

    Register layout (per channel, base at 0xB0 for KON/BLOCK/FNUM):
      0xA0 + ch: FNUM low 8 bits
      0xB0 + ch: KON (bit5), BLOCK (bits4:2), FNUM high 2 bits (bits1:0)
      0xC0 + ch: Feedback (bits5:3), CON (bit0)

    Operator registers (18 slots, indexed in hardware slot order):
      0x20 + slot: AM, VIB, ET, KSR, MULT
      0x40 + slot: KSL, TL
      0x60 + slot: AR, DR
      0x80 + slot: SL, RR
      0xE0 + slot: Waveform (0–3; OPL2 supports 4 waveforms)

    Rhythm voices (when rhythm mode enabled, register 0xBD bit5=1):
      Bass Drum (BD)   — channel 6, both operators
      Hi-Hat (HH)      — channel 7, operator 0
      Tom-Tom (TT)     — channel 8, operator 0
      Snare Drum (SD)  — channel 7, operator 1
      Top Cymbal (CY)  — channel 8, operator 1

Input:
    query (str) — one of: "carrier_slots", "rhythm", "timing", "waveforms", "all"
    con (int)   — optional CON bit value for targeted carrier slot lookup

Output (dict):
    {
        "chip":              str,
        "carrier_slots":     dict[int, frozenset[int]],
        "melodic_channels":  int,
        "rhythm_voices":     dict,
        "waveforms":         dict,
        "adapter":           "nuked_opl2",
    }

Adapter rules:
    • Tier A — static constants only, no compilation, always available.
    • No Helix logic. Translation only.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Carrier topology (from opl2.h: opl2_channel.con register bit)
# ---------------------------------------------------------------------------
# CON = 0: FM synthesis  → only slot 1 (carrier) outputs to DAC
# CON = 1: Additive      → both slot 0 and slot 1 output to DAC

CARRIER_SLOTS_2OP: dict[int, frozenset[int]] = {
    0: frozenset({1}),      # CON=0: FM — carrier = slot 1 only
    1: frozenset({0, 1}),   # CON=1: Additive — both slots are carriers
}

OPERATOR_NAMES: dict[int, str] = {
    0: "M",   # modulator (operator 0 / slotz[0])
    1: "C",   # carrier   (operator 1 / slotz[1])
}

# In FM mode (CON=0), M modulates C. In additive (CON=1), both emit independently.

# ---------------------------------------------------------------------------
# Channel allocation
# ---------------------------------------------------------------------------

_MELODIC_CHANNELS  = 9    # channels 0–8 (all melodic when rhythm off)
_RHYTHM_CHANNELS   = 3    # channels 6, 7, 8 repurposed in rhythm mode
_OPL2_SLOTS_TOTAL  = 18   # 9 channels × 2 slots

# Rhythm mode voices (register 0xBD bit5 = 1)
RHYTHM_VOICES: dict[str, dict[str, Any]] = {
    "BD": {"name": "Bass Drum",  "channel": 6, "operators": (0, 1)},
    "HH": {"name": "Hi-Hat",     "channel": 7, "operators": (0,)},
    "TT": {"name": "Tom-Tom",    "channel": 8, "operators": (0,)},
    "SD": {"name": "Snare Drum", "channel": 7, "operators": (1,)},
    "CY": {"name": "Top Cymbal", "channel": 8, "operators": (1,)},
}

# ---------------------------------------------------------------------------
# Waveforms (OPL2 supports 4 waveforms per operator, unlike OPL = 1 waveform)
# Waveform register: 0xE0 + slot, bits 1:0
# ---------------------------------------------------------------------------

WAVEFORMS: dict[int, str] = {
    0: "Sine",
    1: "Half-sine (negative half silenced)",
    2: "Absolute sine (full-wave rectified)",
    3: "Pulse-sine (quarter-wave, silence rest)",
}

# ---------------------------------------------------------------------------
# Operator register map (hardware slot → channel + slot index)
# OPL2 uses a non-linear hardware slot ordering (18 slots, 2 per channel)
# Slot hardware indices from opl2.c ad_slot[] / ch_slot[]:
#   ch_slot[9] = {0, 1, 2, 6, 7, 8, 12, 13, 14}
#   M slot = ch_slot[ch], C slot = ch_slot[ch] + 3
# ---------------------------------------------------------------------------

# Channel → (M_slot_index, C_slot_index) in hardware register space
CHANNEL_SLOT_MAP: dict[int, tuple[int, int]] = {
    0: (0, 3),
    1: (1, 4),
    2: (2, 5),
    3: (6, 9),
    4: (7, 10),
    5: (8, 11),
    6: (12, 15),
    7: (13, 16),
    8: (14, 17),
}

# ---------------------------------------------------------------------------
# Feedback / TL helpers
# ---------------------------------------------------------------------------

def carrier_tl_brightness(tl: int) -> float:
    """
    Normalized carrier brightness from TL register.
    TL is 6-bit (0–63): 0 = loudest, 63 = near-silent.
    Returns 0.0 (silent) to 1.0 (maximum output).
    """
    return 1.0 - (min(tl, 63) / 63.0)


def get_carrier_slots(con: int) -> frozenset[int]:
    """
    Return the set of carrier slot indices for a given CON bit value.

    Args:
        con: CON bit (0 = FM, 1 = Additive)

    Returns:
        frozenset of slot indices (0 and/or 1) that output to DAC.
    """
    return CARRIER_SLOTS_2OP.get(con & 0x01, CARRIER_SLOTS_2OP[0])


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class Adapter:
    """
    Tier A adapter exposing Nuked-OPL2-Lite (YM3812/OPL2) structural constants.

    OPL2 uses 2-op channels with a CON bit selecting FM vs additive synthesis.
    This is identical to OPL3's 2-op channel model but without 4-op pairing.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → OPL2 constants
    """
    toolkit   = "nuked_opl2"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        if "con" in payload:
            return {"carrier_slots": get_carrier_slots(int(payload["con"])),
                    "adapter": "nuked_opl2"}
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """Return OPL2 structural constants."""
        base: dict[str, Any] = {
            "chip":    "YM3812 / OPL2",
            "adapter": "nuked_opl2",
        }
        if what in ("carrier_slots", "all"):
            base.update({
                "carrier_slots":   CARRIER_SLOTS_2OP,
                "operator_names":  OPERATOR_NAMES,
                "channel_slot_map": CHANNEL_SLOT_MAP,
            })
        if what in ("rhythm", "all"):
            base.update({
                "melodic_channels": _MELODIC_CHANNELS,
                "rhythm_voices":    RHYTHM_VOICES,
            })
        if what in ("waveforms", "all"):
            base["waveforms"] = WAVEFORMS
        return base

    def get_carrier_slots(self, con: int) -> frozenset[int]:
        """Return carrier slot set for given CON bit."""
        return get_carrier_slots(con)

    def all_modes(self) -> dict[str, Any]:
        """Return all CON mode descriptions."""
        return {
            con: {
                "carrier_slots": list(slots),
                "mode": "FM" if con == 0 else "Additive",
            }
            for con, slots in CARRIER_SLOTS_2OP.items()
        }

    def is_available(self) -> bool:
        """Static constants always available."""
        return True
