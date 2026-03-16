"""
rhythm_analyzer.py — Tempo and rhythm analysis
===============================================
Pure Python / stdlib math only.  numpy accelerates autocorrelation when
installed but is not required.

API
---
analyze(note_events, sample_rate: float = 44100.0) -> RhythmResult
    note_events: objects with .start (float, seconds) and .duration (float).
    Returns RhythmResult with tempo, syncopation, beat_regularity.

from_samples(onset_times: list[float]) -> RhythmResult
    Raw onset times in seconds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False


@dataclass
class RhythmResult:
    tempo_bpm:       float   # estimated BPM (0 if no notes)
    syncopation:     float   # 0–1: fraction of onsets on off-beats
    beat_regularity: float   # 0–1: autocorrelation peak at beat period
    ioi_mean:        float   # mean inter-onset interval in seconds
    ioi_std:         float   # std dev of IOI
    onset_count:     int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _median(seq: list[float]) -> float:
    if not seq:
        return 0.0
    s = sorted(seq)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _std(seq: list[float]) -> float:
    if len(seq) < 2:
        return 0.0
    m = sum(seq) / len(seq)
    return math.sqrt(sum((x - m) ** 2 for x in seq) / (len(seq) - 1))


def _autocorr_peak(iois: list[float], period: float, tolerance: float = 0.15) -> float:
    """
    Compute the fraction of IOIs that are close to integer multiples of `period`.
    Returns 0–1.
    """
    if not iois or period <= 0:
        return 0.0
    hits = 0
    for ioi in iois:
        ratio = ioi / period
        nearest = round(ratio)
        if nearest > 0 and abs(ratio - nearest) / nearest < tolerance:
            hits += 1
    return hits / len(iois)


def _syncopation_score(onsets: list[float], beat_period: float) -> float:
    """
    Fraction of onsets that fall on the weakest metrical positions
    (between 0.25 and 0.75 of a beat cycle).
    """
    if not onsets or beat_period <= 0:
        return 0.0
    off_beat = 0
    for t in onsets:
        phase = (t % beat_period) / beat_period
        # Weak metrical positions: between quarter and three-quarter of beat
        if 0.20 < phase < 0.80:
            off_beat += 1
    return off_beat / len(onsets)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def from_samples(onset_times: list[float]) -> RhythmResult:
    """Analyze rhythm from a list of onset times in seconds."""
    onsets = sorted(onset_times)

    if len(onsets) < 2:
        return RhythmResult(
            tempo_bpm=0.0, syncopation=0.0, beat_regularity=0.0,
            ioi_mean=0.0, ioi_std=0.0, onset_count=len(onsets),
        )

    iois = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1)]
    ioi_mean   = sum(iois) / len(iois)
    ioi_std    = _std(iois)
    ioi_median = _median(iois)

    # Tempo via IOI median
    beat_period = ioi_median
    tempo = (60.0 / beat_period) if beat_period > 0 else 0.0

    # Clamp to musical range 40–240 BPM
    while tempo > 240 and beat_period > 0:
        beat_period *= 2
        tempo /= 2
    while 0 < tempo < 40 and beat_period > 0:
        beat_period /= 2
        tempo *= 2

    beat_regularity = _autocorr_peak(iois, beat_period)
    syncopation     = _syncopation_score(onsets, beat_period)

    return RhythmResult(
        tempo_bpm=round(tempo, 2),
        syncopation=round(syncopation, 4),
        beat_regularity=round(beat_regularity, 4),
        ioi_mean=round(ioi_mean, 4),
        ioi_std=round(ioi_std, 4),
        onset_count=len(onsets),
    )


def analyze(note_events: Sequence, sample_rate: float = 44100.0) -> RhythmResult:
    """
    Analyze rhythm from NoteEvent-like objects (.start in seconds).
    """
    onsets = sorted(float(ev.start) for ev in note_events if hasattr(ev, "start"))
    return from_samples(onsets)
