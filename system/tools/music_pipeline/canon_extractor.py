"""
canon_extractor.py — Helix Music Reasoning: High-Signal Canon Identification.
Part of Phase 9.

Identifies the "canon" in each structural tag neighborhood by combining
graph centrality with lifetime signal scores.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music"
GRAPH_DB_PATH = LIB_ROOT / "taste_graph.db"
CANON_PATH = LIB_ROOT / "canon_sets.json"


class CanonExtractor:
    """
    Logic for identifying high-signal sets (canon).
    """

    def __init__(self, min_canon_score: float = 60.0):
        self.min_canon_score = min_canon_score
        self._db_available = GRAPH_DB_PATH.exists()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(GRAPH_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def extract_canon(self, verbose: bool = True):
        """
        Identify canon for each structural tag.
        """
        if not self._db_available:
            print("Taste graph DB not found. Run taste_graph_builder.py first.")
            return {}

        # 1. Reverse index: Tag -> {track_id: {centrality, count}}
        tag_neighborhoods: Dict[str, Dict[str, Any]] = {}

        with self._conn() as conn:
            for row in conn.execute("SELECT source, target, weight, evidence FROM edges"):
                shared_tags = json.loads(row["evidence"] or "{}").get("shared_tags", [])
                for tag in shared_tags:
                    node_stat = tag_neighborhoods.setdefault(tag, {})
                    entry = node_stat.setdefault(row["source"], {"centrality": 0.0, "count": 0})
                    entry["centrality"] += row["weight"]
                    entry["count"] += 1

        # 2. Score and rank
        canon_results = {}
        for tag, stats in tag_neighborhoods.items():
            scored_tracks = []
            for tid, s in stats.items():
                avg_centrality = s["centrality"] / s["count"] if s["count"] > 0 else 0
                score = avg_centrality * 100.0
                scored_tracks.append({
                    "track_id": tid,
                    "score": round(score, 2),
                    "neighborhood_size": s["count"]
                })

            scored_tracks.sort(key=lambda x: x["score"], reverse=True)
            canon_results[tag] = scored_tracks[:15]

            if verbose:
                print(f"Canon for {tag}: {len(canon_results[tag])} tracks identified.")

        # 3. Save
        with open(CANON_PATH, "w", encoding="utf-8") as f:
            json.dump(canon_results, f, indent=2)

        return canon_results


if __name__ == "__main__":
    extractor = CanonExtractor()
    extractor.extract_canon()
