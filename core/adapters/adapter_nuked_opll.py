"""
adapter_nuked_opll.py — Helix adapter for Nuked-OPLL (YM2413/OPLL) constants
==============================================================================
Source reference:
    codex/library/music/source/code/Nuked-OPLL/opll.c
    codex/library/music/source/code/Nuked-OPLL/opll.h

Chip coverage:
    YM2413  — Yamaha OPL-LL (OPLL), used in MSX FM-PAC, Sega Master System FM
    DS1001  — Konami VRC VII (NES mapper with 6-channel FM, YM2413 variant)
    YM2413B — Yamaha YM2413B revision
    YMF281  — Yamaha YMF281 (MSX variant with different ROM patches)
    YMF281B — Yamaha YMF281B
    YM2420  — Yamaha YM2420
    YM2423  — Yamaha YM2423

Architecture:
    OPLL is a simplified 2-operator FM chip. Each channel has exactly two slots:
      slot 0 = M (modulator) — feeds into carrier, does not output directly
      slot 1 = C (carrier)  — always outputs to DAC; no CON-bit algorithm selection

    This is structurally simpler than OPN2/OPM (no 4-op algorithms) or OPL3
    (no CON-bit additive mode at the channel level). The carrier set is fixed.

    9 melodic FM channels + optional rhythm mode (5 voices: BD, HH, TM, SD, TC).

    Each channel selects from 15 ROM patches (instrument presets) plus 1 custom
    user patch (registers 0x00–0x07). The TL register only applies to carrier (C);
    the modulator TL is fixed per patch. Feedback (FB) applies to modulator.

Patch format (from opll.h opll_patch_t):
    Per-slot [M=0, C=1]:
      multi[2]  — frequency multiplier (0–15)
      ksl[2]    — key scale level (0–3)
      am[2]     — AM enable (0/1)
      vib[2]    — vibrato enable (0/1)
      et[2]     — envelope type / sustain (0/1)
      ksr[2]    — key scale rate (0/1)
      ar[2]     — attack rate (0–15)
      dr[2]     — decay rate (0–15)
      sl[2]     — sustain level (0–15)
      rr[2]     — release rate (0–15)
    Per-patch (apply to carrier):
      tl        — total level / volume (0–63), carrier only
      fb        — feedback level (0–7), applies to modulator self-feedback
      dc        — distortion / carrier wave (0/1)
      dm        — distortion / modulator wave (0/1)

Input:
    query (str) — one of: "carrier_slots", "patch_format", "chip_variants",
                          "rhythm_voices", "all"

Output (dict):
    {
        "chip":           str,
        "carrier_slots":  frozenset[int],
        "operator_names": dict,
        "fm_channels":    int,
        "rhythm_voices":  dict,
        "patch_format":   dict,
        "chip_variants":  dict,
        "adapter":        "nuked_opll",
    }

Adapter rules:
    • Tier A — static constants only, no compilation, always available.
    • No Helix logic. Translation only.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Carrier topology
# ---------------------------------------------------------------------------
# OPLL has no algorithm selection. Each channel has 2 operators:
#   Slot 0 = M (modulator)  — feeds C; does NOT output to DAC
#   Slot 1 = C (carrier)   — always outputs to DAC
#
# This is a constant regardless of patch or register settings.
# (Unlike OPL3 which has a CON bit enabling additive synthesis.)

CARRIER_SLOTS: frozenset[int] = frozenset({1})   # C always carries

OPERATOR_NAMES: dict[int, str] = {
    0: "M",   # modulator
    1: "C",   # carrier
}

# ---------------------------------------------------------------------------
# Channel allocation
# ---------------------------------------------------------------------------

_MELODIC_CHANNELS = 9      # channels 0–8
_RHYTHM_CHANNEL_FIRST = 6  # channels 6–8 repurposed in rhythm mode

# Rhythm voices in rhythm mode (enabled via register 0x0E bit6=1)
# Each voice uses one or two operators from the shared rhythm channels.
RHYTHM_VOICES: dict[str, dict[str, Any]] = {
    "BD":  {"name": "Bass Drum",   "channel": 6, "operators": (0, 1)},
    "HH":  {"name": "Hi-Hat",      "channel": 7, "operators": (0,)},
    "TM":  {"name": "Tom",         "channel": 8, "operators": (0,)},
    "SD":  {"name": "Snare Drum",  "channel": 7, "operators": (1,)},
    "TC":  {"name": "Top Cymbal",  "channel": 8, "operators": (1,)},
}

# ---------------------------------------------------------------------------
# Patch ROM presets (15 ROM + 1 user-defined)
# Instrument indices 1–15 select ROM patches; 0 = custom user patch.
# Patch names sourced from opll_patch_t patch_ym2413[] and common MSX docs.
# ---------------------------------------------------------------------------

PATCH_ROM_NAMES: dict[int, str] = {
    0:  "User-Defined",
    1:  "Violin",
    2:  "Guitar",
    3:  "Piano",
    4:  "Flute",
    5:  "Clarinet",
    6:  "Oboe",
    7:  "Trumpet",
    8:  "Organ",
    9:  "Horn",
    10: "Synthesizer",
    11: "Harpsichord",
    12: "Vibraphone",
    13: "Synthesizer Bass",
    14: "Acoustic Bass",
    15: "Electric Guitar",
}

# ---------------------------------------------------------------------------
# Patch register format (user-defined custom patch, registers 0x00–0x07)
# ---------------------------------------------------------------------------
# Registers 0x00–0x07 set the custom patch (instrument 0):
#   0x00: AM/VIB/ET/KSR/MULTI for modulator (M)
#   0x01: AM/VIB/ET/KSR/MULTI for carrier (C)
#   0x02: KSL/TL for modulator
#   0x03: KSL/DC/DM/FB for carrier
#   0x04: AR/DR for modulator
#   0x05: AR/DR for carrier
#   0x06: SL/RR for modulator
#   0x07: SL/RR for carrier

CUSTOM_PATCH_REGISTER_MAP: dict[str, dict[str, Any]] = {
    "0x00_M": {
        "bits": {"AM": 7, "VIB": 6, "ET": 5, "KSR": 4, "MULTI": "3:0"},
        "slot": 0,
        "description": "Modulator: AM enable, vibrato, envelope type, key scale rate, frequency multiplier",
    },
    "0x01_C": {
        "bits": {"AM": 7, "VIB": 6, "ET": 5, "KSR": 4, "MULTI": "3:0"},
        "slot": 1,
        "description": "Carrier: AM enable, vibrato, envelope type, key scale rate, frequency multiplier",
    },
    "0x02_M": {
        "bits": {"KSL": "7:6", "TL": "5:0"},
        "slot": 0,
        "description": "Modulator: key scale level, total level (0=loud, 63=silent)",
    },
    "0x03_C": {
        "bits": {"KSL": "7:6", "DC": 4, "DM": 3, "FB": "2:0"},
        "slot": 1,
        "description": "Carrier: key scale level, carrier waveform, modulator waveform, feedback level",
    },
    "0x04_M": {
        "bits": {"AR": "7:4", "DR": "3:0"},
        "slot": 0,
        "description": "Modulator: attack rate, decay rate",
    },
    "0x05_C": {
        "bits": {"AR": "7:4", "DR": "3:0"},
        "slot": 1,
        "description": "Carrier: attack rate, decay rate",
    },
    "0x06_M": {
        "bits": {"SL": "7:4", "RR": "3:0"},
        "slot": 0,
        "description": "Modulator: sustain level, release rate",
    },
    "0x07_C": {
        "bits": {"SL": "7:4", "RR": "3:0"},
        "slot": 1,
        "description": "Carrier: sustain level, release rate",
    },
}

# ---------------------------------------------------------------------------
# Chip variants (from opll.h enum opll_type_*)
# ---------------------------------------------------------------------------

CHIP_VARIANTS: dict[str, dict[str, Any]] = {
    "YM2413":  {"type_id": 0x00, "description": "Yamaha YM2413 (MSX FM-PAC, Sega SMS FM)"},
    "DS1001":  {"type_id": 0x01, "description": "Konami VRC VII (NES mapper with 6-channel FM)"},
    "YM2413B": {"type_id": 0x02, "description": "Yamaha YM2413B revision"},
    "YMF281":  {"type_id": 0x03, "description": "Yamaha YMF281 (MSX variant, different ROM patches)"},
    "YMF281B": {"type_id": 0x04, "description": "Yamaha YMF281B"},
    "YM2420":  {"type_id": 0x05, "description": "Yamaha YM2420"},
    "YM2423":  {"type_id": 0x06, "description": "Yamaha YM2423"},
}


class Adapter:
    """
    Tier A adapter exposing Nuked-OPLL (YM2413/OPLL) structural constants.

    OPLL is a 2-operator FM chip with no algorithm/CON selection.
    The carrier is always slot 1 (C). Carrier set is a structural constant,
    not a runtime variable.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → OPLL constants
    """
    toolkit  = "nuked_opll"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """Return OPLL structural constants."""
        base: dict[str, Any] = {
            "chip":    "YM2413 / OPLL family",
            "adapter": "nuked_opll",
        }
        if what in ("carrier_slots", "all"):
            base["carrier_slots"]  = CARRIER_SLOTS
            base["operator_names"] = OPERATOR_NAMES
        if what in ("patch_format", "all"):
            base["patch_rom_names"]          = PATCH_ROM_NAMES
            base["custom_patch_register_map"] = CUSTOM_PATCH_REGISTER_MAP
            base["fm_channels"]              = _MELODIC_CHANNELS
        if what in ("chip_variants", "all"):
            base["chip_variants"] = CHIP_VARIANTS
        if what in ("rhythm_voices", "all"):
            base["rhythm_voices"]       = RHYTHM_VOICES
            base["rhythm_channel_first"] = _RHYTHM_CHANNEL_FIRST
        return base

    def get_carrier_slots(self) -> frozenset[int]:
        """
        Always returns {1}. OPLL has no algorithm selection;
        slot 1 (C) is always the carrier.
        """
        return CARRIER_SLOTS

    def carrier_tl(self, patch_tl: int) -> float:
        """
        Normalized carrier brightness from carrier TL.
        TL range 0–63: 0 = loudest, 63 = near-silent.
        Returns 0.0 (silent) to 1.0 (maximum output).
        """
        return 1.0 - (min(patch_tl, 63) / 63.0)

    def is_available(self) -> bool:
        """Static constants always available."""
        return True
