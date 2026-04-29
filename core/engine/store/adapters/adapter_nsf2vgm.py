"""
adapter_nsf2vgm.py — Helix adapter for nsf2vgm_batch
======================================================
Tier A: Binary is pre-compiled and included in the repo.
Binary: domains/music/data/library/source/code/nsf2vgm/v1.0/nsf2vgm_batch.exe

Purpose:
    Convert NSF (NES Sound Format) files to VGM, one VGM file per track.
    The resulting VGM files are fed into the existing vgm_note_reconstructor
    pipeline, which handles NES APU (YM2612 channels 0–5 map to APU; PSG
    channels 6–8 map to SN76489-equivalent triangle/noise in VGM output).

    This closes the NES MIDI gap: NSF → VGM → vgm_note_reconstructor →
    SymbolicScore → MIDI.

Chain:
    adapter_nsf2vgm.execute({"file_path": "game.nsf"})
        → returns {"vgm_paths": [...], "track_count": N, ...}
    For each vgm_path:
        from domains.music.parsing.vgm_parser import parse
        from domains.music.domain_analysis.symbolic_music.vgm_note_reconstructor import reconstruct
        score = reconstruct(parse(vgm_path))

Input (payload dict):
    file_path   (str | Path) — .nsf file (required)
    m3u_path    (str | Path) — optional companion .m3u with track metadata
    output_dir  (str | Path) — optional; temp dir used if omitted
    track_duration (int)    — default per-track duration in seconds (default 180)
    intro_secs  (int)       — seconds before loop point (default 5)
    tracks      (list[int]) — specific 0-based track indices to convert; all if omitted

nsf2vgm_batch usage:
    nsf2vgm_batch.exe <playlist.m3u> [output_dir]

    The binary does not accept a bare .nsf file — it requires an M3U playlist.
    When no .m3u is provided, this adapter synthesises one from the NSF header.

NSF header (bytes):
    0x00–0x04   Magic "NESM\\x1a"
    0x05        Version (1)
    0x06        Total songs (track count)
    0x07        Starting song (1-based)
    0x0E–0x2D   Title   (32 bytes, null-padded ASCII)
    0x2E–0x4D   Artist  (32 bytes)
    0x4E–0x6D   Copyright (32 bytes)
    0x7A        Expansion chip flags (bit 0=FDS, 1=VRC6, 2=VRC7, 3=FDS2,
                                      4=MMC5, 5=N106/Namco163, 6=FME7/Sunsoft5B)

Expansion chip flag → chip name mapping:
    bit 0 = FDS      bit 1 = VRC6     bit 2 = VRC7
    bit 4 = MMC5     bit 5 = N163     bit 6 = FME7 (Sunsoft 5B)

Output (dict):
    {
        "format":         "nsf",
        "title":          str,         # from NSF header
        "artist":         str,
        "copyright":      str,
        "track_count":    int,         # total tracks in NSF
        "converted":      int,         # tracks actually converted
        "expansion_chips": list[str],  # ["VRC6", "MMC5", ...] or []
        "vgm_paths":      list[str],   # absolute paths to output VGM files
        "output_dir":     str,
        "source_path":    str,
        "bridge_mode":    str,         # "nsf2vgm" | "unavailable"
        "adapter":        "nsf2vgm",
    }

Adapter rules:
    • No Helix logic. No audio rendering.
    • Raises AdapterError on file-not-found.
    • Returns unavailable payload (not error) when binary missing.
    • Cleans up synthesised M3U after conversion.
"""
from __future__ import annotations

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

_REPO_ROOT  = Path(__file__).parent.parent.parent
_BINARY_PATH = (
    _REPO_ROOT
    / "data" / "music" / "source" / "code" / "nsf2vgm" / "v1.0"
    / "nsf2vgm_batch.exe"
)

_PATH_NAMES = ["nsf2vgm_batch.exe", "nsf2vgm_batch", "nsf2vgm"]


def _find_binary() -> Path | None:
    if _BINARY_PATH.exists():
        return _BINARY_PATH
    for name in _PATH_NAMES:
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


# ---------------------------------------------------------------------------
# NSF header parsing
# ---------------------------------------------------------------------------

_NSF_MAGIC   = b"NESM\x1a"
_CHIP_FLAGS  = {
    0: "FDS",
    1: "VRC6",
    2: "VRC7",
    4: "MMC5",
    5: "N163",
    6: "FME7",
}


def _parse_nsf_header(data: bytes) -> dict[str, Any]:
    """Extract track count, title, artist, copyright, and expansion chips."""
    if len(data) < 0x80:
        raise AdapterError("NSF file too short to contain a valid header")
    if data[:5] != _NSF_MAGIC:
        raise AdapterError(f"Not an NSF file (magic={data[:5]!r})")

    track_count = data[0x06]
    start_track = data[0x07]   # 1-based

    def _cstr(buf: bytes) -> str:
        return buf.split(b"\x00")[0].decode("ascii", errors="replace").strip()

    title     = _cstr(data[0x0E:0x2E])
    artist    = _cstr(data[0x2E:0x4E])
    copyright = _cstr(data[0x4E:0x6E])

    chip_byte = data[0x7A] if len(data) > 0x7A else 0
    chips = [name for bit, name in _CHIP_FLAGS.items() if chip_byte & (1 << bit)]

    return {
        "track_count": track_count,
        "start_track": start_track,
        "title":       title or "Unknown",
        "artist":      artist or "Unknown",
        "copyright":   copyright or "",
        "expansion_chips": chips,
    }


# ---------------------------------------------------------------------------
# M3U synthesis
# ---------------------------------------------------------------------------

def _synthesise_m3u(
    nsf_path: Path,
    header:   dict[str, Any],
    tracks:   list[int] | None,
    duration: int,
    intro:    int,
    out_path: Path,
) -> None:
    """Write a minimal M3U playlist for nsf2vgm_batch."""
    indices = tracks if tracks is not None else list(range(header["track_count"]))
    title   = header["title"]

    lines: list[str] = []
    for idx in indices:
        track_name = f"{title} - Track {idx + 1:02d}"
        lines.append(
            f"{nsf_path.name}::NSF,{idx},{track_name},{duration},{intro}"
        )

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".nsf"})


class Adapter:
    """
    Tier A adapter: binary ships in repo at
    domains/music/data/library/source/code/nsf2vgm/v1.0/nsf2vgm_batch.exe

    Converts NSF → per-track VGM files, which the vgm_note_reconstructor
    pipeline can then process into SymbolicScore objects.

    Supports all NSF expansion chips: FDS, VRC6, VRC7, MMC5, N163, FME7.
    """
    toolkit   = "nsf2vgm"
    substrate = "music"

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

    def is_available(self) -> bool:
        return _find_binary() is not None

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        payload keys:
            file_path       (str | Path) — .nsf file, required
            m3u_path        (str | Path) — companion .m3u, optional
            output_dir      (str | Path) — where VGM files land, optional
            track_duration  (int)        — seconds per track (default 180)
            intro_secs      (int)        — intro before loop (default 5)
            tracks          (list[int])  — 0-based track indices, optional (all)
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
            return self._unavailable(path, "nsf2vgm_batch binary not found")

        # Parse NSF header
        try:
            header = _parse_nsf_header(path.read_bytes())
        except (AdapterError, OSError) as exc:
            raise AdapterError(f"NSF header read failed: {exc}") from exc

        duration   = int(payload.get("track_duration", 180))
        intro      = int(payload.get("intro_secs",    5))
        tracks     = payload.get("tracks")  # None = all
        output_dir = Path(payload.get("output_dir") or
                          tempfile.mkdtemp(prefix="nsf2vgm_"))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Locate or synthesise M3U
        m3u_path   = payload.get("m3u_path")
        cleanup_m3u = False
        if m3u_path:
            m3u = Path(m3u_path)
            if not m3u.exists():
                raise AdapterError(f"M3U not found: {m3u}")
        else:
            m3u = output_dir / f"{path.stem}_generated.m3u"
            _synthesise_m3u(path, header, tracks, duration, intro, m3u)
            cleanup_m3u = True

        # Run conversion — binary must run from NSF's directory so relative
        # paths in M3U resolve correctly
        vgm_paths = self._run(binary, path, m3u, output_dir)

        if cleanup_m3u:
            try:
                m3u.unlink()
            except OSError:
                pass

        return {
            "format":          "nsf",
            "title":           header["title"],
            "artist":          header["artist"],
            "copyright":       header["copyright"],
            "track_count":     header["track_count"],
            "converted":       len(vgm_paths),
            "expansion_chips": header["expansion_chips"],
            "vgm_paths":       [str(p) for p in vgm_paths],
            "output_dir":      str(output_dir),
            "source_path":     str(path),
            "bridge_mode":     "nsf2vgm",
            "adapter":         "nsf2vgm",
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(
        self,
        binary:     Path,
        nsf_path:   Path,
        m3u:        Path,
        output_dir: Path,
    ) -> list[Path]:
        """
        Invoke nsf2vgm_batch.exe and return a sorted list of output VGM paths.

        nsf2vgm_batch reads NSF relative to the M3U's location, so we copy
        the M3U into the NSF's directory and run from there.
        """
        # nsf2vgm_batch resolves the NSF filename relative to the M3U location.
        # The synthesised M3U uses the bare filename (no directory), so we
        # place both the M3U and run from the NSF's parent.
        work_dir = nsf_path.parent

        # If the M3U is not already in the work dir, copy it there temporarily
        m3u_local = work_dir / m3u.name
        copied_m3u = False
        if m3u_local != m3u:
            shutil.copy2(m3u, m3u_local)
            copied_m3u = True

        try:
            cmd = [str(binary), str(m3u_local), str(output_dir)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(work_dir),
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            raise AdapterError(f"nsf2vgm_batch timed out on {nsf_path}")
        except Exception as exc:
            raise AdapterError(f"nsf2vgm_batch failed: {exc}") from exc
        finally:
            if copied_m3u and m3u_local.exists():
                try:
                    m3u_local.unlink()
                except OSError:
                    pass

        # Collect VGM output files, sorted by name (track order)
        vgm_paths = sorted(
            list(output_dir.glob("*.vgm")) + list(output_dir.glob("*.vgz"))
        )
        return vgm_paths

    @staticmethod
    def _unavailable(path: Path, reason: str) -> dict:
        return {
            "format":          "nsf",
            "title":           "",
            "artist":          "",
            "copyright":       "",
            "track_count":     0,
            "converted":       0,
            "expansion_chips": [],
            "vgm_paths":       [],
            "output_dir":      "",
            "source_path":     str(path),
            "bridge_mode":     "unavailable",
            "adapter":         "nsf2vgm",
            "_reason":         reason,
        }

