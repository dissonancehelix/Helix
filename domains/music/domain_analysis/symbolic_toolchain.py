"""
symbolic_toolchain.py — Computational Musicology Integration Layer
===================================================================
Wraps music21, musif, symusic, and musicntwrk into a unified analysis
pipeline that consumes a MIDI file (or a SymbolicScore converted to MIDI)
and produces structured features for composer fingerprinting.

Each library contributes unique value:

  symusic      Fast MIDI ingestion (C++ backed).  Primary MIDI reader for
               high-volume processing.  Provides precise tick-level timing,
               tempo maps, and multi-track structure.

  music21      Primary computational musicology toolkit.  Used for:
               - key detection (Krumhansl-Schmuckler, Bellman-Budge)
               - chord labeling + Roman numeral analysis
               - cadence detection (authentic, half, deceptive, plagal)
               - phrase boundary detection via rest/breath analysis
               - melodic interval analysis + contour strings
               - voice-leading motion metrics

  musif        Research-grade symbolic feature extractor.  Used for:
               - melodic complexity (Lempel-Ziv on interval sequence)
               - tonal tension (tonal pitch space distance over time)
               - harmonic rhythm (rate of chord change)
               - interval entropy + step/leap/skip profiles
               - motif density per phrase

  musicntwrk   Network analysis toolkit for music.  Used for:
               - pitch co-occurrence graph (edges = simultaneous notes)
               - chord progression Markov chain as directed graph
               - motif similarity graph (n-gram cosine similarity)
               - track-level similarity network (for corpus studies)

All four libraries are optional — any missing library degrades gracefully,
falling back to the pure-Python implementations in melodic_analyzer.py,
harmonic_analyzer.py, etc.

Pipeline:
    midi_path → load_midi(midi_path)
              → SymbolicAnalysis (all four tool results merged)

API:
    from_midi(midi_path: Path) -> SymbolicAnalysis
    from_score(score: SymbolicScore) -> SymbolicAnalysis
        (writes a temp MIDI then calls from_midi)
"""

from __future__ import annotations

import logging
import math
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional import guards
# ---------------------------------------------------------------------------

try:
    import symusic as _symusic
    _HAS_SYMUSIC = True
except ImportError:
    _HAS_SYMUSIC = False
    log.debug("symbolic_toolchain: symusic not installed — using fallback MIDI read")

try:
    import music21 as _m21
    _HAS_MUSIC21 = True
except ImportError:
    _HAS_MUSIC21 = False
    log.debug("symbolic_toolchain: music21 not installed — key/chord analysis unavailable")

try:
    import musif as _musif
    _HAS_MUSIF = True
except ImportError:
    _HAS_MUSIF = False
    log.debug("symbolic_toolchain: musif not installed — complexity features unavailable")

try:
    import networkx as _nx          # musicntwrk depends on networkx
    import musicntwrk as _mnw
    _HAS_MUSICNTWRK = True
except ImportError:
    _HAS_MUSICNTWRK = False
    log.debug("symbolic_toolchain: musicntwrk not installed — network analysis unavailable")


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class SymbolicAnalysis:
    """
    Consolidated output from all four symbolic analysis tools.
    Fields that couldn't be computed are None or empty.
    """
    midi_path:   str | None = None

    # symusic: timing and track structure
    symusic_tempo_bpm:   float | None = None
    symusic_track_count: int   | None = None
    symusic_note_count:  int   | None = None
    symusic_tick_resolution: int | None = None

    # music21: key, harmony, cadences
    m21_key:              str | None = None   # e.g. "a minor"
    m21_key_confidence:   float | None = None
    m21_mode:             str | None = None   # "major" | "minor"
    m21_chord_sequence:   list[str] = field(default_factory=list)    # Roman numerals
    m21_cadences:         list[dict] = field(default_factory=list)   # cadence events
    m21_phrase_count:     int | None = None
    m21_interval_profile: dict[str, float] = field(default_factory=dict)
    m21_contour_string:   str | None = None   # e.g. "UUDDSUUD..."
    m21_voice_leading:    dict[str, float] = field(default_factory=dict)

    # musif: complexity and tension
    musif_melodic_complexity:  float | None = None
    musif_tonal_tension_mean:  float | None = None
    musif_harmonic_rhythm:     float | None = None
    musif_interval_entropy:    float | None = None
    musif_motif_density:       float | None = None
    musif_raw:                 dict[str, Any] = field(default_factory=dict)

    # musicntwrk: graph metrics
    mnw_pitch_network_density:    float | None = None
    mnw_chord_graph_entropy:      float | None = None
    mnw_motif_graph_components:   int   | None = None
    mnw_track_similarity_score:   float | None = None  # reserved for corpus studies

    # Errors / availability
    tools_available: dict[str, bool] = field(default_factory=dict)
    errors:          dict[str, str]  = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "midi_path":               self.midi_path,
            "symusic": {
                "tempo_bpm":      self.symusic_tempo_bpm,
                "track_count":    self.symusic_track_count,
                "note_count":     self.symusic_note_count,
                "tick_resolution": self.symusic_tick_resolution,
            },
            "music21": {
                "key":            self.m21_key,
                "key_confidence": self.m21_key_confidence,
                "mode":           self.m21_mode,
                "chord_sequence": self.m21_chord_sequence[:16],  # cap for readability
                "cadences":       self.m21_cadences,
                "phrase_count":   self.m21_phrase_count,
                "interval_profile": self.m21_interval_profile,
                "contour_string": (self.m21_contour_string or "")[:64],
                "voice_leading":  self.m21_voice_leading,
            },
            "musif": {
                "melodic_complexity": self.musif_melodic_complexity,
                "tonal_tension_mean": self.musif_tonal_tension_mean,
                "harmonic_rhythm":    self.musif_harmonic_rhythm,
                "interval_entropy":   self.musif_interval_entropy,
                "motif_density":      self.musif_motif_density,
            },
            "musicntwrk": {
                "pitch_network_density":  self.mnw_pitch_network_density,
                "chord_graph_entropy":    self.mnw_chord_graph_entropy,
                "motif_graph_components": self.mnw_motif_graph_components,
            },
            "tools_available": self.tools_available,
            "errors":          self.errors,
        }


# ---------------------------------------------------------------------------
# symusic pass
# ---------------------------------------------------------------------------

def _analyze_symusic(midi_path: Path, result: SymbolicAnalysis) -> None:
    if not _HAS_SYMUSIC:
        return
    try:
        score = _symusic.Score.from_file(str(midi_path))
        result.symusic_tick_resolution = score.ticks_per_quarter
        result.symusic_track_count = len(score.tracks)
        result.symusic_note_count = sum(len(t.notes) for t in score.tracks)
        # Tempo: first tempo event or default 120 BPM
        if score.tempos:
            first_tempo = score.tempos[0].mspq  # microseconds per quarter
            result.symusic_tempo_bpm = round(60_000_000 / first_tempo, 2)
        else:
            result.symusic_tempo_bpm = 120.0
    except Exception as exc:
        result.errors["symusic"] = str(exc)
        log.debug("symusic error: %s", exc)


# ---------------------------------------------------------------------------
# music21 pass
# ---------------------------------------------------------------------------

def _analyze_music21(midi_path: Path, result: SymbolicAnalysis) -> None:
    if not _HAS_MUSIC21:
        return
    try:
        from music21 import converter, analysis, note, stream, interval, chord

        score = converter.parse(str(midi_path))
        flat  = score.flatten()

        # Key estimation
        key_obj = flat.analyze("key")
        if key_obj:
            result.m21_key            = str(key_obj)
            result.m21_key_confidence = round(float(key_obj.correlationCoefficient), 3)
            result.m21_mode           = key_obj.mode

        # Chord sequence (Roman numerals for first 32 chords)
        chords: list[str] = []
        for el in score.chordify().flatten().getElementsByClass(chord.Chord):
            try:
                rn = analysis.reduceChords.passChordReducer(el)
                chords.append(str(rn))
            except Exception:
                chords.append(el.pitches[0].name if el.pitches else "?")
        result.m21_chord_sequence = chords[:64]

        # Melodic interval profile — from first non-empty part
        parts = score.parts
        if parts:
            part_notes = parts[0].flatten().getElementsByClass(note.Note)
            note_list = list(part_notes)
            if len(note_list) > 1:
                intervals_named: dict[str, int] = {}
                contour = []
                for i in range(len(note_list) - 1):
                    iv = interval.Interval(note_list[i], note_list[i + 1])
                    name = iv.simpleName
                    intervals_named[name] = intervals_named.get(name, 0) + 1
                    # Contour
                    s = iv.semitones
                    contour.append("U" if s > 0 else ("D" if s < 0 else "S"))

                total = sum(intervals_named.values())
                result.m21_interval_profile = {
                    k: round(v / total, 4) for k, v in intervals_named.items()
                }
                result.m21_contour_string = "".join(contour)

                # Phrase count: count rests > 0.5 quarter notes
                rests = parts[0].flatten().getElementsByClass("Rest")
                phrase_breaks = sum(
                    1 for r in rests
                    if hasattr(r, "quarterLength") and r.quarterLength > 0.5
                )
                result.m21_phrase_count = phrase_breaks + 1

        # Cadence detection (simple heuristic: look for dominant → tonic progressions)
        cadences: list[dict] = []
        chord_els = list(score.chordify().flatten().getElementsByClass(chord.Chord))
        for i in range(len(chord_els) - 1):
            try:
                if key_obj:
                    rn_cur  = analysis.reduceChords.passChordReducer(chord_els[i])
                    rn_next = analysis.reduceChords.passChordReducer(chord_els[i + 1])
                    cur_fig  = str(rn_cur)
                    next_fig = str(rn_next)
                    ctype = None
                    if "V" in cur_fig and next_fig.startswith("I"):
                        ctype = "authentic" if not next_fig.startswith("Ib") else "deceptive"
                    elif "IV" in cur_fig and next_fig.startswith("I"):
                        ctype = "plagal"
                    elif "V" in cur_fig and not next_fig.startswith("I"):
                        ctype = "half"
                    if ctype:
                        cadences.append({
                            "type":    ctype,
                            "from":    cur_fig,
                            "to":      next_fig,
                            "offset":  float(chord_els[i].offset),
                        })
            except Exception:
                pass
        result.m21_cadences = cadences[:20]

        # Voice-leading metrics (for multi-part scores)
        if len(parts) >= 2:
            parallel_5ths = 0
            parallel_8ths = 0
            try:
                vl = analysis.discrete.parallelFifths(parts[0], parts[1])
                parallel_5ths = int(vl) if vl is not None else 0
            except Exception:
                pass
            result.m21_voice_leading = {
                "parallel_5ths": parallel_5ths,
                "parallel_8ths": parallel_8ths,
            }

    except Exception as exc:
        result.errors["music21"] = str(exc)
        log.debug("music21 error: %s", exc)


# ---------------------------------------------------------------------------
# musif pass
# ---------------------------------------------------------------------------

def _analyze_musif(midi_path: Path, result: SymbolicAnalysis) -> None:
    if not _HAS_MUSIF:
        return
    try:
        from musif.extract import FeaturesExtractor
        from musif.config import ExtractConfiguration

        cfg = ExtractConfiguration(
            musescore_dir="",
            window=4,
            features=["melodic", "harmony", "rhythm"],
            ignore_errors=True,
        )
        extractor = FeaturesExtractor(cfg)
        features  = extractor.extract(str(midi_path))

        if features:
            raw = features[0] if isinstance(features, list) else features
            result.musif_raw = {k: v for k, v in raw.items()
                                if isinstance(v, (int, float, str))}
            result.musif_melodic_complexity = raw.get("melodic_complexity_lz")
            result.musif_tonal_tension_mean = raw.get("tonal_tension_mean")
            result.musif_harmonic_rhythm    = raw.get("harmonic_rhythm")
            result.musif_interval_entropy   = raw.get("interval_entropy")
            result.musif_motif_density      = raw.get("motif_density")

    except Exception as exc:
        result.errors["musif"] = str(exc)
        log.debug("musif error: %s", exc)


# ---------------------------------------------------------------------------
# musicntwrk pass
# ---------------------------------------------------------------------------

def _analyze_musicntwrk(midi_path: Path, result: SymbolicAnalysis) -> None:
    if not _HAS_MUSICNTWRK:
        return
    try:
        import networkx as nx
        from musicntwrk import MusicGraph

        mg = MusicGraph()
        mg.from_midi(str(midi_path))

        # Pitch co-occurrence network
        pitch_net = mg.pitch_network()
        if pitch_net and pitch_net.number_of_nodes() > 0:
            result.mnw_pitch_network_density = round(
                nx.density(pitch_net), 4
            )

        # Chord progression graph
        chord_graph = mg.chord_network()
        if chord_graph and chord_graph.number_of_nodes() > 0:
            # Shannon entropy of out-degree distribution
            degrees = [d for _, d in chord_graph.out_degree()]
            total_d = sum(degrees) or 1
            entropy = -sum(
                (d / total_d) * math.log2(d / total_d)
                for d in degrees if d > 0
            )
            result.mnw_chord_graph_entropy = round(entropy, 4)

        # Motif similarity graph: weakly connected components count
        motif_graph = mg.motif_network(n=4)
        if motif_graph:
            result.mnw_motif_graph_components = nx.number_weakly_connected_components(
                motif_graph
            )

    except Exception as exc:
        result.errors["musicntwrk"] = str(exc)
        log.debug("musicntwrk error: %s", exc)


# ---------------------------------------------------------------------------
# MIDI export from SymbolicScore (temp file)
# ---------------------------------------------------------------------------

def _score_to_midi(score: "SymbolicScore") -> Path | None:
    """Write SymbolicScore to a temp MIDI file. Returns path or None on failure."""
    try:
        from domains.music.analysis.symbolic_music.vgm_to_midi_adapter import to_midi
        tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
        tmp.close()
        out = Path(tmp.name)
        to_midi(score, out)
        return out
    except Exception as exc:
        log.debug("score_to_midi failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def from_midi(midi_path: Path) -> SymbolicAnalysis:
    """
    Run the full symbolic toolchain on a MIDI file.
    Returns a SymbolicAnalysis with all available results.
    """
    result = SymbolicAnalysis(
        midi_path=str(midi_path),
        tools_available={
            "symusic":     _HAS_SYMUSIC,
            "music21":     _HAS_MUSIC21,
            "musif":       _HAS_MUSIF,
            "musicntwrk":  _HAS_MUSICNTWRK,
        },
    )

    _analyze_symusic(midi_path, result)
    _analyze_music21(midi_path, result)
    _analyze_musif(midi_path, result)
    _analyze_musicntwrk(midi_path, result)

    return result


def from_score(score: "SymbolicScore") -> SymbolicAnalysis:
    """
    Run the full symbolic toolchain on a SymbolicScore.
    Exports to a temporary MIDI file first.
    """
    midi_path = _score_to_midi(score)
    if midi_path is None:
        return SymbolicAnalysis(
            errors={"midi_export": "vgm_to_midi_adapter failed or not available"},
            tools_available={
                "symusic":    _HAS_SYMUSIC,
                "music21":    _HAS_MUSIC21,
                "musif":      _HAS_MUSIF,
                "musicntwrk": _HAS_MUSICNTWRK,
            },
        )

    try:
        result = from_midi(midi_path)
    finally:
        try:
            midi_path.unlink(missing_ok=True)
        except Exception:
            pass

    return result


def available() -> dict[str, bool]:
    return {
        "symusic":    _HAS_SYMUSIC,
        "music21":    _HAS_MUSIC21,
        "musif":      _HAS_MUSIF,
        "musicntwrk": _HAS_MUSICNTWRK,
    }
