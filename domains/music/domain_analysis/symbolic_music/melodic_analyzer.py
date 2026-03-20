"""
melodic_analyzer.py — Melodic structure analysis from SymbolicScore
====================================================================
Layer 2 primary interpretation: interval distributions, melodic contour,
phrase structure, hook density, repetition patterns.

API
---
analyze(score: SymbolicScore, lead_channel: int | None = None) -> MelodicFeatures
    Analyzes the full score or a single channel.
    If lead_channel is None, uses the channel with the widest pitch range.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence

from domains.music.analysis.symbolic_music.score_representation import (
    NoteEvent,
    SymbolicScore,
)


# ---------------------------------------------------------------------------
# Interval categories (semitone magnitude)
# ---------------------------------------------------------------------------

_INTERVAL_NAMES = [
    "unison",       # 0
    "minor_2nd",    # 1
    "major_2nd",    # 2
    "minor_3rd",    # 3
    "major_3rd",    # 4
    "perfect_4th",  # 5
    "tritone",      # 6
    "perfect_5th",  # 7
    "minor_6th",    # 8
    "major_6th",    # 9
    "minor_7th",    # 10
    "major_7th",    # 11
    "octave_plus",  # 12+
]

# Silence threshold: gaps longer than this (seconds) mark a phrase boundary
_PHRASE_BOUNDARY_SEC = 0.35

# Short motif window for hook detection
_MOTIF_N = 4   # 4-note n-grams


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class MelodicFeatures:
    """Melodic analysis results for a single track (or channel)."""

    # Which channel was analyzed (-1 = aggregate)
    analyzed_channel:      int          = -1

    # Interval distribution (13 bins, normalized 0–1)
    # bins: unison, m2, M2, m3, M3, P4, tri, P5, m6, M6, m7, M7, octave+
    interval_histogram:    list[float]  = field(default_factory=lambda: [0.0] * 13)

    # Summary stats
    mean_abs_interval:     float        = 0.0   # avg semitone jump
    stepwise_ratio:        float        = 0.0   # fraction of intervals ≤ M2
    leap_ratio:            float        = 0.0   # fraction ≥ P4
    interval_entropy:      float        = 0.0

    # Contour (direction sequence U/D/S)
    contour_up_ratio:      float        = 0.0
    contour_down_ratio:    float        = 0.0
    contour_same_ratio:    float        = 0.0
    contour_entropy:       float        = 0.0   # entropy over run lengths
    direction_run_mean:    float        = 0.0   # mean consecutive same-direction notes

    # Phrase structure
    phrase_count:          int          = 0
    phrase_len_mean:       float        = 0.0   # mean notes per phrase
    phrase_len_std:        float        = 0.0
    phrase_len_entropy:    float        = 0.0

    # Repetition / hooks
    motif_4gram_count:     int          = 0     # distinct 4-note motifs
    top_motif_freq:        float        = 0.0   # fraction notes in most-common 4-gram
    repetition_score:      float        = 0.0   # [0,1]: how much material repeats

    # Raw counts
    note_count:            int          = 0
    interval_count:        int          = 0

    def to_dict(self) -> dict:
        return {
            "analyzed_channel":   self.analyzed_channel,
            "interval_histogram": [round(x, 4) for x in self.interval_histogram],
            "mean_abs_interval":  round(self.mean_abs_interval, 3),
            "stepwise_ratio":     round(self.stepwise_ratio, 3),
            "leap_ratio":         round(self.leap_ratio, 3),
            "interval_entropy":   round(self.interval_entropy, 3),
            "contour_up_ratio":   round(self.contour_up_ratio, 3),
            "contour_down_ratio": round(self.contour_down_ratio, 3),
            "contour_same_ratio": round(self.contour_same_ratio, 3),
            "contour_entropy":    round(self.contour_entropy, 3),
            "direction_run_mean": round(self.direction_run_mean, 3),
            "phrase_count":       self.phrase_count,
            "phrase_len_mean":    round(self.phrase_len_mean, 2),
            "phrase_len_std":     round(self.phrase_len_std, 2),
            "phrase_len_entropy": round(self.phrase_len_entropy, 3),
            "motif_4gram_count":  self.motif_4gram_count,
            "top_motif_freq":     round(self.top_motif_freq, 3),
            "repetition_score":   round(self.repetition_score, 3),
            "note_count":         self.note_count,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total)
        for c in counter.values() if c > 0
    )


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def _interval_bin(semitones: int) -> int:
    """Map absolute semitone distance to histogram bin (0–12)."""
    return min(semitones, 12)


def _infer_lead_channel(notes: list[NoteEvent]) -> int:
    """Return the FM channel index with the widest pitch range among pitched notes."""
    ch_pitches: dict[int, list[int]] = {}
    for n in notes:
        if n.note >= 0 and n.chip == "ym2612":
            ch_pitches.setdefault(n.channel, []).append(n.note)
    if not ch_pitches:
        return 0
    return max(ch_pitches, key=lambda c: (max(ch_pitches[c]) - min(ch_pitches[c])))


def _segment_phrases(
    notes: list[NoteEvent],
    gap_sec: float = _PHRASE_BOUNDARY_SEC,
) -> list[list[NoteEvent]]:
    """Split note sequence into phrases separated by gaps > gap_sec."""
    if not notes:
        return []
    phrases: list[list[NoteEvent]] = []
    current: list[NoteEvent] = [notes[0]]
    for i in range(1, len(notes)):
        prev = notes[i - 1]
        curr = notes[i]
        gap = curr.start - (prev.start + prev.duration)
        if gap > gap_sec:
            if current:
                phrases.append(current)
            current = []
        current.append(curr)
    if current:
        phrases.append(current)
    return phrases


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

def analyze(
    score: SymbolicScore,
    lead_channel: int | None = None,
) -> MelodicFeatures:
    """
    Analyze melodic structure of *score*.

    *lead_channel*: FM channel (0–5) to analyze.  If None, auto-selects
    the channel with the widest pitch range.  Pass -1 to use all channels.
    """
    feat = MelodicFeatures()

    all_notes = [n for n in score.notes if n.note >= 0]
    if not all_notes:
        return feat

    if lead_channel == -1:
        # Use all pitched notes across all channels
        notes = all_notes
        feat.analyzed_channel = -1
    else:
        if lead_channel is None:
            lead_channel = _infer_lead_channel(all_notes)
        notes = [n for n in all_notes if n.channel == lead_channel]
        feat.analyzed_channel = lead_channel

    if len(notes) < 2:
        feat.note_count = len(notes)
        return feat

    # Sort by start time
    notes = sorted(notes, key=lambda n: n.start)
    feat.note_count = len(notes)

    # ------------------------------------------------------------------
    # Interval analysis
    # ------------------------------------------------------------------
    pitches = [n.note for n in notes]
    intervals_signed = [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]
    intervals_abs    = [abs(d) for d in intervals_signed]

    feat.interval_count = len(intervals_signed)

    hist_raw = Counter(_interval_bin(a) for a in intervals_abs)
    total = sum(hist_raw.values())
    feat.interval_histogram = [hist_raw.get(b, 0) / total for b in range(13)]

    feat.mean_abs_interval = sum(intervals_abs) / len(intervals_abs)
    feat.stepwise_ratio    = sum(1 for a in intervals_abs if a <= 2) / len(intervals_abs)
    feat.leap_ratio        = sum(1 for a in intervals_abs if a >= 5) / len(intervals_abs)
    feat.interval_entropy  = _entropy(hist_raw)

    # ------------------------------------------------------------------
    # Contour (direction sequence)
    # ------------------------------------------------------------------
    directions = []
    for d in intervals_signed:
        if d > 0:
            directions.append("U")
        elif d < 0:
            directions.append("D")
        else:
            directions.append("S")

    dir_total = len(directions)
    feat.contour_up_ratio   = directions.count("U") / dir_total
    feat.contour_down_ratio = directions.count("D") / dir_total
    feat.contour_same_ratio = directions.count("S") / dir_total

    # Direction run lengths
    run_lengths: list[int] = []
    if directions:
        run = 1
        for i in range(1, len(directions)):
            if directions[i] == directions[i - 1]:
                run += 1
            else:
                run_lengths.append(run)
                run = 1
        run_lengths.append(run)

    if run_lengths:
        feat.direction_run_mean = sum(run_lengths) / len(run_lengths)
        feat.contour_entropy    = _entropy(Counter(run_lengths))

    # ------------------------------------------------------------------
    # Phrase structure
    # ------------------------------------------------------------------
    phrases = _segment_phrases(notes)
    feat.phrase_count = len(phrases)
    phrase_lens = [len(p) for p in phrases]

    if phrase_lens:
        feat.phrase_len_mean    = sum(phrase_lens) / len(phrase_lens)
        feat.phrase_len_std     = _std([float(x) for x in phrase_lens])
        feat.phrase_len_entropy = _entropy(Counter(phrase_lens))

    # ------------------------------------------------------------------
    # Motif repetition (4-note pitch-class n-grams)
    # ------------------------------------------------------------------
    pc_seq = [n.note % 12 for n in notes]
    ngrams: list[tuple] = []
    for i in range(len(pc_seq) - _MOTIF_N + 1):
        ngrams.append(tuple(pc_seq[i:i + _MOTIF_N]))

    if ngrams:
        ngram_counts = Counter(ngrams)
        feat.motif_4gram_count = len(ngram_counts)
        top_count = ngram_counts.most_common(1)[0][1]
        feat.top_motif_freq = (top_count * _MOTIF_N) / max(len(notes), 1)

        # Repetition score: fraction of n-grams that appear >1 time
        repeated = sum(c for c in ngram_counts.values() if c > 1)
        feat.repetition_score = repeated / len(ngrams)

    return feat
