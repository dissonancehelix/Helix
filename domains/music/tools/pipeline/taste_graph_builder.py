"""
taste_graph_builder.py — Helix Music Reasoning: k-NN Similarity Graph Construction.
Part of Phase 9.

This script iterates over the Helix library, calculates pairwise similarity
using SimilarityEngine, and persists a k-Nearest-Neighbor graph to SQLite.
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music"
INDEX_PATH = LIB_ROOT / ".field_index.json"
GRAPH_DB_PATH = LIB_ROOT / "taste_graph.db"

sys.path.insert(0, str(HELIX_ROOT))
from model.domains.music.reasoning.similarity_engine import SimilarityEngine
from domains.music.tools.pipeline.signal_fuser import SignalFuser


def _open_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            source  TEXT NOT NULL,
            target  TEXT NOT NULL,
            weight  REAL NOT NULL,
            evidence TEXT,
            PRIMARY KEY (source, target)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON edges(source)")
    conn.commit()
    return conn


def migrate_json_to_db():
    """One-time migration: import taste_graph.json into taste_graph.db then remove it."""
    json_path = LIB_ROOT / "taste_graph.json"
    if not json_path.exists():
        return
    print(f"Migrating {json_path} → {GRAPH_DB_PATH}...")
    with open(json_path, "r", encoding="utf-8") as f:
        graph = json.load(f)
    conn = _open_db(GRAPH_DB_PATH)
    rows = []
    for source, neighbors in graph.items():
        for n in neighbors:
            rows.append((source, n["t"], n["w"], json.dumps(n.get("e", {}))))
    conn.executemany("INSERT OR REPLACE INTO edges VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()
    json_path.unlink()
    print(f"Migration complete. {len(rows)} edges written. taste_graph.json removed.")


def load_all_tracks() -> List[Dict[str, Any]]:
    """Load all track JSONs from the library."""
    tracks = []
    print(f"Loading library from {LIB_ROOT}...")
    for root, _, files in os.walk(LIB_ROOT):
        for fname in files:
            if not fname.endswith(".json") or fname.startswith("."):
                continue
            fpath = Path(root) / fname
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    tracks.append(json.load(f))
            except:
                continue
    print(f"Loaded {len(tracks)} tracks.")
    return tracks


def build_graph(k: int = 20):
    """
    Build a k-NN similarity graph and persist to SQLite.
    Optimized by grouping tracks by shared features (blocking).
    """
    # Run one-time migration if the old JSON file still exists
    migrate_json_to_db()

    tracks = load_all_tracks()
    engine = SimilarityEngine()

    # Load signal registry
    try:
        fuser = SignalFuser()
        signal_registry = fuser.run(verbose=False)
    except:
        signal_registry = {}
        print("Warning: SignalFuser failed or not available. Proceeding without signal layer.")

    # Attach signals to tracks temporarily for engine
    for t in tracks:
        tid = t.get("id")
        if tid in signal_registry:
            t["metadata"]["signal"] = {
                "lifetime_signal_score": signal_registry[tid].lifetime_signal_score,
                "active_rotation_score": signal_registry[tid].active_rotation_score
            }

    # Similarity Calculation
    # Strategy:
    # 1. Index tracks by Tags and ArtistIDs
    # 2. For each track, compare only with candidates sharing at least one tag or artist
    tag_to_tracks = {}
    artist_to_tracks = {}
    for i, t in enumerate(tracks):
        tags = t.get("semantic", {}).get("structural_tags", [])
        for tag in tags:
            tag_to_tracks.setdefault(tag, set()).add(i)

        artists = t.get("metadata", {}).get("artist_ids", [])
        for artist in artists:
            artist_to_tracks.setdefault(artist, set()).add(i)

    print(f"Computing similarity edges (k-NN) for {len(tracks)} tracks...")
    t0 = time.time()

    # Optional: limit for testing
    limit_tracks = int(os.getenv("HELIX_LIMIT", "5000"))
    process_subset = tracks[:limit_tracks]
    print(f"Limiting to first {limit_tracks} tracks for performance.")

    conn = _open_db(GRAPH_DB_PATH)
    batch = []
    total_edges = 0

    for i, t_a in enumerate(process_subset):
        tid_a = t_a.get("id")
        candidates = set()

        # Collect candidates from shared tags/artists
        tags = t_a.get("semantic", {}).get("structural_tags", [])
        for tag in tags:
            candidates |= tag_to_tracks.get(tag, set())

        artists = t_a.get("metadata", {}).get("artist_ids", [])
        for artist in artists:
            candidates |= artist_to_tracks.get(artist, set())

        candidates.discard(i)  # Don't compare to self

        # Calculate scores for candidates
        results = []
        for j in candidates:
            t_b = tracks[j]
            sim = engine.compute_similarity(t_a, t_b)
            if sim["total_score"] > 0.1:
                results.append((t_b.get("id"), sim))

        # Sort and take top K
        results.sort(key=lambda x: x[1]["total_score"], reverse=True)
        top_k = results[:k]

        for neighbor_id, sim in top_k:
            batch.append((
                tid_a,
                neighbor_id,
                sim["total_score"],
                json.dumps(sim["evidence"])
            ))

        if (i + 1) % 500 == 0:
            conn.executemany("INSERT OR REPLACE INTO edges VALUES (?,?,?,?)", batch)
            conn.commit()
            total_edges += len(batch)
            batch = []
            print(f"  Processed {i+1} / {len(process_subset)} tracks... ({total_edges} edges so far)")

    # Flush remainder
    if batch:
        conn.executemany("INSERT OR REPLACE INTO edges VALUES (?,?,?,?)", batch)
        conn.commit()
        total_edges += len(batch)

    conn.close()
    elapsed = time.time() - t0
    print(f"Taste Graph built in {elapsed:.1f}s. {total_edges} edges written to {GRAPH_DB_PATH}.")


if __name__ == "__main__":
    build_graph()

