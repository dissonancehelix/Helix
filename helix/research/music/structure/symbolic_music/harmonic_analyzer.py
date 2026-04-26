"""
harmonic_analyzer.py — Harmonic structure analysis from SymbolicScore
======================================================================
Layer 2 primary interpretation: simultaneity detection, chord family
classification, progression analysis, bassline movement, tonal density.

API
---
analyze(score: SymbolicScore) -> HarmonicFeatures
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence

from domains.music.domain_analysis.symbolic_music.score_representation import (
    NoteEvent,
    SymbolicScore,
)


# ---------------------------------------------------------------------------
# Chord templates (pitch-class sets, root-relative)
# ---------------------------------------------------------------------------

_CHORD_TEMPLATES: list[tuple[str, frozenset[int]]] = [
    # Triads
    ("major",       frozenset({0, 4, 7})),
    ("minor",       frozenset({0, 3, 7})),
    ("diminished",  frozenset({0, 3, 6})),
    ("augmented",   frozenset({0, 4, 8})),
    # Seventh chords
    ("dom7",        frozenset({0, 4, 7, 10})),
    ("maj7",        frozenset({0, 4, 7, 11})),
    ("min7",        frozenset({0, 3, 7, 10})),
    ("dim7",        frozenset({0, 3, 6, 9})),
]

# Chord family groupings for fingerprint
_FAMILY_NAMES = [t[0] for t in _CHORD_TEMPLATES] + ["power", "sus", "other"]

# Window size for simultaneity detection (seconds)
_WINDOW_SEC = 0.1

# Bassline smoothing: take lowest note in each _BASS_WINDOW_SEC window
_BASS_WINDOW_SEC = 0.5


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class HarmonicFeatures:
    """Harmonic analysis results."""

    # Chord family distribution (11 bins, normalized)
    chord_family_dist:     list[float]  = field(default_factory=lambda: [0.0] * 11)
    chord_family_names:    list[str]    = field(default_factory=lambda: list(_FAMILY_NAMES))

    # Progression analysis
    chord_progression_entropy: float   = 0.0   # entropy over chord bigrams
    chord_change_rate:     float        = 0.0   # chord changes per second
    dominant_chord_family: str          = "other"

    # Tonal density
    simultaneity_ratio:    float        = 0.0   # fraction of time with >1 note
    max_polyphony:         int          = 0     # max simultaneous notes seen
    mean_polyphony:        float        = 0.0

    # Bassline movement
    bassline_step_ratio:   float        = 0.0   # fraction of bass moves ≤ M2
    bassline_leap_ratio:   float        = 0.0   # fraction of bass moves ≥ P4
    bassline_entropy:      float        = 0.0
    bassline_center:       float        = 0.0   # mean bass MIDI pitch

    # Pitch class usage
    pitch_class_entropy:   float        = 0.0   # 12-tone evenness
    chromatic_density:     float        = 0.0   # distinct pitch classes / 12

    # Counts
    chord_sample_count:    int          = 0

    def to_dict(self) -> dict:
        return {
            "chord_family_dist":        [round(x, 4) for x in self.chord_family_dist],
            "chord_family_names":       self.chord_family_names,
            "chord_progression_entropy": round(self.chord_progression_entropy, 3),
            "chord_change_rate":        round(self.chord_change_rate, 3),
            "dominant_chord_family":    self.dominant_chord_family,
            "simultaneity_ratio":       round(self.simultaneity_ratio, 3),
            "max_polyphony":            self.max_polyphony,
            "mean_polyphony":           round(self.mean_polyphony, 3),
            "bassline_step_ratio":      round(self.bassline_step_ratio, 3),
            "bassline_leap_ratio":      round(self.bassline_leap_ratio, 3),
            "bassline_entropy":         round(self.bassline_entropy, 3),
            "bassline_center":          round(self.bassline_center, 2),
            "pitch_class_entropy":      round(self.pitch_class_entropy, 3),
            "chromatic_density":        round(self.chromatic_density, 3),
            "chord_sample_count":       self.chord_sample_count,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total)
        for c in counter.values() if c > 0
    )


def _classify_chord(pitch_classes: frozenset[int]) -> str:
    """
    Match a set of pitch classes (root-normalized) to the closest chord template.
    Tries all 12 transpositions of each template against the observed PC set.
    """
    if len(pitch_classes) < 2:
        return "other"

    # Power chord heuristic: only two distinct PCs, separated by P5 (7) or P4 (5)
    if len(pitch_classes) == 2:
        diff = abs(list(pitch_classes)[0] - list(pitch_classes)[1])
        diff = min(diff, 12 - diff)
        if diff in (5, 7):
            return "power"

    best_name = "other"
    best_overlap = 0

    for name, template in _CHORD_TEMPLATES:
        for root in range(12):
            # Shift template by root
            shifted = frozenset((r + root) % 12 for r in template)
            overlap = len(pitch_classes & shifted)
            # Score: penalize missing notes in template
            score = overlap - 0.3 * len(template - shifted)
            if score > best_overlap and overlap >= min(2, len(template)):
                best_overlap = score
                best_name = name

    return best_name


def _sample_simultaneities(
    notes: list[NoteEvent],
    duration_sec: float,
    window_sec: float = _WINDOW_SEC,
) -> list[frozenset[int]]:
    """
    Slide a window over the track and collect pitch-class sets active at
    each window position.  Returns one set per window step.
    """
    if not notes or duration_sec <= 0:
        return []

    simultaneities: list[frozenset[int]] = []
    t = 0.0
    while t < duration_sec:
        active = frozenset(
            n.note % 12
            for n in notes
            if n.note >= 0 and n.start <= t < (n.start + max(n.duration, 0.001))
        )
        simultaneities.append(active)
        t += window_sec

    return simultaneities


def _extract_bassline(
    notes: list[NoteEvent],
    duration_sec: float,
    window_sec: float = _BASS_WINDOW_SEC,
) -> list[int]:
    """Return lowest MIDI pitch in each time window."""
    bass: list[int] = []
    t = 0.0
    while t < duration_sec:
        t_end = t + window_sec
        active = [
            n.note for n in notes
            if n.note >= 0 and n.start < t_end and (n.start + max(n.duration, 0.001)) > t
        ]
        if active:
            bass.append(min(active))
        t += window_sec
    return bass


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

def analyze(score: SymbolicScore) -> HarmonicFeatures:
    feat = HarmonicFeatures()

    notes = [n for n in score.notes if n.note >= 0]
    if not notes or score.duration_sec <= 0:
        return feat

    # ------------------------------------------------------------------
    # Pitch class entropy
    # ------------------------------------------------------------------
    pc_counter = Counter(n.note % 12 for n in notes)
    feat.pitch_class_entropy = _entropy(pc_counter)
    feat.chromatic_density   = len(pc_counter) / 12.0

    # ------------------------------------------------------------------
    # Simultaneity detection via sliding window
    # ------------------------------------------------------------------
    sim_sets = _sample_simultaneities(notes, score.duration_sec)
    if not sim_sets:
        return feat

    polyphony_counts = [len(s) for s in sim_sets]
    feat.max_polyphony     = max(polyphony_counts)
    feat.mean_polyphony    = sum(polyphony_counts) / len(polyphony_counts)
    feat.simultaneity_ratio = sum(1 for p in polyphony_counts if p > 1) / len(polyphony_counts)

    # ------------------------------------------------------------------
    # Chord classification
    # ------------------------------------------------------------------
    chords = [_classify_chord(s) for s in sim_sets if len(s) >= 2]
    feat.chord_sample_count = len(chords)

    if chords:
        chord_counter = Counter(chords)
        total = len(chords)
        feat.chord_family_dist = [
            chord_counter.get(name, 0) / total for name in _FAMILY_NAMES
        ]
        feat.dominant_chord_family = chord_counter.most_common(1)[0][0]

        # Chord progression bigrams → entropy
        bigrams = Counter(
            (chords[i], chords[i + 1])
            for i in range(len(chords) - 1)
            if chords[i] != chords[i + 1]
        )
        feat.chord_progression_entropy = _entropy(bigrams)

        # Chord change rate: transitions per second
        transitions = sum(
            1 for i in range(len(chords) - 1) if chords[i] != chords[i + 1]
        )
        feat.chord_change_rate = transitions / max(score.duration_sec, 0.001)

    # ------------------------------------------------------------------
    # Bassline analysis
    # ------------------------------------------------------------------
    bass_notes = _extract_bassline(notes, score.duration_sec)
    if len(bass_notes) >= 2:
        feat.bassline_center = sum(bass_notes) / len(bass_notes)
        bass_intervals = [abs(bass_notes[i + 1] - bass_notes[i])
                          for i in range(len(bass_notes) - 1)]
        feat.bassline_step_ratio = sum(1 for b in bass_intervals if b <= 2) / len(bass_intervals)
        feat.bassline_leap_ratio = sum(1 for b in bass_intervals if b >= 5) / len(bass_intervals)
        feat.bassline_entropy    = _entropy(Counter(bass_intervals))

    return feat
