"""
NSF Parser — Helix Music Lab (Tier A)
=======================================
Static parser for NES Sound Format (.nsf / .nsfe) files.

NSF header (0x80 bytes):
  0x000  5   Magic "NESM\x1a"
  0x005  1   Version (currently 1)
  0x006  1   Total songs
  0x007  1   Starting song (1-based)
  0x008  2   Load address (little-endian)
  0x00A  2   Init address
  0x00C  2   Play address
  0x00E  32  Song name (null-padded ASCII)
  0x02E  32  Artist name
  0x04E  32  Copyright holder
  0x06E  2   NTSC play speed (μs per frame, usually 16666)
  0x070  8   Bankswitch init values (0 = no bankswitch)
  0x078  2   PAL play speed
  0x07A  1   PAL/NTSC bits (bit0=PAL, bit1=dual)
  0x07B  1   Extra sound chip flags
  0x07C  4   Reserved (NSF2 metadata size if non-zero)

Extra chip flags (0x07B):
  bit 0 — VRC6    (Konami, 2 pulse + sawtooth)
  bit 1 — VRC7    (Konami, FM)
  bit 2 — FDS     (Famicom Disk System)
  bit 3 — MMC5    (Nintendo, 2 pulse + PCM)
  bit 4 — N163    (Namco 163, up to 8 wavetable channels)
  bit 5 — Sunsoft 5B (AY-3-8910 clone)
  bit 6 — EPSM    (NSF2 extension, OPN2)
  bit 7 — reserved
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION   = "1.0.0"
NSF_MAGIC = b"NESM\x1a"

EXPANSION_CHIPS = {
    0: "VRC6",
    1: "VRC7",
    2: "FDS",
    3: "MMC5",
    4: "N163",
    5: "Sunsoft5B",
    6: "EPSM",
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class NSFTrack:
    path:            Path
    version:         int
    total_songs:     int
    starting_song:   int
    load_addr:       int
    init_addr:       int
    play_addr:       int
    title:           str
    artist:          str
    copyright:       str
    ntsc_speed:      int    # μs per frame
    pal_speed:       int
    is_pal:          bool
    is_dual:         bool   # supports both NTSC and PAL
    bankswitched:    bool
    bankswitch_regs: list[int]
    extra_chip_flags: int
    expansion_chips: list[str]  # decoded names
    # APU channel inventory (static analysis)
    has_pulse1:     bool = True
    has_pulse2:     bool = True
    has_triangle:   bool = True
    has_noise:      bool = True
    has_dpcm:       bool = False  # detected from data segment scan (best-effort)
    # Provenance
    tier:           int   = 1
    confidence:     float = 0.6
    provenance_version: str = f"nsf_parser:{VERSION}"
    extraction_ts:  str   = ""
    error:          str   = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path":            str(self.path),
            "title":           self.title,
            "artist":          self.artist,
            "copyright":       self.copyright,
            "total_songs":     self.total_songs,
            "starting_song":   self.starting_song,
            "load_addr":       hex(self.load_addr),
            "init_addr":       hex(self.init_addr),
            "play_addr":       hex(self.play_addr),
            "ntsc_speed_us":   self.ntsc_speed,
            "pal_speed_us":    self.pal_speed,
            "is_pal":          self.is_pal,
            "is_dual":         self.is_dual,
            "bankswitched":    self.bankswitched,
            "bankswitch_regs": self.bankswitch_regs,
            "expansion_chips": self.expansion_chips,
            "extra_chip_flags_raw": self.extra_chip_flags,
            "apu_channels": {
                "pulse1":    self.has_pulse1,
                "pulse2":    self.has_pulse2,
                "triangle":  self.has_triangle,
                "noise":     self.has_noise,
                "dpcm":      self.has_dpcm,
            },
            "tier":                self.tier,
            "confidence":          self.confidence,
            "provenance_version":  self.provenance_version,
            "extraction_ts":       self.extraction_ts,
            "error":               self.error,
        }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse(path: Path) -> NSFTrack:
    """Parse a .nsf file into an NSFTrack. Never raises."""
    ts = datetime.now(timezone.utc).isoformat()
    try:
        data = path.read_bytes()
    except Exception as e:
        return NSFTrack(
            path=path, version=0, total_songs=0, starting_song=1,
            load_addr=0, init_addr=0, play_addr=0,
            title="", artist="", copyright="",
            ntsc_speed=0, pal_speed=0, is_pal=False, is_dual=False,
            bankswitched=False, bankswitch_regs=[], extra_chip_flags=0,
            expansion_chips=[], error=str(e), extraction_ts=ts,
        )

    if len(data) < 0x80:
        return NSFTrack(
            path=path, version=0, total_songs=0, starting_song=1,
            load_addr=0, init_addr=0, play_addr=0,
            title="", artist="", copyright="",
            ntsc_speed=0, pal_speed=0, is_pal=False, is_dual=False,
            bankswitched=False, bankswitch_regs=[], extra_chip_flags=0,
            expansion_chips=[], error="File too short", extraction_ts=ts,
        )

    if data[:5] != NSF_MAGIC:
        return NSFTrack(
            path=path, version=0, total_songs=0, starting_song=1,
            load_addr=0, init_addr=0, play_addr=0,
            title="", artist="", copyright="",
            ntsc_speed=0, pal_speed=0, is_pal=False, is_dual=False,
            bankswitched=False, bankswitch_regs=[], extra_chip_flags=0,
            expansion_chips=[], error="Not a valid NSF file", extraction_ts=ts,
        )

    def _s(off: int, length: int) -> str:
        return data[off:off + length].rstrip(b"\x00").decode("latin-1", errors="replace").strip()

    version      = data[0x05]
    total_songs  = data[0x06]
    start_song   = data[0x07]
    load_addr,   = struct.unpack_from("<H", data, 0x08)
    init_addr,   = struct.unpack_from("<H", data, 0x0A)
    play_addr,   = struct.unpack_from("<H", data, 0x0C)
    title        = _s(0x0E, 32)
    artist       = _s(0x2E, 32)
    copyright    = _s(0x4E, 32)
    ntsc_speed,  = struct.unpack_from("<H", data, 0x6E)
    bank_regs    = list(data[0x70:0x78])
    pal_speed,   = struct.unpack_from("<H", data, 0x78)
    palntsc_bits = data[0x7A]
    chip_flags   = data[0x7B]

    bankswitched = any(b != 0 for b in bank_regs)
    is_pal       = bool(palntsc_bits & 0x01)
    is_dual      = bool(palntsc_bits & 0x02)

    expansion = [name for bit, name in EXPANSION_CHIPS.items() if chip_flags & (1 << bit)]

    # Best-effort: scan for DPCM sample address patterns ($C000–$FFFF range)
    # NSF data starts at 0x80; scan for 0x11 (APU DPCM frequency) writes — heuristic only
    has_dpcm = False
    if len(data) > 0x80:
        payload = data[0x80:]
        # Look for 0x11 (frequency), 0x12 (delta counter), 0x13 (length), 0x15 write patterns
        # This is a heuristic: check if byte 0x11 appears frequently in the code section
        has_dpcm = payload.count(bytes([0x11])) > 2

    return NSFTrack(
        path=path,
        version=version,
        total_songs=total_songs,
        starting_song=start_song,
        load_addr=load_addr,
        init_addr=init_addr,
        play_addr=play_addr,
        title=title,
        artist=artist,
        copyright=copyright,
        ntsc_speed=ntsc_speed,
        pal_speed=pal_speed,
        is_pal=is_pal,
        is_dual=is_dual,
        bankswitched=bankswitched,
        bankswitch_regs=bank_regs,
        extra_chip_flags=chip_flags,
        expansion_chips=expansion,
        has_dpcm=has_dpcm,
        tier=1, confidence=0.6,
        provenance_version=f"nsf_parser:{VERSION}",
        extraction_ts=ts,
    )
