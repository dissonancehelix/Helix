"""
motif_detector.py — n-gram motif detection over note sequences
==============================================================
Pure Python (stdlib only).

API
---
detect(note_events, n_values: tuple[int,...] = (3, 4, 5),
       top_k: int = 10) -> MotifResult

    note_events: objects with .note (MIDI pitch) and .start (seconds).
    Returns MotifResult with top motifs and occurrence positions.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Motif:
    pitches:    tuple[int, ...]   # MIDI pitch sequence
    n:          int               # n-gram length
    count:      int               # number of occurrences
    positions:  list[float]       # onset times (seconds) of each occurrence


@dataclass
class MotifResult:
    top_motifs:     list[Motif]
    total_notes:    int
    motif_density:  float   # (occurrences of top motif) / total_notes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _quantize_pitch(midi: int, semitones: bool = True) -> int:
    """Return pitch class (0–11) or raw MIDI pitch."""
    return midi if semitones else (midi % 12)


def _ngrams(seq: list[int], n: int) -> list[tuple[int, ...]]:
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

def detect(
    note_events: Sequence,
    n_values: tuple[int, ...] = (3, 4, 5),
    top_k: int = 10,
) -> MotifResult:
    """
    Detect recurring pitch n-grams in note_events.
    Events are sorted by .start before analysis.
    """
    events = sorted(note_events, key=lambda e: float(e.start))
    total  = len(events)

    if total < 2:
        return MotifResult(top_motifs=[], total_notes=total, motif_density=0.0)

    pitches = [int(e.note) for e in events]
    starts  = [float(e.start) for e in events]

    all_motifs: list[Motif] = []

    for n in n_values:
        if n > total:
            continue

        grams = _ngrams(pitches, n)
        counts: Counter[tuple[int, ...]] = Counter(grams)

        for gram, count in counts.most_common(top_k):
            if count < 2:
                break
            positions = [starts[i] for i, g in enumerate(grams) if g == gram]
            all_motifs.append(Motif(pitches=gram, n=n, count=count, positions=positions))

    # Sort by count desc, then n desc (prefer longer motifs)
    all_motifs.sort(key=lambda m: (m.count, m.n), reverse=True)
    top = all_motifs[:top_k]

    density = (top[0].count / total) if top else 0.0

    return MotifResult(
        top_motifs=top,
        total_notes=total,
        motif_density=round(density, 4),
    )
