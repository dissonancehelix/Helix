"""
adapter_gme.py — Helix adapter for Game_Music_Emu (gme)
=========================================================
Wraps the gme ctypes bridge at:
    domains/music/measurement_synthesis/gme_bridge.py

Purpose:
    Decode chip music formats not covered by libvgm:
    SPC (SNES), NSF/NSFE (NES), GBS (Game Boy), HES (PC Engine),
    KSS, AY, SGC (MSX/etc.), GYM (Genesis)

Input:
    file_path (str | Path)  — path to chip music file
    track     (int)         — sub-track index (default: 0)
    sample_rate (int)       — sample rate (default: 44100)

Output (dict — ControlSequence schema):
    {
        "format":          str,         # file extension
        "chip_target":     str,         # chip name (SPC700, 2A03, DMG, etc.)
        "event_count":     int,
        "timing_data":     list[float],
        "register_writes": list[dict],
        "sample_rate":     int,
        "source_path":     str,
        "adapter":         "gme",
        "bridge_mode":     "gme" | "vgmstream" | "empty",
    }

Adapter rules:
    • No Helix logic. Translation only.
    • Falls back to vgmstream proxy on gme miss.
    • Never raises on bridge miss — returns empty ControlSequence with status.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    """Raised when an adapter cannot process its input."""


# Chip name mapping by extension
_CHIP_MAP: dict[str, str] = {
    ".spc":  "SPC700",
    ".nsf":  "2A03",
    ".nsfe": "2A03",
    ".gbs":  "DMG",
    ".hes":  "HuC6280",
    ".kss":  "AY-3-8910",
    ".ay":   "AY-3-8910",
    ".sgc":  "AY-3-8910",
    ".gym":  "YM2612",
    ".vgm":  "multi",
    ".vgz":  "multi",
}

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(_CHIP_MAP.keys())


class Adapter:
    """
    Adapter wrapping gme_bridge for SNES/NES/GBS/etc. chip formats.

    Correct call path:
        HIL → INGEST_TRACK operator → Adapter → gme_bridge
    """
    toolkit = "gme"
    substrate = "music"

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Decode a chip music file and return a ControlSequence dict.

        Returns an empty-events ControlSequence on bridge unavailability
        (non-blocking — upstream operators treat this as Tier A only).
        """
        file_path = payload.get("file_path")
        track = payload.get("track", 0)
        sample_rate = payload.get("sample_rate", 44100)
        
        path = Path(file_path)
        ext  = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise AdapterError(
                f"Unsupported format {ext!r}. "
                f"GmeAdapter handles: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        try:
            from domains.music.measurement_synthesis.gme_bridge import GmeBridge
            bridge = GmeBridge()
            events = bridge.render(path, track=track, sample_rate=sample_rate)
            mode   = "gme" if bridge.is_available() else "vgmstream"
        except ImportError:
            events = []
            mode   = "empty"
        except Exception as exc:
            raise AdapterError(f"gme render failed for {path}: {exc}") from exc

        return self.normalize(events, path, ext, track, sample_rate, mode)

    def is_available(self) -> bool:
        try:
            from domains.music.measurement_synthesis.gme_bridge import GmeBridge  # noqa
            return True
        except ImportError:
            return False

    def normalize(
        self,
        events: list[Any],
        path: Path,
        ext: str,
        track: int,
        sample_rate: int,
        mode: str,
    ) -> dict[str, Any]:
        register_writes: list[dict] = []
        timing_data:     list[float] = []

        for ev in events:
            t = float(getattr(ev, "time", 0.0))
            timing_data.append(t)
            register_writes.append({
                "chip":     str(getattr(ev, "chip", _CHIP_MAP.get(ext, "unknown"))),
                "channel":  getattr(ev, "channel",  0),
                "register": getattr(ev, "register", None),
                "value":    getattr(ev, "value",    None),
                "time":     t,
            })

        return {
            "format":          ext.lstrip("."),
            "chip_target":     _CHIP_MAP.get(ext, "unknown"),
            "event_count":     len(events),
            "timing_data":     timing_data[:1000],
            "register_writes": register_writes,
            "sample_rate":     sample_rate,
            "track_index":     track,
            "source_path":     str(path),
            "adapter":         "gme",
            "bridge_mode":     mode,
        }
