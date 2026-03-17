"""
adapter_music21.py — Helix adapter for music21 (symbolic score analysis)
==========================================================================
Wraps music21 for symbolic music analysis from MIDI or MusicXML.

Purpose:
    Parse symbolic music representations and extract music-theoretic
    features including key, chord progressions, melodic intervals,
    phrase structure, and rhythm statistics.

Input:
    file_path (str | Path)  — MIDI (.mid/.midi) or MusicXML (.xml/.mxl) file

Output (dict — SymbolicScore schema):
    {
        "notes":                list[dict],  # {pitch, octave, duration, offset}
        "duration_total":       float,       # in quarter notes
        "tempo_map":            list[dict],  # [{offset, bpm}]
        "key_estimates":        list[dict],  # [{key, mode, confidence}]
        "chord_progression":    list[str],   # Roman numeral chords (sampled)
        "phrase_segmentation":  list[dict],  # [{start, end, length}]
        "interval_histogram":   dict,        # semitone count → frequency
        "melodic_contour":      list[int],   # +1 (up), -1 (down), 0 (repeat)
        "time_signatures":      list[str],
        "source_path":          str,
        "adapter":              "music21",
        "available":            bool,
    }

Adapter rules:
    • Returns available=False dict if music21 not installed.
    • No Helix logic.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


class Music21Adapter:
    """
    Adapter wrapping music21 for symbolic score analysis.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Music21Adapter → music21
    """

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
        ".mid", ".midi", ".xml", ".mxl", ".musicxml",
    })

    def analyze(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse and analyze a symbolic music file.

        Returns available=False if music21 is not installed.
        """
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise AdapterError(
                f"Unsupported format {path.suffix!r}. "
                f"Music21Adapter handles: {sorted(self.SUPPORTED_EXTENSIONS)}"
            )

        try:
            import music21 as m21
        except ImportError:
            return self._empty_profile(str(path))

        try:
            score = m21.converter.parse(str(path))
        except Exception as exc:
            raise AdapterError(f"music21 parse failed for {path}: {exc}") from exc

        # Notes
        notes: list[dict] = []
        pitches_seq: list[int] = []
        for el in score.flat.notes:
            if hasattr(el, "pitch"):
                midi_pitch = el.pitch.midi
                pitches_seq.append(midi_pitch)
                notes.append({
                    "pitch":    el.pitch.name,
                    "midi":     midi_pitch,
                    "octave":   el.pitch.octave,
                    "duration": float(el.duration.quarterLength),
                    "offset":   float(el.offset),
                })
            elif hasattr(el, "pitches"):
                for p in el.pitches:
                    pitches_seq.append(p.midi)
                    notes.append({
                        "pitch":    p.name,
                        "midi":     p.midi,
                        "octave":   p.octave,
                        "duration": float(el.duration.quarterLength),
                        "offset":   float(el.offset),
                    })

        # Duration total
        try:
            duration_total = float(score.duration.quarterLength)
        except Exception:
            duration_total = 0.0

        # Tempo map
        tempo_map: list[dict] = []
        for el in score.flat.getElementsByClass(m21.tempo.MetronomeMark):
            try:
                tempo_map.append({
                    "offset": float(el.offset),
                    "bpm":    float(el.number) if el.number else None,
                })
            except Exception:
                pass

        # Key estimates
        key_estimates: list[dict] = []
        try:
            key = score.analyze("key")
            key_estimates.append({
                "key":        str(key.tonic),
                "mode":       str(key.mode),
                "confidence": float(key.correlationCoefficient) if hasattr(key, "correlationCoefficient") else None,
            })
        except Exception:
            pass

        # Chord progression (sampled, first 32 chords)
        chord_progression: list[str] = []
        try:
            chords = score.chordify()
            count  = 0
            for c in chords.flat.getElementsByClass(m21.chord.Chord):
                if count >= 32:
                    break
                try:
                    rn = m21.roman.romanNumeralFromChord(c, m21.key.Key("C"))
                    chord_progression.append(str(rn.figure))
                    count += 1
                except Exception:
                    pass
        except Exception:
            pass

        # Interval histogram
        interval_histogram: dict[str, int] = {}
        melodic_contour:    list[int]      = []
        for i in range(1, len(pitches_seq)):
            interval = pitches_seq[i] - pitches_seq[i - 1]
            key_s    = str(interval)
            interval_histogram[key_s] = interval_histogram.get(key_s, 0) + 1
            melodic_contour.append(1 if interval > 0 else (-1 if interval < 0 else 0))

        # Time signatures
        time_sigs: list[str] = []
        for ts in score.flat.getElementsByClass(m21.meter.TimeSignature):
            ts_str = str(ts)
            if ts_str not in time_sigs:
                time_sigs.append(ts_str)

        # Basic phrase segmentation (by measure boundaries, up to 32)
        phrase_seg: list[dict] = []
        try:
            measures = list(score.flat.getElementsByClass(m21.stream.Measure))[:32]
            for m in measures:
                phrase_seg.append({
                    "start":  float(m.offset),
                    "end":    float(m.offset + m.duration.quarterLength),
                    "length": float(m.duration.quarterLength),
                })
        except Exception:
            pass

        return {
            "notes":               notes[:500],  # cap for serialization
            "duration_total":      duration_total,
            "tempo_map":           tempo_map,
            "key_estimates":       key_estimates,
            "chord_progression":   chord_progression,
            "phrase_segmentation": phrase_seg,
            "interval_histogram":  interval_histogram,
            "melodic_contour":     melodic_contour[:500],
            "time_signatures":     time_sigs,
            "source_path":         str(path),
            "adapter":             "music21",
            "available":           True,
        }

    def is_available(self) -> bool:
        try:
            import music21  # noqa
            return True
        except ImportError:
            return False

    def _empty_profile(self, source_path: str) -> dict[str, Any]:
        return {
            "notes":               [],
            "duration_total":      0.0,
            "tempo_map":           [],
            "key_estimates":       [],
            "chord_progression":   [],
            "phrase_segmentation": [],
            "interval_histogram":  {},
            "melodic_contour":     [],
            "time_signatures":     [],
            "source_path":         source_path,
            "adapter":             "music21",
            "available":           False,
        }
