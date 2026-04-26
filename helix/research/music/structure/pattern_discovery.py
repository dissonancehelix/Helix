"""
pattern_discovery.py — Pattern Discovery Engine (Layer 8)
==========================================================
Applies clustering and network analysis to composer fingerprint vectors
to discover:
  - composer style clusters (HDBSCAN primary, k-means fallback)
  - recurring motif families (from melodic n-gram hashes)
  - shared synthesis palettes (algorithm/TL distribution clusters)
  - track similarity network (edges = cosine similarity above threshold)

API
---
discover(track_ids, vectors, labels=None, melodic_features=None) -> PatternResult
"""

from __future__ import annotations

import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------

try:
    import numpy as _np
    _HAS_NUMPY = True
except ImportError:
    _np = None  # type: ignore
    _HAS_NUMPY = False

try:
    import hdbscan as _hdbscan
    _HAS_HDBSCAN = True
except ImportError:
    _hdbscan = None  # type: ignore
    _HAS_HDBSCAN = False

try:
    from sklearn.cluster import KMeans as _KMeans
    from sklearn.metrics import silhouette_score as _silhouette_score
    _HAS_SKLEARN = True
except ImportError:
    _KMeans = None
    _silhouette_score = None
    _HAS_SKLEARN = False

try:
    import networkx as _nx
    _HAS_NETWORKX = True
except ImportError:
    _nx = None  # type: ignore
    _HAS_NETWORKX = False


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ClusterResult:
    algorithm:   str              # "hdbscan" | "kmeans" | "cosine_greedy"
    labels:      list[int]        # cluster label per track (-1 = noise in HDBSCAN)
    n_clusters:  int
    silhouette:  float | None = None   # overall silhouette score
    cluster_info: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm":   self.algorithm,
            "n_clusters":  self.n_clusters,
            "silhouette":  round(self.silhouette, 4) if self.silhouette is not None else None,
            "noise_count": sum(1 for l in self.labels if l == -1),
            "clusters":    self.cluster_info,
        }


@dataclass
class SimilarityEdge:
    source:     str
    target:     str
    similarity: float


@dataclass
class PatternResult:
    track_ids:    list[str]
    labels:       list[str | None]  # composer labels (ground truth where known)

    # Clustering
    hdbscan_result:  ClusterResult | None = None
    kmeans_result:   ClusterResult | None = None
    cosine_clusters: ClusterResult | None = None   # greedy cosine (always available)

    # Track similarity network
    similarity_edges:         list[SimilarityEdge] = field(default_factory=list)
    similarity_threshold:     float = 0.80
    network_density:          float | None = None
    network_components:       int | None = None
    network_modularity:       float | None = None

    # Motif families (from melodic n-gram hashes across tracks)
    motif_families:           list[dict[str, Any]] = field(default_factory=list)

    # Synthesis palette clusters (algorithm distribution similarity)
    synthesis_palette_groups: list[dict[str, Any]] = field(default_factory=list)

    tools_used: dict[str, bool] = field(default_factory=dict)
    errors:     dict[str, str]  = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_count":        len(self.track_ids),
            "tools_used":         self.tools_used,
            "hdbscan":            self.hdbscan_result.to_dict() if self.hdbscan_result else None,
            "kmeans":             self.kmeans_result.to_dict() if self.kmeans_result else None,
            "cosine_clusters":    self.cosine_clusters.to_dict() if self.cosine_clusters else None,
            "similarity_network": {
                "threshold":    self.similarity_threshold,
                "edge_count":   len(self.similarity_edges),
                "density":      round(self.network_density, 4) if self.network_density is not None else None,
                "components":   self.network_components,
                "modularity":   round(self.network_modularity, 4) if self.network_modularity is not None else None,
                "edges": [
                    {"source": e.source, "target": e.target, "similarity": round(e.similarity, 4)}
                    for e in self.similarity_edges
                ],
            },
            "motif_families":           self.motif_families,
            "synthesis_palette_groups": self.synthesis_palette_groups,
            "errors":                   self.errors,
        }


# ---------------------------------------------------------------------------
# Cosine helpers
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _build_sim_matrix_np(X: Any) -> Any:
    norms = _np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    Xn = X / norms
    M = Xn @ Xn.T
    _np.clip(M, -1.0, 1.0, out=M)
    return M


# ---------------------------------------------------------------------------
# Greedy cosine clustering (always available)
# ---------------------------------------------------------------------------

def _greedy_cosine_clusters(
    track_ids: list[str],
    vectors:   list[list[float]],
    threshold: float = 0.85,
) -> ClusterResult:
    n = len(track_ids)
    labels = [-1] * n
    cluster_id = 0
    clustered = set()

    for i in range(n):
        if i in clustered:
            continue
        members = [i]
        for j in range(i + 1, n):
            if j not in clustered and _cosine(vectors[i], vectors[j]) >= threshold:
                members.append(j)
        if len(members) > 1:
            for m in members:
                labels[m] = cluster_id
                clustered.add(m)
            cluster_id += 1

    # Build cluster info
    cluster_map: dict[int, list[str]] = defaultdict(list)
    for i, lbl in enumerate(labels):
        if lbl >= 0:
            cluster_map[lbl].append(track_ids[i])

    info = [
        {"cluster_id": k, "members": v, "size": len(v)}
        for k, v in sorted(cluster_map.items())
    ]

    return ClusterResult(
        algorithm="cosine_greedy",
        labels=labels,
        n_clusters=cluster_id,
        cluster_info=info,
    )


# ---------------------------------------------------------------------------
# HDBSCAN clustering
# ---------------------------------------------------------------------------

def _run_hdbscan(
    X: Any,
    track_ids: list[str],
    min_cluster_size: int = 2,
    min_samples: int = 1,
) -> ClusterResult:
    clusterer = _hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
    )
    lbls = clusterer.fit_predict(X)
    labels = [int(l) for l in lbls]
    n_clusters = max(labels) + 1 if max(labels) >= 0 else 0

    # Silhouette (exclude noise points)
    sil = None
    non_noise = [i for i, l in enumerate(labels) if l >= 0]
    if len(non_noise) >= 4 and _HAS_SKLEARN and len(set(labels[i] for i in non_noise)) >= 2:
        try:
            sil = float(_silhouette_score(X[non_noise], [labels[i] for i in non_noise]))
        except Exception:
            pass

    # Cluster info
    cluster_map: dict[int, list[str]] = defaultdict(list)
    for i, lbl in enumerate(labels):
        if lbl >= 0:
            cluster_map[lbl].append(track_ids[i])

    info = [
        {"cluster_id": k, "members": v, "size": len(v)}
        for k, v in sorted(cluster_map.items())
    ]

    return ClusterResult(
        algorithm="hdbscan",
        labels=labels,
        n_clusters=n_clusters,
        silhouette=sil,
        cluster_info=info,
    )


# ---------------------------------------------------------------------------
# k-means clustering
# ---------------------------------------------------------------------------

def _run_kmeans(
    X: Any,
    track_ids: list[str],
    k_range: range = range(2, 7),
    random_state: int = 42,
) -> ClusterResult:
    """Auto-select k by best silhouette score."""
    best_k = 2
    best_sil = -1.0
    best_labels = None

    for k in k_range:
        if k >= len(track_ids):
            break
        try:
            km = _KMeans(n_clusters=k, random_state=random_state, n_init=10)
            lbls = km.fit_predict(X)
            sil = float(_silhouette_score(X, lbls))
            if sil > best_sil:
                best_sil = sil
                best_k = k
                best_labels = [int(l) for l in lbls]
        except Exception:
            continue

    if best_labels is None:
        best_labels = [0] * len(track_ids)

    cluster_map: dict[int, list[str]] = defaultdict(list)
    for i, lbl in enumerate(best_labels):
        cluster_map[lbl].append(track_ids[i])

    info = [
        {"cluster_id": k, "members": v, "size": len(v)}
        for k, v in sorted(cluster_map.items())
    ]

    return ClusterResult(
        algorithm="kmeans",
        labels=best_labels,
        n_clusters=best_k,
        silhouette=best_sil if best_sil > -1 else None,
        cluster_info=info,
    )


# ---------------------------------------------------------------------------
# Similarity network
# ---------------------------------------------------------------------------

def _build_similarity_network(
    track_ids: list[str],
    vectors:   list[list[float]],
    threshold: float,
    sim_matrix: Any,
) -> tuple[list[SimilarityEdge], float | None, int | None, float | None]:
    """Build similarity network. Returns (edges, density, components, modularity)."""
    n = len(track_ids)
    edges: list[SimilarityEdge] = []

    for i in range(n):
        for j in range(i + 1, n):
            if _HAS_NUMPY:
                s = float(sim_matrix[i, j])
            else:
                s = _cosine(vectors[i], vectors[j])
            if s >= threshold:
                edges.append(SimilarityEdge(track_ids[i], track_ids[j], s))

    density = None
    components = None
    modularity = None

    if _HAS_NETWORKX:
        G = _nx.Graph()
        G.add_nodes_from(track_ids)
        for e in edges:
            G.add_edge(e.source, e.target, weight=e.similarity)

        possible_edges = n * (n - 1) / 2
        density = round(len(edges) / possible_edges, 4) if possible_edges > 0 else 0.0
        components = _nx.number_connected_components(G)

        # Modularity using community detection if available
        try:
            from networkx.algorithms import community as _nxc
            if G.number_of_edges() > 0:
                comms = list(_nxc.greedy_modularity_communities(G))
                modularity = round(float(_nxc.modularity(G, comms)), 4)
        except Exception:
            pass

    return edges, density, components, modularity


# ---------------------------------------------------------------------------
# Motif families (cross-track shared melodic n-grams)
# ---------------------------------------------------------------------------

def _find_motif_families(
    track_ids:       list[str],
    melodic_features: list[dict[str, Any] | None],
    min_tracks: int = 2,
) -> list[dict[str, Any]]:
    """
    Find melodic n-gram motifs shared across multiple tracks.
    melodic_features: list of `layer2_melodic` dicts (or None) per track.
    Returns list of motif family dicts sorted by track_count desc.
    """
    # Collect n-gram hashes from each track's top_motifs
    motif_to_tracks: dict[str, list[str]] = defaultdict(list)

    for tid, mf in zip(track_ids, melodic_features):
        if not mf:
            continue
        # top_motifs is a list of {"ngram": [...], "count": int} or similar
        top_motifs = mf.get("top_motifs", [])
        if isinstance(top_motifs, list):
            for m in top_motifs:
                if isinstance(m, dict):
                    ngram = m.get("ngram") or m.get("hash")
                    if ngram is not None:
                        key = str(ngram)
                        motif_to_tracks[key].append(tid)
                elif isinstance(m, (list, tuple)):
                    key = str(list(m))
                    motif_to_tracks[key].append(tid)

    # Filter to shared motifs
    families = [
        {
            "motif":       motif,
            "track_count": len(tracks),
            "tracks":      sorted(set(tracks)),
        }
        for motif, tracks in motif_to_tracks.items()
        if len(set(tracks)) >= min_tracks
    ]
    families.sort(key=lambda x: -x["track_count"])
    return families[:20]


# ---------------------------------------------------------------------------
# Synthesis palette groups (algorithm distribution clustering)
# ---------------------------------------------------------------------------

def _synthesis_palette_groups(
    track_ids:     list[str],
    layer1_data:   list[dict[str, Any] | None],
    threshold: float = 0.90,
) -> list[dict[str, Any]]:
    """
    Group tracks by algorithm distribution similarity.
    Uses cosine similarity on their alg_dist vectors (8 bins, alg 0–7).
    """
    def alg_vec(l1: dict[str, Any] | None) -> list[float]:
        if not l1:
            return [0.0] * 8
        dist = l1.get("algorithm_dist", {})
        total = sum(dist.values()) or 1
        return [dist.get(str(i), dist.get(i, 0)) / total for i in range(8)]

    vecs = [alg_vec(l1) for l1 in layer1_data]
    clustered = set()
    groups: list[dict[str, Any]] = []

    for i in range(len(track_ids)):
        if i in clustered:
            continue
        members = [track_ids[i]]
        base = vecs[i]
        for j in range(i + 1, len(track_ids)):
            if j not in clustered and _cosine(base, vecs[j]) >= threshold:
                members.append(track_ids[j])
                clustered.add(j)
        if len(members) > 1:
            clustered.add(i)
            groups.append({
                "members":      members,
                "size":         len(members),
                "dominant_alg": int(base.index(max(base))),
            })

    groups.sort(key=lambda g: -g["size"])
    return groups


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def discover(
    track_ids:        list[str],
    vectors:          list[list[float]],
    labels:           list[str | None] | None = None,
    melodic_features: list[dict[str, Any] | None] | None = None,
    layer1_data:      list[dict[str, Any] | None] | None = None,
    sim_threshold:    float = 0.80,
    hdbscan_min_size: int = 2,
    kmeans_k_range:   range = range(2, 7),
    random_state:     int = 42,
) -> PatternResult:
    """
    Run full pattern discovery on a set of track fingerprint vectors.

    track_ids: list of track name strings
    vectors:   parallel list of 56-dim (or N-dim) fingerprint vectors
    labels:    optional composer ground truth per track
    melodic_features: list of layer2_melodic dicts for motif family detection
    layer1_data:      list of layer1 dicts for synthesis palette grouping
    """
    n = len(track_ids)
    if labels is None:
        labels = [None] * n

    result = PatternResult(
        track_ids=list(track_ids),
        labels=list(labels),
        similarity_threshold=sim_threshold,
        tools_used={
            "numpy":    _HAS_NUMPY,
            "hdbscan":  _HAS_HDBSCAN,
            "sklearn":  _HAS_SKLEARN,
            "networkx": _HAS_NETWORKX,
        },
    )

    if n < 2:
        result.errors["all"] = "need ≥2 tracks for pattern discovery"
        return result

    # Precompute similarity matrix (numpy fast path)
    sim_matrix = None
    if _HAS_NUMPY:
        X = _np.array(vectors, dtype=float)
        sim_matrix = _build_sim_matrix_np(X)

    # --- Cosine greedy clustering (always) ---
    result.cosine_clusters = _greedy_cosine_clusters(track_ids, vectors, threshold=0.85)

    # --- HDBSCAN ---
    if _HAS_HDBSCAN and _HAS_NUMPY and n >= 4:
        try:
            result.hdbscan_result = _run_hdbscan(
                X, track_ids,
                min_cluster_size=hdbscan_min_size,
            )
        except Exception as exc:
            result.errors["hdbscan"] = str(exc)
            log.debug("HDBSCAN error: %s", exc)

    # --- k-means ---
    if _HAS_SKLEARN and _HAS_NUMPY and n >= 4:
        try:
            result.kmeans_result = _run_kmeans(
                X, track_ids,
                k_range=kmeans_k_range,
                random_state=random_state,
            )
        except Exception as exc:
            result.errors["kmeans"] = str(exc)
            log.debug("k-means error: %s", exc)

    # --- Similarity network ---
    try:
        edges, density, components, modularity = _build_similarity_network(
            track_ids, vectors, sim_threshold, sim_matrix
        )
        result.similarity_edges    = edges
        result.network_density     = density
        result.network_components  = components
        result.network_modularity  = modularity
    except Exception as exc:
        result.errors["similarity_network"] = str(exc)
        log.debug("similarity network error: %s", exc)

    # --- Motif families ---
    if melodic_features:
        try:
            result.motif_families = _find_motif_families(track_ids, melodic_features)
        except Exception as exc:
            result.errors["motif_families"] = str(exc)

    # --- Synthesis palette groups ---
    if layer1_data:
        try:
            result.synthesis_palette_groups = _synthesis_palette_groups(track_ids, layer1_data)
        except Exception as exc:
            result.errors["synthesis_palettes"] = str(exc)

    return result
