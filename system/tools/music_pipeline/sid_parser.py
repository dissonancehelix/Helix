"""
SID Parser — Helix Music Lab (Tier A)
========================================
Static parser for Commodore 64 .sid files (PSID v1/v2/v3/v4 and RSID).

PSID/RSID format:
  0x00  4   Magic "PSID" or "RSID"
  0x04  2   Version (1–4)
  0x06  2   Data offset (0x76 for v1, 0x7C for v2+)
  0x08  2   Load address (0 = read from first 2 bytes of data)
  0x0A  2   Init address
  0x0C  2   Play address
  0x0E  2   Number of songs
  0x10  2   Default song (1-based)
  0x12  4   Speed flags (bit N = song N uses CIA1 timer if set, else VBI)
  0x16  32  Title (ISO Latin-1, null-padded)
  0x36  32  Author
  0x56  32  Released/Copyright
  --- v2+ ---
  0x76  2   Flags
  0x78  1   StartPage / PSID specific page
  0x79  1   PageLength
  0x7A  2   SecondSID address (v3+)
  0x7C  2   ThirdSID address (v4+)

v2 Flags (0x76):
  bits 1:0  — MUS data (0=built-in, 1=Compute! SidPlayer)
  bit  2    — PlaySID specific / BASIC (RSID only)
  bits 4:3  — SID model: 0=unknown, 1=6581, 2=8580, 3=6581+8580
  bits 6:5  — Clock: 0=unknown, 1=PAL, 2=NTSC, 3=PAL+NTSC
  bits 8:7  — Second SID model (v3+)
  bits 10:9 — Third SID model (v4+)

SID register layout (per chip, 29 regs):
  Voice 1: 0x00–0x06 (FREQ_LO, FREQ_HI, PW_LO, PW_HI, CR, AD, SR)
  Voice 2: 0x07–0x0D
  Voice 3: 0x0E–0x14
  Filter:  0x15 FCUT_LO, 0x16 FCUT_HI, 0x17 FRES (resonance + routing), 0x18 MODE_VOL
  Misc:    0x19 OSC3 (voice 3 oscillator), 0x1A ENV3 (voice 3 envelope)

Control Register (CR) bits:
  bit 0  GATE    — key-on/off
  bit 1  SYNC    — hard sync to voice N-1
  bit 2  RING    — ring modulation
  bit 3  TEST    — oscillator test (resets)
  bits 7:4  waveform: 0001=triangle, 0010=sawtooth, 0100=pulse, 1000=noise
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"

WAVEFORM_NAMES = {
    0x10: "triangle",
    0x20: "sawtooth",
    0x40: "pulse",
    0x80: "noise",
    0x30: "tri+saw",
    0x50: "tri+pulse",
    0x60: "saw+pulse",
    0x70: "tri+saw+pulse",
}

SID_MODELS = {0: "unknown", 1: "SID6581", 2: "SID8580", 3: "6581+8580"}
CLOCK_MODES = {0: "unknown", 1: "PAL", 2: "NTSC", 3: "PAL+NTSC"}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SIDVoice:
    voice_index:  int
    frequency:    int    # 16-bit raw
    pulse_width:  int    # 12-bit
    waveform:     str    # decoded waveform name
    gate:         bool   # GATE bit of CR
    sync:         bool
    ring_mod:     bool
    test:         bool
    attack:       int    # 0–15
    decay:        int    # 0–15
    sustain:      int    # 0–15
    release:      int    # 0–15
    # Approximated frequency in Hz (PAL: 985248 Hz / (16 * FREQ_REG))
    freq_hz:      float  = 0.0


@dataclass
class SIDTrack:
    path:            Path
    format:          str   # "PSID" | "RSID"
    version:         int
    load_addr:       int
    init_addr:       int
    play_addr:       int
    total_songs:     int
    default_song:    int
    title:           str
    author:          str
    released:        str
    # v2+ fields
    sid_model:       str   = "unknown"
    clock_mode:      str   = "unknown"
    second_sid_addr: int   = 0
    third_sid_addr:  int   = 0
    sid_count:       int   = 1   # 1, 2, or 3
    # Derived from flags
    is_rsid:         bool  = False
    # Voice analysis (first data block, static)
    voices:          list[SIDVoice] = field(default_factory=list)
    filter_cutoff:   int   = 0
    filter_res:      int   = 0
    filter_routing:  int   = 0   # bits 0–3 route voices to filter
    filter_mode:     str   = ""  # LP/BP/HP/notch
    master_volume:   int   = 0
    waveform_distribution: dict[str, int] = field(default_factory=dict)
    # Provenance
    tier:            int   = 1
    confidence:      float = 0.6
    provenance_version: str = f"sid_parser:{VERSION}"
    extraction_ts:   str   = ""
    error:           str   = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path":          str(self.path),
            "format":        self.format,
            "version":       self.version,
            "title":         self.title,
            "author":        self.author,
            "released":      self.released,
            "total_songs":   self.total_songs,
            "default_song":  self.default_song,
            "sid_model":     self.sid_model,
            "clock_mode":    self.clock_mode,
            "sid_count":     self.sid_count,
            "load_addr":     hex(self.load_addr),
            "init_addr":     hex(self.init_addr),
            "play_addr":     hex(self.play_addr),
            "filter": {
                "cutoff":   self.filter_cutoff,
                "resonance": self.filter_res,
                "routing":  bin(self.filter_routing),
                "mode":     self.filter_mode,
            },
            "master_volume": self.master_volume,
            "waveform_distribution": self.waveform_distribution,
            "voices": [
                {
                    "voice":      v.voice_index,
                    "waveform":   v.waveform,
                    "gate":       v.gate,
                    "sync":       v.sync,
                    "ring_mod":   v.ring_mod,
                    "freq_raw":   v.frequency,
                    "freq_hz":    round(v.freq_hz, 2),
                    "pulse_width": v.pulse_width,
                    "attack":     v.attack,
                    "decay":      v.decay,
                    "sustain":    v.sustain,
                    "release":    v.release,
                }
                for v in self.voices
            ],
            "tier":               self.tier,
            "confidence":         self.confidence,
            "provenance_version": self.provenance_version,
            "extraction_ts":      self.extraction_ts,
            "error":              self.error,
        }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _sid_freq_hz(freq_reg: int, clock: str = "PAL") -> float:
    """Convert SID frequency register to Hz."""
    clk = 985248 if clock == "PAL" else 1022727  # NTSC
    if freq_reg == 0:
        return 0.0
    return (freq_reg * clk) / (1 << 24)


def _parse_voice(data: bytes, base: int, clock: str) -> SIDVoice:
    freq_lo  = data[base + 0]
    freq_hi  = data[base + 1]
    pw_lo    = data[base + 2]
    pw_hi    = data[base + 3] & 0x0F
    cr       = data[base + 4]
    ad       = data[base + 5]
    sr       = data[base + 6]

    frequency = (freq_hi << 8) | freq_lo
    pulse_w   = (pw_hi << 8) | pw_lo
    wave_bits = cr & 0xF0
    waveform  = WAVEFORM_NAMES.get(wave_bits, f"0x{wave_bits:02X}")

    return SIDVoice(
        voice_index=base // 7,
        frequency=frequency,
        pulse_width=pulse_w,
        waveform=waveform,
        gate=bool(cr & 0x01),
        sync=bool(cr & 0x02),
        ring_mod=bool(cr & 0x04),
        test=bool(cr & 0x08),
        attack=(ad >> 4) & 0x0F,
        decay=ad & 0x0F,
        sustain=(sr >> 4) & 0x0F,
        release=sr & 0x0F,
        freq_hz=_sid_freq_hz(frequency, clock),
    )


def parse(path: Path) -> SIDTrack:
    """Parse a .sid file into a SIDTrack. Never raises."""
    ts = datetime.now(timezone.utc).isoformat()
    try:
        data = path.read_bytes()
    except Exception as e:
        return SIDTrack(path=path, format="", version=0, load_addr=0,
                        init_addr=0, play_addr=0, total_songs=0, default_song=1,
                        title="", author="", released="", error=str(e), extraction_ts=ts)

    if len(data) < 0x76:
        return SIDTrack(path=path, format="", version=0, load_addr=0,
                        init_addr=0, play_addr=0, total_songs=0, default_song=1,
                        title="", author="", released="",
                        error="File too short", extraction_ts=ts)

    magic = data[:4].decode("ascii", errors="replace")
    if magic not in ("PSID", "RSID"):
        return SIDTrack(path=path, format="", version=0, load_addr=0,
                        init_addr=0, play_addr=0, total_songs=0, default_song=1,
                        title="", author="", released="",
                        error=f"Not a valid SID file (magic={magic!r})", extraction_ts=ts)

    def _s(off: int, length: int) -> str:
        return data[off:off + length].rstrip(b"\x00").decode("latin-1", errors="replace").strip()

    version,     = struct.unpack_from(">H", data, 0x04)
    data_offset, = struct.unpack_from(">H", data, 0x06)
    load_addr,   = struct.unpack_from(">H", data, 0x08)
    init_addr,   = struct.unpack_from(">H", data, 0x0A)
    play_addr,   = struct.unpack_from(">H", data, 0x0C)
    num_songs,   = struct.unpack_from(">H", data, 0x0E)
    def_song,    = struct.unpack_from(">H", data, 0x10)
    title        = _s(0x16, 32)
    author       = _s(0x36, 32)
    released     = _s(0x56, 32)

    sid_model    = "unknown"
    clock_mode   = "unknown"
    second_addr  = 0
    third_addr   = 0
    sid_count    = 1

    if version >= 2 and len(data) >= 0x7C:
        flags, = struct.unpack_from(">H", data, 0x76)
        model_bits = (flags >> 4) & 0x03
        clock_bits = (flags >> 2) & 0x03
        sid_model  = SID_MODELS.get(model_bits, "unknown")
        clock_mode = CLOCK_MODES.get(clock_bits, "unknown")

    if version >= 3 and len(data) >= 0x7C:
        second_addr, = struct.unpack_from(">H", data, 0x7A)
        if second_addr:
            sid_count = 2

    if version >= 4 and len(data) >= 0x7E:
        third_addr, = struct.unpack_from(">H", data, 0x7C)
        if third_addr:
            sid_count = 3

    # If load_addr == 0, first 2 bytes of data section are actual load address
    if load_addr == 0 and len(data) > data_offset + 1:
        load_addr, = struct.unpack_from("<H", data, data_offset)
        actual_data_start = data_offset + 2
    else:
        actual_data_start = data_offset

    # Parse voice register snapshot from start of data if it looks like SID regs
    # (heuristic: if load_addr in SID I/O range 0xD400–0xD7FF or data is available)
    voices: list[SIDVoice] = []
    wave_dist: dict[str, int] = {}
    filter_cutoff = filter_res = filter_routing = master_volume = 0
    filter_mode = ""

    if len(data) >= actual_data_start + 29:
        seg = data[actual_data_start:actual_data_start + 29]
        for i in range(3):
            v = _parse_voice(seg, i * 7, clock_mode)
            voices.append(v)
            wave_dist[v.waveform] = wave_dist.get(v.waveform, 0) + 1

        if len(seg) >= 25:
            fcut_lo  = seg[0x15]
            fcut_hi  = seg[0x16]
            fres_reg = seg[0x17]
            mode_vol = seg[0x18]
            filter_cutoff  = ((fcut_hi & 0x07) << 8) | fcut_lo
            filter_res     = (fres_reg >> 4) & 0x0F
            filter_routing = fres_reg & 0x07
            master_volume  = mode_vol & 0x0F
            mode_bits      = (mode_vol >> 4) & 0x0F
            modes = []
            if mode_bits & 0x01: modes.append("LP")
            if mode_bits & 0x02: modes.append("BP")
            if mode_bits & 0x04: modes.append("HP")
            if mode_bits & 0x08: modes.append("notch")
            filter_mode = "+".join(modes) if modes else "off"

    return SIDTrack(
        path=path, format=magic, version=version,
        load_addr=load_addr, init_addr=init_addr, play_addr=play_addr,
        total_songs=num_songs, default_song=def_song,
        title=title, author=author, released=released,
        sid_model=sid_model, clock_mode=clock_mode,
        second_sid_addr=second_addr, third_sid_addr=third_addr,
        sid_count=sid_count, is_rsid=(magic == "RSID"),
        voices=voices,
        filter_cutoff=filter_cutoff, filter_res=filter_res,
        filter_routing=filter_routing, filter_mode=filter_mode,
        master_volume=master_volume,
        waveform_distribution=wave_dist,
        tier=1, confidence=0.6,
        provenance_version=f"sid_parser:{VERSION}",
        extraction_ts=ts,
    )
