"""
composer_fingerprint.py — Composer style fingerprint vector
=============================================================
Consolidates all three analysis layers into a single composer-style
fingerprint vector for attribution, clustering, and comparison.

This is separate from the 64-dim similarity vector (feature_vector.py).
The composer fingerprint prioritizes compositional style over timbral identity,
with symbolic features weighted as the primary signal.

Vector layout (56 dims):
  dims  0–12: melodic interval histogram (13 bins)
  dims 13–15: melodic contour (up/down/same ratios)
  dims 16–17: stepwise ratio, leap ratio
  dims 18–19: phrase length mean (normalized), phrase len entropy
  dims 20–21: repetition score, top motif freq
  dims 22–23: interval entropy, contour entropy
  dims 24–34: chord family distribution (11 bins)
  dims 35–36: chord progression entropy, chord change rate (normalized)
  dims 37–38: bassline step ratio, bassline leap ratio
  dims 39–40: simultaneity ratio, mean polyphony (normalized /6)
  dims 41–42: pitch class entropy, chromatic density
  dims 43–45: density mean, density variance, breakdown fraction
  dims 46–47: full texture fraction, handoff count (normalized)
  dims 48–49: section count (normalized), active channel mean (normalized /8)
  dims 50–55: algorithm distribution (6 most common algs, normalized)
              [alg0, alg1, alg2, alg3, alg4, alg5, alg6, alg7] compressed to 6

API
---
build_vector(melodic, harmonic, arrangement, layer1_features) -> list[float]
    All inputs optional; missing values default to 0.0.

ComposerProfiler:
    add_track(track_id, vector, ground_truth_composer)
    get_profiles()             → {composer: centroid_vector}
    predict(vector, top_k=3)  → [(composer, score), ...]
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

FINGERPRINT_DIM = 56


# ---------------------------------------------------------------------------
# Vector builder
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def build_vector(
    melodic:     Any = None,   # MelodicFeatures | None
    harmonic:    Any = None,   # HarmonicFeatures | None
    arrangement: Any = None,   # ArrangementFeatures | None
    layer1:      Any = None,   # TrackFeatures | None (from feature_extractor.py)
) -> list[float]:
    """
    Build the 56-dim composer fingerprint vector.
    All inputs are optional; unknown dims default to 0.
    """
    v = [0.0] * FINGERPRINT_DIM

    # --- Melodic (dims 0–23) ---
    if melodic is not None:
        ih = melodic.interval_histogram or [0.0] * 13
        for i, x in enumerate(ih[:13]):
            v[i] = _clamp(x)                             # 0–12
        v[13] = _clamp(melodic.contour_up_ratio)
        v[14] = _clamp(melodic.contour_down_ratio)
        v[15] = _clamp(melodic.contour_same_ratio)
        v[16] = _clamp(melodic.stepwise_ratio)
        v[17] = _clamp(melodic.leap_ratio)
        # phrase length mean normalized by 32 (typical max phrase)
        v[18] = _clamp(melodic.phrase_len_mean / 32.0)
        v[19] = _clamp(melodic.phrase_len_entropy / 5.0)
        v[20] = _clamp(melodic.repetition_score)
        v[21] = _clamp(melodic.top_motif_freq)
        v[22] = _clamp(melodic.interval_entropy / 4.0)   # max ~3.7 for 13 uniform bins
        v[23] = _clamp(melodic.contour_entropy / 4.0)

    # --- Harmonic (dims 24–42) ---
    if harmonic is not None:
        cf = harmonic.chord_family_dist or [0.0] * 11
        for i, x in enumerate(cf[:11]):
            v[24 + i] = _clamp(x)                       # 24–34
        v[35] = _clamp(harmonic.chord_progression_entropy / 5.0)
        v[36] = _clamp(harmonic.chord_change_rate / 4.0)  # 4 changes/sec ~ max
        v[37] = _clamp(harmonic.bassline_step_ratio)
        v[38] = _clamp(harmonic.bassline_leap_ratio)
        v[39] = _clamp(harmonic.simultaneity_ratio)
        v[40] = _clamp(harmonic.mean_polyphony / 6.0)    # max 6 FM channels
        v[41] = _clamp(harmonic.pitch_class_entropy / math.log2(12))
        v[42] = _clamp(harmonic.chromatic_density)

    # --- Arrangement (dims 43–49) ---
    if arrangement is not None:
        v[43] = _clamp(arrangement.density_mean)
        v[44] = _clamp(arrangement.density_variance)
        v[45] = _clamp(arrangement.breakdown_fraction)
        v[46] = _clamp(arrangement.full_texture_fraction)
        v[47] = _clamp(arrangement.handoff_count / 8.0)  # normalize by section_windows/2
        v[48] = _clamp(arrangement.section_count / 10.0)
        v[49] = _clamp(arrangement.active_channel_mean / 8.0)

    # --- Layer 1 chip features (dims 50–55): algorithm distribution ---
    if layer1 is not None and hasattr(layer1, "algorithm_dist"):
        alg_dist = layer1.algorithm_dist or {}
        total = sum(alg_dist.values()) or 1
        for alg in range(6):
            v[50 + alg] = alg_dist.get(alg, 0) / total  # alg 0–5 → dims 50–55

    return v


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------------------
# ComposerProfiler
# ---------------------------------------------------------------------------

@dataclass
class ComposerProfile:
    composer:     str
    track_ids:    list[str]         = field(default_factory=list)
    vectors:      list[list[float]] = field(default_factory=list)
    centroid:     list[float]       = field(default_factory=lambda: [0.0] * FINGERPRINT_DIM)

    def update_centroid(self) -> None:
        if not self.vectors:
            return
        n = len(self.vectors)
        self.centroid = [
            sum(v[i] for v in self.vectors) / n
            for i in range(FINGERPRINT_DIM)
        ]


class ComposerProfiler:
    """
    Builds per-composer centroids from fingerprint vectors and supports
    attribution via cosine similarity to centroids.

    Usage:
        profiler = ComposerProfiler()
        profiler.add_track("track_01", vector, "Masayuki Nagao")
        ...
        profiler.finalize()
        predictions = profiler.predict(unknown_vector, top_k=3)
    """

    def __init__(self) -> None:
        self._profiles: dict[str, ComposerProfile] = {}
        self._all_vectors: dict[str, list[float]] = {}
        self._all_labels: dict[str, str] = {}

    def add_track(
        self,
        track_id: str,
        vector: list[float],
        composer: str,
    ) -> None:
        if composer not in self._profiles:
            self._profiles[composer] = ComposerProfile(composer=composer)
        p = self._profiles[composer]
        p.track_ids.append(track_id)
        p.vectors.append(vector)
        self._all_vectors[track_id] = vector
        self._all_labels[track_id] = composer

    def finalize(self) -> None:
        """Recompute all centroids after adding tracks."""
        for p in self._profiles.values():
            p.update_centroid()

    def get_profiles(self) -> dict[str, ComposerProfile]:
        return dict(self._profiles)

    def predict(
        self,
        vector: list[float],
        top_k: int = 3,
        method: str = "cosine",
    ) -> list[tuple[str, float]]:
        """
        Predict composer(s) for *vector*.
        Returns [(composer, score), ...] sorted by descending score.
        method: "cosine" (similarity) or "euclidean" (inverted distance)
        """
        if not self._profiles:
            return []

        scores: list[tuple[str, float]] = []
        for composer, profile in self._profiles.items():
            if method == "cosine":
                score = _cosine(vector, profile.centroid)
            else:
                dist  = _euclidean(vector, profile.centroid)
                score = 1.0 / (1.0 + dist)
            scores.append((composer, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def knn_predict(
        self,
        vector: list[float],
        k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        k-NN prediction across all individual tracks (not centroids).
        Returns [(composer, vote_fraction), ...] sorted by vote share.
        """
        if not self._all_vectors:
            return []

        sims = [
            (tid, _cosine(vector, vec))
            for tid, vec in self._all_vectors.items()
        ]
        sims.sort(key=lambda x: x[1], reverse=True)
        top_k = sims[:k]

        votes: dict[str, int] = defaultdict(int)
        for tid, _ in top_k:
            votes[self._all_labels[tid]] += 1

        total = sum(votes.values())
        return sorted(
            [(c, v / total) for c, v in votes.items()],
            key=lambda x: x[1], reverse=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            composer: {
                "track_count": len(p.track_ids),
                "track_ids":   p.track_ids,
                "centroid":    [round(x, 4) for x in p.centroid],
            }
            for composer, p in self._profiles.items()
        }
