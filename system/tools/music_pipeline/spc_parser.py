"""
SPC700 Parser — Helix Music Lab (Tier A)
==========================================
Parses SNES .spc files (SPC700 CPU + DSP state snapshots).

SPC format:
  Offset  Size  Description
  0x00    27    Magic "SNES-SPC700 Sound File Data v0.30\x1a\x1a"
  0x21    1     Has ID666 tags (0x1a=binary, 0x1d=text, else=none)
  0x22    1     Version minor
  0x25    2     PC (program counter)
  0x27    1     A register
  0x28    1     X register
  0x29    1     Y register
  0x2A    1     PSW (processor status word)
  0x2B    1     SP (stack pointer)
  0x2E    32    Song title (if ID666)
  0x4E    32    Game name (if ID666)
  0x6E    16    Dumper name (if ID666)
  0x7E    32    Comments (if ID666)
  0x9E    11    Date dumped (if ID666)
  0xA9    3     Seconds to play before fading
  0xAC    5     Fade length in ms
  0xB1    32    Artist name (if ID666)
  0xBF    1     Default channel disables
  0xC0    1     Emulator used to dump
  0x100   65536 64KB SPC700 RAM
  0x10100 128   DSP register file
  0x10180 64    Unused
  0x101C0 64    Extra RAM (IPL area)

DSP register layout (128 bytes, indexed by DSP addr 0x00–0x7F):
  Voice registers (8 voices × 16 regs starting at 0x00, 0x10, ... 0x70):
    +0  VOL_L    Gain left   (signed)
    +1  VOL_R    Gain right  (signed)
    +2  PITCH_L  Pitch low
    +3  PITCH_H  Pitch high (only 6 bits used)
    +4  SRCN     Sample source number
    +5  ADSR_1   Attack/Decay
    +6  ADSR_2   Sustain level + release
    +7  GAIN     Gain / ADSR mode
    +8  ENVX     Current envelope level (read-only)
    +9  OUTX     Current output level (read-only)
  Global registers:
    0x0C  MVOL_L   Main volume left
    0x1C  MVOL_R   Main volume right
    0x2C  EVOL_L   Echo volume left
    0x3C  EVOL_R   Echo volume right
    0x4C  KON      Key-on bitmask
    0x5C  KOFF     Key-off bitmask
    0x6C  FLG      DSP flags (noise freq, echo off, mute, soft reset)
    0x7C  ENDX     Sample end bitmask (read-only)
    0x0D  EFB      Echo feedback
    0x2D  PMON     Pitch modulation enables
    0x3D  NON      Noise enables
    0x4D  EON      Echo enables
    0x5D  DIR      Sample table directory page
    0x6D  ESA      Echo buffer start page
    0x7D  EDL      Echo delay (ring buffer length)
    0x0F–0x7F (step 0x10)  FIR coefficients C0–C7
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
SPC_MAGIC = b"SNES-SPC700 Sound File Data v0.30\x1a\x1a"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SPCVoice:
    """DSP register snapshot for one SPC700 voice."""
    voice_index:  int
    vol_l:        int    # signed byte
    vol_r:        int    # signed byte
    pitch:        int    # 14-bit raw pitch value
    srcn:         int    # sample number
    adsr1:        int    # attack/decay raw byte
    adsr2:        int    # sustain/release raw byte
    gain:         int
    envx:         int    # current envelope (read-only snapshot)
    outx:         int    # current output (read-only snapshot)
    # Decoded ADSR fields
    adsr_enabled: bool   = False
    attack:       int    = 0    # 0–15
    decay:        int    = 0    # 0–7
    sustain_level: int   = 0   # 0–7
    release:      int    = 0   # 0–31
    # Derived
    active:       bool   = False   # voice in KON state at snapshot time


@dataclass
class SPCTrack:
    """Full SPC700 state snapshot extracted from a .spc file."""
    path:         Path
    # Header fields
    has_id666:    bool
    pc:           int
    a:            int
    x:            int
    y:            int
    psw:          int
    sp:           int
    # ID666 metadata
    title:        str   = ""
    game:         str   = ""
    artist:       str   = ""
    dumper:       str   = ""
    comment:      str   = ""
    date_dumped:  str   = ""
    play_seconds: int   = 0
    fade_ms:      int   = 0
    # DSP state
    voices:       list[SPCVoice] = field(default_factory=list)
    kon_mask:     int   = 0    # which voices were keyed on
    koff_mask:    int   = 0    # which voices were keyed off
    non_mask:     int   = 0    # noise enable mask
    eon_mask:     int   = 0    # echo enable mask
    flg:          int   = 0    # DSP flags
    dir_page:     int   = 0    # sample directory page
    echo_delay:   int   = 0    # EDL: echo ring buffer length
    echo_feedback: int  = 0    # EFB
    echo_vol_l:   int   = 0
    echo_vol_r:   int   = 0
    fir_coefs:    list[int] = field(default_factory=list)
    mvol_l:       int   = 0
    mvol_r:       int   = 0
    # Derived summaries
    active_voice_count: int = 0
    sample_count:   int = 0   # distinct SRCN values in use
    echo_enabled:   bool = False
    # Provenance
    tier:         int   = 1
    confidence:   float = 0.6
    provenance_version: str = f"spc_parser:{VERSION}"
    extraction_ts: str  = ""
    error:        str   = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path":                str(self.path),
            "title":               self.title,
            "game":                self.game,
            "artist":              self.artist,
            "dumper":              self.dumper,
            "comment":             self.comment,
            "date_dumped":         self.date_dumped,
            "play_seconds":        self.play_seconds,
            "fade_ms":             self.fade_ms,
            "pc":                  hex(self.pc),
            "kon_mask":            bin(self.kon_mask),
            "active_voice_count":  self.active_voice_count,
            "sample_count":        self.sample_count,
            "echo_enabled":        self.echo_enabled,
            "echo_delay":          self.echo_delay,
            "echo_feedback":       self.echo_feedback,
            "dir_page":            self.dir_page,
            "fir_coefs":           self.fir_coefs,
            "voices": [
                {
                    "voice":   v.voice_index,
                    "active":  v.active,
                    "srcn":    v.srcn,
                    "pitch":   v.pitch,
                    "adsr_en": v.adsr_enabled,
                    "attack":  v.attack,
                    "decay":   v.decay,
                    "sustain": v.sustain_level,
                    "release": v.release,
                    "gain":    v.gain,
                    "vol_l":   v.vol_l,
                    "vol_r":   v.vol_r,
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

def _signed_byte(b: int) -> int:
    return b if b < 128 else b - 256


def parse(path: Path) -> SPCTrack:
    """Parse a .spc file into an SPCTrack. Never raises — errors in .error."""
    ts = datetime.now(timezone.utc).isoformat()
    try:
        data = path.read_bytes()
    except Exception as e:
        return SPCTrack(path=path, has_id666=False, pc=0, a=0, x=0, y=0, psw=0,
                        sp=0, error=str(e), extraction_ts=ts)

    if len(data) < 0x10200:
        return SPCTrack(path=path, has_id666=False, pc=0, a=0, x=0, y=0, psw=0,
                        sp=0, error=f"File too short: {len(data)} bytes", extraction_ts=ts)

    if data[:len(SPC_MAGIC)] != SPC_MAGIC:
        return SPCTrack(path=path, has_id666=False, pc=0, a=0, x=0, y=0, psw=0,
                        sp=0, error="Not a valid SPC file (bad magic)", extraction_ts=ts)

    has_id666 = data[0x21] in (0x1A, 0x1D)
    pc,  = struct.unpack_from("<H", data, 0x25)
    a   = data[0x27]
    x   = data[0x28]
    y   = data[0x29]
    psw = data[0x2A]
    sp  = data[0x2B]

    title = game = artist = dumper = comment = date_dumped = ""
    play_seconds = fade_ms = 0

    if has_id666:
        def _s(off: int, length: int) -> str:
            return data[off:off + length].rstrip(b"\x00").decode("ascii", errors="replace").strip()
        title        = _s(0x2E, 32)
        game         = _s(0x4E, 32)
        dumper       = _s(0x6E, 16)
        comment      = _s(0x7E, 32)
        date_dumped  = _s(0x9E, 11)
        play_seconds = int(_s(0xA9, 3) or "0")
        fade_ms      = int(_s(0xAC, 5) or "0")
        artist       = _s(0xB1, 32)

    # DSP registers at 0x10100
    dsp = data[0x10100:0x10180]

    # Global DSP registers
    mvol_l       = _signed_byte(dsp[0x0C])
    mvol_r       = _signed_byte(dsp[0x1C])
    evol_l       = _signed_byte(dsp[0x2C])
    evol_r       = _signed_byte(dsp[0x3C])
    kon_mask     = dsp[0x4C]
    koff_mask    = dsp[0x5C]
    flg          = dsp[0x6C]
    eon_mask     = dsp[0x4D]
    dir_page     = dsp[0x5D]
    echo_delay   = dsp[0x7D] & 0x0F
    echo_fb      = _signed_byte(dsp[0x0D])
    non_mask     = dsp[0x3D]
    fir_coefs    = [_signed_byte(dsp[0x0F + i * 0x10]) for i in range(8)]

    # Per-voice registers
    voices = []
    src_used: set[int] = set()
    for i in range(8):
        base   = i * 0x10
        vol_l  = _signed_byte(dsp[base + 0])
        vol_r  = _signed_byte(dsp[base + 1])
        pitch  = ((dsp[base + 3] & 0x3F) << 8) | dsp[base + 2]
        srcn   = dsp[base + 4]
        adsr1  = dsp[base + 5]
        adsr2  = dsp[base + 6]
        gain   = dsp[base + 7]
        envx   = dsp[base + 8]
        outx   = dsp[base + 9]

        adsr_enabled = bool(adsr1 & 0x80)
        attack       = adsr1 & 0x0F
        decay        = (adsr1 >> 4) & 0x07
        sustain_lvl  = (adsr2 >> 5) & 0x07
        release      = adsr2 & 0x1F

        active = bool(kon_mask & (1 << i))
        if active or envx > 0:
            src_used.add(srcn)

        voices.append(SPCVoice(
            voice_index=i, vol_l=vol_l, vol_r=vol_r, pitch=pitch,
            srcn=srcn, adsr1=adsr1, adsr2=adsr2, gain=gain,
            envx=envx, outx=outx, adsr_enabled=adsr_enabled,
            attack=attack, decay=decay, sustain_level=sustain_lvl,
            release=release, active=active,
        ))

    active_count  = bin(kon_mask).count("1")
    echo_enabled  = not bool(flg & 0x20)   # bit 5 of FLG = disable echo

    return SPCTrack(
        path=path, has_id666=has_id666,
        pc=pc, a=a, x=x, y=y, psw=psw, sp=sp,
        title=title, game=game, artist=artist,
        dumper=dumper, comment=comment, date_dumped=date_dumped,
        play_seconds=play_seconds, fade_ms=fade_ms,
        voices=voices,
        kon_mask=kon_mask, koff_mask=koff_mask,
        non_mask=non_mask, eon_mask=eon_mask, flg=flg,
        dir_page=dir_page, echo_delay=echo_delay,
        echo_feedback=echo_fb, echo_vol_l=evol_l, echo_vol_r=evol_r,
        fir_coefs=fir_coefs, mvol_l=mvol_l, mvol_r=mvol_r,
        active_voice_count=active_count,
        sample_count=len(src_used),
        echo_enabled=echo_enabled,
        tier=1, confidence=0.6,
        provenance_version=f"spc_parser:{VERSION}",
        extraction_ts=ts,
    )
