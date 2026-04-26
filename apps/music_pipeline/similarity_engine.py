"""
similarity_engine.py — Helix Music Reasoning: Multi-weighted Similarity logic.
Part of Phase 9.

Calculates the "Helix Distance" between tracks based on structural evidence,
authorship, and signal layers.
"""
from __future__ import annotations
from typing import Dict, List, Set, Any, Optional

class SimilarityEngine:
    """
    Engine for computing pairwise similarity between tracks.
    
    Similarity Metric (0.0 - 1.0):
    - Structural Tags: 50% (Jaccard similarity of tags)
    - Composer/Artist: 25% (Identity match)
    - Context (Franchise/Release): 15% (Inherited context)
    - Signal affinity: 10% (Normalized playcount correlation)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "structural": 0.50,
            "authorship": 0.25,
            "context":    0.15,
            "signal":     0.10,
        }

    def compute_similarity(self, track_a: Dict[str, Any], track_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute weighted similarity between two track objects.
        Returns a result dict with total score and breakdown.
        """
        scores = {
            "structural": 0.0,
            "authorship": 0.0,
            "context":    0.0,
            "signal":     0.0
        }
        evidence = {}

        # 1. Structural Tags (Jaccard)
        tags_a = set(track_a.get("semantic", {}).get("structural_tags", []))
        tags_b = set(track_b.get("semantic", {}).get("structural_tags", []))
        if tags_a or tags_b:
            intersection = tags_a & tags_b
            union = tags_a | tags_b
            scores["structural"] = len(intersection) / len(union) if union else 0.0
            if intersection:
                evidence["shared_tags"] = sorted(list(intersection))

        # 2. Authorship (Composer IDs)
        auth_a = set(track_a.get("metadata", {}).get("artist_ids", []))
        auth_b = set(track_b.get("metadata", {}).get("artist_ids", []))
        if auth_a & auth_b:
            scores["authorship"] = 1.0
            evidence["shared_composers"] = sorted(list(auth_a & auth_b))
        
        # 3. Context (Franchise/Album)
        franch_a = track_a.get("metadata", {}).get("franchise_id")
        franch_b = track_b.get("metadata", {}).get("franchise_id")
        album_a = track_a.get("metadata", {}).get("album_id")
        album_b = track_b.get("metadata", {}).get("album_id")
        
        if franch_a and franch_a == franch_b:
            scores["context"] = 1.0
            evidence["shared_franchise"] = franch_a
        elif album_a and album_a == album_b:
            scores["context"] = 0.8
            evidence["shared_album"] = album_a

        # 4. Signal (Simplified correlation based on lifetime_signal_score)
        # Note: In a full implementation, we might use playcount trends.
        sig_a = track_a.get("metadata", {}).get("signal", {}).get("lifetime_signal_score", 0)
        sig_b = track_b.get("metadata", {}).get("signal", {}).get("lifetime_signal_score", 0)
        # Handle cases where signals are not yet fused into track JSON (Phase 8 fallback)
        if not sig_a: sig_a = 0
        if not sig_b: sig_b = 0
        
        score_diff = abs(sig_a - sig_b)
        scores["signal"] = 1.0 - (min(score_diff, 50) / 50.0) # Within 50 points of each other

        # Weighted Total
        total = sum(scores[k] * self.weights[k] for k in self.weights)
        
        return {
            "total_score": round(total, 4),
            "breakdown": scores,
            "evidence": evidence
        }

if __name__ == "__main__":
    # Test stub
    engine = SimilarityEngine()
    t1 = {"semantic": {"structural_tags": ["groove_engine", "FM"]}, "metadata": {"artist_ids": ["mitsuda"]}}
    t2 = {"semantic": {"structural_tags": ["groove_engine"]}, "metadata": {"artist_ids": ["mitsuda"]}}
    print(engine.compute_similarity(t1, t2))
