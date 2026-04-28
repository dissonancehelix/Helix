"""
VGM Note Reconstructor — Helix Music Lab
=========================================
Converts a parsed VGMTrack into a SymbolicScore by replaying the register
write stream and reconstructing discrete note events with onset, pitch,
duration, and velocity for every chip in the VGM spec.

Supported chips
---------------
YM2612  (OPN2)   — Sega Mega Drive FM, 6 channels          logical ch 0–5
SN76489 (PSG)    — Sega/Texas Instruments, 3 tone + noise   logical ch 6–8
YM2151  (OPM)    — X68000/Arcade, 8 channels                logical ch 10–17
YM2413  (OPLL)   — MSX-MUSIC/Sega FM Unit, 9 melodic ch     logical ch 20–28
YM2203  (OPN)    — PC-88/Arcade, 3 FM + 3 SSG               logical ch 30–35
YM2608  (OPNA)   — PC-88VA/Arcade, 6 FM + 3 SSG             logical ch 40–48
YM2610  (OPNB)   — Neo Geo, 4 FM + 3 SSG                    logical ch 50–56
YM3812  (OPL2)   — AdLib/PC, 9 channels                     logical ch 60–68
YM3526  (OPL1)   — OPL1, 9 channels                         logical ch 60–68
YMF262  (OPL3)   — Sound Blaster Pro, 18 channels           logical ch 70–87
AY-3-8910        — ZX Spectrum/MSX/CPC, 3 tone              logical ch 90–92
NES APU          — Famicom/NES, 5 channels                  logical ch 100–104
Game Boy DMG     — 4 channels                               logical ch 110–113
HuC6280          — PC Engine/TG16, 6 channels               logical ch 120–125

Algorithm
---------
Each chip's register stream is replayed in VGM sample order.
For FM chips (OPN, OPM, OPLL, OPL): key-on register writes trigger note-on;
  key-off or a second key-on on the same channel triggers note-off.
For PSG/SSG chips (SN76489, AY-3-8910): volume-register transitions from
  silence (max attenuation) to sounding trigger note-on/off.
For NES APU and DMG: write to the length/trigger register triggers note-on.
For HuC6280: bit 7 of the control register enables/disables each channel.

All timing is in VGM samples (44100 Hz). Duration = (off_sample - on_sample) / 44100.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from model.domains.music.parsing.vgm_parser import VGMTrack, VGMEvent
from model.domains.music.domain_analysis.symbolic_music.score_representation import (
    NoteEvent,
    SymbolicScore,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE     = 44100
_A4_REF         = 653.0 * 16   # YM2612 fnum × 2^block for A4 at ~7.67 MHz
_PSG_CLOCK_HZ   = 3_579_545    # SN76489 clock (Mega Drive)
_PSG_DIVIDER    = 32
_PSG_VOL_SILENT = 15


# ---------------------------------------------------------------------------
# Pitch conversion helpers
# ---------------------------------------------------------------------------

def _fnum_to_midi(fnum: int, block: int) -> int:
    """YM2612/OPN family: F-number + block → MIDI note."""
    if fnum == 0:
        return -1
    try:
        ratio = fnum * (2 ** block) / _A4_REF
        if ratio <= 0:
            return -1
        return max(0, min(127, round(69 + 12 * math.log2(ratio))))
    except (ValueError, ZeroDivisionError):
        return -1


def _opl_fnum_to_midi(fnum: int, block: int) -> int:
    """OPL family (YM3812/YMF262): F-number + block → MIDI note.
    OPL reference: A4 at block=4, fnum=577 (OPL2 spec).
    """
    if fnum == 0:
        return -1
    try:
        f_hz = fnum * 49716.0 / (1 << (19 - block))
        if f_hz <= 0:
            return -1
        return max(0, min(127, round(69 + 12 * math.log2(f_hz / 440.0))))
    except (ValueError, ZeroDivisionError):
        return -1


# YM2151 (OPM): KC byte bits[6:4]=octave, bits[3:0]=note code
# Note code 0=C# through 10=B, 11=C (C is top of octave, not bottom)
_YM2151_NOTE_SEMI = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4]

def _kc_to_midi(kc: int) -> int:
    """YM2151 Key Code → MIDI note. octave 0 = C1 region."""
    octave = (kc >> 4) & 0x07
    note   = kc & 0x0F
    return max(0, min(127, (octave + 1) * 12 + _YM2151_NOTE_SEMI[note]))


def _psg_period_to_midi(period: int, psg_clock: int = _PSG_CLOCK_HZ) -> int:
    """SN76489 tone period → MIDI note."""
    if period <= 0:
        return -1
    freq = psg_clock / (_PSG_DIVIDER * period)
    try:
        return max(0, min(127, round(69 + 12 * math.log2(freq / 440.0))))
    except (ValueError, ZeroDivisionError):
        return -1


def _ay_period_to_midi(period: int, clock: int = 2_000_000) -> int:
    """AY-3-8910 tone period → MIDI note."""
    if period <= 0:
        return -1
    try:
        f_hz = clock / (16 * period)
        return max(0, min(127, round(69 + 12 * math.log2(f_hz / 440.0))))
    except (ValueError, ZeroDivisionError):
        return -1


def _nes_period_to_midi(period: int, is_triangle: bool = False) -> int:
    """NES APU pulse/triangle period → MIDI note."""
    if period < 0:
        return -1
    try:
        cpu_clock = 1_789_773
        divisor = 32 if is_triangle else 16
        f_hz = cpu_clock / (divisor * (period + 1))
        return max(0, min(127, round(69 + 12 * math.log2(f_hz / 440.0))))
    except (ValueError, ZeroDivisionError):
        return -1


def _dmg_freq_to_midi(freq_val: int) -> int:
    """Game Boy DMG pulse/wave freq register → MIDI note."""
    if freq_val >= 2048:
        return -1
    try:
        f_hz = 131072.0 / (2048 - freq_val)
        return max(0, min(127, round(69 + 12 * math.log2(f_hz / 440.0))))
    except (ValueError, ZeroDivisionError):
        return -1


def _huc_period_to_midi(period: int, clock: int = 3_579_545) -> int:
    """HuC6280 PC Engine PSG period → MIDI note."""
    if period <= 0:
        return -1
    try:
        f_hz = clock / (32 * period)
        return max(0, min(127, round(69 + 12 * math.log2(f_hz / 440.0))))
    except (ValueError, ZeroDivisionError):
        return -1


def _tl_to_velocity(tl: int) -> int:
    """YM2612/OPN Total Level (0=loud, 127=silent) → MIDI velocity."""
    return max(1, 127 - tl)


def _psg_vol_to_velocity(vol4: int) -> int:
    """PSG 4-bit volume (0=max, 15=silent) → MIDI velocity."""
    if vol4 >= _PSG_VOL_SILENT:
        return 0
    return max(1, round(127 * (1.0 - vol4 / 14.0)))


def _ay_amp_to_velocity(amp4: int) -> int:
    """AY amplitude (0=silent, 15=max) → MIDI velocity."""
    return max(1, round(amp4 / 15.0 * 127))


# ---------------------------------------------------------------------------
# Channel state dataclasses
# ---------------------------------------------------------------------------

@dataclass
class _FmState:
    """OPN/OPM-family FM channel state."""
    fnum:        int   = 0
    block:       int   = 0
    kc:          int   = -1    # YM2151 key code
    tl_op1:      int   = 100
    active_note: int   = -1
    on_sample:   int   = -1


@dataclass
class _OplState:
    """OPL-family channel state."""
    fnum_lo:     int   = 0
    fnum_hi:     int   = 0    # top 2 bits of 10-bit F-number
    block:       int   = 0
    active_note: int   = -1
    on_sample:   int   = -1


@dataclass
class _PsgChState:
    """SN76489 PSG tone channel state."""
    period_lo:   int   = 0
    period_hi:   int   = 0
    volume:      int   = 15
    active_note: int   = -1
    on_sample:   int   = -1
    on_velocity: int   = 64

    @property
    def period(self) -> int:
        return (self.period_hi << 4) | self.period_lo


@dataclass
class _AyChState:
    """AY-3-8910 single tone channel state."""
    period_lo:   int   = 0
    period_hi:   int   = 0    # bits 3-0 of hi reg
    amplitude:   int   = 0
    active_note: int   = -1
    on_sample:   int   = -1

    @property
    def period(self) -> int:
        return (self.period_hi << 8) | self.period_lo


@dataclass
class _PsgNoiseState:
    """SN76489 noise channel (ch 3) state."""
    noise_type:  int   = 1     # bit 2 of control byte: 0=periodic, 1=white
    rate:        int   = 0     # bits 1:0: 0=high,1=mid,2=low,3=tone2
    volume:      int   = 15    # 4-bit attenuation (15=silent)
    active_note: int   = -1
    on_sample:   int   = -1
    on_velocity: int   = 64

    @property
    def midi_note(self) -> int:
        """GM drum note based on noise type and rate."""
        if self.noise_type:   # white noise
            # High rate = closed hi-hat, low rate = open hi-hat
            return 46 if self.rate >= 2 else 42
        else:                 # periodic noise = buzz/tone → snare
            return 38


@dataclass
class _NesChState:
    """NES APU channel state."""
    period_lo:   int   = 0
    period_hi:   int   = 0    # top 3 bits
    active_note: int   = -1
    on_sample:   int   = -1
    is_triangle: bool  = False

    @property
    def period(self) -> int:
        return (self.period_hi << 8) | self.period_lo


@dataclass
class _DmgChState:
    """Game Boy DMG channel state."""
    freq_lo:     int   = 0
    freq_hi:     int   = 0    # top 3 bits
    active_note: int   = -1
    on_sample:   int   = -1

    @property
    def freq_val(self) -> int:
        return (self.freq_hi << 8) | self.freq_lo


@dataclass
class _HucChState:
    """HuC6280 PC Engine PSG channel state."""
    freq_lo:     int   = 0
    freq_hi:     int   = 0    # bits 3-0
    on_flag:     bool  = False
    volume:      int   = 0
    active_note: int   = -1
    on_sample:   int   = -1

    @property
    def period(self) -> int:
        return (self.freq_hi << 8) | self.freq_lo


# ---------------------------------------------------------------------------
# Reconstructor
# ---------------------------------------------------------------------------

def reconstruct(track: VGMTrack) -> SymbolicScore:
    """
    Replay VGM events and build a SymbolicScore with note-on/off events
    for every chip present in the track.
    """
    h = track.header
    duration_sec = h.total_samples / SAMPLE_RATE if h.total_samples > 0 else 1.0

    score = SymbolicScore(
        track_name=track.path.stem,
        duration_sec=duration_sec,
        sample_rate=SAMPLE_RATE,
    )

    if track.error:
        score.reconstruction_stats = {"error": track.error, "notes_reconstructed": 0}
        return score

    # -----------------------------------------------------------------------
    # Per-chip channel state
    # -----------------------------------------------------------------------
    ym2612_state:  list[_FmState]    = [_FmState()    for _ in range(6)]   # ch 0–5
    psg_state:     list[_PsgChState] = [_PsgChState() for _ in range(3)]   # ch 6–8
    psg_noise:     _PsgNoiseState   = _PsgNoiseState()                     # ch 141
    psg_latch_ch:  int = -1
    psg_latch_type:int = 0

    ym2151_state:  list[_FmState]    = [_FmState()    for _ in range(8)]   # ch 10–17
    ym2413_state:  list[_OplState]   = [_OplState()   for _ in range(9)]   # ch 20–28

    # OPN family share FM structure; SSG (AY-like) on same chip
    ym2203_fm:  list[_FmState]    = [_FmState()    for _ in range(3)]   # ch 30–32
    ym2203_ssg: list[_AyChState]  = [_AyChState()  for _ in range(3)]   # ch 33–35
    ym2608_fm:  list[_FmState]    = [_FmState()    for _ in range(6)]   # ch 40–45
    ym2608_ssg: list[_AyChState]  = [_AyChState()  for _ in range(3)]   # ch 46–48
    ym2610_fm:  list[_FmState]    = [_FmState()    for _ in range(4)]   # ch 50–53
    ym2610_ssg: list[_AyChState]  = [_AyChState()  for _ in range(3)]   # ch 54–56

    ym3812_state:  list[_OplState]   = [_OplState()   for _ in range(9)]   # ch 60–68
    ymf262_state:  list[_OplState]   = [_OplState()   for _ in range(18)]  # ch 70–87
    # YM3526/Y8950 share OPL register layout with YM3812
    ym3526_state:  list[_OplState]   = [_OplState()   for _ in range(9)]   # ch 60–68 (same base)

    ay_state:      list[_AyChState]  = [_AyChState()  for _ in range(3)]   # ch 90–92
    nes_state:     list[_NesChState] = [_NesChState()  for _ in range(5)]  # ch 100–104
    nes_state[2].is_triangle = True  # channel 2 = triangle

    dmg_state:     list[_DmgChState] = [_DmgChState() for _ in range(4)]   # ch 110–113
    huc_state:     list[_HucChState] = [_HucChState() for _ in range(6)]   # ch 120–125
    huc_sel:       int = 0

    # -----------------------------------------------------------------------
    # DAC / PCM percussion state
    # -----------------------------------------------------------------------

    # YM2612 DAC: channel 6 can be repurposed as 8-bit PCM (usually kick/snare).
    # We detect write bursts — any DAC write after a gap of >DAC_GAP_SAMPLES
    # is treated as a new percussion hit. Pitch is fixed (can't identify sample
    # type from PCM bytes without audio analysis).
    _DAC_GAP_SAMPLES  = 1000          # ~22ms gap → new hit
    _DAC_HIT_DURATION = 0.08          # 80ms placeholder duration
    _DAC_MIDI_NOTE    = 35            # GM: Bass Drum 2 (generic placeholder)
    _DAC_CHANNEL      = 9             # logical ch 9 = YM2612 DAC
    dac_enabled:       bool = False   # reg 0x2B bit 7
    dac_last_sample:   int  = -99999  # last sample a DAC write fired

    # ADPCM-A (YM2608/YM2610 port-1 regs 0x00–0x3F): 6 structured drum channels.
    # key-on reg 0x01 bits[5:0], key-off reg 0x02 bits[5:0].
    # GM mapping by convention (PC-88 / Neo Geo drum kit order):
    _ADPCM_A_NOTES = [35, 38, 49, 42, 47, 37]   # BD, SD, Crash, HH, Tom, Rim
    _ADPCM_A_BASE  = 130   # logical channels 130–135 (won't clash with melodic)

    @dataclass
    class _AdpcmAChState:
        active: bool = False
        on_sample: int = -1
        active_note: int = -1

    adpcm_a_2608: list = [_AdpcmAChState() for _ in range(6)]
    adpcm_a_2610: list = [_AdpcmAChState() for _ in range(6)]

    def _adpcm_a_event(reg: int, val: int, states: list, chip: str) -> None:
        """Handle ADPCM-A key-on (0x01) / key-off (0x02) registers."""
        if reg == 0x01:   # key-on mask
            for bit in range(6):
                if (val >> bit) & 0x01:
                    st = states[bit]
                    if st.active:   # re-trigger: close first
                        dur = max(0.0, (current_sample - st.on_sample) / SAMPLE_RATE)
                        completed_notes.append(NoteEvent(
                            channel=_ADPCM_A_BASE + bit,
                            note=_ADPCM_A_NOTES[bit],
                            start=st.on_sample / SAMPLE_RATE,
                            duration=dur,
                            velocity=90,
                            chip=chip,
                        ))
                    st.active      = True
                    st.on_sample   = current_sample
                    st.active_note = _ADPCM_A_NOTES[bit]
        elif reg == 0x02:  # key-off mask
            for bit in range(6):
                if (val >> bit) & 0x01:
                    st = states[bit]
                    if st.active:
                        dur = max(0.0, (current_sample - st.on_sample) / SAMPLE_RATE)
                        completed_notes.append(NoteEvent(
                            channel=_ADPCM_A_BASE + bit,
                            note=_ADPCM_A_NOTES[bit],
                            start=st.on_sample / SAMPLE_RATE,
                            duration=dur,
                            velocity=90,
                            chip=chip,
                        ))
                        st.active    = False
                        st.on_sample = -1

    completed_notes: list[NoteEvent] = []
    current_sample:  int = 0

    # -----------------------------------------------------------------------
    # Generic note open/close helpers
    # -----------------------------------------------------------------------

    def _open(ch_logical: int, note: int, start_sample: int, velocity: int,
              chip: str, state_obj) -> None:
        """Open a new note on a state object that has active_note / on_sample."""
        if state_obj.active_note >= 0:
            _close(ch_logical, start_sample, chip, state_obj)
        if note < 0:
            return
        state_obj.active_note = note
        state_obj.on_sample   = start_sample
        if hasattr(state_obj, 'on_velocity'):
            state_obj.on_velocity = velocity

    def _close(ch_logical: int, end_sample: int, chip: str, state_obj,
               velocity: int = 80) -> None:
        """Close an open note, appending a NoteEvent."""
        if state_obj.on_sample < 0 or state_obj.active_note < 0:
            return
        duration = max(0.0, (end_sample - state_obj.on_sample) / SAMPLE_RATE)
        completed_notes.append(NoteEvent(
            channel  = ch_logical,
            note     = state_obj.active_note,
            start    = state_obj.on_sample / SAMPLE_RATE,
            duration = duration,
            velocity = velocity,
            chip     = chip,
        ))
        state_obj.active_note = -1
        state_obj.on_sample   = -1

    # -----------------------------------------------------------------------
    # OPN-family FM helpers (YM2612, YM2203, YM2608, YM2610)
    # key-on reg 0x28 appears only on port-0 events per VGM spec
    # -----------------------------------------------------------------------

    def _opn_keyon(kind_p0: str, ev: VGMEvent,
                   states: list[_FmState], ch_base: int, chip: str) -> None:
        if ev.kind != kind_p0 or ev.reg != 0x28:
            return
        ch_raw  = ev.val & 0x07
        if ch_raw == 3:
            return               # invalid slot
        ch_idx  = ch_raw if ch_raw < 3 else ch_raw - 1
        if ch_idx >= len(states):
            return
        slots   = (ev.val >> 4) & 0x0F
        st      = states[ch_idx]
        if slots:
            note = _fnum_to_midi(st.fnum, st.block)
            vel  = _tl_to_velocity(st.tl_op1)
            _open(ch_base + ch_idx, note, current_sample, vel, chip, st)
        else:
            _close(ch_base + ch_idx, current_sample, chip, st,
                   _tl_to_velocity(st.tl_op1))

    def _opn_fnum(ev: VGMEvent, states: list[_FmState], port: int) -> None:
        ch_offset = port * 3
        r, v = ev.reg, ev.val
        if 0xA0 <= r <= 0xA2:
            ch = ch_offset + (r - 0xA0)
            if ch < len(states):
                states[ch].fnum = (states[ch].fnum & ~0xFF) | v
        elif 0xA4 <= r <= 0xA6:
            ch = ch_offset + (r - 0xA4)
            if ch < len(states):
                states[ch].fnum  = (states[ch].fnum & 0xFF) | ((v & 0x07) << 8)
                states[ch].block = (v >> 3) & 0x07
        elif 0x40 <= r <= 0x4F:
            ch = ch_offset + (r & 0x03)
            if ch < len(states) and ((r >> 2) & 0x03) == 0:
                states[ch].tl_op1 = v & 0x7F

    # -----------------------------------------------------------------------
    # OPL-family helpers (YM3812, YMF262, YM3526, Y8950, YM2413)
    # key-on: bit 5 of 0xB0–0xB8
    # -----------------------------------------------------------------------

    def _opl_reg(ev: VGMEvent, states: list[_OplState],
                 ch_base: int, chip: str) -> None:
        r, v = ev.reg, ev.val
        if 0xA0 <= r <= 0xA8:
            ch = r - 0xA0
            if ch < len(states):
                states[ch].fnum_lo = v
        elif 0xB0 <= r <= 0xB8:
            ch = r - 0xB0
            if ch >= len(states):
                return
            st        = states[ch]
            key_on    = (v >> 5) & 0x01
            block     = (v >> 2) & 0x07
            fnum_hi   = v & 0x03
            fnum      = (fnum_hi << 8) | st.fnum_lo
            note      = _opl_fnum_to_midi(fnum, block)
            st.block  = block
            st.fnum_hi = fnum_hi
            if key_on:
                _open(ch_base + ch, note, current_sample, 80, chip, st)
            else:
                _close(ch_base + ch, current_sample, chip, st)

    # -----------------------------------------------------------------------
    # SSG/AY helpers shared by OPN chips and standalone AY-3-8910
    # -----------------------------------------------------------------------

    def _ssg_reg(ev: VGMEvent, states: list[_AyChState],
                 ch_base: int, chip: str) -> None:
        r, v = ev.reg, ev.val
        if 0 <= r <= 5:
            ch = r >> 1
            if ch < len(states):
                if r & 1:
                    states[ch].period_hi = v & 0x0F
                else:
                    states[ch].period_lo = v
        elif 8 <= r <= 10:
            ch  = r - 8
            if ch >= len(states):
                return
            st  = states[ch]
            amp = v & 0x0F
            prev = st.amplitude
            st.amplitude = amp
            if prev == 0 and amp > 0:
                note = _ay_period_to_midi(st.period)
                vel  = _ay_amp_to_velocity(amp)
                _open(ch_base + ch, note, current_sample, vel, chip, st)
            elif prev > 0 and amp == 0:
                _close(ch_base + ch, current_sample, chip, st,
                       _ay_amp_to_velocity(prev))

    # -----------------------------------------------------------------------
    # Main event loop
    # -----------------------------------------------------------------------

    for ev in track.events:

        # --- Timing ---
        if ev.kind == "wait":
            current_sample += ev.samples
            continue
        if ev.kind == "end":
            break

        # --- YM2612 DAC burst detection — ch 9 ---
        # 0x80–0x8F: PCM byte written to DAC + wait n samples.
        # Gap > _DAC_GAP_SAMPLES between writes = new percussion hit.
        if ev.kind == "ym2612_dac":
            if dac_enabled and (current_sample - dac_last_sample) > _DAC_GAP_SAMPLES:
                completed_notes.append(NoteEvent(
                    channel  = _DAC_CHANNEL,
                    note     = _DAC_MIDI_NOTE,
                    start    = current_sample / SAMPLE_RATE,
                    duration = _DAC_HIT_DURATION,
                    velocity = 90,
                    chip     = "ym2612_dac",
                ))
            dac_last_sample = current_sample
            continue

        # --- YM2612 (Mega Drive) — ch 0–5 ---
        if ev.kind in ("ym2612_p0", "ym2612_p1"):
            port = 0 if ev.kind == "ym2612_p0" else 1
            # DAC enable: reg 0x2B bit 7 (port 0 only)
            if ev.kind == "ym2612_p0" and ev.reg == 0x2B:
                dac_enabled = bool((ev.val >> 7) & 0x01)
            _opn_keyon("ym2612_p0", ev, ym2612_state, 0, "ym2612")
            _opn_fnum(ev, ym2612_state, port)

        # --- SN76489 PSG — ch 6–8 ---
        elif ev.kind == "psg":
            b = ev.val
            if b & 0x80:
                ch        = (b >> 5) & 0x03
                reg_type  = (b >> 4) & 0x01
                data4     = b & 0x0F
                psg_latch_ch   = ch
                psg_latch_type = reg_type
                if ch <= 2:
                    ps = psg_state[ch]
                    if reg_type == 0:
                        ps.period_lo = data4
                        if ps.active_note >= 0:
                            new_note = _psg_period_to_midi(ps.period)
                            if new_note != ps.active_note:
                                _close(6 + ch, current_sample, "sn76489", ps,
                                       ps.on_velocity)
                                if new_note >= 0 and ps.volume < _PSG_VOL_SILENT:
                                    vel = _psg_vol_to_velocity(ps.volume)
                                    ps.on_velocity = vel
                                    _open(6 + ch, new_note, current_sample,
                                          vel, "sn76489", ps)
                    else:
                        old_vol = ps.volume
                        ps.volume = data4
                        if old_vol == _PSG_VOL_SILENT and ps.volume < _PSG_VOL_SILENT:
                            note = _psg_period_to_midi(ps.period)
                            vel  = _psg_vol_to_velocity(ps.volume)
                            ps.on_velocity = vel
                            _open(6 + ch, note, current_sample, vel, "sn76489", ps)
                        elif old_vol < _PSG_VOL_SILENT and ps.volume == _PSG_VOL_SILENT:
                            _close(6 + ch, current_sample, "sn76489", ps,
                                   ps.on_velocity)
                elif ch == 3:
                    # Noise channel
                    if reg_type == 0:
                        # Control byte: bit 2 = noise type, bits 1:0 = rate
                        psg_noise.noise_type = (data4 >> 2) & 0x01
                        psg_noise.rate       = data4 & 0x03
                        # Re-evaluate note if already sounding (type/rate changed)
                        if psg_noise.active_note >= 0:
                            new_note = psg_noise.midi_note
                            if new_note != psg_noise.active_note:
                                _close(141, current_sample, "sn76489_noise",
                                       psg_noise, psg_noise.on_velocity)
                                if psg_noise.volume < _PSG_VOL_SILENT:
                                    vel = _psg_vol_to_velocity(psg_noise.volume)
                                    psg_noise.on_velocity = vel
                                    _open(141, new_note, current_sample,
                                          vel, "sn76489_noise", psg_noise)
                    else:
                        # Volume byte
                        old_vol = psg_noise.volume
                        psg_noise.volume = data4
                        if old_vol == _PSG_VOL_SILENT and data4 < _PSG_VOL_SILENT:
                            note = psg_noise.midi_note
                            vel  = _psg_vol_to_velocity(data4)
                            psg_noise.on_velocity = vel
                            _open(141, note, current_sample, vel,
                                  "sn76489_noise", psg_noise)
                        elif old_vol < _PSG_VOL_SILENT and data4 == _PSG_VOL_SILENT:
                            _close(141, current_sample, "sn76489_noise",
                                   psg_noise, psg_noise.on_velocity)
            else:
                data6 = b & 0x3F
                if 0 <= psg_latch_ch <= 2 and psg_latch_type == 0:
                    ps = psg_state[psg_latch_ch]
                    ps.period_hi = data6
                    if ps.active_note >= 0:
                        new_note = _psg_period_to_midi(ps.period)
                        if new_note != ps.active_note:
                            _close(6 + psg_latch_ch, current_sample, "sn76489",
                                   ps, ps.on_velocity)
                            if new_note >= 0 and ps.volume < _PSG_VOL_SILENT:
                                vel = _psg_vol_to_velocity(ps.volume)
                                ps.on_velocity = vel
                                _open(6 + psg_latch_ch, new_note, current_sample,
                                      vel, "sn76489", ps)

        # --- YM2151 (OPM) — ch 10–17 ---
        elif ev.kind == "ym2151":
            r, v = ev.reg, ev.val
            if r == 0x08:
                # Key-on: bits[6:3]=slot mask, bits[2:0]=channel
                ch   = v & 0x07
                slots = (v >> 3) & 0x0F
                if ch < 8:
                    st   = ym2151_state[ch]
                    note = _kc_to_midi(st.kc) if st.kc >= 0 else -1
                    vel  = _tl_to_velocity(st.tl_op1)
                    if slots:
                        _open(10 + ch, note, current_sample, vel, "ym2151", st)
                    else:
                        _close(10 + ch, current_sample, "ym2151", st, vel)
            elif 0x28 <= r <= 0x2F:
                # KC pitch register
                ch = r - 0x28
                if ch < 8:
                    ym2151_state[ch].kc = v
            elif 0x60 <= r <= 0x7F:
                # TL (Total Level) for operators — carrier is op4 (slot 3)
                # Layout: slots 0–3 for channels 0–7; regs 0x60–0x7F
                op   = (r - 0x60) >> 3
                ch   = (r - 0x60) & 0x07
                if ch < 8 and op == 3:    # op4 = carrier
                    ym2151_state[ch].tl_op1 = v & 0x7F

        # --- YM2413 (OPLL) — ch 20–28 ---
        elif ev.kind == "ym2413":
            r, v = ev.reg, ev.val
            if 0x10 <= r <= 0x18:
                ch = r - 0x10
                if ch < 9:
                    ym2413_state[ch].fnum_lo = v
            elif 0x20 <= r <= 0x28:
                ch      = r - 0x20
                if ch >= 9:
                    continue
                st      = ym2413_state[ch]
                key_on  = (v >> 4) & 0x01
                block   = (v >> 1) & 0x07
                fnum_hi = v & 0x01
                fnum    = (fnum_hi << 8) | st.fnum_lo
                note    = _opl_fnum_to_midi(fnum, block)   # OPLL same formula as OPL
                st.block   = block
                st.fnum_hi = fnum_hi
                if key_on:
                    _open(20 + ch, note, current_sample, 80, "ym2413", st)
                else:
                    _close(20 + ch, current_sample, "ym2413", st)

        # --- YM2203 (OPN) — FM ch 30–32, SSG ch 33–35 ---
        elif ev.kind == "ym2203":
            r, v = ev.reg, ev.val
            if r == 0x28:
                # Key-on: same layout as YM2612 but only 3 channels
                ch_raw = v & 0x03
                slots  = (v >> 4) & 0x0F
                if ch_raw < 3:
                    st   = ym2203_fm[ch_raw]
                    note = _fnum_to_midi(st.fnum, st.block)
                    vel  = _tl_to_velocity(st.tl_op1)
                    if slots:
                        _open(30 + ch_raw, note, current_sample, vel, "ym2203", st)
                    else:
                        _close(30 + ch_raw, current_sample, "ym2203", st, vel)
            elif 0xA0 <= r <= 0xA2:
                ch = r - 0xA0
                if ch < 3:
                    ym2203_fm[ch].fnum = (ym2203_fm[ch].fnum & ~0xFF) | v
            elif 0xA4 <= r <= 0xA6:
                ch = r - 0xA4
                if ch < 3:
                    ym2203_fm[ch].fnum  = (ym2203_fm[ch].fnum & 0xFF) | ((v & 0x07) << 8)
                    ym2203_fm[ch].block = (v >> 3) & 0x07
            elif 0x40 <= r <= 0x4B:
                ch = r & 0x03
                op = (r - 0x40) >> 2
                if ch < 3 and op == 0:
                    ym2203_fm[ch].tl_op1 = v & 0x7F
            elif r <= 0x0F:
                # SSG registers (AY-compatible)
                _ssg_reg(ev, ym2203_ssg, 33, "ym2203_ssg")

        # --- YM2608 (OPNA) — FM ch 40–45, SSG ch 46–48, ADPCM-A ch 130–135 ---
        elif ev.kind in ("ym2608_p0", "ym2608_p1"):
            port = 0 if ev.kind == "ym2608_p0" else 1
            _opn_keyon("ym2608_p0", ev, ym2608_fm, 40, "ym2608")
            _opn_fnum(ev, ym2608_fm, port)
            if port == 0 and ev.reg <= 0x0F:
                _ssg_reg(ev, ym2608_ssg, 46, "ym2608_ssg")
            elif port == 1 and ev.reg in (0x01, 0x02):
                # ADPCM-A key-on (0x01) / key-off (0x02)
                _adpcm_a_event(ev.reg, ev.val, adpcm_a_2608, "ym2608_adpcm_a")

        # --- YM2610 (OPNB) — FM ch 50–53, SSG ch 54–56, ADPCM-A ch 130–135 ---
        elif ev.kind in ("ym2610_p0", "ym2610_p1"):
            port = 0 if ev.kind == "ym2610_p0" else 1
            _opn_keyon("ym2610_p0", ev, ym2610_fm, 50, "ym2610")
            _opn_fnum(ev, ym2610_fm, port)
            if port == 0 and ev.reg <= 0x0F:
                _ssg_reg(ev, ym2610_ssg, 54, "ym2610_ssg")
            elif port == 1 and ev.reg in (0x01, 0x02):
                _adpcm_a_event(ev.reg, ev.val, adpcm_a_2610, "ym2610_adpcm_a")

        # --- YM3812 (OPL2) — ch 60–68 ---
        elif ev.kind == "ym3812":
            _opl_reg(ev, ym3812_state, 60, "ym3812")

        # --- YM3526 (OPL1) — ch 60–68 (same base, won't coexist with OPL2) ---
        elif ev.kind == "ym3526":
            _opl_reg(ev, ym3526_state, 60, "ym3526")

        # --- Y8950 (OPL1 + ADPCM) — ch 60–68 ---
        elif ev.kind == "y8950":
            _opl_reg(ev, ym3526_state, 60, "y8950")

        # --- YMF262 (OPL3) — port 0 ch 70–78, port 1 ch 79–87 ---
        elif ev.kind in ("ymf262_p0", "ymf262_p1"):
            port     = 0 if ev.kind == "ymf262_p0" else 1
            ch_base  = 70 + port * 9
            states   = ymf262_state[port * 9 : port * 9 + 9]
            _opl_reg(ev, states, ch_base, "ymf262")

        # --- AY-3-8910 — ch 90–92 ---
        elif ev.kind == "ay8910":
            _ssg_reg(ev, ay_state, 90, "ay8910")

        # --- NES APU — ch 100–104 ---
        elif ev.kind == "nes_apu":
            r, v = ev.reg, ev.val
            # Pulse 1: regs 0x00–0x03; Pulse 2: 0x04–0x07
            # Triangle: 0x08–0x0B; Noise: 0x0C–0x0F; DMC: 0x10–0x13
            ch_map = {
                0: 0, 1: 0, 2: 0, 3: 0,       # pulse 1 → ch 0
                4: 1, 5: 1, 6: 1, 7: 1,        # pulse 2 → ch 1
                8: 2, 9: 2, 10: 2, 11: 2,      # triangle → ch 2
                12: 3, 13: 3, 14: 3, 15: 3,    # noise → ch 3
                16: 4, 17: 4, 18: 4, 19: 4,    # DMC → ch 4
            }
            ch = ch_map.get(r, -1)
            if ch < 0 or ch >= 5:
                pass
            else:
                st = nes_state[ch]
                ch_r = r - (ch * 4)   # register within the 4-register group
                if ch_r == 2:
                    # Period low (8 bits for pulse/triangle, 4 bits for noise)
                    st.period_lo = v
                elif ch_r == 3:
                    # Period high (top 3 bits) + length counter load → key-on
                    st.period_hi = (v >> 3) & 0x07
                    note = _nes_period_to_midi(st.period, st.is_triangle)
                    _open(100 + ch, note, current_sample, 80, "nes_apu", st)

        # --- Game Boy DMG — ch 110–113 ---
        elif ev.kind == "dmg":
            r, v = ev.reg, ev.val
            # Ch 1: 0x10–0x14, Ch 2: 0x15–0x19, Ch 3: 0x1A–0x1E, Ch 4: 0x1F–0x23
            if 0x10 <= r <= 0x14:
                ch, base = 0, 0x10
            elif 0x15 <= r <= 0x19:
                ch, base = 1, 0x15
            elif 0x1A <= r <= 0x1E:
                ch, base = 2, 0x1A
            elif 0x1F <= r <= 0x23:
                ch, base = 3, 0x1F
            else:
                continue
            st   = dmg_state[ch]
            r_ch = r - base
            if r_ch == 3:   # freq lo
                st.freq_lo = v
            elif r_ch == 4: # trigger (bit 7) + freq hi (bits 2–0)
                st.freq_hi = v & 0x07
                if (v >> 7) & 0x01:
                    note = _dmg_freq_to_midi(st.freq_val)
                    _open(110 + ch, note, current_sample, 80, "dmg", st)
            # No explicit key-off in DMG — length counter expires, but that
            # requires cycle-accurate emulation. Leave notes open until track end
            # or next trigger on same channel (handled by _open closing previous).

        # --- HuC6280 (PC Engine PSG) — ch 120–125 ---
        elif ev.kind == "huc6280":
            r, v = ev.reg, ev.val
            if r == 0x00:
                huc_sel = v & 0x07
            elif r == 0x02:
                if huc_sel < 6:
                    huc_state[huc_sel].freq_lo = v
            elif r == 0x03:
                if huc_sel < 6:
                    huc_state[huc_sel].freq_hi = v & 0x0F
            elif r == 0x04:
                if huc_sel >= 6:
                    pass
                else:
                    st      = huc_state[huc_sel]
                    on_new  = bool((v >> 7) & 0x01)
                    vol     = v & 0x0F
                    st.volume = vol
                    if on_new and not st.on_flag:
                        note = _huc_period_to_midi(st.period)
                        vel  = max(1, round(vol / 15.0 * 127))
                        _open(120 + huc_sel, note, current_sample, vel, "huc6280", st)
                    elif not on_new and st.on_flag:
                        vel = max(1, round(st.volume / 15.0 * 127))
                        _close(120 + huc_sel, current_sample, "huc6280", st, vel)
                    st.on_flag = on_new

    # -----------------------------------------------------------------------
    # Close any notes still open at end of track
    # -----------------------------------------------------------------------
    end_sample = h.total_samples if h.total_samples > 0 else current_sample

    def _close_all(states, ch_base: int, chip: str) -> None:
        for idx, st in enumerate(states):
            if getattr(st, 'active_note', -1) >= 0:
                vel = _tl_to_velocity(getattr(st, 'tl_op1', 80))
                _close(ch_base + idx, end_sample, chip, st, vel)

    _close_all(ym2612_state,  0,   "ym2612")
    _close_all(ym2151_state,  10,  "ym2151")
    _close_all(ym2413_state,  20,  "ym2413")
    _close_all(ym2203_fm,     30,  "ym2203")
    _close_all(ym2203_ssg,    33,  "ym2203_ssg")
    _close_all(ym2608_fm,     40,  "ym2608")
    _close_all(ym2608_ssg,    46,  "ym2608_ssg")
    _close_all(ym2610_fm,     50,  "ym2610")
    _close_all(ym2610_ssg,    54,  "ym2610_ssg")
    _close_all(ym3812_state,  60,  "ym3812")
    _close_all(ym3526_state,  60,  "ym3526")
    _close_all(ymf262_state,  70,  "ymf262")
    _close_all(ay_state,      90,  "ay8910")
    _close_all(nes_state,     100, "nes_apu")
    _close_all(dmg_state,     110, "dmg")
    _close_all(huc_state,     120, "huc6280")
    for ch_idx, ps in enumerate(psg_state):
        if ps.active_note >= 0:
            _close(6 + ch_idx, end_sample, "sn76489", ps, ps.on_velocity)
    if psg_noise.active_note >= 0:
        _close(141, end_sample, "sn76489_noise", psg_noise, psg_noise.on_velocity)

    # ADPCM-A — close any drums still flagged active at track end
    for bit, st in enumerate(adpcm_a_2608):
        if st.active and st.on_sample >= 0:
            dur = max(0.0, (end_sample - st.on_sample) / SAMPLE_RATE)
            completed_notes.append(NoteEvent(
                channel=_ADPCM_A_BASE + bit, note=_ADPCM_A_NOTES[bit],
                start=st.on_sample / SAMPLE_RATE, duration=dur,
                velocity=90, chip="ym2608_adpcm_a",
            ))
    for bit, st in enumerate(adpcm_a_2610):
        if st.active and st.on_sample >= 0:
            dur = max(0.0, (end_sample - st.on_sample) / SAMPLE_RATE)
            completed_notes.append(NoteEvent(
                channel=_ADPCM_A_BASE + bit, note=_ADPCM_A_NOTES[bit],
                start=st.on_sample / SAMPLE_RATE, duration=dur,
                velocity=90, chip="ym2610_adpcm_a",
            ))

    # -----------------------------------------------------------------------
    # Sort and finalise
    # -----------------------------------------------------------------------
    completed_notes.sort(key=lambda n: (n.start, n.channel))
    score.notes = completed_notes

    chip_counts: dict[str, int] = {}
    for n in completed_notes:
        chip_counts[n.chip] = chip_counts.get(n.chip, 0) + 1

    score.reconstruction_stats = {
        "notes_reconstructed": len(completed_notes),
        "notes_by_chip":       chip_counts,
        "unique_pitches":      len(score.unique_pitches),
        "pitch_range":         score.pitch_range,
        "avg_duration_sec":    round(score.avg_duration(), 4),
        "chips_active":        sorted(chip_counts.keys()),
    }

    return score

