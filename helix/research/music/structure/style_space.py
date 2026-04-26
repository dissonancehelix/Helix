"""
style_space.py — Style Space Mapping (Layer 7)
===============================================
Reduces high-dimensional composer fingerprint vectors to 2D/3D using
PCA (always available), t-SNE (sklearn), and UMAP (umap-learn).

These projections produce visualizable style maps showing:
  - composer clusters
  - soundtrack families
  - stylistic relationships between tracks

API
---
StyleSpaceResult.from_vectors(track_ids, vectors, labels=None) -> StyleSpaceResult
to_json(result) -> dict
compute_style_space(ids, vectors, labels=None) -> dict
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

try:
    import numpy as _np
    _HAS_NUMPY = True
except ImportError:
    _np = None  # type: ignore
    _HAS_NUMPY = False

try:
    from sklearn.decomposition import PCA as _SKLearnPCA
    from sklearn.manifold import TSNE as _TSNE
    _HAS_SKLEARN = True
except ImportError:
    _SKLearnPCA = None
    _TSNE = None
    _HAS_SKLEARN = False

try:
    import umap as _umap
    _HAS_UMAP = True
except ImportError:
    _umap = None  # type: ignore
    _HAS_UMAP = False


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class StyleSpaceResult:
    """2D/3D projections of track fingerprint vectors."""
    track_ids:    list[str]
    labels:       list[str | None]

    # PCA 2D: always computed when numpy available
    pca_2d:       list[tuple[float, float]] = field(default_factory=list)
    pca_variance_explained: list[float] = field(default_factory=list)

    # t-SNE 2D (sklearn)
    tsne_2d:      list[tuple[float, float]] = field(default_factory=list)

    # UMAP 2D
    umap_2d:      list[tuple[float, float]] = field(default_factory=list)

    # Tools used
    tools_used:   dict[str, bool] = field(default_factory=dict)
    errors:       dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_count": len(self.track_ids),
            "tools_used":  self.tools_used,
            "pca_variance_explained": [round(v, 4) for v in self.pca_variance_explained],
            "points": [
                {
                    "track_id": tid,
                    "label":    lbl,
                    "pca":      list(self.pca_2d[i]) if i < len(self.pca_2d) else None,
                    "tsne":     list(self.tsne_2d[i]) if i < len(self.tsne_2d) else None,
                    "umap":     list(self.umap_2d[i]) if i < len(self.umap_2d) else None,
                }
                for i, (tid, lbl) in enumerate(zip(self.track_ids, self.labels))
            ],
            "errors": self.errors,
        }

    def nearest_neighbors(self, track_id: str, k: int = 5) -> list[tuple[str, float]]:
        """
        Return k nearest neighbors in PCA space by Euclidean distance.
        Returns [(track_id, distance), ...] sorted ascending.
        """
        if not self.pca_2d:
            return []
        try:
            idx = self.track_ids.index(track_id)
        except ValueError:
            return []
        qx, qy = self.pca_2d[idx]
        dists: list[tuple[str, float]] = []
        for i, (tx, ty) in enumerate(self.pca_2d):
            if i == idx:
                continue
            d = math.sqrt((tx - qx) ** 2 + (ty - qy) ** 2)
            dists.append((self.track_ids[i], round(d, 4)))
        dists.sort(key=lambda x: x[1])
        return dists[:k]


# ---------------------------------------------------------------------------
# Pure-numpy PCA (fallback when sklearn unavailable)
# ---------------------------------------------------------------------------

def _numpy_pca_2d(X: Any) -> tuple[list[tuple[float, float]], list[float]]:
    """
    Compute 2-component PCA using only numpy.
    Returns (projected_2d, variance_explained).
    """
    X = _np.array(X, dtype=float)
    mean = X.mean(axis=0)
    Xc = X - mean
    cov = _np.cov(Xc.T)
    if Xc.shape[0] < 2:
        return [(float(row[0]), 0.0) for row in Xc], [1.0, 0.0]
    try:
        eigvals, eigvecs = _np.linalg.eigh(cov)
        idx = _np.argsort(eigvals)[::-1]
        eigvals = eigvals[idx]
        eigvecs = eigvecs[:, idx]
        W = eigvecs[:, :2]
        Z = Xc @ W
        total = float(_np.sum(eigvals)) or 1.0
        var = [float(eigvals[0]) / total, float(eigvals[1]) / total]
        return [(float(r[0]), float(r[1])) for r in Z], var
    except Exception:
        # Degenerate: return zeros
        return [(0.0, 0.0)] * len(X), [0.0, 0.0]


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def compute(
    track_ids: list[str],
    vectors:   list[list[float]],
    labels:    list[str | None] | None = None,
    tsne_perplexity: float = 5.0,
    umap_n_neighbors: int = 5,
    random_state: int = 42,
) -> StyleSpaceResult:
    """
    Compute PCA, t-SNE, and UMAP projections of track fingerprint vectors.

    track_ids: parallel to vectors
    labels:    per-track composer label (for coloring in visualizations)
    """
    n = len(track_ids)
    if labels is None:
        labels = [None] * n

    result = StyleSpaceResult(
        track_ids=track_ids,
        labels=list(labels),
        tools_used={
            "numpy":   _HAS_NUMPY,
            "sklearn": _HAS_SKLEARN,
            "umap":    _HAS_UMAP,
        },
    )

    if n < 2 or not _HAS_NUMPY:
        result.errors["pca"] = "need numpy and ≥2 tracks"
        return result

    X = _np.array(vectors, dtype=float)

    # --- PCA ---
    try:
        if _HAS_SKLEARN and n >= 3:
            pca = _SKLearnPCA(n_components=min(2, n), random_state=random_state)
            Z = pca.fit_transform(X)
            result.pca_2d = [(float(r[0]), float(r[1])) for r in Z]
            result.pca_variance_explained = [round(float(v), 4)
                                              for v in pca.explained_variance_ratio_[:2]]
        else:
            result.pca_2d, result.pca_variance_explained = _numpy_pca_2d(X)
    except Exception as exc:
        result.errors["pca"] = str(exc)
        log.debug("style_space PCA error: %s", exc)

    # --- t-SNE ---
    if _HAS_SKLEARN and n >= 4:
        try:
            perp = min(tsne_perplexity, max(1.0, n / 3.0))
            tsne = _TSNE(n_components=2, perplexity=perp, random_state=random_state,
                         n_iter=500, verbose=0)
            Z_tsne = tsne.fit_transform(X)
            result.tsne_2d = [(float(r[0]), float(r[1])) for r in Z_tsne]
        except Exception as exc:
            result.errors["tsne"] = str(exc)
            log.debug("style_space t-SNE error: %s", exc)

    # --- UMAP ---
    if _HAS_UMAP and n >= 4:
        try:
            nn = min(umap_n_neighbors, n - 1)
            reducer = _umap.UMAP(n_components=2, n_neighbors=nn,
                                  random_state=random_state)
            Z_umap = reducer.fit_transform(X)
            result.umap_2d = [(float(r[0]), float(r[1])) for r in Z_umap]
        except Exception as exc:
            result.errors["umap"] = str(exc)
            log.debug("style_space UMAP error: %s", exc)

    return result


# ---------------------------------------------------------------------------
# Similarity matrix
# ---------------------------------------------------------------------------

def cosine_similarity_matrix(vectors: list[list[float]]) -> list[list[float]]:
    """
    Compute n×n cosine similarity matrix.
    Returns list-of-lists for JSON serialization.
    """
    if not _HAS_NUMPY:
        # Pure Python fallback
        def cos(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na  = math.sqrt(sum(x * x for x in a))
            nb  = math.sqrt(sum(x * x for x in b))
            return dot / (na * nb) if na and nb else 0.0
        n = len(vectors)
        return [[round(cos(vectors[i], vectors[j]), 4) for j in range(n)] for i in range(n)]

    X  = _np.array(vectors, dtype=float)
    norms = _np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    Xn = X / norms
    M  = Xn @ Xn.T
    _np.clip(M, -1.0, 1.0, out=M)
    n = len(vectors)
    return [[round(float(M[i, j]), 4) for j in range(n)] for i in range(n)]


def compute_style_space(ids: list[str], vectors: list[list[float]], labels: list[str | None] | None = None) -> dict[str, Any]:
    """Helper for MasterPipeline to compute and return a serializable style space."""
    res = compute(ids, vectors, labels)
    return res.to_dict()
