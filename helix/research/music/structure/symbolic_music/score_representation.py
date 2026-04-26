"""
Symbolic Score Representation — Helix Music Lab
================================================
Dataclasses for representing VGM-derived note events in a symbolic,
MIDI-compatible format.

A NoteEvent represents a single note: which chip channel it came from,
its MIDI note number, when it starts (in seconds from track start), how
long it lasts, and an optional velocity.

A SymbolicScore collects all NoteEvents for a single track and provides
convenience accessors and serialization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# NoteEvent
# ---------------------------------------------------------------------------

@dataclass
class NoteEvent:
    """Single note reconstructed from chip register activity.

    Fields:
        channel   - logical chip channel (0–5 for YM2612 FM, 6–8 for PSG tone,
                    9 for PSG noise)
        note      - MIDI note number (0–127); -1 if pitch is indeterminate
        start     - onset time in seconds from track start
        duration  - note duration in seconds (0.0 if key-off not detected)
        velocity  - MIDI velocity approximated from Total Level (0–127);
                    defaults to 100
        chip      - source chip: "ym2612", "sn76489", or "psg" (legacy alias)
    """
    channel:   int
    note:      int
    start:     float
    duration:  float
    velocity:  int   = 100
    chip:      str   = "ym2612"

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel":  self.channel,
            "note":     self.note,
            "start":    round(self.start, 4),
            "duration": round(self.duration, 4),
            "velocity": self.velocity,
            "chip":     self.chip,
        }


# ---------------------------------------------------------------------------
# SymbolicScore
# ---------------------------------------------------------------------------

@dataclass
class SymbolicScore:
    """Container for all NoteEvents reconstructed from a VGM track.

    Attributes:
        track_name      - stem of the source VGZ/VGM filename
        duration_sec    - total track duration in seconds
        sample_rate     - samples per second used during reconstruction (44100)
        notes           - list of NoteEvent objects, ordered by start time
        reconstruction_stats - metadata about the reconstruction pass
    """
    track_name:           str
    duration_sec:         float
    sample_rate:          int                  = 44100
    notes:                list[NoteEvent]      = field(default_factory=list)
    reconstruction_stats: dict[str, Any]       = field(default_factory=dict)
    metadata:             dict[str, Any]       = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def note_count(self) -> int:
        return len(self.notes)

    @property
    def unique_pitches(self) -> set[int]:
        return {n.note for n in self.notes if n.note >= 0}

    @property
    def pitch_range(self) -> int:
        valid = [n.note for n in self.notes if n.note >= 0]
        return (max(valid) - min(valid)) if len(valid) > 1 else 0

    def notes_for_channel(self, channel: int) -> list[NoteEvent]:
        return [n for n in self.notes if n.channel == channel]

    def avg_duration(self) -> float:
        ds = [n.duration for n in self.notes if n.duration > 0]
        return sum(ds) / len(ds) if ds else 0.0

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_name":           self.track_name,
            "duration_sec":         round(self.duration_sec, 3),
            "sample_rate":          self.sample_rate,
            "note_count":           self.note_count,
            "unique_pitches":       len(self.unique_pitches),
            "pitch_range":          self.pitch_range,
            "avg_note_duration":    round(self.avg_duration(), 4),
            "reconstruction_stats": self.reconstruction_stats,
            "metadata":             self.metadata,
            "notes":                [n.to_dict() for n in self.notes],
        }

    def save(self, path: Path) -> None:
        """Write JSON representation to *path*."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    def to_midi(self, path: Path) -> None:
        """Export the symbolic score to a standard MIDI file."""
        try:
            import pretty_midi
            midi = pretty_midi.PrettyMIDI()
            
            # Map chip channels to MIDI instruments (Simplified)
            # 0-5 (FM) -> 1 (Piano/Synth), 6-8 (PSG) -> 81 (Lead), 9 (PSG Noise) -> 119 (Synth Drum)
            instruments = {}
            
            for n in self.notes:
                if n.channel not in instruments:
                    # Basic mapping logic: 
                    # FM 0-5 -> Piano/E-Piano, PSG 6-8 -> Square Wave
                    program = 0 # Default Piano
                    is_drum = False
                    if n.chip in ("psg", "sn76489"):
                        if n.channel == 9: # Noise
                            is_drum = True
                            program = 118 # Synth Drum
                        else:
                            program = 80 # Lead 1 (Square)
                    else:
                        program = 4 # Electric Piano / 0 Piano
                    
                    inst = pretty_midi.Instrument(program=program, is_drum=is_drum, name=f"Ch {n.channel} ({n.chip})")
                    instruments[n.channel] = inst
                    midi.instruments.append(inst)
                
                # Create the note
                # MIDI note -1 means indeterminate, skip or map to default
                note_num = n.note if n.note >= 0 else 60
                duration = n.duration if n.duration > 0 else 0.1
                
                midi_note = pretty_midi.Note(
                    velocity=n.velocity,
                    pitch=note_num,
                    start=n.start,
                    end=n.start + duration
                )
                instruments[n.channel].notes.append(midi_note)
            
            path.parent.mkdir(parents=True, exist_ok=True)
            midi.write(str(path))
            print(f"      MIDI exported: {path.name}")
        except Exception as e:
            print(f"      MIDI export failed for {self.track_name}: {e}")

    @classmethod
    def load(cls, path: Path) -> "SymbolicScore":
        """Load a previously saved SymbolicScore JSON."""
        data = json.loads(path.read_text())
        notes = [
            NoteEvent(
                channel=n["channel"],
                note=n["note"],
                start=n["start"],
                duration=n["duration"],
                velocity=n.get("velocity", 100),
                chip=n.get("chip", "ym2612"),
            )
            for n in data.get("notes", [])
        ]
        score = cls(
            track_name=data["track_name"],
            duration_sec=data["duration_sec"],
            sample_rate=data.get("sample_rate", 44100),
            notes=notes,
            reconstruction_stats=data.get("reconstruction_stats", {}),
            metadata=data.get("metadata", {}),
        )
        return score
