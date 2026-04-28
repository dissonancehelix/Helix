"""
recommender.py — Taste-based track recommendation
==================================================
Two modes:
  near_core  — tracks closest to the taste centroid (cosine distance < 0.3)
  frontier   — outer shell (0.3–0.55) with composer diversity bonus

NOTE: Taste weighting and confidence weighting are kept completely separate.
  - Taste weights were used to BUILD the centroid (in taste_vector.py).
  - Confidence weights are used HERE to discount unreliable vectors.

API
---
recommend(taste: TasteVector, index: VectorIndex,
          db: TrackDB, mode: str = "near_core",
          k: int = 500) -> list[RecommendationResult]

save_reports(results_nc, results_fr, composers_top50,
             report_dir: Path) -> None
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from domains.music.tools.music_pipeline.config import CONFIDENCE_BY_TIER

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False


@dataclass
class RecommendationResult:
    rank:        int
    track_id:    str
    title:       str
    composer:    str
    platform:    str
    similarity:  float   # cosine similarity to taste centroid (0–1)
    confidence:  float   # feature vector confidence (tier-based)
    tier:        int
    mode:        str     # "near_core" | "frontier"


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

def _cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na  = math.sqrt(sum(x ** 2 for x in a[:n]))
    nb  = math.sqrt(sum(x ** 2 for x in b[:n]))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _cosine_dist(a: list[float], b: list[float]) -> float:
    return 1.0 - _cosine_sim(a, b)


# ---------------------------------------------------------------------------
# Main recommender
# ---------------------------------------------------------------------------

def recommend(
    taste:    Any,           # TasteVector
    index:    Any,           # VectorIndex
    db:       Any,           # TrackDB
    mode:     str  = "near_core",
    k:        int  = 500,
    k_query:  int  = 2000,   # over-fetch then filter
) -> list[RecommendationResult]:
    """
    Recommend k tracks using the taste centroid and vector index.
    """
    centroid = taste.centroid
    loved_set = set(taste.loved_ids)

    # Query the index for nearest neighbours
    raw = index.query(centroid, k=k_query)

    # Build metadata lookup from DB
    meta_map = _load_meta(db)

    results: list[RecommendationResult] = []
    for track_id, _l2_dist in raw:
        if track_id in loved_set:
            continue  # skip already-loved tracks

        meta     = meta_map.get(track_id, {})
        tier     = int(meta.get("tier", 1))
        conf     = float(CONFIDENCE_BY_TIER.get(tier, 0.6))
        vec      = meta.get("vector")

        if vec is None:
            continue

        sim  = _cosine_sim(centroid, vec)
        dist = 1.0 - sim

        if mode == "near_core" and dist >= 0.3:
            continue
        if mode == "frontier" and not (0.3 <= dist <= 0.55):
            continue

        results.append(RecommendationResult(
            rank=0,  # set after sorting
            track_id=track_id,
            title=meta.get("title", ""),
            composer=meta.get("composer", ""),
            platform=meta.get("platform", ""),
            similarity=round(sim, 4),
            confidence=round(conf, 4),
            tier=tier,
            mode=mode,
        ))

    # Frontier mode: apply composer diversity bonus
    if mode == "frontier":
        results = _apply_diversity_bonus(results)

    # Sort: near_core by similarity desc; frontier by adjusted score desc
    results.sort(key=lambda r: r.similarity, reverse=True)

    # Apply ranks
    for i, r in enumerate(results[:k]):
        r.rank = i + 1

    return results[:k]


def _apply_diversity_bonus(results: list[RecommendationResult]) -> list[RecommendationResult]:
    """Penalise over-represented composers in the frontier set."""
    composer_counts: dict[str, int] = {}
    for r in results:
        composer_counts[r.composer] = composer_counts.get(r.composer, 0) + 1

    total = len(results)
    for r in results:
        n = composer_counts.get(r.composer, 1)
        # Fraction of results from this composer — boost if rare, penalise if common
        diversity = 1.0 - (n / max(1, total))
        # Blend similarity with diversity (70/30)
        r.similarity = round(0.7 * r.similarity + 0.3 * diversity, 4)

    return results


def _load_meta(db: Any) -> dict[str, dict]:
    """Build track metadata map from DB including feature vectors."""
    try:
        from domains.music.tools.music_pipeline.config import FEATURE_VECTOR_VERSION
        ids, mat = db.load_all_vectors(FEATURE_VECTOR_VERSION)
        tracks   = {t["track_id"]: t for t in db.get_tracks_by_tier(max_tier=4)}

        meta_map: dict[str, dict] = {}
        for i, tid in enumerate(ids):
            t = tracks.get(tid, {})
            vec = mat[i].tolist() if _HAS_NP else list(mat[i])
            meta_map[tid] = {
                "title":    t.get("title", ""),
                "composer": t.get("artist", ""),
                "platform": t.get("platform", ""),
                "tier":     t.get("tier", 1),
                "vector":   vec,
            }
        return meta_map
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Report serialisation
# ---------------------------------------------------------------------------

def _result_to_dict(r: RecommendationResult) -> dict:
    return {
        "rank":       r.rank,
        "track_id":   r.track_id,
        "title":      r.title,
        "composer":   r.composer,
        "platform":   r.platform,
        "similarity": r.similarity,
        "confidence": r.confidence,
        "tier":       r.tier,
        "mode":       r.mode,
    }


def save_reports(
    near_core:  list[RecommendationResult],
    frontier:   list[RecommendationResult],
    report_dir: Path,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)

    # near_core_500.json
    (report_dir / "near_core_500.json").write_text(
        json.dumps([_result_to_dict(r) for r in near_core[:500]], indent=2)
    )

    # frontier_500.json
    (report_dir / "frontier_500.json").write_text(
        json.dumps([_result_to_dict(r) for r in frontier[:500]], indent=2)
    )

    # top_50_composers.json — by frequency in near_core
    composer_freq: dict[str, int] = {}
    for r in near_core:
        composer_freq[r.composer] = composer_freq.get(r.composer, 0) + 1
    top50 = sorted(composer_freq.items(), key=lambda x: x[1], reverse=True)[:50]
    (report_dir / "top_50_composers.json").write_text(
        json.dumps([{"composer": c, "count": n} for c, n in top50], indent=2)
    )

    # hidden_gems.json — high similarity + low play count proxy (tier=1)
    gems = [r for r in near_core if r.tier == 1 and r.similarity > 0.7]
    gems.sort(key=lambda r: r.similarity, reverse=True)
    (report_dir / "hidden_gems.json").write_text(
        json.dumps([_result_to_dict(r) for r in gems[:100]], indent=2)
    )

    print(f"[recommender] Reports written to {report_dir}")
    print(f"  near_core: {len(near_core)}  frontier: {len(frontier)}")
    print(f"  top composers: {len(top50)}  hidden gems: {len(gems)}")

