"""
VGM Note Reconstructor — Helix Music Lab
=========================================
Converts a parsed VGMTrack into a SymbolicScore by replaying the register
write stream and reconstructing discrete note events.

Algorithm — YM2612 FM (logical channels 0–5):
  - Maintain a cursor of the current sample position (incremented by wait events)
  - Track FNUM + BLOCK per YM2612 channel (channels 0–5) across port 0/1 writes
  - Track Total Level (op1) per channel as a velocity proxy
  - On reg 0x28 (KEY_ON):
      slots = (val >> 4) & 0x0F
      ch_raw = val & 0x07  →  ch_idx ∈ {0,1,2,4,5,6} → logical 0–5
      If slots > 0 → note-on: close any open note on that channel, open new
      If slots = 0 → note-off: close open note on that channel
  - FNUM→MIDI: semitone = round(69 + 12 × log2(fnum × 2^block / (653 × 16)))
  - Velocity proxy: 127 − TL_op1  (op1 carrier TL, 0 = loudest, 127 = silent)

Algorithm — SN76489 PSG (logical channels 6–8, tone only):
  SN76489 uses a serial byte protocol. Each VGM PSG event is one byte:
    - Bit 7 = 1  → LATCH/DATA byte
        bits 6:5  = channel (0–3; ch3 = noise, not tracked here)
        bit  4    = register type (0 = tone period, 1 = volume)
        bits 3:0  = data
    - Bit 7 = 0  → DATA continuation byte (upper 6 bits of 10-bit period)
  Period reconstruction: tone_period[ch] = (data_high << 4) | data_low  (10-bit)
  Frequency: f = PSG_CLOCK / (32 × period)   [Genesis clock = 3_579_545 Hz]
  Volume: 4-bit, 0 = max, 15 = silence
  Note detection:
    - Volume transitions 15→<15 with period > 0: note-on
    - Volume transitions →15: note-off
    - Period change while sounding: note-off (previous pitch) + note-on (new pitch)
  MIDI pitch: round(69 + 12 × log2(f / 440))

Output: SymbolicScore with all NoteEvents sorted by start time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from domains.music.vgm_parser import VGMTrack, VGMEvent
from domains.music.analysis.symbolic_music.score_representation import (
    NoteEvent,
    SymbolicScore,
)


# ---------------------------------------------------------------------------
# Constants (mirrors feature_extractor.py for consistency)
# ---------------------------------------------------------------------------

SAMPLE_RATE  = 44100
REG_KEY_ON   = 0x28
REG_FREQ_LO  = 0xA0   # A0–A2 (per port)
REG_FREQ_HI  = 0xA4   # A4–A6 (per port), carries block in bits 5:3
REG_ALG_FB   = 0xB0   # B0–B2 (per port)
REG_TL_BASE  = 0x40   # 0x40–0x4F total level

# Genesis YM2612 A4 reference: fnum=653, block=4 ≈ 440 Hz at ~7.67 MHz clock
_A4_REF = 653.0 * 16   # fnum × 2^block for A4

# SN76489 PSG constants (Genesis / Mega Drive)
# Clock = master OSC / 15 = 53,693,100 / 15 = 3,579,540 Hz
_PSG_CLOCK_HZ = 3_579_545   # standard Genesis SN76489 clock
_PSG_DIVIDER  = 32           # period → frequency divisor
_PSG_VOL_SILENT = 15         # 4-bit volume value that means silence


def _fnum_to_midi(fnum: int, block: int) -> int:
    """Convert YM2612 F-number + block to MIDI note number (0–127)."""
    if fnum == 0:
        return -1
    try:
        ratio = fnum * (2 ** block) / _A4_REF
        if ratio <= 0:
            return -1
        semitone = round(69 + 12 * math.log2(ratio))
        return max(0, min(127, semitone))
    except (ValueError, ZeroDivisionError):
        return -1


def _tl_to_velocity(tl: int) -> int:
    """Map Total Level (0=loudest, 127=silent) to MIDI velocity (0–127)."""
    return max(1, 127 - tl)


def _psg_period_to_midi(period: int, psg_clock: int = _PSG_CLOCK_HZ) -> int:
    """Convert a 10-bit SN76489 tone period to MIDI note number.

    f = psg_clock / (32 × period)
    midi = round(69 + 12 × log2(f / 440))
    Returns -1 when period is 0 or out of audible MIDI range.
    """
    if period <= 0:
        return -1
    freq = psg_clock / (_PSG_DIVIDER * period)
    if freq <= 0.0:
        return -1
    try:
        note = round(69 + 12 * math.log2(freq / 440.0))
    except (ValueError, ZeroDivisionError):
        return -1
    return note if 0 <= note <= 127 else -1


def _psg_vol_to_velocity(vol4: int) -> int:
    """Map PSG 4-bit volume (0=max, 15=silent) to MIDI velocity (1–127)."""
    # Each step is ~2 dB attenuation; 0 → velocity 127, 14 → ~9
    if vol4 >= _PSG_VOL_SILENT:
        return 0
    return max(1, round(127 * (1.0 - vol4 / 14.0)))


# ---------------------------------------------------------------------------
# Channel state
# ---------------------------------------------------------------------------

@dataclass
class _ChState:
    """Mutable per-channel state during reconstruction (YM2612 FM channel)."""
    fnum:        int   = 0
    block:       int   = 0
    tl_op1:      int   = 100   # Total Level for op1 (carrier proxy)
    active_note: int   = -1    # MIDI note currently sounding (-1 = silent)
    on_sample:   int   = -1    # sample at which current note started (-1 = off)


@dataclass
class _PsgChState:
    """Mutable per-channel state for SN76489 PSG tone reconstruction."""
    period_lo:   int   = 0     # lower 4 bits of 10-bit period (from LATCH byte)
    period_hi:   int   = 0     # upper 6 bits of 10-bit period (from DATA byte)
    volume:      int   = 15    # 4-bit volume (15 = silent)
    latch_ch:    int   = -1    # channel currently latched for DATA continuation
    latch_type:  int   = 0     # 0 = tone, 1 = volume
    active_note: int   = -1    # MIDI note currently sounding (-1 = silent)
    on_sample:   int   = -1    # sample at which current note started
    on_velocity: int   = 64    # velocity when note started

    @property
    def period(self) -> int:
        return (self.period_hi << 4) | self.period_lo


# ---------------------------------------------------------------------------
# Reconstructor
# ---------------------------------------------------------------------------

def reconstruct(track: VGMTrack) -> SymbolicScore:
    """
    Replay *track* events and build a SymbolicScore.

    Returns a SymbolicScore.  On error, returns a score with empty notes and
    the error captured in reconstruction_stats.
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

    # ---- channel state -------------------------------------------------
    # 6 YM2612 FM channels (0–5), 3 PSG tone channels (6–8), 1 PSG noise (9)
    fm_state:  list[_ChState]    = [_ChState()    for _ in range(6)]
    psg_state: list[_PsgChState] = [_PsgChState() for _ in range(3)]  # ch0–ch2 tone
    # psg_latch tracks which channel+type is awaiting a DATA continuation byte
    psg_latch_ch:   int = -1
    psg_latch_type: int = 0

    completed_notes: list[NoteEvent] = []
    current_sample: int = 0

    # counters for stats
    keyon_events      = 0
    keyoff_events     = 0
    orphan_keyons     = 0   # key-ons where note stayed open until track end
    psg_note_events   = 0

    def _close_channel(ch_idx: int, end_sample: int) -> None:
        """Close an open note on *ch_idx*, computing duration."""
        st = fm_state[ch_idx]
        if st.on_sample < 0:
            return
        duration = (end_sample - st.on_sample) / SAMPLE_RATE
        if duration < 0.0:
            duration = 0.0
        completed_notes.append(NoteEvent(
            channel=ch_idx,
            note=st.active_note,
            start=st.on_sample / SAMPLE_RATE,
            duration=duration,
            velocity=_tl_to_velocity(st.tl_op1),
            chip="ym2612",
        ))
        st.active_note = -1
        st.on_sample   = -1

    # ---- PSG note helpers ------------------------------------------------

    def _psg_open(ch: int, note: int, vel: int) -> None:
        """Open a new PSG note on tone channel *ch* (0–2 → logical 6–8)."""
        nonlocal psg_note_events
        ps = psg_state[ch]
        if ps.active_note >= 0:
            _psg_close(ch, current_sample)
        if note < 0:
            return
        ps.active_note = note
        ps.on_sample   = current_sample
        ps.on_velocity = vel
        psg_note_events += 1

    def _psg_close(ch: int, end_sample: int) -> None:
        """Close an open PSG note on tone channel *ch*."""
        nonlocal keyoff_events
        ps = psg_state[ch]
        if ps.on_sample < 0:
            return
        duration = max(0.0, (end_sample - ps.on_sample) / SAMPLE_RATE)
        completed_notes.append(NoteEvent(
            channel=6 + ch,           # logical channel 6–8
            note=ps.active_note,
            start=ps.on_sample / SAMPLE_RATE,
            duration=duration,
            velocity=ps.on_velocity,
            chip="sn76489",
        ))
        ps.active_note = -1
        ps.on_sample   = -1
        keyoff_events += 1

    for ev in track.events:

        # ---- timing -------------------------------------------------------
        if ev.kind == "wait":
            current_sample += ev.samples
            continue

        if ev.kind == "end":
            break

        # ---- SN76489 PSG --------------------------------------------------
        if ev.kind == "psg":
            b = ev.val
            if b & 0x80:
                # LATCH/DATA byte: set latched channel + type
                ch        = (b >> 5) & 0x03   # bits 6:5
                reg_type  = (b >> 4) & 0x01   # bit 4: 0=tone, 1=vol
                data4     = b & 0x0F           # bits 3:0
                psg_latch_ch   = ch
                psg_latch_type = reg_type

                if ch <= 2:
                    ps = psg_state[ch]
                    if reg_type == 0:
                        # Tone period lower nibble
                        ps.period_lo = data4
                        # Period changed while sounding → pitch change
                        if ps.active_note >= 0:
                            new_note = _psg_period_to_midi(ps.period)
                            if new_note != ps.active_note:
                                _psg_close(ch, current_sample)
                                if new_note >= 0 and ps.volume < _PSG_VOL_SILENT:
                                    vel = _psg_vol_to_velocity(ps.volume)
                                    _psg_open(ch, new_note, vel)
                    else:
                        # Volume update
                        old_vol = ps.volume
                        ps.volume = data4
                        if old_vol == _PSG_VOL_SILENT and ps.volume < _PSG_VOL_SILENT:
                            # Silence → sounding: note-on
                            note = _psg_period_to_midi(ps.period)
                            vel  = _psg_vol_to_velocity(ps.volume)
                            _psg_open(ch, note, vel)
                        elif old_vol < _PSG_VOL_SILENT and ps.volume == _PSG_VOL_SILENT:
                            # Sounding → silence: note-off
                            _psg_close(ch, current_sample)
            else:
                # DATA continuation byte: upper 6 bits of tone period
                data6 = b & 0x3F
                ch = psg_latch_ch
                if 0 <= ch <= 2 and psg_latch_type == 0:
                    ps = psg_state[ch]
                    ps.period_hi = data6
                    # Period high changed — if sounding, re-evaluate pitch
                    if ps.active_note >= 0:
                        new_note = _psg_period_to_midi(ps.period)
                        if new_note != ps.active_note:
                            _psg_close(ch, current_sample)
                            if new_note >= 0 and ps.volume < _PSG_VOL_SILENT:
                                vel = _psg_vol_to_velocity(ps.volume)
                                _psg_open(ch, new_note, vel)
            continue

        if ev.kind not in ("ym2612_p0", "ym2612_p1"):
            continue

        port      = 0 if ev.kind == "ym2612_p0" else 1
        ch_offset = port * 3   # port0 → ch 0–2, port1 → ch 3–5
        r, v      = ev.reg, ev.val

        # ---- KEY_ON (port 0 only per VGM spec) ----------------------------
        if r == REG_KEY_ON and port == 0:
            ch_raw = v & 0x07
            # Map 0,1,2,4,5,6 → logical 0–5  (3 is invalid)
            if ch_raw == 3:
                continue
            ch_idx = ch_raw if ch_raw < 3 else (ch_raw - 1)
            if ch_idx >= 6:
                continue

            slots = (v >> 4) & 0x0F

            if slots:
                # Note-on: implicitly close any currently sounding note
                _close_channel(ch_idx, current_sample)
                note = _fnum_to_midi(fm_state[ch_idx].fnum, fm_state[ch_idx].block)
                fm_state[ch_idx].active_note = note
                fm_state[ch_idx].on_sample   = current_sample
                keyon_events += 1
            else:
                # Note-off
                if fm_state[ch_idx].on_sample >= 0:
                    _close_channel(ch_idx, current_sample)
                    keyoff_events += 1

        # ---- F-number low (A0–A2 per port) --------------------------------
        elif 0xA0 <= r <= 0xA2:
            ch_idx = ch_offset + (r - 0xA0)
            if ch_idx < 6:
                fm_state[ch_idx].fnum = (fm_state[ch_idx].fnum & ~0xFF) | v

        # ---- F-number high + block (A4–A6 per port) -----------------------
        elif 0xA4 <= r <= 0xA6:
            ch_idx = ch_offset + (r - 0xA4)
            if ch_idx < 6:
                fm_state[ch_idx].fnum  = (fm_state[ch_idx].fnum & 0xFF) | ((v & 0x07) << 8)
                fm_state[ch_idx].block = (v >> 3) & 0x07

        # ---- Total Level op1 carrier (0x40–0x42 / 0x44–0x46 per port) ----
        # Layout: op1=0x40+ch, op3=0x44+ch, op2=0x48+ch, op4=0x4C+ch
        # We capture op1 (index 0) and op4 (index 3) as carrier proxies.
        elif 0x40 <= r <= 0x4F:
            ch_idx  = ch_offset + (r & 0x03)
            op_slot = (r >> 2) & 0x03
            if ch_idx < 6 and op_slot == 0:
                fm_state[ch_idx].tl_op1 = v & 0x7F

    # ---- Close notes still open at end of track --------------------------
    end_sample = h.total_samples if h.total_samples > 0 else current_sample
    for ch_idx in range(6):
        if fm_state[ch_idx].on_sample >= 0:
            _close_channel(ch_idx, end_sample)
            orphan_keyons += 1
    for psg_ch in range(3):
        if psg_state[psg_ch].on_sample >= 0:
            _psg_close(psg_ch, end_sample)
            orphan_keyons += 1

    # ---- Sort by start time, then channel --------------------------------
    completed_notes.sort(key=lambda n: (n.start, n.channel))
    score.notes = completed_notes

    score.reconstruction_stats = {
        "notes_reconstructed": len(completed_notes),
        "keyon_events":        keyon_events,
        "keyoff_events":       keyoff_events,
        "orphan_keyons":       orphan_keyons,
        "psg_note_events":     psg_note_events,
        "unique_pitches":      len(score.unique_pitches),
        "pitch_range":         score.pitch_range,
        "avg_duration_sec":    round(score.avg_duration(), 4),
    }

    return score
