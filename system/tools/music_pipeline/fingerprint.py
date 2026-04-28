"""
model/domains/music/attribution/fingerprint.py
=========================================
ComposerFingerprint — builds a normalized feature vector from TrackAnalysis artifacts.

CURRENT FEATURE VECTOR (9 features, all from DCP + structural data):

DCP TIER (indices 0-5): structural dynamics from VGM register stream
  [0] dcp_composite      — overall DCP score (0-1)
  [1] dcp_possibility    — possibility_space: pitch entropy proxy (0-1)
  [2] dcp_constraint     — register saturation / chip utilization (0-1)
  [3] dcp_tension        — pre-seam variance elevation (0-1)
  [4] dcp_collapse       — loop seam sharpness (0-1)
  [5] dcp_post_narrowing — post-seam trajectory narrowing (0-1)

STRUCTURAL TIER (indices 6-8): composition-level habits
  [6] loop_pre_ratio     — loop_start_s / duration_s (intro proportion: 0=no intro, 1=all intro)
  [7] has_sn76489        — SN76489 PSG chip present (0 or 1, Maeda signal)
  [8] log_duration       — log2(duration_s + 1) / log2(181) normalized to 0-1

NOTE: Symbolic (note_count, pitch_entropy etc.) and Voice (ADSR) tiers require
vgm_note_reconstructor wiring into codec_pipeline — not yet done.
These will be added when the symbolic pipeline is live.

Similarity: cosine similarity (1.0 = identical, 0.0 = orthogonal).
Confidence: weighted by track count and DCP qualification rate.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

_STRIP_HASH = re.compile(r'_[0-9a-f]{5,}$')

FEATURE_NAMES = [
    # DCP tier (from VGM register stream dynamics)
    "dcp_composite",
    "dcp_possibility_space",
    "dcp_constraint",
    "dcp_tension",
    "dcp_collapse",
    "dcp_post_narrowing",
    # Structural tier
    "loop_pre_ratio",
    "has_sn76489",
    "log_duration",
]

N_FEATURES = len(FEATURE_NAMES)

_DCP_QUALIFIED = {"FULL", "UNCONFIRMED"}


def _safe(d: dict, key: str, default: float = 0.0) -> float:
    v = d.get(key, default)
    return float(v) if v is not None else default


def _extract_vector(entry: dict) -> list[float] | None:
    """
    Extract a normalized feature vector from a TrackAnalysis artifact dict.
    Works with whatever fields are currently populated by the codec_pipeline.
    """
    analysis = entry.get("analysis", entry)

    dcp   = analysis.get("dcp") or {}
    chips = analysis.get("chips") or []

    dcp_q = dcp.get("qualification", "INSUFFICIENT")
    if dcp_q not in _DCP_QUALIFIED:
        return None   # no usable DCP data at all

    # Loop pre-ratio
    loop_start = analysis.get("loop_start_s")
    duration   = _safe(analysis, "duration_s")
    loop_pre   = (loop_start / duration) if (loop_start and duration > 0) else 0.0

    # SN76489 presence
    has_psg = 1.0 if any("SN76489" in str(c) or "SN76" in str(c) for c in chips) else 0.0

    # Duration (log-normalized: log2(1+d)/log2(181) so 3min→1.0)
    log_dur = math.log2(1.0 + duration) / math.log2(181.0) if duration > 0 else 0.0

    return [
        # DCP tier
        min(_safe(dcp, "composite"), 1.0),
        min(_safe(dcp, "possibility_space"), 1.0),
        min(_safe(dcp, "constraint"), 1.0),
        min(_safe(dcp, "tension"), 1.0),
        min(_safe(dcp, "collapse"), 1.0),
        min(_safe(dcp, "post_narrowing"), 1.0),
        # Structural tier
        min(loop_pre, 1.0),
        has_psg,
        min(log_dur, 1.0),
    ]


def _cosine(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


@dataclass
class ComposerFingerprint:
    """Per-composer DCP+structural centroid built from confirmed tracks."""

    composer:      str
    track_count:   int         = 0
    dcp_qualified: int         = 0
    vector:        list[float] = field(default_factory=lambda: [0.0] * N_FEATURES)
    track_ids:     list[str]   = field(default_factory=list)

    @classmethod
    def from_analyses(cls, composer: str, analyses: list[dict]) -> "ComposerFingerprint":
        vectors   = []
        track_ids = []

        for entry in analyses:
            vec = _extract_vector(entry)
            if vec is None:
                continue
            vectors.append(vec)
            track_ids.append(entry.get("entity_id", ""))

        if not vectors:
            return cls(composer=composer)

        n = len(vectors)
        centroid = [sum(v[i] for v in vectors) / n for i in range(N_FEATURES)]

        return cls(
            composer=composer,
            track_count=n,
            dcp_qualified=n,   # all entries here had qualified DCP
            vector=centroid,
            track_ids=track_ids,
        )

    def similarity(self, track_vector: list[float]) -> float:
        return _cosine(self.vector, track_vector)

    def confidence_weight(self) -> float:
        """
        0-1 reliability weight. Saturates at 30 tracks.
        Lower confidence than symbolic version since DCP alone is less discriminating.
        """
        return round(min(self.track_count / 30.0, 1.0), 4)

    def to_dict(self) -> dict:
        return {
            "composer":          self.composer,
            "track_count":       self.track_count,
            "dcp_qualified":     self.dcp_qualified,
            "confidence_weight": self.confidence_weight(),
            "vector":            {FEATURE_NAMES[i]: round(v, 4) for i, v in enumerate(self.vector)},
            "track_ids":         self.track_ids,
        }

