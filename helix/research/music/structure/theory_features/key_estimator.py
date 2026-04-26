"""
key_estimator.py — Krumhansl-Schmuckler key estimation
=======================================================
Pure numpy.  music21 is used only for validation if installed.

API
---
estimate(pitch_counts: dict[int, float] | list[float]) -> KeyResult
    pitch_counts: MIDI pitch → count  OR  12-element pitch class histogram
    Returns KeyResult with .key (e.g. "C"), .mode ("major"|"minor"), .confidence (0–1)

pitch_histogram(note_events) -> list[float]
    Build a 12-element pitch class histogram from a list of NoteEvent-like objects
    that have `.note` (MIDI pitch) and `.duration` attributes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

# ---------------------------------------------------------------------------
# Krumhansl-Kessler key profiles (1982)
# ---------------------------------------------------------------------------

_MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                  2.52, 5.19, 2.39, 3.66, 2.29, 2.88]

_MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                  2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
               "F#", "G", "G#", "A", "A#", "B"]

_ENHARMONIC = {
    "C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb",
}


@dataclass
class KeyResult:
    key:        str    # e.g. "C", "G", "F#"
    mode:       str    # "major" or "minor"
    confidence: float  # 0.0–1.0 (normalised correlation)
    all_scores: dict[str, float]  # key+mode → correlation score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mean(seq: list[float]) -> float:
    return sum(seq) / len(seq) if seq else 0.0


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n == 0:
        return 0.0
    ma, mb = _mean(a), _mean(b)
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da  = math.sqrt(sum((x - ma) ** 2 for x in a))
    db  = math.sqrt(sum((x - mb) ** 2 for x in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def _rotate(profile: list[float], steps: int) -> list[float]:
    """Rotate a 12-element profile by `steps` semitones."""
    return profile[steps:] + profile[:steps]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def pitch_histogram(note_events: Sequence) -> list[float]:
    """
    Build a 12-element pitch class histogram weighted by note duration.
    note_events must have .note (int, MIDI pitch) and .duration (float, seconds).
    """
    hist = [0.0] * 12
    for ev in note_events:
        pc = ev.note % 12
        hist[pc] += max(0.0, float(ev.duration))
    total = sum(hist)
    if total > 0:
        hist = [x / total for x in hist]
    return hist


def estimate(pitch_counts) -> KeyResult:
    """
    Estimate key from MIDI pitch counts or 12-element histogram.

    pitch_counts: dict[int, float]  →  MIDI pitch → total duration/count
                  list[float]        →  12-element pitch-class histogram

    Returns KeyResult.
    """
    # Build 12-element histogram
    if isinstance(pitch_counts, dict):
        hist = [0.0] * 12
        for midi, cnt in pitch_counts.items():
            hist[int(midi) % 12] += float(cnt)
        total = sum(hist)
        if total > 0:
            hist = [x / total for x in hist]
    else:
        hist = [float(x) for x in pitch_counts]
        if len(hist) != 12:
            hist = (hist + [0.0] * 12)[:12]
        total = sum(hist)
        if total > 0:
            hist = [x / total for x in hist]

    # Compute Pearson correlation for all 24 keys
    scores: dict[str, float] = {}
    for tonic in range(12):
        maj_corr = _pearson(hist, _rotate(_MAJOR_PROFILE, tonic))
        min_corr = _pearson(hist, _rotate(_MINOR_PROFILE, tonic))
        note = _NOTE_NAMES[tonic]
        scores[f"{note} major"] = maj_corr
        scores[f"{note} minor"] = min_corr

    best_label = max(scores, key=lambda k: scores[k])
    best_score = scores[best_label]

    # Normalise confidence: map from [-1, 1] → [0, 1]
    confidence = (best_score + 1.0) / 2.0

    parts = best_label.split(" ", 1)
    key_name = parts[0]
    mode     = parts[1] if len(parts) > 1 else "major"

    return KeyResult(
        key=key_name,
        mode=mode,
        confidence=round(confidence, 4),
        all_scores={k: round(v, 4) for k, v in scores.items()},
    )
