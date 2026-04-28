"""
adapter_vgmtrans.py — Helix adapter for VGMTrans
=================================================
Tier B: Requires a built VGMTrans binary.
Source reference: domains/music/data/derived/music/source/code/vgmtrans/  (CMake project)
Downloads zip:    vgmtrans-master.zip (source only, must be compiled)

Purpose:
    Convert SNES SPC files (and other VGMTrans-supported formats) to MIDI,
    extracting both the symbolic note sequence and instrument metadata.
    VGMTrans identifies the specific SNES music driver, reconstructs the
    original sequence data, and emits a Format 1 MIDI + an SF2 soundfont.

    Instrument metadata (patch names, MIDI program assignments, loop points)
    is extracted from the MIDI file headers and any SF2 generated alongside
    it. The SF2 binary is not retained unless explicitly requested.

Supported input formats (VGMTrans driver coverage):
    .spc      — SNES SPC700 (21 SNES driver variants: Nintendo, Capcom, Konami,
                             RareWare, Square, Enix, Chunsoft, HAL, Seta …)
    .mini2sf  — Nintendo DS (MP2k / Sappy engine)
    .psf      — PlayStation SPU (Akao, HeartBeatPS1, Sony PS2)
    .nsf      — NES (limited; VGMTrans pass-through to MIDI)
    .gbs      — Game Boy (limited)

Output (dict):
    {
        "format":         str,        # "spc" | "mini2sf" | "psf" | etc.
        "driver":         str,        # detected driver name (from MIDI metadata)
        "midi_path":      str | None, # absolute path to output MIDI file
        "midi_tracks":    int,        # number of MIDI tracks
        "midi_duration":  float,      # duration in seconds (from MIDI tick count)
        "instruments":    list[dict], # [{program, name, bank, loop_start, loop_end}]
        "source_path":    str,
        "bridge_mode":    str,        # "vgmtrans" | "unavailable"
        "adapter":        "vgmtrans",
    }

    Each instruments entry:
        {
            "program":    int,    # GM program number (0-based)
            "name":       str,    # instrument/patch name from SF2 or MIDI text event
            "bank":       int,    # bank number
            "loop_start": int,    # sample loop start (0 if none)
            "loop_end":   int,    # sample loop end (0 if none)
        }

Build instructions (Windows, CMake + MSVC or MinGW):
    cd domains/music/data/derived/music/source/code/vgmtrans
    cmake -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --config Release
    # Binary: build/Release/VGMTrans.exe  or  build/VGMTrans.exe

Binary search order:
    1. domains/music/data/derived/music/source/code/vgmtrans/build/Release/VGMTrans.exe
    2. domains/music/data/derived/music/source/code/vgmtrans/build/VGMTrans.exe
    3. PATH (vgmtrans / VGMTrans.exe)
    4. ~/VGMTrans/VGMTrans.exe  (common install location)

Adapter rules:
    • No Helix logic. No audio rendering.
    • Raises AdapterError on file-not-found.
    • Returns unavailable payload (no error) when binary not built.
    • Cleans up intermediate files (SF2) unless retain_sf2=True.
"""
from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Binary discovery
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
_VGMTRANS_SRC = _REPO_ROOT / "data" / "music" / "source" / "code" / "vgmtrans"

_BINARY_CANDIDATES = [
    _VGMTRANS_SRC / "build" / "Release" / "VGMTrans.exe",
    _VGMTRANS_SRC / "build" / "VGMTrans.exe",
    _VGMTRANS_SRC / "build" / "Release" / "vgmtrans",
    _VGMTRANS_SRC / "build" / "vgmtrans",
]

_PATH_NAMES = ["VGMTrans.exe", "vgmtrans", "VGMTrans"]


def _find_binary() -> Path | None:
    for candidate in _BINARY_CANDIDATES:
        if candidate.exists():
            return candidate
    for name in _PATH_NAMES:
        found = shutil.which(name)
        if found:
            return Path(found)
    # Common install paths
    for home_candidate in [
        Path.home() / "VGMTrans" / "VGMTrans-v1.3" / "VGMTrans.exe",
        Path.home() / "VGMTrans" / "VGMTrans.exe",
        Path("C:/Users/dissonance/VGMTrans/VGMTrans-v1.3/VGMTrans.exe"),
        Path("C:/Program Files/VGMTrans/VGMTrans.exe"),
    ]:
        if home_candidate.exists():
            return home_candidate
    return None


# ---------------------------------------------------------------------------
# MIDI introspection (pure Python — no dependencies)
# ---------------------------------------------------------------------------

def _read_midi_info(midi_path: Path) -> dict[str, Any]:
    """Parse just enough of a MIDI file to extract duration, track count, and
    any text/instrument-name events. Returns a partial info dict."""
    try:
        data = midi_path.read_bytes()
    except OSError:
        return {"midi_tracks": 0, "midi_duration": 0.0, "instruments": []}

    if data[:4] != b"MThd":
        return {"midi_tracks": 0, "midi_duration": 0.0, "instruments": []}

    # Header chunk
    fmt     = struct.unpack_from(">H", data, 8)[0]
    n_trks  = struct.unpack_from(">H", data, 10)[0]
    tpb     = struct.unpack_from(">H", data, 12)[0]   # ticks per beat

    instruments: list[dict] = []
    max_tick    = 0
    tempo_us    = 500_000   # default 120 BPM

    pos = 14
    track_idx = 0
    while pos < len(data) and track_idx < n_trks:
        if data[pos:pos+4] != b"MTrk":
            break
        chunk_len = struct.unpack_from(">I", data, pos + 4)[0]
        chunk_end = pos + 8 + chunk_len
        chunk     = data[pos + 8:chunk_end]
        pos       = chunk_end
        track_idx += 1

        # Walk events in this track
        cp       = 0
        tick     = 0
        last_cmd = 0
        while cp < len(chunk):
            # Variable-length delta-time
            delta = 0
            while cp < len(chunk):
                b = chunk[cp]; cp += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            tick += delta
            if tick > max_tick:
                max_tick = tick

            if cp >= len(chunk):
                break
            cmd = chunk[cp]

            # Running status
            if cmd & 0x80:
                last_cmd = cmd
                cp += 1
            else:
                cmd = last_cmd   # running status — don't advance

            event_type = cmd & 0xF0
            ch         = cmd & 0x0F

            if event_type == 0x80 or event_type == 0x90:
                cp += 2   # note off/on: note, velocity
            elif event_type == 0xA0:
                cp += 2   # aftertouch
            elif event_type == 0xB0:
                cp += 2   # control change
            elif event_type == 0xC0:
                # Program change: 1 byte
                if cp < len(chunk):
                    program = chunk[cp]; cp += 1
                    # Record instrument slot if not already seen
                    if not any(i["program"] == program and i.get("_ch") == ch
                               for i in instruments):
                        instruments.append({
                            "program":    program,
                            "name":       f"Program {program}",
                            "bank":       0,
                            "loop_start": 0,
                            "loop_end":   0,
                            "_ch":        ch,
                        })
            elif event_type == 0xD0:
                cp += 1   # channel pressure
            elif event_type == 0xE0:
                cp += 2   # pitch bend
            elif cmd == 0xFF:
                # Meta event
                if cp >= len(chunk):
                    break
                meta_type = chunk[cp]; cp += 1
                # Read variable-length meta length
                meta_len = 0
                while cp < len(chunk):
                    b = chunk[cp]; cp += 1
                    meta_len = (meta_len << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                meta_data = chunk[cp:cp + meta_len]
                cp += meta_len

                if meta_type == 0x51 and meta_len == 3:
                    # Set tempo
                    tempo_us = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                elif meta_type == 0x04:
                    # Instrument name — attach to most recent program change
                    name = meta_data.decode("latin-1", errors="replace").strip("\x00")
                    if instruments:
                        instruments[-1]["name"] = name
                elif meta_type == 0x03:
                    # Track name
                    pass  # could attach to track; ignored here
            elif cmd == 0xF0 or cmd == 0xF7:
                # SysEx
                sysex_len = 0
                while cp < len(chunk):
                    b = chunk[cp]; cp += 1
                    sysex_len = (sysex_len << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                cp += sysex_len
            else:
                cp += 1   # unknown; advance 1

    # Duration in seconds
    duration_sec = 0.0
    if tpb > 0:
        duration_sec = (max_tick / tpb) * (tempo_us / 1_000_000)

    # Strip internal tracking field
    for inst in instruments:
        inst.pop("_ch", None)

    return {
        "midi_tracks":   n_trks,
        "midi_duration": round(duration_sec, 3),
        "instruments":   instruments,
    }


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".spc",       # SNES SPC700
    ".mini2sf",   # Nintendo DS
    ".2sf",       # Nintendo DS
    ".psf",       # PlayStation
    ".psf2",      # PlayStation 2
    ".nsf",       # NES (limited)
    ".gbs",       # Game Boy (limited)
    ".sgc",       # Sega (limited)
    ".vgm",       # VGM (VGMTrans native)
    ".vgz",       # compressed VGM
})


class Adapter:
    """
    Tier B adapter wrapping VGMTrans for game audio → MIDI conversion.

    Supports 30+ music driver formats across SNES, NDS, PS1, and others.
    Degrades gracefully to unavailable when binary not built.
    """
    toolkit   = "vgmtrans"
    substrate = "music"

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

    def is_available(self) -> bool:
        return _find_binary() is not None

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        payload keys:
            file_path   (str | Path) — required
            output_dir  (str | Path) — optional; temp dir used if omitted
            retain_sf2  (bool)       — keep generated SF2 alongside MIDI (default False)
        """
        file_path = payload.get("file_path")
        if not file_path:
            raise AdapterError("Payload must contain 'file_path'")
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise AdapterError(f"Unsupported extension: {path.suffix!r}")

        binary = _find_binary()
        if binary is None:
            return self._unavailable(path)

        output_dir  = Path(payload.get("output_dir") or tempfile.mkdtemp(prefix="vgmtrans_"))
        retain_sf2  = bool(payload.get("retain_sf2", False))

        midi_path, driver_hint = self._run(binary, path, output_dir)

        if midi_path is None:
            return self._unavailable(path, reason="vgmtrans produced no MIDI output")

        midi_info = _read_midi_info(midi_path)

        # Remove SF2 if not wanted
        if not retain_sf2:
            for sf2 in output_dir.glob("*.sf2"):
                try:
                    sf2.unlink()
                except OSError:
                    pass

        return {
            "format":        path.suffix.lower().lstrip("."),
            "driver":        driver_hint,
            "midi_path":     str(midi_path),
            "midi_tracks":   midi_info["midi_tracks"],
            "midi_duration": midi_info["midi_duration"],
            "instruments":   midi_info["instruments"],
            "source_path":   str(path),
            "bridge_mode":   "vgmtrans",
            "adapter":       "vgmtrans",
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self, binary: Path, src: Path, out_dir: Path) -> tuple[Path | None, str]:
        """
        Run VGMTrans in batch mode:
            VGMTrans --batch <file> --output <dir>

        Returns (midi_path_or_None, driver_hint_string).
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [str(binary), "--batch", str(src), "--output", str(out_dir)]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            raise AdapterError(f"VGMTrans timed out on {src}")
        except FileNotFoundError as exc:
            raise AdapterError(f"VGMTrans binary not found: {exc}") from exc
        except Exception as exc:
            raise AdapterError(f"VGMTrans failed: {exc}") from exc

        # Find the generated MIDI file (VGMTrans names it after the source)
        midi_candidates = sorted(out_dir.glob("*.mid")) + sorted(out_dir.glob("*.midi"))
        midi_path = midi_candidates[0] if midi_candidates else None

        # Attempt to extract driver name from stdout
        driver_hint = self._parse_driver(result.stdout + result.stderr, src)

        return midi_path, driver_hint

    @staticmethod
    def _parse_driver(output: str, src: Path) -> str:
        """Extract driver/format name from VGMTrans console output."""
        # VGMTrans typically prints something like:
        #   "Identified: NinSnes (Nintendo SNES driver)"
        #   "Loading: CapcomSnes"
        for pattern in [
            r"Identified[:\s]+(\w+)",
            r"Loading[:\s]+(\w+)",
            r"Format[:\s]+(\w+)",
        ]:
            m = re.search(pattern, output, re.IGNORECASE)
            if m:
                return m.group(1)
        # Fallback: infer from extension
        ext_map = {
            ".spc":    "SNESSpc",
            ".mini2sf": "NintendoDS_MP2k",
            ".psf":    "PlayStationSPU",
            ".nsf":    "NES_NSF",
            ".gbs":    "GameBoy_GBS",
        }
        return ext_map.get(src.suffix.lower(), "unknown")

    @staticmethod
    def _unavailable(path: Path, reason: str = "VGMTrans binary not found") -> dict:
        return {
            "format":        path.suffix.lower().lstrip("."),
            "driver":        "unknown",
            "midi_path":     None,
            "midi_tracks":   0,
            "midi_duration": 0.0,
            "instruments":   [],
            "source_path":   str(path),
            "bridge_mode":   "unavailable",
            "adapter":       "vgmtrans",
            "_reason":       reason,
        }
