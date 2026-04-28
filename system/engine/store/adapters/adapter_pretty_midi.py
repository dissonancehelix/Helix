"""
adapter_pretty_midi.py — Helix adapter for pretty_midi (MIDI analysis)
=======================================================================
Wraps pretty_midi for efficient MIDI feature extraction.

Purpose:
    Parse MIDI files and extract note events, instrument programs,
    pitch statistics, rhythm density, and velocity distributions.
    Faster than music21 for large MIDI batches.

Input:
    file_path (str | Path)  — MIDI file (.mid or .midi)

Output (dict — SymbolicScore schema):
    {
        "notes":                list[dict],    # {pitch, velocity, start, end, instrument}
        "duration_total":       float,         # seconds
        "tempo_map":            list[dict],    # [{time, tempo_bpm}]
        "instruments":          list[dict],    # [{program, name, is_drum, note_count}]
        "pitch_histogram":      list[float],   # 128-bin pitch class distribution
        "velocity_histogram":   list[float],   # 128-bin velocity distribution
        "note_density":         float,         # notes per second
        "pitch_range":          dict,          # {min_midi, max_midi, span}
        "interval_histogram":   dict,          # semitone → frequency
        "melodic_contour":      list[int],
        "chord_progression":    list[str],     # simplified chord labels
        "phrase_segmentation":  list,
        "key_estimates":        list,
        "time_signatures":      list[str],
        "source_path":          str,
        "adapter":              "pretty_midi",
        "available":            bool,
    }

Adapter rules:
    • Returns available=False if pretty_midi not installed.
    • No Helix logic.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


class Adapter:
    """
    Adapter wrapping pretty_midi for efficient MIDI feature extraction.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → pretty_midi
    """
    toolkit = "pretty_midi"
    substrate = "music"

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".mid", ".midi"})

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a MIDI file and extract features.

        Returns available=False if pretty_midi is not installed.
        """
        file_path = payload.get("file_path")
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise AdapterError(
                f"Unsupported format {path.suffix!r}. "
                f"PrettyMidiAdapter handles: {sorted(self.SUPPORTED_EXTENSIONS)}"
            )

        try:
            import pretty_midi
            import numpy as np
        except ImportError:
            return self._empty_profile(str(path))

        try:
            midi = pretty_midi.PrettyMIDI(str(path))
        except Exception as exc:
            raise AdapterError(f"pretty_midi parse failed for {path}: {exc}") from exc

        duration_total = float(midi.get_end_time())

        # Tempo map
        tempo_change_times, tempos = midi.get_tempo_changes()
        tempo_map = [
            {"time": float(t), "tempo_bpm": float(bpm)}
            for t, bpm in zip(tempo_change_times, tempos)
        ]

        # Notes (capped at 2000 for serialization)
        all_notes: list[dict] = []
        instruments_info: list[dict] = []

        for inst in midi.instruments:
            inst_notes = sorted(inst.notes, key=lambda n: n.start)
            instruments_info.append({
                "program":    inst.program,
                "name":       pretty_midi.program_to_instrument_name(inst.program),
                "is_drum":    inst.is_drum,
                "note_count": len(inst_notes),
            })
            if not inst.is_drum:
                for n in inst_notes[:500]:
                    all_notes.append({
                        "pitch":      n.pitch,
                        "velocity":   n.velocity,
                        "start":      float(n.start),
                        "end":        float(n.end),
                        "instrument": inst.program,
                    })

        all_notes = sorted(all_notes, key=lambda n: n["start"])

        # Pitch histogram (128 bins)
        pitch_histogram = [0.0] * 128
        velocity_histogram = [0.0] * 128
        pitches_seq: list[int] = []
        for n in all_notes:
            p = n["pitch"]
            v = n["velocity"]
            if 0 <= p < 128:
                pitch_histogram[p] += 1.0
                pitches_seq.append(p)
            if 0 <= v < 128:
                velocity_histogram[v] += 1.0

        # Normalize
        ph_total = sum(pitch_histogram)
        vh_total = sum(velocity_histogram)
        if ph_total > 0:
            pitch_histogram = [x / ph_total for x in pitch_histogram]
        if vh_total > 0:
            velocity_histogram = [x / vh_total for x in velocity_histogram]

        # Note density
        note_density = len(all_notes) / duration_total if duration_total > 0 else 0.0

        # Pitch range
        if pitches_seq:
            pitch_range = {
                "min_midi": min(pitches_seq),
                "max_midi": max(pitches_seq),
                "span":     max(pitches_seq) - min(pitches_seq),
            }
        else:
            pitch_range = {"min_midi": 0, "max_midi": 0, "span": 0}

        # Interval histogram + melodic contour
        interval_histogram: dict[str, int] = {}
        melodic_contour: list[int] = []
        for i in range(1, len(pitches_seq)):
            interval = pitches_seq[i] - pitches_seq[i - 1]
            key_s = str(interval)
            interval_histogram[key_s] = interval_histogram.get(key_s, 0) + 1
            melodic_contour.append(1 if interval > 0 else (-1 if interval < 0 else 0))

        # Time signatures
        time_sigs: list[str] = []
        for ts in midi.time_signature_changes:
            ts_str = f"{ts.numerator}/{ts.denominator}"
            if ts_str not in time_sigs:
                time_sigs.append(ts_str)

        result = {
            "notes":               all_notes[:2000],
            "duration_total":      duration_total,
            "tempo_map":           tempo_map,
            "instruments":         instruments_info,
            "pitch_histogram":     pitch_histogram,
            "velocity_histogram":  velocity_histogram,
            "note_density":        note_density,
            "pitch_range":         pitch_range,
            "interval_histogram":  interval_histogram,
            "melodic_contour":     melodic_contour[:500],
            "chord_progression":   [],   # populated by ANALYZE_TRACK if needed
            "phrase_segmentation": [],   # populated by music21 if needed
            "key_estimates":       [],   # populated by music21 if needed
            "time_signatures":     time_sigs,
            "source_path":         str(path),
            "adapter":             "pretty_midi",
            "available":           True,
        }
        return self.normalize(result)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def is_available(self) -> bool:
        try:
            import pretty_midi  # noqa
            return True
        except ImportError:
            return False

    def _empty_profile(self, source_path: str) -> dict[str, Any]:
        return {
            "notes":               [],
            "duration_total":      0.0,
            "tempo_map":           [],
            "instruments":         [],
            "pitch_histogram":     [0.0] * 128,
            "velocity_histogram":  [0.0] * 128,
            "note_density":        0.0,
            "pitch_range":         {"min_midi": 0, "max_midi": 0, "span": 0},
            "interval_histogram":  {},
            "melodic_contour":     [],
            "chord_progression":   [],
            "phrase_segmentation": [],
            "key_estimates":       [],
            "time_signatures":     [],
            "source_path":         source_path,
            "adapter":             "pretty_midi",
            "available":           False,
        }
