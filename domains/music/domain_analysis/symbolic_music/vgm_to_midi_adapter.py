"""
VGM → MIDI Adapter — Helix Music Lab
======================================
Converts a SymbolicScore into a Standard MIDI File (.mid).

Uses zero external dependencies — MIDI bytes are built directly using
Python's struct module, following the SMF specification:
  - Format 0 (single multi-channel track)
  - Ticks per quarter note: 480
  - Default tempo: 120 BPM (500 000 μs/beat)
  - YM2612 channels 0–5 → MIDI channels 1–6
  - Notes with note=-1 (indeterminate pitch) are skipped

Usage:
    from domains.music.analysis.symbolic_music.vgm_to_midi_adapter import to_midi

    midi_bytes = to_midi(score)
    Path("output.mid").write_bytes(midi_bytes)

    # or, convenience wrapper:
    export_midi(score, Path("artifacts/symbolic_scores/track.mid"))
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Sequence

from domains.music.analysis.symbolic_music.score_representation import (
    NoteEvent,
    SymbolicScore,
)


# ---------------------------------------------------------------------------
# MIDI constants
# ---------------------------------------------------------------------------

TICKS_PER_BEAT = 480
DEFAULT_BPM    = 120
USEC_PER_BEAT  = 60_000_000 // DEFAULT_BPM   # 500 000

# Ticks per second at 120 BPM: 480 * 2 = 960
TICKS_PER_SEC  = TICKS_PER_BEAT * (1_000_000 / USEC_PER_BEAT)


def _sec_to_ticks(seconds: float) -> int:
    """Convert seconds to MIDI ticks at 120 BPM, 480 TPB."""
    return max(0, round(seconds * TICKS_PER_SEC))


# ---------------------------------------------------------------------------
# Variable-length quantity (VLQ) encoding
# ---------------------------------------------------------------------------

def _vlq(value: int) -> bytes:
    """Encode an integer as a MIDI variable-length quantity."""
    if value < 0:
        value = 0
    result = bytearray()
    result.append(value & 0x7F)
    value >>= 7
    while value:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.reverse()
    return bytes(result)


# ---------------------------------------------------------------------------
# MIDI event helpers
# ---------------------------------------------------------------------------

def _tempo_event() -> bytes:
    """Meta event: set tempo (500 000 μs/beat = 120 BPM)."""
    tempo_bytes = struct.pack(">I", USEC_PER_BEAT)[1:]  # 3 bytes big-endian
    return _vlq(0) + b"\xFF\x51\x03" + tempo_bytes


def _note_on(channel: int, note: int, velocity: int, delta_ticks: int) -> bytes:
    ch = (channel - 1) & 0x0F
    return _vlq(delta_ticks) + bytes([0x90 | ch, note & 0x7F, velocity & 0x7F])


def _note_off(channel: int, note: int, delta_ticks: int) -> bytes:
    ch = (channel - 1) & 0x0F
    return _vlq(delta_ticks) + bytes([0x80 | ch, note & 0x7F, 0x00])


def _end_of_track(delta_ticks: int = 0) -> bytes:
    return _vlq(delta_ticks) + b"\xFF\x2F\x00"


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def to_midi(score: SymbolicScore) -> bytes:
    """
    Convert *score* to a Standard MIDI File (Format 0) and return the raw bytes.

    Channel mapping:
        YM2612 ch 0–5  →  MIDI channel 1–6
        Unmapped/PSG   →  MIDI channel 10 (drums, omitted if note=-1)

    Notes with note < 0 are silently skipped.
    """
    if not score.notes:
        # Return a valid but empty MIDI file
        track_data = _tempo_event() + _end_of_track()
        return _make_midi_file(track_data)

    # Build list of (tick, event_bytes) pairs
    raw_events: list[tuple[int, bytes]] = []

    for note_ev in score.notes:
        if note_ev.note < 0:
            continue

        midi_ch  = (note_ev.channel % 6) + 1   # clamp to 1–6
        on_tick  = _sec_to_ticks(note_ev.start)
        dur_sec  = note_ev.duration if note_ev.duration > 0 else 0.05
        off_tick = _sec_to_ticks(note_ev.start + dur_sec)

        velocity = max(1, min(127, note_ev.velocity))

        raw_events.append((on_tick,  ("on",  midi_ch, note_ev.note, velocity)))
        raw_events.append((off_tick, ("off", midi_ch, note_ev.note, 0)))

    # Sort by tick; within same tick, note-offs before note-ons (avoids clicks)
    def _sort_key(item):
        tick, ev = item
        return (tick, 0 if ev[0] == "off" else 1)

    raw_events.sort(key=_sort_key)

    # Convert absolute ticks to delta ticks
    track_bytes = bytearray(_tempo_event())
    prev_tick = 0
    for tick, ev in raw_events:
        delta = tick - prev_tick
        prev_tick = tick
        kind, ch, note, vel = ev
        if kind == "on":
            track_bytes += _note_on(ch, note, vel, delta)
        else:
            track_bytes += _note_off(ch, note, delta)

    track_bytes += _end_of_track(0)
    return _make_midi_file(bytes(track_bytes))


def _make_midi_file(track_data: bytes) -> bytes:
    """Wrap track_data in MIDI header + track chunk."""
    # Header chunk: MThd + length(6) + format(0) + ntracks(1) + division
    header = struct.pack(
        ">4sIHHH",
        b"MThd",
        6,
        0,           # format 0
        1,           # 1 track
        TICKS_PER_BEAT,
    )
    # Track chunk: MTrk + length + data
    track_chunk = b"MTrk" + struct.pack(">I", len(track_data)) + track_data
    return header + track_chunk


# ---------------------------------------------------------------------------
# Convenience export
# ---------------------------------------------------------------------------

def export_midi(score: SymbolicScore, output_path: Path) -> Path:
    """
    Convert *score* to MIDI and write to *output_path*.

    Creates parent directories as needed.  Returns the resolved output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    midi_bytes = to_midi(score)
    output_path.write_bytes(midi_bytes)
    return output_path
