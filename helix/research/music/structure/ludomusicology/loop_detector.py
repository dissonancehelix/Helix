"""
loop_detector.py — Loop Architecture Analysis
==============================================
VGM tracks loop. This module detects loop boundaries, measures harmonic
behavior at loop restart points, and computes loop stability metrics.

VGM files encode loop start/end via header offsets (parsed by vgm_parser).
This module takes the symbolic score and loop metadata to measure:

  - loop_start_sec / loop_end_sec    from VGM header
  - loop_phrase_alignment            does the loop start on a phrase boundary?
  - loop_harmonic_continuity         harmonic compatibility at loop point
  - loop_cadence_type                cadence just before loop restart
  - loop_stability_index             0–1 (1=perfectly seamless loop)

API
---
analyze_loop(score, vgm_header=None) -> LoopResult
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoopResult:
    loop_start_sec:           float | None = None
    loop_end_sec:             float | None = None
    loop_duration_sec:        float | None = None
    loop_count:               int | None   = None   # loops before track end

    # Harmonic analysis at loop point
    chord_before_loop:        str | None   = None   # last chord before restart
    chord_at_loop_start:      str | None   = None   # first chord of loop
    loop_harmonic_continuity: float        = 0.0    # 0–1 pitch class overlap
    loop_cadence_type:        str          = "none"  # authentic/half/plagal/abrupt/none

    # Phrase alignment
    phrase_near_loop_start:   bool         = False
    phrase_near_loop_end:     bool         = False
    loop_phrase_alignment:    float        = 0.0    # 0–1 (1=loop on phrase boundary)

    # Loop stability index
    loop_stability_index:     float        = 0.0    # composite 0–1

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_start_sec":           self.loop_start_sec,
            "loop_end_sec":             self.loop_end_sec,
            "loop_duration_sec":        self.loop_duration_sec,
            "loop_cadence_type":        self.loop_cadence_type,
            "loop_harmonic_continuity": round(self.loop_harmonic_continuity, 3),
            "loop_phrase_alignment":    round(self.loop_phrase_alignment, 3),
            "loop_stability_index":     round(self.loop_stability_index, 3),
            "chord_before_loop":        self.chord_before_loop,
            "chord_at_loop_start":      self.chord_at_loop_start,
        }


def analyze_loop(
    score: Any,           # SymbolicScore from vgm_note_reconstructor
    vgm_header: Any = None,
) -> LoopResult:
    """
    Analyze loop architecture of a VGM track.

    score: SymbolicScore with .notes list of Note(time_sec, duration_sec, pitch, channel)
           and optionally .metadata with loop_start, loop_end
    vgm_header: optional parsed header with loop_offset, loop_length fields
    """
    result = LoopResult()

    if not hasattr(score, "notes") or not score.notes:
        return result

    notes = score.notes
    total_dur = max((n.start + n.duration for n in notes), default=0.0)

    # Extract loop points from header or score metadata
    loop_start = None
    loop_end   = None

    if vgm_header is not None:
        loop_start = getattr(vgm_header, "loop_offset_sec", None)
        loop_end   = getattr(vgm_header, "loop_end_sec", None) or total_dur

    if loop_start is None and hasattr(score, "metadata"):
        md = score.metadata or {}
        loop_start = md.get("loop_start_sec")
        loop_end   = md.get("loop_end_sec") or total_dur

    # Default: assume loop covers the full track
    if loop_start is None:
        loop_start = 0.0
    if loop_end is None:
        loop_end = total_dur

    result.loop_start_sec  = round(loop_start, 3)
    result.loop_end_sec    = round(loop_end, 3)
    result.loop_duration_sec = round(loop_end - loop_start, 3) if loop_end > loop_start else None

    # --- Harmonic continuity at loop point ---
    # Compare pitch classes in last 1s before loop end vs first 1s of loop start
    window = 1.0
    before_notes = [n for n in notes if loop_end - window <= n.start < loop_end]
    after_notes  = [n for n in notes if loop_start <= n.start < loop_start + window]

    if before_notes and after_notes:
        before_pcs = set(n.note % 12 for n in before_notes)
        after_pcs  = set(n.note % 12 for n in after_notes)
        union = len(before_pcs | after_pcs)
        inter = len(before_pcs & after_pcs)
        result.loop_harmonic_continuity = inter / union if union > 0 else 0.0

        # Cadence heuristic: what's the lowest-pitched note just before loop end?
        # A note cluster near the tonic implies a proper cadence
        result.chord_before_loop  = _infer_chord_label(before_notes)
        result.chord_at_loop_start = _infer_chord_label(after_notes)
        result.loop_cadence_type   = _infer_cadence(before_notes, after_notes)

    # --- Phrase alignment ---
    # Find phrase boundaries (gaps > 0.35s between consecutive notes)
    phrase_starts = _phrase_boundaries(notes)
    if phrase_starts:
        # Check if loop start/end is within 0.25s of a phrase boundary
        near_start = any(abs(p - loop_start) < 0.25 for p in phrase_starts)
        near_end   = any(abs(p - loop_end)   < 0.25 for p in phrase_starts)
        result.phrase_near_loop_start = near_start
        result.phrase_near_loop_end   = near_end
        result.loop_phrase_alignment  = (0.5 * float(near_start) + 0.5 * float(near_end))

    # --- Loop stability index: composite score ---
    result.loop_stability_index = (
        0.4 * result.loop_harmonic_continuity
        + 0.4 * result.loop_phrase_alignment
        + 0.2 * (1.0 if result.loop_cadence_type in ("authentic", "plagal") else
                 0.5 if result.loop_cadence_type == "half" else 0.0)
    )

    return result


def _infer_chord_label(notes: list) -> str | None:
    if not notes:
        return None
    pitches = sorted(set(n.note % 12 for n in notes))
    # Simple: return pitch class set as string
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return "/".join(note_names[p] for p in pitches[:4])


def _infer_cadence(before: list, after: list) -> str:
    """Simple cadence heuristic from pitch class context."""
    if not before or not after:
        return "none"

    before_pcs = set(n.note % 12 for n in before)
    after_pcs  = set(n.note % 12 for n in after)

    # Dominants = {2, 7, 11} (G, B, D in C major = V chord)
    # Tonics    = {0, 4, 7}  (C, E, G in C major = I chord)
    # These are approximate — we don't know the key here
    overlap = len(before_pcs & after_pcs)
    total   = len(before_pcs | after_pcs)

    if total == 0:
        return "none"

    jaccard = overlap / total
    if jaccard >= 0.6:
        return "plagal"          # high overlap = smooth harmonic continuation
    elif jaccard >= 0.3:
        return "half"            # partial overlap = semi-cadential
    elif jaccard > 0:
        return "authentic"       # low overlap = strong harmonic resolution
    else:
        return "abrupt"          # no overlap = jarring loop restart


def _phrase_boundaries(notes: list, gap_sec: float = 0.35) -> list[float]:
    """Return list of phrase start times (times after a gap > gap_sec)."""
    if not notes:
        return []
    sorted_notes = sorted(notes, key=lambda n: n.start)
    boundaries = [sorted_notes[0].start]
    for i in range(1, len(sorted_notes)):
        prev_end = sorted_notes[i - 1].start + sorted_notes[i - 1].duration
        if sorted_notes[i].start - prev_end > gap_sec:
            boundaries.append(sorted_notes[i].start)

    return boundaries
