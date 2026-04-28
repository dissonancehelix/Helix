"""
retrieval_engine.py — Helix Music Reasoning: Taste Graph Retrieval.
Part of Phase 9.

Supports querying the Helix Taste Graph for nearest neighbors,
structural clusters, and cross-genre affinity.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music"
GRAPH_DB_PATH = LIB_ROOT / "taste_graph.db"
FIELD_INDEX_PATH = LIB_ROOT / ".field_index.json"


class RetrievalEngine:
    """
    Engine for retrieving tracks from the Taste Graph (SQLite-backed).
    """

    def __init__(self):
        self.field_index = {}
        self._db_available = GRAPH_DB_PATH.exists()
        if FIELD_INDEX_PATH.exists():
            with open(FIELD_INDEX_PATH, "r", encoding="utf-8") as f:
                self.field_index = json.load(f)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(GRAPH_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def get_nearest_neighbors(self, track_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the top-N nearest neighbors for a track."""
        if not self._db_available:
            return []
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT target, weight, evidence FROM edges WHERE source = ? ORDER BY weight DESC LIMIT ?",
                (track_id, limit)
            ).fetchall()
        return [{"t": r["target"], "w": r["weight"], "e": json.loads(r["evidence"] or "{}")} for r in rows]

    def get_structural_cluster(self, tags: List[str], min_score: float = 0.5) -> List[str]:
        """
        Find tracks that carry a specific set of structural tags.
        Uses the field index if available, otherwise falls back to the graph.
        """
        pass

    def explain_similarity(self, source_id: str, target_id: str) -> str:
        """Provide a human-readable explanation for why two tracks are similar."""
        if not self._db_available:
            return "Taste graph not available."
        with self._conn() as conn:
            row = conn.execute(
                "SELECT evidence FROM edges WHERE source = ? AND target = ?",
                (source_id, target_id)
            ).fetchone()
        if not row:
            return "No direct similarity edge found in the top-K neighborhood."
        evidence = json.loads(row["evidence"] or "{}")
        parts = []
        if "shared_tags" in evidence:
            parts.append(f"shared structural tags ({', '.join(evidence['shared_tags'])})")
        if "shared_composers" in evidence:
            parts.append(f"shared authorship ({', '.join(evidence['shared_composers'])})")
        if "shared_franchise" in evidence:
            parts.append(f"shared franchise context ({evidence['shared_franchise']})")
        if "shared_album" in evidence:
            parts.append(f"common album ({evidence['shared_album']})")
        return "Clusters together due to: " + " and ".join(parts) + "." if parts else "Similar (no tagged evidence)."


if __name__ == "__main__":
    engine = RetrievalEngine()
    # print(engine.get_nearest_neighbors("music.track.10_000_bullets.04_d_o_l_l"))
