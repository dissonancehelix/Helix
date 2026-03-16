"""
composer_similarity.py — Probabilistic composer attribution
============================================================
Builds per-composer Gaussian fingerprints (centroid + covariance) from
known-attribution tracks, then computes posterior attribution for unknown
tracks via Bayesian multi-Gaussian scoring.

API
---
ComposerProfiler:
    .fit(track_vectors, track_attributions) -> None
    .predict(vec, top_k=5) -> list[AttributionResult]
    .save(path: Path) -> None
    .load(path: Path) -> None

AttributionResult:
    composer: str
    probability: float   # posterior probability (normalised)
    distance:    float   # Mahalanobis-like distance to centroid
    method:      str     # "bayesian_gaussian"
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

from labs.music_lab.config import FEATURE_VECTOR_DIM


@dataclass
class AttributionResult:
    composer:    str
    probability: float
    distance:    float
    method:      str = "bayesian_gaussian"
    confidence:  float = 0.0


class ComposerProfiler:
    """
    Gaussian composer fingerprinter.

    Each composer is modelled as a multivariate Gaussian:
        N(μ_c, σ_c²)   — diagonal covariance for efficiency

    Attribution posterior:
        P(c | x) ∝ P(x | c) · P(c)
    where P(x | c) = exp(-0.5 * ||x - μ_c||² / σ_c²)
    and   P(c) = uniform over all seen composers.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, Any]] = {}
        self._fitted = False

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit(
        self,
        track_vectors:      list[Any],        # list of 64-dim vectors
        track_attributions: list[str],         # composer name per track
    ) -> None:
        """Compute per-composer centroid and per-dim variance."""
        if not track_vectors:
            return

        # Group vectors by composer
        groups: dict[str, list[list[float]]] = {}
        for vec, comp in zip(track_vectors, track_attributions):
            if comp not in groups:
                groups[comp] = []
            v = _to_list(vec)
            groups[comp].append(v)

        self._profiles = {}
        for comp, vecs in groups.items():
            n   = len(vecs)
            dim = len(vecs[0])
            # Centroid
            centroid = [sum(v[d] for v in vecs) / n for d in range(dim)]
            # Per-dim variance + regularisation (Laplace smoothing)
            var = [
                max(1e-4, sum((v[d] - centroid[d]) ** 2 for v in vecs) / max(1, n - 1))
                for d in range(dim)
            ]
            self._profiles[comp] = {
                "n": n,
                "centroid": centroid,
                "var": var,
            }

        self._fitted = True

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    def predict(
        self,
        vec: Any,
        top_k: int = 5,
        prior: dict[str, float] | None = None,
    ) -> list[AttributionResult]:
        """
        Return top_k composer attributions sorted by posterior probability.
        """
        if not self._fitted or not self._profiles:
            return []

        v = _to_list(vec)
        n_composers = len(self._profiles)

        scores: list[tuple[str, float, float]] = []  # (composer, log_likelihood, distance)

        for comp, prof in self._profiles.items():
            centroid = prof["centroid"]
            var      = prof["var"]
            dim      = len(centroid)

            # Log Gaussian likelihood (diagonal covariance)
            log_ll = 0.0
            dist_sq = 0.0
            for d in range(min(dim, len(v))):
                diff     = v[d] - centroid[d]
                dist_sq += diff ** 2 / var[d]
                log_ll  -= 0.5 * (diff ** 2 / var[d] + math.log(var[d] + 1e-12))

            # Add uniform prior (or custom prior)
            if prior and comp in prior:
                log_ll += math.log(max(1e-12, prior[comp]))
            else:
                log_ll += math.log(1.0 / n_composers)

            scores.append((comp, log_ll, math.sqrt(dist_sq)))

        # Normalise via softmax over log likelihoods
        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:top_k]

        max_ll   = top[0][1] if top else 0.0
        exp_sums = sum(math.exp(s[1] - max_ll) for s in scores)

        results = []
        for comp, log_ll, dist in top:
            prob = math.exp(log_ll - max_ll) / max_ll if exp_sums > 0 else 0.0
            # Simpler normalisation: fraction of top scores
            prob = math.exp(log_ll - max_ll) / (exp_sums + 1e-12)
            results.append(AttributionResult(
                composer=comp,
                probability=round(prob, 6),
                distance=round(dist, 4),
                method="bayesian_gaussian",
                confidence=round(min(1.0, prob * n_composers / top_k), 4),
            ))

        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._profiles, indent=2))

    def load(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            self._profiles = json.loads(path.read_text())
            self._fitted   = bool(self._profiles)
        except Exception:
            pass

    def composer_count(self) -> int:
        return len(self._profiles)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._profiles)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_list(vec: Any) -> list[float]:
    if _HAS_NP:
        import numpy as np
        if isinstance(vec, np.ndarray):
            return vec.tolist()
    return [float(x) for x in vec]
