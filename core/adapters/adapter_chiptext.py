"""
adapter_chiptext.py — Helix adapter for chiptext.c static tables
=================================================================
Tier A: Pure Python — no compilation required.
Source reference: domains/music/toolkits/vgmtools/chiptext.c

Purpose:
    Expose chip-specific register maps, frequency tables, mode enumerations,
    and waveform definitions extracted verbatim from chiptext.c.

    Covers chips not handled by the Nuked FM adapters:
        NES APU, Game Boy DMG, Atari Pokey, AY-8910 family,
        OPN/OPL family type flags, OKIM6258, OKIM6295, MultiPCM.

Input (payload dict):
    chip (str)  — chip name key (see SUPPORTED_CHIPS)

Output (dict):
    {
        "chip":         str,
        "registers":    dict | None,    # register_name -> offset
        "flags":        dict | None,    # flag_name -> bit value
        "tables":       dict | None,    # table_name -> values
        "adapter":      "chiptext",
    }

Adapter rules:
    • No Helix logic. No audio rendering.
    • All constants extracted verbatim from chiptext.c.
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ── OPN family type flags (chiptext.c lines 87-104) ──────────────────────────

OPN_TYPE_SSG    = 0x01  # SSG support
OPN_TYPE_LFOPAN = 0x02  # OPN type LFO and PAN
OPN_TYPE_6CH    = 0x04  # FM 6CH / 3CH
OPN_TYPE_DAC    = 0x08  # YM2612 DAC device
OPN_TYPE_ADPCM  = 0x10  # two ADPCM units
OPN_TYPE_2610   = 0x20  # differentiates YM2608 from YM2610

OPN_TYPE_FLAGS: dict[str, int] = {
    "SSG":    OPN_TYPE_SSG,
    "LFOPAN": OPN_TYPE_LFOPAN,
    "6CH":    OPN_TYPE_6CH,
    "DAC":    OPN_TYPE_DAC,
    "ADPCM":  OPN_TYPE_ADPCM,
    "2610":   OPN_TYPE_2610,
}

# Composite chip type values
OPN_CHIP_TYPES: dict[str, int] = {
    "YM2203": OPN_TYPE_SSG,
    "YM2608": OPN_TYPE_SSG | OPN_TYPE_LFOPAN | OPN_TYPE_6CH | OPN_TYPE_ADPCM,
    "YM2610": OPN_TYPE_SSG | OPN_TYPE_LFOPAN | OPN_TYPE_6CH | OPN_TYPE_ADPCM | OPN_TYPE_2610,
    "YM2612": OPN_TYPE_DAC | OPN_TYPE_LFOPAN | OPN_TYPE_6CH,
}

# Active flags per chip
OPN_CHIP_ACTIVE_FLAGS: dict[str, list[str]] = {
    chip: [name for name, bit in OPN_TYPE_FLAGS.items() if flags & bit]
    for chip, flags in OPN_CHIP_TYPES.items()
}


# ── OPL family type flags (chiptext.c lines 107-126) ─────────────────────────

OPL_TYPE_WAVESEL  = 0x01  # waveform select
OPL_TYPE_ADPCM    = 0x02  # DELTA-T ADPCM unit
OPL_TYPE_KEYBOARD = 0x04  # keyboard interface
OPL_TYPE_IO       = 0x08  # I/O port
OPL_TYPE_OPL3     = 0x10  # OPL3 Mode
OPL_TYPE_OPL4     = 0x20  # OPL4 Mode

OPL_TYPE_FLAGS: dict[str, int] = {
    "WAVESEL":  OPL_TYPE_WAVESEL,
    "ADPCM":    OPL_TYPE_ADPCM,
    "KEYBOARD": OPL_TYPE_KEYBOARD,
    "IO":       OPL_TYPE_IO,
    "OPL3":     OPL_TYPE_OPL3,
    "OPL4":     OPL_TYPE_OPL4,
}

OPL_CHIP_TYPES: dict[str, int] = {
    "YM3526": 0,
    "YM3812": OPL_TYPE_WAVESEL,
    "Y8950":  OPL_TYPE_ADPCM | OPL_TYPE_KEYBOARD | OPL_TYPE_IO,
    "YMF262": OPL_TYPE_WAVESEL | OPL_TYPE_OPL3,
    "YMF278B": OPL_TYPE_WAVESEL | OPL_TYPE_OPL3 | OPL_TYPE_OPL4,
}

OPL_CHIP_ACTIVE_FLAGS: dict[str, list[str]] = {
    chip: [name for name, bit in OPL_TYPE_FLAGS.items() if flags & bit]
    for chip, flags in OPL_CHIP_TYPES.items()
}


# ── OPN LFO frequency table (chiptext.c line 75) ─────────────────────────────

OPN_LFO_FREQS_HZ: tuple[str, ...] = (
    "3.98", "5.56", "6.02", "6.37", "6.88", "9.63", "48.1", "72.2"
)


# ── YM2151 waveform names (chiptext.c line 71) ───────────────────────────────

YM2151_WAVE_FORMS: tuple[str, ...] = (
    "Sawtooth", "Square", "Triangle", "Random Noise"
)


# ── YMZ280B modes (chiptext.c line 73) ───────────────────────────────────────

YMZ280B_MODES: tuple[str, ...] = (
    "Unknown", "ADPCM", "PCM8", "PCM16"
)


# ── ES5503 modes (chiptext.c) ─────────────────────────────────────────────────

ES5503_MODES: tuple[str, ...] = (
    "Free-Run", "One-Shot", "Sync", "Swap"
)


# ── K054539 sample modes ──────────────────────────────────────────────────────

K054539_SAMPLE_MODES: tuple[str, ...] = (
    "8-bit PCM", "16-bit PCM", "4-bit DPCM", "unknown"
)


# ── OPX sync types (YMF271) ───────────────────────────────────────────────────

OPX_SYNC_TYPES: tuple[str, ...] = (
    "4op FM", "2x 2op FM", "3op FM + PCM", "PCM"
)

# OPX PCM dB volume table
OPX_PCM_DB_VOL: tuple[float, ...] = (
    0.0, 2.5, 6.0, 8.5, 12.0, 14.5, 18.1, 20.6,
    24.1, 26.6, 30.1, 32.6, 36.1, 96.1, 96.1, 96.1,
)


# ── OKIM6258 clock dividers (chiptext.c line 191) ────────────────────────────

OKIM6258_DIVIDERS: tuple[int, ...] = (1024, 768, 512, 512)


# ── OKIM6295 volume table (chiptext.c) ───────────────────────────────────────

OKIM6295_VOLTBL: tuple[int, ...] = (
    0x20, 0x16, 0x10, 0x0B, 0x08, 0x06, 0x04, 0x03,
    0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
)


# ── MultiPCM channel map (chiptext.c) ────────────────────────────────────────

MULTIPCM_VAL2CHAN: tuple[int, ...] = (
     0,  1,  2,  3,  4,  5,  6, -1,
     7,  8,  9, 10, 11, 12, 13, -1,
    14, 15, 16, 17, 18, 19, 20, -1,
    21, 22, 23, 24, 25, 26, 27, -1,
)


# ── NES APU register offsets (chiptext.c lines 152-172) ──────────────────────

NES_APU_REGISTERS: dict[str, int] = {
    "APU_WRA0": 0x00,   # Pulse 1 Volume/Duty
    "APU_WRA1": 0x01,   # Pulse 1 Sweep
    "APU_WRA2": 0x02,   # Pulse 1 Frequency Low
    "APU_WRA3": 0x03,   # Pulse 1 Frequency High / Length
    "APU_WRB0": 0x04,   # Pulse 2 Volume/Duty
    "APU_WRB1": 0x05,   # Pulse 2 Sweep
    "APU_WRB2": 0x06,   # Pulse 2 Frequency Low
    "APU_WRB3": 0x07,   # Pulse 2 Frequency High / Length
    "APU_WRC0": 0x08,   # Triangle Linear Counter
    "APU_WRC2": 0x0A,   # Triangle Frequency Low
    "APU_WRC3": 0x0B,   # Triangle Frequency High / Length
    "APU_WRD0": 0x0C,   # Noise Volume
    "APU_WRD2": 0x0E,   # Noise Mode / Period
    "APU_WRD3": 0x0F,   # Noise Length
    "APU_WRE0": 0x10,   # DMC Flags / Rate
    "APU_WRE1": 0x11,   # DMC Direct Load
    "APU_WRE2": 0x12,   # DMC Sample Address
    "APU_WRE3": 0x13,   # DMC Sample Length
    "APU_SMASK": 0x15,  # Status / Channel Enable
    "APU_IRQCTRL": 0x17,  # Frame Counter / IRQ
}

# NES DPCM rate lookup table (chiptext.c line 172) — CPU cycles per sample
NES_DPCM_CLOCKS: tuple[int, ...] = (
    428, 380, 340, 320, 286, 254, 226, 214,
    190, 160, 142, 128, 106,  85,  72,  54,
)


# ── Game Boy DMG register offsets (chiptext.c lines 128-149) ─────────────────

GB_DMG_REGISTERS: dict[str, int] = {
    "NR10": 0x00,   # CH1 Sweep
    "NR11": 0x01,   # CH1 Sound Length / Wave Duty
    "NR12": 0x02,   # CH1 Volume Envelope
    "NR13": 0x03,   # CH1 Frequency Low
    "NR14": 0x04,   # CH1 Frequency High / Control
    "NR21": 0x06,   # CH2 Sound Length / Wave Duty
    "NR22": 0x07,   # CH2 Volume Envelope
    "NR23": 0x08,   # CH2 Frequency Low
    "NR24": 0x09,   # CH2 Frequency High / Control
    "NR30": 0x0A,   # CH3 Sound On/Off
    "NR31": 0x0B,   # CH3 Sound Length
    "NR32": 0x0C,   # CH3 Output Level
    "NR33": 0x0D,   # CH3 Frequency Low
    "NR34": 0x0E,   # CH3 Frequency High / Control
    "NR41": 0x10,   # CH4 Sound Length
    "NR42": 0x11,   # CH4 Volume Envelope
    "NR43": 0x12,   # CH4 Polynomial Counter
    "NR44": 0x13,   # CH4 Counter/Consecutive / Initial
    "NR50": 0x14,   # Channel Control / Volume
    "NR51": 0x15,   # Sound Output Terminal Selection
    "NR52": 0x16,   # Sound On/Off
}

# Game Boy wave duty cycles in % (chiptext.c line 149)
GB_WAVE_DUTY_PCT: tuple[float, ...] = (12.5, 25.0, 50.0, 75.0)

# Game Boy noise modes
GB_NOISE_MODES: tuple[str, ...] = ("Counter", "Consecutive")


# ── Atari Pokey register offsets (chiptext.c lines 175-189) ──────────────────

ATARI_POKEY_REGISTERS: dict[str, int] = {
    "AUDF1":  0x00,   # Audio Frequency 1
    "AUDC1":  0x01,   # Audio Control 1
    "AUDF2":  0x02,   # Audio Frequency 2
    "AUDC2":  0x03,   # Audio Control 2
    "AUDF3":  0x04,   # Audio Frequency 3
    "AUDC3":  0x05,   # Audio Control 3
    "AUDF4":  0x06,   # Audio Frequency 4
    "AUDC4":  0x07,   # Audio Control 4
    "AUDCTL": 0x08,   # Audio Control
    "STIMER": 0x09,   # Start Timers
    "SKREST": 0x0A,   # Reset LFSR
    "POTGO":  0x0B,   # Start Pot Scan Sequence
    "SEROUT": 0x0D,   # Serial Port Data Output
    "IRQEN":  0x0E,   # IRQ Enable
    "SKCTL":  0x0F,   # Serial Port Control
}


# ── SN76489 noise constants ───────────────────────────────────────────────────

SN76489_NOISE_TYPES: tuple[str, ...] = ("Periodic", "White")
SN76489_NOISE_FREQS: tuple[str, ...] = (
    "High (6927Hz)", "Med (3463Hz)", "Low (1731Hz)", "Ch 2"
)


# ── AY-3-8910 / YM2149 note strings ──────────────────────────────────────────

NOTE_STRINGS: tuple[str, ...] = (
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
)


# ── Supported chips registry ──────────────────────────────────────────────────

SUPPORTED_CHIPS: frozenset[str] = frozenset({
    "NES_APU", "GB_DMG", "Pokey",
    "YM2203", "YM2608", "YM2610", "YM2612",      # OPN family
    "YM3526", "YM3812", "Y8950", "YMF262", "YMF278B",  # OPL family
    "YMZ280B", "OKIM6258", "OKIM6295", "MultiPCM",
    "ES5503", "K054539", "YMF271", "SN76489",
})


class Adapter:
    """
    Adapter exposing chiptext.c static chip constants.

    Tier A — no build required.
    """
    toolkit  = "chiptext"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        chip = payload.get("chip", "").upper().replace("-", "_")
        result = self._query(chip)
        return self.normalize(result)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def is_available(self) -> bool:
        return True

    def get_opn_type(self, chip: str) -> dict[str, Any]:
        """Return OPN family type flags for the given chip."""
        chip = chip.upper()
        if chip not in OPN_CHIP_TYPES:
            raise AdapterError(f"Unknown OPN chip: {chip!r}. Valid: {sorted(OPN_CHIP_TYPES)}")
        return {
            "chip":         chip,
            "type_value":   OPN_CHIP_TYPES[chip],
            "active_flags": OPN_CHIP_ACTIVE_FLAGS[chip],
            "flag_bits":    OPN_TYPE_FLAGS,
            "adapter":      "chiptext",
        }

    def get_opl_type(self, chip: str) -> dict[str, Any]:
        """Return OPL family type flags for the given chip."""
        chip = chip.upper()
        if chip not in OPL_CHIP_TYPES:
            raise AdapterError(f"Unknown OPL chip: {chip!r}. Valid: {sorted(OPL_CHIP_TYPES)}")
        return {
            "chip":         chip,
            "type_value":   OPL_CHIP_TYPES[chip],
            "active_flags": OPL_CHIP_ACTIVE_FLAGS[chip],
            "flag_bits":    OPL_TYPE_FLAGS,
            "adapter":      "chiptext",
        }

    def _query(self, chip: str) -> dict[str, Any]:
        base: dict[str, Any] = {"chip": chip, "adapter": "chiptext"}

        if chip == "NES_APU":
            base["registers"] = NES_APU_REGISTERS
            base["tables"]    = {"dpcm_clocks": NES_DPCM_CLOCKS}

        elif chip == "GB_DMG":
            base["registers"] = GB_DMG_REGISTERS
            base["tables"]    = {
                "wave_duty_pct": GB_WAVE_DUTY_PCT,
                "noise_modes":   GB_NOISE_MODES,
            }

        elif chip == "POKEY":
            base["registers"] = ATARI_POKEY_REGISTERS

        elif chip == "SN76489":
            base["tables"] = {
                "noise_types": SN76489_NOISE_TYPES,
                "noise_freqs": SN76489_NOISE_FREQS,
            }

        elif chip in OPN_CHIP_TYPES:
            base["flags"]  = OPN_TYPE_FLAGS
            base["tables"] = {
                "lfo_freqs_hz": OPN_LFO_FREQS_HZ,
                "chip_type":    OPN_CHIP_TYPES[chip],
                "active_flags": OPN_CHIP_ACTIVE_FLAGS[chip],
            }
            if chip == "YM2151":
                base["tables"]["waveforms"] = YM2151_WAVE_FORMS

        elif chip in OPL_CHIP_TYPES:
            base["flags"]  = OPL_TYPE_FLAGS
            base["tables"] = {
                "chip_type":    OPL_CHIP_TYPES[chip],
                "active_flags": OPL_CHIP_ACTIVE_FLAGS[chip],
            }

        elif chip == "YMZ280B":
            base["tables"] = {"modes": YMZ280B_MODES}

        elif chip == "OKIM6258":
            base["tables"] = {"dividers": OKIM6258_DIVIDERS}

        elif chip == "OKIM6295":
            base["tables"] = {"voltbl": OKIM6295_VOLTBL}

        elif chip == "MULTIPCM":
            base["tables"] = {"val2chan": MULTIPCM_VAL2CHAN}

        elif chip == "ES5503":
            base["tables"] = {"modes": ES5503_MODES}

        elif chip == "K054539":
            base["tables"] = {"sample_modes": K054539_SAMPLE_MODES}

        elif chip == "YMF271":
            base["tables"] = {
                "sync_types":  OPX_SYNC_TYPES,
                "pcm_db_vol":  OPX_PCM_DB_VOL,
            }

        else:
            raise AdapterError(
                f"Unknown chip {chip!r}. Supported: {sorted(SUPPORTED_CHIPS)}"
            )

        return base

    def all_chips(self) -> list[str]:
        return sorted(SUPPORTED_CHIPS)
