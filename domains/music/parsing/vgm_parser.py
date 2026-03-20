"""
VGM/VGZ Parser — Helix Music Lab
==================================
Parses VGM (Video Game Music) v1.50/1.60/1.71 and gzip-compressed VGZ files.

Extracts chip-level command streams: YM2612, SN76489 (PSG), YM2151, etc.
Returns structured per-command event lists suitable for feature extraction.

Spec reference: https://vgmrips.net/packs/wiki/vgm_file_format
"""

from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# VGM Header
# ---------------------------------------------------------------------------

@dataclass
class VGMHeader:
    version:          int      # e.g. 0x00000161 = v1.61
    eof_offset:       int
    gd3_offset:       int
    total_samples:    int
    loop_offset:      int
    loop_samples:     int
    rate:             int      # Hz (50/60)
    sn76489_clock:    int      # PSG clock
    ym2413_clock:     int
    ym2612_clock:     int
    ym2151_clock:     int
    vgm_data_offset:  int      # absolute offset to data start
    # v1.51+
    sn76489_feedback: int = 0
    sn76489_shift_width: int = 0
    # chip presence flags derived from clocks
    has_ym2612:       bool = False
    has_psg:          bool = False
    has_ym2151:       bool = False


@dataclass
class VGMEvent:
    cmd:      int    # raw command byte
    kind:     str    # 'ym2612_port0', 'ym2612_port1', 'psg', 'wait', 'end', 'other'
    reg:      int = 0
    val:      int = 0
    samples:  int = 0   # for wait events


@dataclass
class VGMTrack:
    path:     Path
    header:   VGMHeader
    events:   list[VGMEvent] = field(default_factory=list)
    gd3:      dict = field(default_factory=dict)
    error:    str = ""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _read_header(data: bytes) -> VGMHeader:
    if data[:4] != b"Vgm ":
        raise ValueError(f"Not a VGM file (magic={data[:4]!r})")

    eof_offset      = struct.unpack_from("<I", data, 0x04)[0]
    version         = struct.unpack_from("<I", data, 0x08)[0]
    sn76489_clock   = struct.unpack_from("<I", data, 0x0C)[0]
    ym2413_clock    = struct.unpack_from("<I", data, 0x10)[0]
    gd3_offset      = struct.unpack_from("<I", data, 0x14)[0]
    total_samples   = struct.unpack_from("<I", data, 0x18)[0]
    loop_offset     = struct.unpack_from("<I", data, 0x1C)[0]
    loop_samples    = struct.unpack_from("<I", data, 0x20)[0]
    rate            = struct.unpack_from("<I", data, 0x24)[0]

    sn_fb           = struct.unpack_from("<H", data, 0x28)[0] if version >= 0x110 else 0
    sn_sw           = data[0x2A] if version >= 0x110 else 0

    ym2612_clock    = struct.unpack_from("<I", data, 0x2C)[0] if version >= 0x110 else 0
    ym2151_clock    = struct.unpack_from("<I", data, 0x30)[0] if version >= 0x110 else 0

    # VGM data offset
    if version >= 0x150 and len(data) > 0x34:
        rel = struct.unpack_from("<I", data, 0x34)[0]
        vgm_data_offset = 0x34 + rel if rel else 0x40
    else:
        vgm_data_offset = 0x40

    return VGMHeader(
        version=version,
        eof_offset=eof_offset,
        gd3_offset=gd3_offset,
        total_samples=total_samples,
        loop_offset=loop_offset,
        loop_samples=loop_samples,
        rate=rate,
        sn76489_clock=sn76489_clock & 0x3FFFFFFF,
        ym2413_clock=ym2413_clock,
        ym2612_clock=ym2612_clock & 0x3FFFFFFF,
        ym2151_clock=ym2151_clock & 0x3FFFFFFF,
        vgm_data_offset=vgm_data_offset,
        sn76489_feedback=sn_fb,
        sn76489_shift_width=sn_sw,
        has_ym2612=bool(ym2612_clock & 0x3FFFFFFF),
        has_psg=bool(sn76489_clock & 0x3FFFFFFF),
        has_ym2151=bool(ym2151_clock & 0x3FFFFFFF),
    )


def _parse_gd3(data: bytes, header: VGMHeader) -> dict:
    if not header.gd3_offset:
        return {}
    abs_offset = 0x14 + header.gd3_offset
    if abs_offset + 12 > len(data):
        return {}
    if data[abs_offset:abs_offset+4] != b"Gd3 ":
        return {}
    length = struct.unpack_from("<I", abs_offset + 8, data)[0] if False else \
             struct.unpack_from("<I", data, abs_offset + 8)[0]
    raw = data[abs_offset + 12: abs_offset + 12 + length]
    fields_raw = raw.decode("utf-16-le", errors="replace").split("\x00")
    keys = ["track_en", "track_jp", "game_en", "game_jp",
            "system_en", "system_jp", "author_en", "author_jp",
            "date", "ripper", "notes"]
    return {k: v for k, v in zip(keys, fields_raw)}


def _parse_events(data: bytes, start: int) -> list[VGMEvent]:
    events: list[VGMEvent] = []
    pos = start
    n = len(data)

    while pos < n:
        cmd = data[pos]
        pos += 1

        # YM2612 port 0 write
        if cmd == 0x52:
            if pos + 1 >= n:
                break
            reg, val = data[pos], data[pos + 1]
            pos += 2
            events.append(VGMEvent(cmd=cmd, kind="ym2612_p0", reg=reg, val=val))

        # YM2612 port 1 write
        elif cmd == 0x53:
            if pos + 1 >= n:
                break
            reg, val = data[pos], data[pos + 1]
            pos += 2
            events.append(VGMEvent(cmd=cmd, kind="ym2612_p1", reg=reg, val=val))

        # SN76489 PSG write
        elif cmd == 0x50:
            if pos >= n:
                break
            val = data[pos]
            pos += 1
            events.append(VGMEvent(cmd=cmd, kind="psg", val=val))

        # Wait n samples
        elif cmd == 0x61:
            if pos + 1 >= n:
                break
            samples = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=samples))

        # Wait 1/60s (735 samples)
        elif cmd == 0x62:
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=735))

        # Wait 1/50s (882 samples)
        elif cmd == 0x63:
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=882))

        # Wait n+1 samples (0x70–0x7F)
        elif 0x70 <= cmd <= 0x7F:
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=(cmd & 0x0F) + 1))

        # End of sound data
        elif cmd == 0x66:
            events.append(VGMEvent(cmd=cmd, kind="end"))
            break

        # YM2413 / other 2-byte commands
        elif cmd in (0x51, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A,
                     0x5B, 0x5C, 0x5D, 0x5E, 0x5F):
            pos += 2
            events.append(VGMEvent(cmd=cmd, kind="other"))

        # data block (0x67)
        elif cmd == 0x67:
            if pos + 6 > n:
                break
            pos += 1  # skip 0x66 compatibility byte
            block_type = data[pos]; pos += 1
            block_size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            pos += block_size
            events.append(VGMEvent(cmd=cmd, kind="other"))

        # PCM seek / other 4-byte
        elif cmd in (0xE0,):
            pos += 4
            events.append(VGMEvent(cmd=cmd, kind="other"))

        else:
            # Unknown — skip 1 byte conservatively
            events.append(VGMEvent(cmd=cmd, kind="other"))

    return events


def parse_vgm_file(path: Path) -> VGMTrack:
    return parse(path)


def parse(path: Path) -> VGMTrack:
    """Parse a VGM or VGZ file. Returns VGMTrack."""
    try:
        raw = path.read_bytes()
        # Decompress VGZ
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        header = _read_header(raw)
        gd3    = _parse_gd3(raw, header)
        events = _parse_events(raw, header.vgm_data_offset)
        return VGMTrack(path=path, header=header, events=events, gd3=gd3)
    except Exception as e:
        return VGMTrack(
            path=path,
            header=VGMHeader(0,0,0,0,0,0,0,0,0,0,0,0),
            error=str(e),
        )
