"""
style_queries.py — Style Graph Query Layer
==========================================
High-level queries that combine the ComposerGraph with Helix fingerprint
vectors to answer musicological research questions.

All queries return ranked lists of (entity, score) tuples or structured dicts.

API
---
StyleQueryEngine(graph, vectors)
    .tracks_similar_to_composer(composer_id, k) -> list[TrackResult]
    .composers_with_overlapping_vectors(composer_id, k) -> list[ComposerResult]
    .stylistic_clusters_in_soundtrack(game_id) -> list[ClusterResult]
    .composers_sharing_synthesis_practices(composer_id) -> list[ComposerResult]
    .composer_influence_chain(composer_id, depth) -> list[str]
    .find_stylistic_outliers(game_id, threshold) -> list[TrackResult]
    .cross_game_motif_families(min_games) -> list[dict]
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Any

from domains.music.atlas_integration.composer_graph import ComposerGraph

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TrackResult:
    track_id:    str
    title:       str | None
    composer_id: str | None
    score:       float
    notes:       str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id":    self.track_id,
            "title":       self.title,
            "composer_id": self.composer_id,
            "score":       round(self.score, 4),
            "notes":       self.notes,
        }


@dataclass
class ComposerResult:
    composer_id: str
    full_name:   str
    score:       float
    shared_traits: list[str] = field(default_factory=list)
    notes:       str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "composer_id":   self.composer_id,
            "full_name":     self.full_name,
            "score":         round(self.score, 4),
            "shared_traits": self.shared_traits,
            "notes":         self.notes,
        }


@dataclass
class ClusterResult:
    cluster_id:  str
    track_ids:   list[str]
    centroid:    list[float]
    composers:   list[str]
    cohesion:    float          # average intra-cluster cosine similarity

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "track_ids":  self.track_ids,
            "composers":  self.composers,
            "cohesion":   round(self.cohesion, 4),
        }


# ---------------------------------------------------------------------------
# StyleQueryEngine
# ---------------------------------------------------------------------------

class StyleQueryEngine:
    """
    Combines graph topology with fingerprint vectors for style-level queries.

    Parameters
    ----------
    graph : ComposerGraph
    vectors : dict[str, list[float]]
        Mapping track_id → feature vector (all same dimension).
    """

    def __init__(
        self,
        graph:   ComposerGraph,
        vectors: dict[str, list[float]] | None = None,
    ) -> None:
        self.graph   = graph
        self.vectors = vectors or {}

    # -----------------------------------------------------------------------
    # Tracks similar to a composer's style
    # -----------------------------------------------------------------------

    def tracks_similar_to_composer(
        self,
        composer_id: str,
        k:           int = 10,
        min_confidence: float = 0.0,
    ) -> list[TrackResult]:
        """
        Find tracks whose fingerprint is closest to the composer's centroid vector.
        Centroid = mean of all vectors for tracks attributed to this composer.

        Searches across all tracks in the graph, not just those by this composer.
        """
        c_node = self.graph.get_composer(composer_id)
        if not c_node:
            return []

        # Build composer centroid
        if c_node.fingerprint_vector:
            centroid = c_node.fingerprint_vector
        else:
            attributed_tracks = self.graph.tracks_for_composer(composer_id)
            centroid_vecs = [
                self.vectors[t.track_id]
                for t in attributed_tracks
                if t.track_id in self.vectors
            ]
            if not centroid_vecs:
                log.debug("style_queries: no vectors for composer '%s'", composer_id)
                return []
            centroid = _mean_vector(centroid_vecs)

        # Score all tracks
        results: list[TrackResult] = []
        for track_id, vec in self.vectors.items():
            track = self.graph.get_track(track_id)
            if not track:
                continue
            sim = _cosine(centroid, vec)
            if sim < min_confidence:
                continue
            # Find primary composer attribution
            composers_for_track = self.graph.composers_for_track(track_id)
            primary_c = composers_for_track[0].composer_id if composers_for_track else None
            results.append(TrackResult(
                track_id=track_id,
                title=track.title,
                composer_id=primary_c,
                score=sim,
            ))

        results.sort(key=lambda r: -r.score)
        return results[:k]

    # -----------------------------------------------------------------------
    # Composers with overlapping fingerprint vectors
    # -----------------------------------------------------------------------

    def composers_with_overlapping_vectors(
        self,
        composer_id: str,
        k: int = 10,
    ) -> list[ComposerResult]:
        """
        Find composers whose centroid vectors are most similar to the target.
        Uses composer fingerprint_vector if available, else computes from tracks.
        """
        target_vec = self._composer_vector(composer_id)
        if target_vec is None:
            return []

        results: list[ComposerResult] = []
        for c in self.graph.all_composers():
            if c.composer_id == composer_id:
                continue
            vec = self._composer_vector(c.composer_id)
            if vec is None:
                continue
            sim = _cosine(target_vec, vec)
            shared = _shared_style_traits(
                self.graph.get_composer(composer_id),
                c,
            )
            results.append(ComposerResult(
                composer_id=c.composer_id,
                full_name=c.full_name,
                score=sim,
                shared_traits=shared,
            ))

        results.sort(key=lambda r: -r.score)
        return results[:k]

    # -----------------------------------------------------------------------
    # Stylistic clusters within a soundtrack
    # -----------------------------------------------------------------------

    def stylistic_clusters_in_soundtrack(
        self,
        game_id:      str,
        n_clusters:   int | None = None,
        threshold:    float = 0.80,
    ) -> list[ClusterResult]:
        """
        Group tracks from a game into stylistic clusters using greedy cosine.
        Returns clusters sorted by cohesion (descending).
        """
        # Collect track IDs for this game
        game_tracks = [
            t for t in self.graph.all_tracks()
            if t.game_id == game_id and t.track_id in self.vectors
        ]
        if not game_tracks:
            return []

        track_ids  = [t.track_id for t in game_tracks]
        vecs       = [self.vectors[tid] for tid in track_ids]

        # Greedy cosine clustering
        raw_clusters = _greedy_cosine_clusters(track_ids, vecs, threshold)

        results = []
        for i, cluster_tids in enumerate(raw_clusters):
            c_vecs  = [self.vectors[tid] for tid in cluster_tids]
            centroid = _mean_vector(c_vecs)
            cohesion = _mean_cosine(c_vecs) if len(c_vecs) > 1 else 1.0

            # Collect composers for this cluster
            composers_seen: list[str] = []
            for tid in cluster_tids:
                for c in self.graph.composers_for_track(tid):
                    if c.composer_id not in composers_seen:
                        composers_seen.append(c.composer_id)

            results.append(ClusterResult(
                cluster_id=f"{game_id}_cluster_{i:02d}",
                track_ids=cluster_tids,
                centroid=[round(x, 4) for x in centroid],
                composers=composers_seen,
                cohesion=cohesion,
            ))

        results.sort(key=lambda c: -c.cohesion)
        return results

    # -----------------------------------------------------------------------
    # Composers sharing synthesis practices
    # -----------------------------------------------------------------------

    def composers_sharing_synthesis_practices(
        self,
        composer_id: str,
        k: int = 5,
    ) -> list[ComposerResult]:
        """
        Find composers who use similar synthesis practices based on style_traits.
        Matches: primary_chip, driver, technique keywords.
        """
        c_node = self.graph.get_composer(composer_id)
        if not c_node:
            return []

        target_chip   = c_node.style_traits.get("primary_chip", "")
        target_driver = c_node.style_traits.get("driver", "")

        results: list[ComposerResult] = []
        for c in self.graph.all_composers():
            if c.composer_id == composer_id:
                continue
            shared: list[str] = []
            if target_chip and c.style_traits.get("primary_chip") == target_chip:
                shared.append(f"chip:{target_chip}")
            if target_driver and c.style_traits.get("driver") == target_driver:
                shared.append(f"driver:{target_driver}")
            if not shared:
                continue

            score = len(shared) / 3.0   # max 3 shared traits for score=1
            results.append(ComposerResult(
                composer_id=c.composer_id,
                full_name=c.full_name,
                score=score,
                shared_traits=shared,
                notes="Matched synthesis practices",
            ))

        results.sort(key=lambda r: -r.score)
        return results[:k]

    # -----------------------------------------------------------------------
    # Influence chain traversal
    # -----------------------------------------------------------------------

    def composer_influence_chain(
        self,
        composer_id: str,
        depth: int = 3,
    ) -> list[str]:
        """
        BFS traversal of `influenced_by` edges up to `depth` hops.
        Returns ordered list of composer_ids (breadth-first).
        """
        visited: list[str] = []
        queue = [(composer_id, 0)]
        seen = {composer_id}

        while queue:
            current_id, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue
            for inf in self.graph.influenced_by(current_id):
                if inf.composer_id not in seen:
                    seen.add(inf.composer_id)
                    visited.append(inf.composer_id)
                    queue.append((inf.composer_id, current_depth + 1))

        return visited

    # -----------------------------------------------------------------------
    # Stylistic outliers
    # -----------------------------------------------------------------------

    def find_stylistic_outliers(
        self,
        game_id:   str,
        threshold: float = 0.50,
    ) -> list[TrackResult]:
        """
        Find tracks that are stylistically distant from the game's centroid.
        Returns tracks with cosine similarity to centroid below threshold.
        """
        game_tracks = [
            t for t in self.graph.all_tracks()
            if t.game_id == game_id and t.track_id in self.vectors
        ]
        if not game_tracks:
            return []

        all_vecs = [self.vectors[t.track_id] for t in game_tracks]
        centroid = _mean_vector(all_vecs)

        results: list[TrackResult] = []
        for t in game_tracks:
            sim = _cosine(centroid, self.vectors[t.track_id])
            if sim < threshold:
                composers = self.graph.composers_for_track(t.track_id)
                results.append(TrackResult(
                    track_id=t.track_id,
                    title=t.title,
                    composer_id=composers[0].composer_id if composers else None,
                    score=sim,
                    notes=f"Outlier: cosine={sim:.3f} < threshold={threshold}",
                ))

        results.sort(key=lambda r: r.score)  # lowest similarity first
        return results

    # -----------------------------------------------------------------------
    # Full query report
    # -----------------------------------------------------------------------

    def full_style_report(
        self,
        composer_id: str,
        game_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a complete style analysis report for a composer.
        """
        c = self.graph.get_composer(composer_id)
        if not c:
            return {"error": f"Composer '{composer_id}' not found"}

        report: dict[str, Any] = {
            "composer_id": composer_id,
            "full_name":   c.full_name,
        }

        report["similar_tracks"] = [
            r.to_dict() for r in self.tracks_similar_to_composer(composer_id, k=10)
        ]
        report["similar_composers"] = [
            r.to_dict() for r in self.composers_with_overlapping_vectors(composer_id, k=5)
        ]
        report["synthesis_peers"] = [
            r.to_dict() for r in self.composers_sharing_synthesis_practices(composer_id, k=5)
        ]
        report["influence_chain"] = self.composer_influence_chain(composer_id, depth=3)

        if game_id:
            report["soundtrack_clusters"] = [
                c.to_dict() for c in self.stylistic_clusters_in_soundtrack(game_id)
            ]
            report["stylistic_outliers"] = [
                r.to_dict() for r in self.find_stylistic_outliers(game_id)
            ]

        return report

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _composer_vector(self, composer_id: str) -> list[float] | None:
        c = self.graph.get_composer(composer_id)
        if not c:
            return None
        if c.fingerprint_vector:
            return c.fingerprint_vector
        tracks = self.graph.tracks_for_composer(composer_id)
        vecs = [self.vectors[t.track_id] for t in tracks if t.track_id in self.vectors]
        if not vecs:
            return None
        return _mean_vector(vecs)


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    n = _norm(a) * _norm(b)
    return _dot(a, b) / n if n > 1e-10 else 0.0


def _mean_vector(vecs: list[list[float]]) -> list[float]:
    if not vecs:
        return []
    dim = len(vecs[0])
    return [sum(v[i] for v in vecs) / len(vecs) for i in range(dim)]


def _mean_cosine(vecs: list[list[float]]) -> float:
    """Average pairwise cosine similarity."""
    if len(vecs) < 2:
        return 1.0
    centroid = _mean_vector(vecs)
    return sum(_cosine(centroid, v) for v in vecs) / len(vecs)


def _greedy_cosine_clusters(
    track_ids:  list[str],
    vecs:       list[list[float]],
    threshold:  float,
) -> list[list[str]]:
    """Simple greedy cosine clustering: assign each track to the nearest cluster."""
    clusters:  list[list[str]]        = []
    centroids: list[list[float]]      = []

    for tid, vec in zip(track_ids, vecs):
        best_idx  = -1
        best_sim  = threshold
        for i, centroid in enumerate(centroids):
            sim = _cosine(centroid, vec)
            if sim > best_sim:
                best_sim = sim
                best_idx = i

        if best_idx >= 0:
            clusters[best_idx].append(tid)
            # Update centroid incrementally
            cluster_vecs = [vecs[track_ids.index(t)] for t in clusters[best_idx]]
            centroids[best_idx] = _mean_vector(cluster_vecs)
        else:
            clusters.append([tid])
            centroids.append(list(vec))

    return clusters


def _shared_style_traits(a: Any, b: Any) -> list[str]:
    """Return list of style trait keys with matching values."""
    if not a or not b:
        return []
    shared = []
    for key in ("primary_chip", "driver", "nationality"):
        va = a.style_traits.get(key) or getattr(a, key, None)
        vb = b.style_traits.get(key) or getattr(b, key, None)
        if va and vb and va == vb:
            shared.append(f"{key}:{va}")
    return shared
