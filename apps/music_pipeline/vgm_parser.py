"""
VGM/VGZ Parser — Helix Music Lab
==================================
Parses VGM (Video Game Music) v1.50/1.60/1.71 and gzip-compressed VGZ files.

Extracts chip-level command streams: YM2612, SN76489 (PSG), YM2151, etc.
Returns structured per-command event lists suitable for feature extraction.

Policy:
  - GD3 metadata (title/game/author) is NOT parsed. Helix library is the
    metadata source (codex/library/music/). Synthesis structure only.
  - loop_offset from the header IS used to tag pre-loop vs post-loop events.

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
    # v1.51+ chip clocks
    ym2203_clock:  int = 0
    ym2608_clock:  int = 0
    ym2610_clock:  int = 0
    ym3812_clock:  int = 0
    ym3526_clock:  int = 0
    y8950_clock:   int = 0
    ymf262_clock:  int = 0
    ymf278b_clock: int = 0
    ymf271_clock:  int = 0
    ymz280b_clock: int = 0
    ay8910_clock:  int = 0
    # v1.60+ chip clocks
    dmg_clock:     int = 0
    nes_apu_clock: int = 0
    huc6280_clock: int = 0
    k051649_clock: int = 0   # SCC
    k054539_clock: int = 0
    # chip presence flags
    has_ym2203:  bool = False
    has_ym2608:  bool = False
    has_ym3812:  bool = False
    has_ymf262:  bool = False
    has_ay8910:  bool = False
    has_dmg:     bool = False
    has_nes_apu: bool = False
    has_huc6280: bool = False
    has_k051649: bool = False


@dataclass
class VGMEvent:
    cmd:      int    # raw command byte
    kind:     str    # 'ym2612_p0', 'ym2612_p1', 'psg', 'wait', 'end', 'other'
    reg:      int = 0
    val:      int = 0
    samples:  int = 0   # for wait events
    time_s:   float = 0.0  # absolute time in seconds at event
    is_loop:  bool = False  # True if this event is at/after the loop point


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

    # v1.51+ chip clocks
    ym2203_clock = ym2608_clock = ym2610_clock = ym3812_clock = 0
    ym3526_clock = y8950_clock = ymf262_clock = ymf278b_clock = 0
    ymf271_clock = ymz280b_clock = ay8910_clock = 0
    dmg_clock = nes_apu_clock = huc6280_clock = k051649_clock = k054539_clock = 0

    def _u32(offset: int) -> int:
        if len(data) > offset + 3:
            return struct.unpack_from("<I", data, offset)[0] & 0x3FFFFFFF
        return 0

    if version >= 0x151:
        ym2203_clock  = _u32(0x44)
        ym2608_clock  = _u32(0x48)
        ym2610_clock  = _u32(0x4C)
        ym3812_clock  = _u32(0x50)
        ym3526_clock  = _u32(0x54)
        y8950_clock   = _u32(0x58)
        ymf262_clock  = _u32(0x5C)
        ymf278b_clock = _u32(0x60)
        ymf271_clock  = _u32(0x64)
        ymz280b_clock = _u32(0x68)
        ay8910_clock  = _u32(0x74)

    if version >= 0x160:
        dmg_clock     = _u32(0x7C)
        nes_apu_clock = _u32(0x80)
        huc6280_clock = _u32(0x9C)
        k051649_clock = _u32(0x94)
        k054539_clock = _u32(0x98)

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
        ym2203_clock=ym2203_clock,
        ym2608_clock=ym2608_clock,
        ym2610_clock=ym2610_clock,
        ym3812_clock=ym3812_clock,
        ym3526_clock=ym3526_clock,
        y8950_clock=y8950_clock,
        ymf262_clock=ymf262_clock,
        ymf278b_clock=ymf278b_clock,
        ymf271_clock=ymf271_clock,
        ymz280b_clock=ymz280b_clock,
        ay8910_clock=ay8910_clock,
        dmg_clock=dmg_clock,
        nes_apu_clock=nes_apu_clock,
        huc6280_clock=huc6280_clock,
        k051649_clock=k051649_clock,
        k054539_clock=k054539_clock,
        has_ym2203=bool(ym2203_clock),
        has_ym2608=bool(ym2608_clock),
        has_ym3812=bool(ym3812_clock),
        has_ymf262=bool(ymf262_clock),
        has_ay8910=bool(ay8910_clock),
        has_dmg=bool(dmg_clock),
        has_nes_apu=bool(nes_apu_clock),
        has_huc6280=bool(huc6280_clock),
        has_k051649=bool(k051649_clock),
    )


def _parse_gd3(data: bytes, header: VGMHeader) -> dict:
    # GD3 metadata intentionally not parsed. Helix library is the metadata source.
    # See codex/library/music/ for authoritative track/artist data.
    return {}


# ---------------------------------------------------------------------------
# VGM command dispatch tables (spec: https://vgmrips.net/wiki/VGM_Specification)
# ---------------------------------------------------------------------------

# Map command byte → (extra_bytes, kind_string)
# 'extra_bytes' = bytes to read after the command byte (skip if unrecognised chip)
# The 'kind' string is used to categorise events for feature extraction.

# 1 extra byte (dd): chip single-data writes + reserved 0x30-0x3F, 0x41-0x4E
_1B = {
    0x30: "reserved",    # reserved (future 2nd chip PSG)
    0x31: "reserved",
    0x32: "reserved",
    0x33: "reserved",
    0x34: "reserved",
    0x35: "reserved",
    0x36: "reserved",
    0x37: "reserved",
    0x38: "reserved",
    0x39: "reserved",
    0x3A: "reserved",
    0x3B: "reserved",
    0x3C: "reserved",
    0x3D: "reserved",
    0x3E: "reserved",
    0x3F: "reserved",
    0x40: "mikey",       # Lynx MIKEY (1.71)
    0x41: "reserved",    # reserved
    0x42: "reserved",
    0x43: "reserved",
    0x44: "reserved",
    0x45: "reserved",
    0x46: "reserved",
    0x47: "reserved",
    0x48: "reserved",
    0x49: "reserved",
    0x4A: "reserved",
    0x4B: "reserved",
    0x4C: "reserved",
    0x4D: "reserved",
    0x4E: "reserved",
    0x4F: "dmg_stereo",  # Game Boy SGB stereo
    0x50: "psg",         # SN76489 / PSG
}

# 2 extra bytes (aa dd): chip addr+data register writes
_2B = {
    0x51: "ym2413",
    0x52: "ym2612_p0",
    0x53: "ym2612_p1",
    0x54: "ym2151",
    0x55: "ym2203",
    0x56: "ym2608_p0",
    0x57: "ym2608_p1",
    0x58: "ym2610_p0",
    0x59: "ym2610_p1",
    0x5A: "ym3812",
    0x5B: "ym3526",
    0x5C: "y8950",
    0x5D: "ymz280b",
    0x5E: "ymf262_p0",
    0x5F: "ymf262_p1",
    0xA0: "ay8910",
    0xA1: "rf5c68",
    0xA2: "rf5c164",
    0xA3: "pwm_3b",      # PWM uses 4 nibbles = 3 bytes but here 2-byte command
    0xA4: "dmg",
    0xA5: "nes_apu",
    0xA6: "multipcm",
    0xA7: "upd7759",
    0xA8: "msm6258",
    0xA9: "msm6295",
    0xAA: "huc6280",
    0xAB: "k053260",
    0xAC: "pokey",
    0xAD: "wonderswan",
    0xAE: "saa1099",
    0xAF: "es5506_short",
    0xB0: "ga20",
    0xB1: "mikey_2b",
    0xB2: "reserved",
    0xB3: "reserved",
    0xB4: "reserved",
    0xB5: "reserved",
    0xB6: "reserved",
    0xB7: "reserved",
    0xB8: "reserved",
    0xB9: "reserved",
    0xBA: "reserved",
    0xBB: "reserved",
    0xBC: "reserved",
    0xBD: "reserved",
    0xBE: "reserved",
    0xBF: "reserved",
}

# 3 extra bytes:
# 0xC0 aa bb dd: SegaPCM
# 0xC1 aa bb dd: RF5C68 memory write
# 0xC2 aa bb dd: RF5C164 memory write
# 0xC3 mm ll cc: MultiPCM offset
# 0xC4 mm ll rr: QSound
# 0xC5 mm ll dd: SCSP
# 0xC6 mm ll dd: WonderSwan
# 0xC7 mm ll dd: VSU
# 0xC8 mm ll dd: X1-010
# 0xC9..0xCF: reserved (3 extra bytes)
# 0xD0 pp dd aa: YMF278B
# 0xD1 pp dd aa: YMF271
# 0xD2 pp dd aa: SCC1
# 0xD3 pp dd aa: K054539
# 0xD4 pp dd aa / pp aa dd: C140 / ES5503
# 0xD5: ES5506 (4 bytes: aa dd)
# 0xD6: C352 (4 bytes: mm ll)
# 0xD7..0xDF: reserved (3 extra bytes)
_3B = {
    **{c: "segapcm_family"   for c in range(0xC0, 0xC9)},  # 0xC0-0xC8
    **{c: "reserved"         for c in range(0xC9, 0xD0)},  # 0xC9-0xCF reserved
    **{c: "extended_chip"    for c in range(0xD0, 0xD5)},  # 0xD0-0xD4
    **{c: "reserved"         for c in range(0xD7, 0xE0)},  # 0xD7-0xDF reserved
}
_3B[0xD5] = "es5506_long"   # 3 extra bytes
_3B[0xD6] = "c352"          # 3 extra bytes (mmll)

# 4 extra bytes: 0xE0 offset32 (PCM data seek), 0xE1 (C352)
# 0xE2..0xFF: reserved (4 extra bytes each per spec)
_4B = {
    0xE0: "pcm_seek",
    0xE1: "c352_long",
    **{c: "reserved"  for c in range(0xE2, 0x100)},
}

# Combined lookup: cmd -> (extra_bytes, kind)
_CMD_TABLE: dict[int, tuple[int, str]] = (
    {k: (1, v) for k, v in _1B.items()} |
    {k: (2, v) for k, v in _2B.items()} |
    {k: (3, v) for k, v in _3B.items()} |
    {k: (4, v) for k, v in _4B.items()}
)

# Convenience alias for 3-byte chip writes that have reg+val (our structured events)
_STRUCTURED_CHIPS = set(_2B.keys())  # all 2-extra-byte commands get reg+val events


def _parse_events(data: bytes, start: int, loop_abs_offset: int = 0) -> list[VGMEvent]:
    """
    Parse VGM command stream into VGMEvent list.

    Events are timestamped in seconds and tagged is_loop=True at/after
    the loop point (loop_abs_offset = absolute file offset of loop start).

    Uses the full VGM spec command size table to avoid parse desync on
    files using chips other than YM2612/SN76489.
    """
    events: list[VGMEvent] = []
    pos = start
    n = len(data)
    current_sample = 0
    sample_rate = 44100
    past_loop = False

    while pos < n:
        # Mark loop point crossing
        if loop_abs_offset and not past_loop and pos >= loop_abs_offset:
            past_loop = True

        time_s = current_sample / sample_rate
        cmd = data[pos]
        pos += 1

        # --- Timing events ---
        if cmd == 0x61:  # Wait n samples
            if pos + 1 >= n:
                break
            samples = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=samples,
                                   time_s=time_s, is_loop=past_loop))
            current_sample += samples
            continue

        if cmd == 0x62:  # Wait 735 samples (1/60s)
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=735,
                                   time_s=time_s, is_loop=past_loop))
            current_sample += 735
            continue

        if cmd == 0x63:  # Wait 882 samples (1/50s)
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=882,
                                   time_s=time_s, is_loop=past_loop))
            current_sample += 882
            continue

        if 0x70 <= cmd <= 0x7F:  # Wait n+1 samples
            samples = (cmd & 0x0F) + 1
            events.append(VGMEvent(cmd=cmd, kind="wait", samples=samples,
                                   time_s=time_s, is_loop=past_loop))
            current_sample += samples
            continue

        # DAC stream write + wait (0x80-0x8F): YM2612 DAC + n samples
        if 0x80 <= cmd <= 0x8F:
            samples = cmd & 0x0F
            events.append(VGMEvent(cmd=cmd, kind="ym2612_dac", samples=samples,
                                   time_s=time_s, is_loop=past_loop))
            current_sample += samples
            continue

        # End of data
        if cmd == 0x66:
            events.append(VGMEvent(cmd=cmd, kind="end", time_s=time_s, is_loop=past_loop))
            break

        # Data block (0x67): variable length, must be handled before size table
        if cmd == 0x67:
            if pos + 6 > n:
                break
            pos += 1  # skip 0x66 compatibility byte
            block_type = data[pos]; pos += 1
            block_size = struct.unpack_from("<I", data, pos)[0]; pos += 4
            pos += block_size
            events.append(VGMEvent(cmd=cmd, kind="data_block",
                                   time_s=time_s, is_loop=past_loop))
            continue

        # PCM RAM write (0x68): 11 extra bytes
        if cmd == 0x68:
            pos += 11
            events.append(VGMEvent(cmd=cmd, kind="pcm_write",
                                   time_s=time_s, is_loop=past_loop))
            continue

        # DAC stream control (0x90-0x95)
        if 0x90 <= cmd <= 0x95:
            skip = {0x90: 4, 0x91: 4, 0x92: 5, 0x93: 10, 0x94: 1, 0x95: 4}.get(cmd, 4)
            pos += skip
            events.append(VGMEvent(cmd=cmd, kind="dac_stream",
                                   time_s=time_s, is_loop=past_loop))
            continue

        # --- All other commands: table-driven dispatch (spec-accurate) ---
        entry = _CMD_TABLE.get(cmd)
        if entry is not None:
            extra, kind = entry
            if pos + extra > n: break
            if extra == 1:
                val = data[pos]; pos += 1
                events.append(VGMEvent(cmd=cmd, kind=kind, val=val,
                                       time_s=time_s, is_loop=past_loop))
            elif extra == 2:
                reg = data[pos]; val = data[pos + 1]; pos += 2
                events.append(VGMEvent(cmd=cmd, kind=kind, reg=reg, val=val,
                                       time_s=time_s, is_loop=past_loop))
            elif extra == 3:
                reg = struct.unpack_from("<H", data, pos)[0]
                val = data[pos + 2]; pos += 3
                events.append(VGMEvent(cmd=cmd, kind=kind, reg=reg, val=val,
                                       time_s=time_s, is_loop=past_loop))
            elif extra == 4:
                reg = struct.unpack_from("<I", data, pos)[0]; pos += 4
                events.append(VGMEvent(cmd=cmd, kind=kind, reg=reg,
                                       time_s=time_s, is_loop=past_loop))
            continue

        # Fallback: unknown cmd — skip 0 extra bytes, flag for debugging
        events.append(VGMEvent(cmd=cmd, kind="unknown",
                               time_s=time_s, is_loop=past_loop))

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
        # GD3 intentionally not parsed — library is the metadata source
        gd3 = {}
        # Compute absolute loop offset for event tagging
        # VGM spec: loop_offset is relative to 0x1C; absolute = 0x1C + loop_offset
        loop_abs = (0x1C + header.loop_offset) if header.loop_offset else 0
        events = _parse_events(raw, header.vgm_data_offset, loop_abs_offset=loop_abs)
        return VGMTrack(path=path, header=header, events=events, gd3=gd3)
    except Exception as e:
        return VGMTrack(
            path=path,
            header=VGMHeader(0,0,0,0,0,0,0,0,0,0,0,0),
            error=str(e),
        )
