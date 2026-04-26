"""
arrangement_analyzer.py — Arrangement structure analysis from SymbolicScore
=============================================================================
Layer 2 primary interpretation: channel role inference, texture density
over time, structural section detection, instrument handoff patterns.

API
---
analyze(score: SymbolicScore, layer1_features=None) -> ArrangementFeatures
    layer1_features: optional TrackFeatures from feature_extractor (for
    algorithm/patch context when inferring channel roles).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from domains.music.domain_analysis.symbolic_music.score_representation import (
    NoteEvent,
    SymbolicScore,
)


# ---------------------------------------------------------------------------
# Channel roles
# ---------------------------------------------------------------------------

class ChannelRole:
    LEAD      = "lead"       # primary melody — widest pitch range, highest density
    BASS      = "bass"       # low register, often foundational
    HARMONY   = "harmony"    # mid-register sustained notes
    COUNTER   = "counter"    # independent melody line (secondary lead)
    RHYTHM    = "rhythm"     # short, repeated notes, percussive feel
    NOISE     = "noise"      # PSG noise / percussion channel
    INACTIVE  = "inactive"   # very few notes

# Thresholds for role assignment
_BASS_CEILING_MIDI   = 52    # below E3 → bass candidate
_MIN_NOTES_ACTIVE    = 3     # at least this many notes to not be INACTIVE
_DENSITY_RHYTHM_THR  = 4.0   # key-ons/sec above this → rhythm candidate (was 8.0; FM drums run 4-6/sec)
_SHORT_NOTE_RATIO    = 0.55  # fraction of notes < 0.12s → rhythm pattern (was 0.65; FM hits decay fast)
# FM percussion detection: channel uses wide pitch range as drum-trigger space (not melody)
_FM_PERC_RANGE_MIN   = 36    # semitones — 3+ octave spread = likely percussion triggers
_FM_PERC_UNIQUE_MIN  = 8     # unique pitches — drum channels hit many distinct trigger pitches


# ---------------------------------------------------------------------------
# Section detection constants
# ---------------------------------------------------------------------------

# Divide track into N windows for density analysis
_SECTION_WINDOWS = 16

# Gap between notes that signals a structural break (seconds)
_SECTION_GAP_SEC = 2.0


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ChannelProfile:
    """Per-channel summary used for role inference."""
    channel:        int
    chip:           str    # "ym2612" or "psg"
    note_count:     int    = 0
    mean_pitch:     float  = 0.0
    pitch_range:    int    = 0
    pitch_entropy:  float  = 0.0
    unique_pitches: int    = 0     # distinct MIDI pitches used (percussion channels have many)
    density_per_sec: float = 0.0   # notes per second
    short_note_ratio: float = 0.0  # fraction of notes < 0.12s
    role:           str    = ChannelRole.INACTIVE

    def to_dict(self) -> dict:
        return {
            "channel":          self.channel,
            "chip":             self.chip,
            "note_count":       self.note_count,
            "mean_pitch":       round(self.mean_pitch, 1),
            "pitch_range":      self.pitch_range,
            "pitch_entropy":    round(self.pitch_entropy, 3),
            "unique_pitches":   self.unique_pitches,
            "density_per_sec":  round(self.density_per_sec, 3),
            "short_note_ratio": round(self.short_note_ratio, 3),
            "role":             self.role,
        }


@dataclass
class ArrangementFeatures:
    """Arrangement analysis results."""

    # Channel roles
    channel_profiles:      list[ChannelProfile] = field(default_factory=list)
    lead_channel:          int                  = -1
    bass_channel:          int                  = -1
    role_distribution:     dict[str, int]       = field(default_factory=dict)

    # Texture density over time (SECTION_WINDOWS buckets, normalized)
    density_timeline:      list[float]          = field(default_factory=list)
    density_mean:          float                = 0.0
    density_variance:      float                = 0.0

    # Structural sections
    section_count:         int                  = 0
    breakdown_fraction:    float                = 0.0   # fraction of windows < 2 channels
    full_texture_fraction: float                = 0.0   # fraction of windows ≥ 4 channels

    # Active channels over time
    active_channel_mean:   float                = 0.0
    max_simultaneous_channels: int              = 0

    # Handoff patterns (how often the lead melodic role passes between channels)
    handoff_count:         int                  = 0

    def to_dict(self) -> dict:
        return {
            "channel_profiles":           [p.to_dict() for p in self.channel_profiles],
            "lead_channel":               self.lead_channel,
            "bass_channel":               self.bass_channel,
            "role_distribution":          self.role_distribution,
            "density_timeline":           [round(x, 3) for x in self.density_timeline],
            "density_mean":               round(self.density_mean, 3),
            "density_variance":           round(self.density_variance, 3),
            "section_count":              self.section_count,
            "breakdown_fraction":         round(self.breakdown_fraction, 3),
            "full_texture_fraction":      round(self.full_texture_fraction, 3),
            "active_channel_mean":        round(self.active_channel_mean, 3),
            "max_simultaneous_channels":  self.max_simultaneous_channels,
            "handoff_count":              self.handoff_count,
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


def _assign_role(
    profile: ChannelProfile,
    all_profiles: list["ChannelProfile"],
    duration_sec: float,
) -> str:
    if profile.note_count < _MIN_NOTES_ACTIVE:
        return ChannelRole.INACTIVE

    if profile.chip == "psg" and profile.channel == 9:  # PSG noise
        return ChannelRole.NOISE

    # PSG tone: likely rhythmic counter-melody or lead
    if profile.chip == "psg":
        return ChannelRole.HARMONY if profile.density_per_sec < 4.0 else ChannelRole.COUNTER

    # FM channel classification

    # FM percussion: wide pitch range used as drum-trigger space, not melodic motion.
    # Distinguishes from chromatic lead by requiring short notes + non-melodic density.
    unique_pitches = getattr(profile, "unique_pitches", None)
    if (
        profile.pitch_range >= _FM_PERC_RANGE_MIN
        and (unique_pitches is None or unique_pitches >= _FM_PERC_UNIQUE_MIN)
        and profile.short_note_ratio > _SHORT_NOTE_RATIO
        and profile.density_per_sec > _DENSITY_RHYTHM_THR
    ):
        return ChannelRole.RHYTHM

    if profile.mean_pitch < _BASS_CEILING_MIDI and profile.pitch_range < 24:
        return ChannelRole.BASS

    if profile.short_note_ratio > _SHORT_NOTE_RATIO and profile.density_per_sec > _DENSITY_RHYTHM_THR:
        return ChannelRole.RHYTHM

    # Among active FM channels, the one with widest pitch range is lead
    fm_active = [
        p for p in all_profiles
        if p.chip == "ym2612" and p.note_count >= _MIN_NOTES_ACTIVE
        and p.mean_pitch >= _BASS_CEILING_MIDI
        and p.pitch_range < _FM_PERC_RANGE_MIN  # exclude percussion candidates from lead election
    ]
    if fm_active:
        max_range = max(p.pitch_range for p in fm_active)
        if profile.pitch_range == max_range:
            return ChannelRole.LEAD

    return ChannelRole.HARMONY


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

def analyze(
    score: SymbolicScore,
    layer1_features: Any = None,
) -> ArrangementFeatures:
    feat = ArrangementFeatures()

    notes = [n for n in score.notes if n.note >= 0]
    if not notes or score.duration_sec <= 0:
        return feat

    # ------------------------------------------------------------------
    # Build per-channel profiles
    # ------------------------------------------------------------------
    ch_notes: dict[tuple[int, str], list[NoteEvent]] = defaultdict(list)
    for n in notes:
        ch_notes[(n.channel, n.chip)].append(n)

    profiles: list[ChannelProfile] = []
    for (ch, chip), ch_ns in sorted(ch_notes.items()):
        pitches = [n.note for n in ch_ns if n.note >= 0]
        if not pitches:
            continue

        profile = ChannelProfile(channel=ch, chip=chip)
        profile.note_count     = len(ch_ns)
        profile.mean_pitch     = sum(pitches) / len(pitches)
        profile.unique_pitches = len(set(pitches))
        profile.pitch_range    = max(pitches) - min(pitches)
        profile.pitch_entropy  = _entropy(Counter(pitches))
        profile.density_per_sec = len(ch_ns) / max(score.duration_sec, 0.001)
        profile.short_note_ratio = (
            sum(1 for n in ch_ns if n.duration < 0.12) / len(ch_ns)
        )
        profiles.append(profile)

    # Assign roles
    for p in profiles:
        p.role = _assign_role(p, profiles, score.duration_sec)

    feat.channel_profiles = profiles

    # Identify lead and bass channels
    leads = [p for p in profiles if p.role == ChannelRole.LEAD]
    basses = [p for p in profiles if p.role == ChannelRole.BASS]
    if leads:
        feat.lead_channel = max(leads, key=lambda p: p.pitch_range).channel
    if basses:
        feat.bass_channel = min(basses, key=lambda p: p.mean_pitch).channel

    feat.role_distribution = dict(Counter(p.role for p in profiles))

    # ------------------------------------------------------------------
    # Density timeline (SECTION_WINDOWS equal-time windows)
    # ------------------------------------------------------------------
    window_dur = score.duration_sec / _SECTION_WINDOWS
    density_timeline: list[float] = []
    channel_counts: list[int] = []

    for w in range(_SECTION_WINDOWS):
        t_start = w * window_dur
        t_end   = t_start + window_dur
        active_notes = [
            n for n in notes
            if n.start < t_end and (n.start + max(n.duration, 0.001)) > t_start
        ]
        active_chs = len({n.channel for n in active_notes})
        # Density: notes per second in this window
        density = len(active_notes) / window_dur if window_dur > 0 else 0.0
        density_timeline.append(density)
        channel_counts.append(active_chs)

    feat.density_timeline = density_timeline

    if density_timeline:
        max_d = max(density_timeline) or 1.0
        feat.density_timeline = [d / max_d for d in density_timeline]  # normalize
        raw = density_timeline  # already in normalized form
        feat.density_mean     = sum(raw) / len(raw)
        m = feat.density_mean
        feat.density_variance = sum((d - m) ** 2 for d in raw) / len(raw)

    if channel_counts:
        feat.active_channel_mean        = sum(channel_counts) / len(channel_counts)
        feat.max_simultaneous_channels  = max(channel_counts)
        feat.breakdown_fraction         = sum(1 for c in channel_counts if c < 2) / len(channel_counts)
        feat.full_texture_fraction      = sum(1 for c in channel_counts if c >= 4) / len(channel_counts)

    # ------------------------------------------------------------------
    # Section detection via structural gaps
    # ------------------------------------------------------------------
    all_starts = sorted(n.start for n in notes)
    gaps = [all_starts[i + 1] - all_starts[i]
            for i in range(len(all_starts) - 1)
            if all_starts[i + 1] - all_starts[i] > _SECTION_GAP_SEC]
    feat.section_count = len(gaps) + 1

    # ------------------------------------------------------------------
    # Handoff detection: consecutive windows where lead channel changes
    # ------------------------------------------------------------------
    window_leads: list[int] = []
    for w in range(_SECTION_WINDOWS):
        t_start = w * window_dur
        t_end   = t_start + window_dur
        active = [
            n for n in notes
            if n.start < t_end and (n.start + max(n.duration, 0.001)) > t_start
        ]
        if active:
            # Channel with most distinct pitches in window = temporary lead
            ch_variety = Counter()
            ch_notes_win: dict[int, set[int]] = defaultdict(set)
            for n in active:
                ch_notes_win[n.channel].add(n.note)
            for ch, ps in ch_notes_win.items():
                ch_variety[ch] = len(ps)
            if ch_variety:
                window_leads.append(ch_variety.most_common(1)[0][0])
            else:
                window_leads.append(-1)
        else:
            window_leads.append(-1)

    feat.handoff_count = sum(
        1 for i in range(len(window_leads) - 1)
        if window_leads[i] != window_leads[i + 1]
        and window_leads[i] >= 0 and window_leads[i + 1] >= 0
    )

    return feat
