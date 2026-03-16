"""
chip_state_tracer.py — Tier B unified chip-state trace
=======================================================
Dispatches to libvgm_bridge or gme_bridge depending on file format,
then emits a normalised sequence of ChipState snapshots.

Each snapshot records the full logical state of all chip channels at
a given sample timestamp, derived from accumulated register writes.
This feeds both:
  - feature_extractor (keyon_density, rhythmic_entropy, TL means …)
  - vgm_note_reconstructor (note events via key-on/off detection)

Public API
----------
trace(path: Path, track: int = 0, sample_rate: int = 44100) -> list[dict]
    Returns list of snapshot dicts:
    {
        "t":    int,    # sample offset
        "chip": str,    # e.g. "YM2612"
        "ch":   int,    # logical channel (0-based)
        "op":   int,    # operator (-1 if n/a)
        "reg":  int,    # register address written
        "val":  int,    # value written
    }

trace_path_supported(path: Path) -> bool
    True if at least one bridge supports this file.

is_tier_b(path: Path) -> bool
    True if Tier B (real emulated timing) is available for this file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from labs.music_lab.emulation.libvgm_bridge import ChipEvent, render as _vgm_render, is_available as _vgm_avail
from labs.music_lab.emulation.gme_bridge    import render as _gme_render, supports as _gme_supports, is_available as _gme_avail

_VGM_EXTENSIONS = {".vgm", ".vgz", ".gym"}
_GME_EXTENSIONS = {".spc", ".nsf", ".nsfe", ".gbs", ".hes", ".kss", ".ay", ".sgc"}


def trace_path_supported(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext in _VGM_EXTENSIONS or _gme_supports(path)


def is_tier_b(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext in _VGM_EXTENSIONS:
        return _vgm_avail()
    return _gme_avail()


def trace(path: Path, track: int = 0, sample_rate: int = 44100) -> list[dict[str, Any]]:
    """
    Dispatch to the appropriate bridge and return normalised ChipEvent dicts.
    Always returns a list (may be empty).
    """
    ext = path.suffix.lower()

    events: list[ChipEvent]
    if ext in _VGM_EXTENSIONS:
        events = _vgm_render(path, sample_rate)
    elif _gme_supports(path):
        events = _gme_render(path, track, sample_rate)
    else:
        return []

    return [
        {
            "t":    e.t,
            "chip": e.chip,
            "ch":   e.ch,
            "op":   e.op,
            "reg":  e.reg,
            "val":  e.val,
        }
        for e in events
    ]


# ---------------------------------------------------------------------------
# Channel-state accumulator (used by feature_extractor and reconstructor)
# ---------------------------------------------------------------------------

class ChannelStateAccumulator:
    """
    Accumulates raw register writes into per-channel logical state.
    Designed for YM2612; other chips use only a subset of fields.
    """

    def __init__(self) -> None:
        # 6 FM channels + SN channels
        self._ch: dict[tuple[str, int], dict[str, Any]] = {}

    def _get(self, chip: str, ch: int) -> dict[str, Any]:
        key = (chip, ch)
        if key not in self._ch:
            self._ch[key] = {
                "chip": chip, "ch": ch,
                "keyon": False, "slots_on": 0,
                "fnum": 0, "block": 0,
                "tl": [127, 127, 127, 127],   # per-operator TL (0=max, 127=min)
                "alg": 0, "fb": 0,
                "ams": 0, "fms": 0,
                "last_keyon_t": -1, "last_keyoff_t": -1,
            }
        return self._ch[key]

    def apply(self, event: dict[str, Any]) -> None:
        chip = event["chip"]
        ch   = event["ch"]
        reg  = event["reg"]
        val  = event["val"]
        t    = event["t"]

        if ch < 0:
            return  # unknown channel

        s = self._get(chip, ch)

        if chip == "YM2612":
            if reg == 0x28:
                slots = (val >> 4) & 0x0F
                on    = slots != 0
                s["keyon"]      = on
                s["slots_on"]   = slots
                if on and not s["keyon"]:
                    s["last_keyon_t"] = t
                elif not on and s["keyon"]:
                    s["last_keyoff_t"] = t

            elif 0xA0 <= reg <= 0xA2:    # FNUM_1
                s["fnum"] = (s["fnum"] & 0x700) | val

            elif 0xA4 <= reg <= 0xA6:    # FNUM_2 + block
                s["block"] = (val >> 3) & 0x07
                s["fnum"]  = ((val & 0x07) << 8) | (s["fnum"] & 0xFF)

            elif 0xB0 <= reg <= 0xB2:    # ALG + FB
                s["alg"] = val & 0x07
                s["fb"]  = (val >> 3) & 0x07

            elif 0xB4 <= reg <= 0xB6:    # AMS + FMS
                s["ams"] = (val >> 4) & 0x03
                s["fms"] = val & 0x07

            elif 0x40 <= reg <= 0x4F:    # TL per operator
                op = (reg >> 2) & 0x03
                if 0 <= op < 4:
                    s["tl"][op] = val & 0x7F

        # SN76489 — simplified: volume latch
        elif chip == "SN76489":
            if (val & 0x90) == 0x90:
                s["tl"][0] = val & 0x0F

    def snapshot(self) -> list[dict[str, Any]]:
        """Return current state of all seen channels."""
        return [dict(v) for v in self._ch.values()]

    def keyon_density(self) -> float:
        """Fraction of channels that are currently keyed on."""
        channels = list(self._ch.values())
        if not channels:
            return 0.0
        return sum(1 for c in channels if c["keyon"]) / len(channels)

    def tl_means(self) -> tuple[float, float]:
        """Mean TL for op1 and op2 across all channels."""
        vals1 = [c["tl"][0] for c in self._ch.values()]
        vals2 = [c["tl"][1] for c in self._ch.values()]
        mean1 = sum(vals1) / len(vals1) if vals1 else 64.0
        mean2 = sum(vals2) / len(vals2) if vals2 else 64.0
        return mean1, mean2
