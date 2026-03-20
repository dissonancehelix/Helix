"""
router.py — Format dispatch to Tier A parsers and Tier B emulation
===================================================================
Maps file extensions to:
  - Tier A: static parsers (spc_parser, nsf_parser, sid_parser, vgm_parser)
  - Tier B: emulation bridges (libvgm_bridge, gme_bridge)

Usage:
    result = FormatRouter().parse(path)     # Tier A static parse
    events = FormatRouter().trace(path)     # Tier B chip-state trace
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
    ".vgm":  "libvgm",
    ".vgz":  "libvgm",
    ".gym":  "libvgm",
    ".spc":  "gme",
    ".nsf":  "gme",
    ".nsfe": "gme",
    ".gbs":  "gme",
    ".hes":  "gme",
    ".kss":  "gme",
    ".ay":   "gme",
    ".sgc":  "gme",
    # vgmstream formats
    ".2sf":     "vgmstream",
    ".ncsf":    "vgmstream",
    ".usf":     "vgmstream",
    ".gsf":     "vgmstream",
    ".psf":     "vgmstream",
    ".psf2":    "vgmstream",
    ".ssf":     "vgmstream",
    ".dsf":     "vgmstream",
    ".s98":     "vgmstream",
    ".minipsf": "vgmstream",
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

        If `enrich=True` (default), codec-specific reference enrichment is
        appended automatically via CodecReferenceLibrary.  Pass
        `enrich=False` for raw parse output without reference lookup.
        """
        ext = path.suffix.lower()
        parser_type = _TIER_A_PARSERS.get(ext)

        if parser_type == "spc":
            from domains.music.parsers.spc_parser import parse
            result = parse(path).to_dict()

        elif parser_type == "nsf":
            from domains.music.parsers.nsf_parser import parse
            result = parse(path).to_dict()

        elif parser_type == "sid":
            from domains.music.parsers.sid_parser import parse
            result = parse(path).to_dict()

        elif parser_type == "vgm":
            try:
                from domains.music.vgm_parser import parse_vgm_file
                track = parse_vgm_file(path)
                result = track.__dict__ if hasattr(track, "__dict__") else {}
            except ImportError:
                result = {"path": str(path), "format": ext.lstrip(".").upper(),
                          "error": "vgm_parser not importable"}

        else:
            result = {"path": str(path), "format": ext.lstrip(".").upper(),
                      "error": f"No Tier A parser for {ext}"}

        if enrich:
            try:
                from domains.music.analysis.codec_reference import enrich as _enrich
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

        If `enrich=True` (default), the raw event list is passed through
        CodecReferenceLibrary.enrich_trace_result() so callers can access
        per-channel patch-match data in result["reference"].
        """
        try:
            from domains.music.emulation.chip_state_tracer import trace
            events = trace(path, track=track, sample_rate=sample_rate)
        except Exception:
            events = []

        if enrich and events:
            try:
                from domains.music.analysis.codec_reference import get_library
                enriched = get_library().enrich_trace_result(path, events)
                return enriched  # type: ignore[return-value]
            except Exception:
                pass  # enrichment is always non-blocking

        return events

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
