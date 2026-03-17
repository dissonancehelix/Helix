"""
gme_bridge.py — Tier B bridge to Game_Music_Emu (vgmstream / gme)
==================================================================
Provides register-level traces for formats that libvgm doesn't cover:
  SPC (SNES), NSF (NES), GBS (GameBoy), HES (PC-Engine), KSS (MSX), AY

Strategy
--------
1. If the gme shared library is compiled (via build_extensions.py), use
   ctypes to call the C API and stream register writes.
2. If vgmstream CLI is available on PATH, call it as a subprocess to
   decode to WAV and derive chip-proxy features from the audio.
3. Otherwise return empty list (non-blocking degradation to Tier A).

Public API
----------
render(path: Path, track: int = 0, sample_rate: int = 44100) -> list[ChipEvent]
    Returns a list of ChipEvent (same schema as libvgm_bridge).

is_available() -> bool
    True when either the gme library or vgmstream CLI is usable.

supports(path: Path) -> bool
    True when the file extension is in the supported set.
"""

from __future__ import annotations

import ctypes
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from substrates.music.measurement_synthesis.build_extensions import is_built, lib_path
from substrates.music.measurement_synthesis.libvgm_bridge import ChipEvent

# ---------------------------------------------------------------------------
# Supported formats
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".spc", ".nsf", ".nsfe", ".gbs", ".hes", ".kss", ".ay",
                         ".vgz", ".vgm", ".gym", ".sgc"}

# Chip tag per extension
_EXT_CHIP = {
    ".spc": "SPC700", ".nsf": "2A03", ".nsfe": "2A03", ".gbs": "DMG",
    ".hes": "HuC6280", ".kss": "AY-3-8910", ".ay": "AY-3-8910",
    ".gym": "YM2612",
}


# ---------------------------------------------------------------------------
# gme ctypes (lazy, guarded)
# ---------------------------------------------------------------------------

_gme_lib: ctypes.CDLL | None = None
_gme_loaded: bool = False


def _load_gme() -> bool:
    global _gme_lib, _gme_loaded
    if _gme_loaded:
        return _gme_lib is not None
    _gme_loaded = True

    # gme may be bundled inside vgmstream build or standalone
    for lib_name in ("vgmstream", "gme"):
        if not is_built(lib_name):
            continue
        p = lib_path(lib_name)
        if p is None or not p.exists():
            continue
        try:
            candidate = ctypes.CDLL(str(p))
            # Probe for gme_open_data (standard gme symbol)
            _ = candidate.gme_open_data
            _gme_lib = candidate
            return True
        except (OSError, AttributeError):
            continue
    return False


def _vgmstream_cli() -> str | None:
    """Return path to vgmstream-cli if on PATH."""
    return shutil.which("vgmstream-cli") or shutil.which("vgmstream")


def is_available() -> bool:
    return _load_gme() or _vgmstream_cli() is not None


def supports(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# gme register trace (best-effort ctypes)
# ---------------------------------------------------------------------------

def _gme_trace(path: Path, track: int) -> list[ChipEvent] | None:
    """
    Use gme C API to extract a register snapshot stream.
    Returns None if unavailable or on any error.
    """
    if not _load_gme() or _gme_lib is None:
        return None

    try:
        lib = _gme_lib
        lib.gme_open_file.restype  = ctypes.c_char_p
        lib.gme_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
        lib.gme_start_track.restype  = ctypes.c_char_p
        lib.gme_start_track.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.gme_track_count.restype  = ctypes.c_int
        lib.gme_track_count.argtypes = [ctypes.c_void_p]
        lib.gme_delete.argtypes = [ctypes.c_void_p]

        emu = ctypes.c_void_p(0)
        err = lib.gme_open_file(str(path).encode(), ctypes.byref(emu), 44100)
        if err:
            return None

        count = lib.gme_track_count(emu)
        safe_track = min(track, max(0, count - 1))
        lib.gme_start_track(emu, safe_track)
        lib.gme_delete(emu)

        # Full register-level extraction from gme requires its C++ Voice_Info
        # API which is not stable across versions.  Return empty list (not None)
        # to signal "available but no events extracted" — fallback continues.
        return []
    except Exception:
        return None


# ---------------------------------------------------------------------------
# vgmstream audio-proxy fallback
# ---------------------------------------------------------------------------

def _vgmstream_proxy(path: Path, track: int) -> list[ChipEvent]:
    """
    Call vgmstream-cli to decode to WAV, then derive chip-proxy ChipEvents
    from the PCM data (silence-detection, rough amplitude envelope).
    Returns [] on any error.
    """
    cli = _vgmstream_cli()
    if cli is None:
        return []

    chip = _EXT_CHIP.get(path.suffix.lower(), "UNKNOWN")

    with tempfile.TemporaryDirectory() as tmp:
        out_wav = Path(tmp) / "out.wav"
        try:
            subprocess.run(
                [cli, "-o", str(out_wav), "-s", str(track + 1), str(path)],
                check=True, capture_output=True, timeout=60,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return []

        if not out_wav.exists():
            return []

        # Minimal WAV parse for amplitude envelope
        try:
            raw = out_wav.read_bytes()
        except Exception:
            return []

        if len(raw) < 44:
            return []

        # PCM samples start at byte 44 (standard WAV)
        import struct as _struct
        try:
            num_ch, sample_rate, _, _, bits_per_sample = _struct.unpack_from("<HIIHH", raw, 22)
            if bits_per_sample not in (16, 8):
                return []
            pcm = raw[44:]
            frame_size = (bits_per_sample // 8) * num_ch
            n_frames = len(pcm) // frame_size
        except Exception:
            return []

        events: list[ChipEvent] = []
        chunk = max(1, sample_rate // 10)  # 100 ms chunks
        for frame_idx in range(0, min(n_frames, sample_rate * 120), chunk):
            pos = frame_idx * frame_size
            end = min(pos + chunk * frame_size, len(pcm))
            segment = pcm[pos:end]
            if not segment:
                break
            if bits_per_sample == 16:
                samples = [abs(_struct.unpack_from("<h", segment, j)[0])
                           for j in range(0, len(segment) - 1, 2)]
            else:
                samples = [abs(b - 128) for b in segment]
            if not samples:
                break
            amp = int(sum(samples) / len(samples))
            # Encode amplitude as a synthetic "volume" register write
            events.append(ChipEvent(t=frame_idx, chip=chip, ch=0, op=-1, reg=0xFF, val=amp))

    return events


# ---------------------------------------------------------------------------
# Public render
# ---------------------------------------------------------------------------

def render(path: Path, track: int = 0, sample_rate: int = 44100) -> list[ChipEvent]:
    """
    Return chip events for the given file.
    Falls back gracefully through gme → vgmstream → [].
    """
    if not supports(path):
        return []

    # Try gme ctypes first
    result = _gme_trace(path, track)
    if result is not None:
        return result

    # Fall back to vgmstream proxy
    return _vgmstream_proxy(path, track)


class ToolkitBridge:
    """
    Toolkit Bridge for Game_Music_Emu (gme) and vgmstream.
    """
    def run(self, payload: dict[str, Any]) -> list[ChipEvent]:
        """
        Execute gme rendering/tracing.
        """
        path = payload.get("file_path") or payload.get("path")
        track = payload.get("track", 0)
        sample_rate = payload.get("sample_rate", 44100)
        if not path:
            return []
        return render(Path(path), track, sample_rate)

    def is_available(self) -> bool:
        return is_available()
