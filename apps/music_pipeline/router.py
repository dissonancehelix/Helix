"""
router.py — Format dispatch to Tier A parsers and Tier B emulation
===================================================================
Maps file extensions to:
  - Tier A: static parsers (spc_parser, nsf_parser, sid_parser, vgm_parser)
  - Tier B: emulation bridges (libvgm_bridge, gme_bridge)

Usage:
    result = FormatRouter().parse(path)     # Tier A static parse
    events = FormatRouter().trace(path)     # Tier B chip-state trace

Note: ID666 (SPC) and GD3 (VGM) tags are intentionally NOT used.
      Metadata is sourced from the Helix library (codex/library/music/).
      Only structural/synthesis data is extracted from format headers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Extension → decoder routing tables
# ---------------------------------------------------------------------------

# Tier A: static parsers
_TIER_A_PARSERS: dict[str, str] = {
    ".spc":  "spc",
    ".nsf":  "nsf",
    ".nsfe": "nsf",
    ".sid":  "sid",
    ".psid": "sid",
    ".rsid": "sid",
    ".vgm":  "vgm",
    ".vgz":  "vgm",
    ".gym":  "vgm",
}

# Tier B: emulation type
_TIER_B_ENGINE: dict[str, str] = {
    ".vgm":     "libvgm",
    ".vgz":     "libvgm",
    ".gym":     "libvgm",
    ".spc":     "gme",
    ".nsf":     "gme",
    ".nsfe":    "gme",
    ".gbs":     "gme",
    ".hes":     "gme",
    ".kss":     "gme",
    ".ay":      "gme",
    ".sgc":     "gme",
    # vgmstream formats (render-to-waveform → essentia path)
    ".2sf":     "vgmstream",
    ".mini2sf": "vgmstream",
    ".ncsf":    "vgmstream",
    ".minincsf":"vgmstream",
    ".usf":     "vgmstream",
    ".miniusf": "vgmstream",
    ".gsf":     "vgmstream",
    ".psf":     "vgmstream",
    ".psf2":    "vgmstream",
    ".ssf":     "vgmstream",
    ".dsf":     "vgmstream",
    ".s98":     "vgmstream",
    ".minipsf": "vgmstream",
}

# Waveform-only formats — no chip data, straight to essentia
_WAVEFORM_EXTENSIONS: set[str] = {
    ".mp3", ".opus", ".flac", ".ogg", ".wav", ".m4a", ".aac"
}

# All known emulated formats (Tier A+B)
ALL_EMULATED_EXTENSIONS = set(_TIER_A_PARSERS) | set(_TIER_B_ENGINE)


class FormatRouter:
    """Routes files to appropriate Tier A parser or Tier B emulation bridge."""

    def get_decoder_type(self, file_path: str) -> str | None:
        ext = Path(file_path).suffix.lower()
        return _TIER_B_ENGINE.get(ext)

    def get_parser_type(self, file_path: str) -> str | None:
        ext = Path(file_path).suffix.lower()
        return _TIER_A_PARSERS.get(ext)

    def is_waveform_only(self, path: Path) -> bool:
        return path.suffix.lower() in _WAVEFORM_EXTENSIONS

    def route(self, file_path: str) -> str:
        """Legacy API: return decoder engine name."""
        t = self.get_decoder_type(file_path)
        return t or "vgmstream"

    # ------------------------------------------------------------------
    # Tier A: static parse
    # ------------------------------------------------------------------

    def parse(self, path: Path, enrich: bool = True) -> dict[str, Any]:
        """
        Run the Tier A static parser for `path`.
        Returns the track's .to_dict() result or an error dict.

        Note: ID666 (SPC) and GD3 (VGM) tag data is present in the raw
        parser output but is ignored by the pipeline. Library metadata
        is used instead. Parsers extract synthesis/structure data only.

        If `enrich=True`, codec-specific reference enrichment is appended
        via CodecReferenceLibrary. Pass `enrich=False` for raw parse output.
        """
        ext = path.suffix.lower()
        parser_type = _TIER_A_PARSERS.get(ext)

        if parser_type == "spc":
            from domains.music.parsing.spc_parser import parse
            result = parse(path).to_dict()

        elif parser_type == "nsf":
            from domains.music.parsing.nsf_parser import parse
            result = parse(path).to_dict()

        elif parser_type == "sid":
            from domains.music.parsing.sid_parser import parse
            result = parse(path).to_dict()

        elif parser_type == "vgm":
            from domains.music.parsing.vgm_parser import parse
            track = parse(path)
            result = {
                "path":             str(track.path),
                "format":           ext.lstrip(".").upper(),
                "version":          hex(track.header.version),
                "total_samples":    track.header.total_samples,
                "loop_offset":      track.header.loop_offset,
                "loop_samples":     track.header.loop_samples,
                "loop_point_s":     track.header.loop_offset / 44100.0 if track.header.loop_offset else None,
                "duration_s":       track.header.total_samples / 44100.0,
                "has_loop":         bool(track.header.loop_offset),
                "chips":            _vgm_chip_names(track.header),
                "ym2612_clock":     track.header.ym2612_clock,
                "psg_clock":        track.header.sn76489_clock,
                "ym2151_clock":     track.header.ym2151_clock,
                "event_count":      len(track.events),
                "error":            track.error,
            }

        else:
            result = {
                "path": str(path),
                "format": ext.lstrip(".").upper(),
                "error": f"No Tier A parser for {ext}",
            }

        if enrich:
            try:
                from core.engine.adapters.adapter_chip_library import enrich as _enrich
                result = _enrich(path, result)
            except Exception:
                pass  # enrichment is always non-blocking

        return result

    # ------------------------------------------------------------------
    # Tier B: chip-state trace
    # ------------------------------------------------------------------

    def trace(self, path: Path, track: int = 0,
              sample_rate: int = 44100,
              enrich: bool = True) -> list[dict[str, Any]]:
        """
        Run Tier B emulation trace for `path`.
        Returns list of ChipEvent dicts (may be empty if not supported).

        For VGM/VGZ: uses libvgm bridge.
        For SPC/NSF/GBS etc: uses GME bridge.
        For PSF/USF/mini*: uses vgmstream render → waveform (no chip events).
        """
        engine = _TIER_B_ENGINE.get(path.suffix.lower(), "")
        events: list[dict[str, Any]] = []

        if engine == "libvgm":
            try:
                from core.engine.adapters.adapter_libvgm import Adapter
                events = Adapter().execute({"file_path": str(path), "track": track})
            except Exception:
                pass

        elif engine == "gme":
            try:
                from core.engine.adapters.adapter_gme import Adapter
                events = Adapter().execute({"file_path": str(path), "track": track})
            except Exception:
                pass

        elif engine == "vgmstream":
            # vgmstream produces waveform only — no chip events
            # caller should use waveform_analyze() instead
            return []

        return events

    # ------------------------------------------------------------------
    # Waveform path: essentia
    # ------------------------------------------------------------------

    def waveform_analyze(self, path: Path) -> dict[str, Any]:
        """
        Run waveform analysis on an audio file.
        Tries essentia first; falls back to librosa if essentia is unavailable.
        Used for: mp3, opus, flac, m4a, ogg, wav, and vgmstream-rendered files.
        """
        try:
            from core.engine.adapters.adapter_essentia import Adapter
            result = Adapter().execute({"file_path": str(path)})
            if result.get("available"):
                return result
        except Exception:
            pass

        # Fallback: librosa
        try:
            from core.engine.adapters.adapter_librosa import Adapter as LibrosaAdapter
            return LibrosaAdapter().execute({"file_path": str(path)})
        except Exception as e:
            return {"source_path": str(path), "adapter": "none",
                    "available": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def supports_tier_a(self, path: Path) -> bool:
        return path.suffix.lower() in _TIER_A_PARSERS

    def supports_tier_b(self, path: Path) -> bool:
        return path.suffix.lower() in _TIER_B_ENGINE

    @staticmethod
    def is_emulated(ext: str) -> bool:
        return ext.lstrip(".").lower() in {e.lstrip(".") for e in ALL_EMULATED_EXTENSIONS}


def _vgm_chip_names(header) -> list[str]:
    """Derive chip name list from VGM header clock fields."""
    chips = []
    if getattr(header, "ym2612_clock", 0):   chips.append("YM2612")
    if getattr(header, "sn76489_clock", 0):  chips.append("SN76489")
    if getattr(header, "ym2151_clock", 0):   chips.append("YM2151")
    if getattr(header, "ym2413_clock", 0):   chips.append("YM2413")
    return chips
