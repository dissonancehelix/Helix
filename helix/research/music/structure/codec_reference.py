"""
codec_reference.py — Codec-dependent reference library dispatcher
=================================================================
Every audio format routes to its associated source code and reference
tools automatically. Libraries are loaded lazily and cached in memory
(and on disk for the build-heavy SMPS voice library).

Codec keys:
  vgm_ym2612   Genesis/Mega Drive  → SMPS Z80 v1.3 + 68k v1.1 voice patches
  spc_spc700   SNES                → SPC parser (no additional source in ref dir)
  nsf_2a03     NES                 → NSF parser
  sid_6581     C64 SID             → SID parser
  gems         GEMS patch bank     → GEMS FMLIB (patch bank stub)

Integration points:
  FormatRouter.parse()   calls enrich_parse_result()  (Tier A enrichment)
  FormatRouter.trace()   calls enrich_trace_result()  (Tier B enrichment)
  feature_vector.py      calls get_voice_library()    for patch-match dims

Usage:
    from domains.music.domain_analysis.codec_reference import CodecReferenceLibrary
    lib = CodecReferenceLibrary()
    result = lib.enrich_parse_result(path, parse_result)
    # result["reference"]["patch_matches"] → list of closest SMPS voice matches
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Codec constants
# ---------------------------------------------------------------------------

CODEC_VGM_YM2612 = "vgm_ym2612"   # Genesis / Mega Drive (SMPS + GEMS)
CODEC_SPC_SPC700 = "spc_spc700"   # SNES / Super Famicom
CODEC_NSF_2A03   = "nsf_2a03"     # NES / Famicom
CODEC_SID_6581   = "sid_6581"     # Commodore 64
CODEC_GEMS       = "gems"          # GEMS engine (SoA Genesis titles)

# Extension → primary codec
_EXT_TO_CODEC: dict[str, str] = {
    ".vgm":  CODEC_VGM_YM2612,
    ".vgz":  CODEC_VGM_YM2612,
    ".gym":  CODEC_VGM_YM2612,
    ".spc":  CODEC_SPC_SPC700,
    ".nsf":  CODEC_NSF_2A03,
    ".nsfe": CODEC_NSF_2A03,
    ".sid":  CODEC_SID_6581,
    ".psid": CODEC_SID_6581,
    ".rsid": CODEC_SID_6581,
}

# Reference source directories under TEMP_DIR (populated from Desktop/temp)
_SOURCE_DIRS: dict[str, dict[str, str]] = {
    CODEC_VGM_YM2612: {
        "smps_z80_v13": "SMPS-Z80_source_code/ver13",
        "smps_68k_v11": "SMPS-68000_source_code/ver11",
    },
    CODEC_GEMS: {
        "gems_fmlib": "GEMS/FMLIB",
    },
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class CodecReferenceLibrary:
    """
    Codec-dependent reference library dispatcher.

    Instantiate once and reuse; voice libraries are loaded lazily
    and cached in memory plus written to codex/library/tech/smps_voice_library.json.
    """

    def __init__(self) -> None:
        self._cache: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def codec_for_path(self, path: Path) -> str | None:
        return _EXT_TO_CODEC.get(path.suffix.lower())

    def get_voice_library(self, codec: str) -> list[dict[str, Any]]:
        """Return the loaded voice/patch library for *codec* (empty list if none)."""
        if codec not in self._cache:
            self._cache[codec] = self._load(codec)
        return self._cache[codec]

    def enrich_parse_result(
        self,
        path: Path,
        parse_result: dict[str, Any],
        chip_regs: dict[int, int] | None = None,
    ) -> dict[str, Any]:
        """
        Attach a ``reference`` sub-dict to *parse_result* with codec-specific
        enrichment.  If *chip_regs* is provided (YM2612 register snapshot from
        a single FM channel), patch matching is also performed.

        Always returns *parse_result* (mutated in-place, also returned for
        convenience).
        """
        codec = self.codec_for_path(path)
        if codec is None:
            return parse_result

        ref: dict[str, Any] = {
            "codec":         codec,
            "library_size":  0,
            "patch_matches": [],
            "source_dirs":   self._resolved_source_dirs(codec),
        }

        if codec == CODEC_VGM_YM2612:
            library = self.get_voice_library(codec)
            ref["library_size"] = len(library)
            if chip_regs and library:
                ref["patch_matches"] = self._match_patches(chip_regs, library)

        elif codec == CODEC_SPC_SPC700:
            ref["notes"] = "SPC700 — static parse only; no additional voice source in ref dir"

        elif codec == CODEC_NSF_2A03:
            ref["notes"] = "2A03 — static parse only; no additional voice source in ref dir"

        elif codec == CODEC_SID_6581:
            ref["notes"] = "SID 6581/8580 — static parse only; no additional voice source in ref dir"

        parse_result["reference"] = ref
        return parse_result

    def enrich_trace_result(
        self,
        path: Path,
        trace_events: list[dict[str, Any]],
        per_channel_regs: dict[int, dict[int, int]] | None = None,
    ) -> dict[str, Any]:
        """
        Post-process a Tier B chip-state trace with reference enrichment.
        Returns a new dict: {
            "events": trace_events,
            "reference": { "codec": ..., "channel_patches": {ch: [...matches]} }
        }
        """
        codec = self.codec_for_path(path)
        result: dict[str, Any] = {"events": trace_events, "reference": {"codec": codec}}

        if codec == CODEC_VGM_YM2612 and per_channel_regs:
            library = self.get_voice_library(codec)
            channel_patches: dict[str, list[dict[str, Any]]] = {}
            for ch, regs in per_channel_regs.items():
                channel_patches[str(ch)] = self._match_patches(regs, library)
            result["reference"]["channel_patches"] = channel_patches
            result["reference"]["library_size"] = len(library)

        return result

    def build_all(self, force: bool = False) -> dict[str, int]:
        """
        Eagerly build all reference libraries (call once on setup).
        Returns {codec: library_size} mapping.
        """
        sizes: dict[str, int] = {}
        for codec in [CODEC_VGM_YM2612]:
            if force:
                self._cache.pop(codec, None)
                try:
                    from domains.music.ingestion.config import SMPS_VOICE_LIBRARY_PATH
                    SMPS_VOICE_LIBRARY_PATH.unlink(missing_ok=True)
                except Exception:
                    pass
            sizes[codec] = len(self.get_voice_library(codec))
        return sizes

    # ------------------------------------------------------------------
    # Internal loaders
    # ------------------------------------------------------------------

    def _load(self, codec: str) -> list[dict[str, Any]]:
        if codec == CODEC_VGM_YM2612:
            return self._load_smps_library()
        return []

    def _load_smps_library(self) -> list[dict[str, Any]]:
        """
        Load SMPS voice library from disk cache or build from source.
        Source trees: SMPS-Z80_source_code/ver13 + SMPS-68000_source_code/ver11
        Cache: codex/library/tech/smps_voice_library.json
        """
        try:
            from domains.music.ingestion.config import TEMP_DIR, SMPS_VOICE_LIBRARY_PATH as cache_path
        except ImportError:
            log.warning("codec_reference: config not importable — no voice library loaded")
            return []

        # Return cached build
        if cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    library = json.load(f)
                log.debug("codec_reference: loaded %d SMPS voices from %s", len(library), cache_path)
                return library
            except Exception as exc:
                log.warning("codec_reference: cache corrupt (%s), rebuilding", exc)

        # Build from source
        try:
            from domains.music.parsing.smps_voice_parser import build_reference_library
        except ImportError as exc:
            log.warning("codec_reference: smps_voice_parser not importable (%s)", exc)
            return []

        source_dirs: dict[str, Path] = {}
        for name, rel in _SOURCE_DIRS[CODEC_VGM_YM2612].items():
            candidate = TEMP_DIR / rel
            if candidate.is_dir():
                source_dirs[name] = candidate
            else:
                log.debug("codec_reference: source dir not found: %s", candidate)

        if not source_dirs:
            log.warning(
                "codec_reference: no SMPS source dirs found under %s — "
                "voice library will be empty",
                TEMP_DIR,
            )
            return []

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            library = build_reference_library(source_dirs, cache_path)
            log.info(
                "codec_reference: built SMPS voice library — %d patches from %s",
                len(library),
                list(source_dirs.keys()),
            )
            return library
        except Exception as exc:
            log.warning("codec_reference: build_reference_library failed (%s)", exc)
            return []

    # ------------------------------------------------------------------
    # Patch matching
    # ------------------------------------------------------------------

    def _match_patches(
        self,
        chip_regs: dict[int, int],
        library: list[dict[str, Any]],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Delegate to smps_voice_parser.match_channel_to_patch()."""
        try:
            from domains.music.parsing.smps_voice_parser import match_channel_to_patch
            return match_channel_to_patch(chip_regs, library, top_k=top_k)
        except Exception as exc:
            log.debug("codec_reference: match_channel_to_patch failed (%s)", exc)
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolved_source_dirs(self, codec: str) -> dict[str, str]:
        """Return source dir paths as strings for the reference metadata."""
        try:
            from domains.music.ingestion.config import TEMP_DIR
        except ImportError:
            return {}
        dirs: dict[str, str] = {}
        for name, rel in _SOURCE_DIRS.get(codec, {}).items():
            dirs[name] = str(TEMP_DIR / rel)
        return dirs


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_library: CodecReferenceLibrary | None = None


def get_library() -> CodecReferenceLibrary:
    """Return the module-level singleton CodecReferenceLibrary."""
    global _default_library
    if _default_library is None:
        _default_library = CodecReferenceLibrary()
    return _default_library


def enrich(
    path: Path,
    parse_result: dict[str, Any],
    chip_regs: dict[int, int] | None = None,
) -> dict[str, Any]:
    """
    Module-level convenience wrapper — enriches *parse_result* with
    codec-specific reference data using the singleton library.
    """
    return get_library().enrich_parse_result(path, parse_result, chip_regs)
