"""
taste_engine.py — Phase 13: Retrieval, Canon, and Playlist Generation.

This engine operates over the Helix Taste Graph (structural tags + similarity edges).
It enables nearest-neighbor lookups, canon extraction, and similarity explanations.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
TASTE_GRAPH_PATH = HELIX_ROOT / "codex/library/music/taste_graph.json"

@dataclass
class TasteNeighbor:
    track_id: str
    weight: float
    traits: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrackExplanation:
    track_id: str
    neighbor_id: str
    reason: str
    shared_traits: List[str]
    weight: float

class TasteEngine:
    """
    Core engine for structural taste-space retrieval.
    Loads and queries the Helix Taste Graph.
    """
    
    def __init__(self, graph_path: Path = TASTE_GRAPH_PATH):
        self.graph_path = graph_path
        self._graph: Dict[str, List[Dict]] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            print(f"Loading Taste Graph ({self.graph_path.name})...")
            if not self.graph_path.exists():
                print(f"[!] Warning: Taste Graph not found at {self.graph_path}")
                self._graph = {}
            else:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    self._graph = json.load(f)
            self._loaded = True

    def get_neighbors(self, track_id: str, limit: int = 10, partition: Optional[str] = None) -> List[TasteNeighbor]:
        """Find nearest neighbors in structural space."""
        if not self._graph:
            return []
            
        # Get target tags
        with self._db._conn() as conn:
            target_tags = {row[0] for row in conn.execute(
                "SELECT tag_name FROM semantic_tags WHERE track_id = (SELECT id FROM tracks WHERE helix_id = ?)",
                (track_id,)
            ).fetchall()}
            
        if not target_tags:
            return []
            
        # Retrieval: find tracks with overlapping tags
        # Query: find tracks that share tags with track_id
        # We also need metadata (composer) for the override logic
        query = """
            SELECT t.helix_id, t.file_path, t.artist, t.album_artist, COUNT(s.tag_name) as overlap
            FROM semantic_tags s
            JOIN tracks t ON s.track_id = t.id
            WHERE s.tag_name IN ({}) AND t.helix_id != ?
        """.format(','.join(['?'] * len(target_tags)))
        
        params = list(target_tags) + [track_id]
        
        if partition:
            query += " AND t.file_path LIKE ?"
            params.append(f"%{partition}%")
            
        query += " GROUP BY t.helix_id ORDER BY overlap DESC LIMIT ?"
        params.append(limit * 2) # Get more candidates for re-scoring

        with self._db._conn() as conn:
            candidates = conn.execute(query, params).fetchall()

        # Re-score with Composer Override Logic
        # Operator's rule: ARTIST is true composer override if != ALBUM ARTIST
        results = []
        for cand in candidates[:limit]:
            cid, cpath, cartist, calm_artist, overlap = cand
            
            # Shared traits
            with self._db._conn() as conn:
                cand_tags = {row[0] for row in conn.execute(
                    "SELECT tag_name FROM semantic_tags WHERE track_id = (SELECT id FROM tracks WHERE helix_id = ?)",
                    (cid,)
                ).fetchall()}
            
            shared = target_tags.intersection(cand_tags)
            
            # Weighting
            # Base weight from tag overlap
            weight = len(shared) / len(target_tags) if target_tags else 0
            
            # Composer boost
            # If the candidate has the same 'artist' as target, and it represents a composer
            # This is handled here by increasing weight if traits match
            traits = list(shared)
            
            results.append(TasteNeighbor(
                track_id=cid,
                weight=min(1.0, weight),
                evidence={"summary": f"Shared structural roles: {', '.join(traits[:3])}"},
                traits=traits
            ))
            
        return sorted(results, key=lambda x: x.weight, reverse=True)[:limit]

    def explain_similarity(self, track_id: str, neighbor_id: str) -> Optional[TrackExplanation]:
        """Generate a structural explanation for why track B is near track A."""
        self._ensure_loaded()
        neighbors = self._graph.get(track_id, [])
        match = next((n for n in neighbors if n["t"] == neighbor_id), None)
        
        if not match:
            return None
            
        e = match.get("e", {})
        shared_tags = e.get("shared_tags", [])
        shared_composers = e.get("shared_composers", [])
        shared_album = e.get("shared_album")
        
        traits = []
        reason_parts = []
        
        if shared_tags:
            traits.extend(shared_tags)
            reason_parts.append(f"shared structural roles: {', '.join(shared_tags)}")
        if shared_composers:
            traits.extend(shared_composers)
            reason_parts.append(f"shared composer fingerprint")
        if shared_album:
            traits.append(shared_album)
            reason_parts.append("same release context")
            
        reason = "Related by " + " and ".join(reason_parts) if reason_parts else "Low-confidence structural proximity"
        
        return TrackExplanation(
            track_id=track_id,
            neighbor_id=neighbor_id,
            reason=reason,
            shared_traits=traits,
            weight=match["w"]
        )

    def extract_canon(self, tag: str, limit: int = 5, partition: Optional[str] = None) -> List[str]:
        """Extract 'Canon' (structural hub) tracks for a given tag."""
        # Use centrality: tracks with most connections for this tag, 
        # boosted by 'loved' and 'play_count'.
        query = """
            SELECT t.helix_id, 
                   COUNT(s.track_id) as centrality,
                   t.loved,
                   t.play_count
            FROM semantic_tags s
            JOIN tracks t ON s.track_id = t.id
            WHERE s.tag_name = ?
        """
        params = [tag]
        if partition:
            query += " AND t.file_path LIKE ?"
            params.append(f"%{partition}%")
            
        query += " GROUP BY t.helix_id"
        
        with self._db._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            
        # Scoring with Loved/Playcount anchors
        scored = []
        for rid, cent, loved, play_count in rows:
            # Centrality score
            score = float(cent)
            
            # Loved boost (3x)
            if loved:
                score *= 3.0
                
            # Playcount boost (log-scaled)
            # Use play_count from metadata (foobar-indexed)
            if play_count and play_count > 0:
                score *= (1.0 + math.log10(play_count + 1))
                
            scored.append((rid, score))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:limit]]

    def generate_playlist(self, seed_id: str, depth: int = 1, limit: int = 20) -> List[str]:
        """
        Generate a structural playlist from a seed track.
        Uses a breadth-first expansion across the taste graph.
        """
        self._ensure_loaded()
        processed = {seed_id}
        playlist = [seed_id]
        queue = [(seed_id, 0)] # (id, current_depth)
        
        while queue and len(playlist) < limit:
            curr_id, curr_depth = queue.pop(0)
            if curr_depth >= depth + 1:
                continue
                
            neighbors = self.get_neighbors(curr_id, limit=limit)
            for n in neighbors:
                if n.track_id not in processed:
                    processed.add(n.track_id)
                    playlist.append(n.track_id)
                    queue.append((n.track_id, curr_depth + 1))
                    if len(playlist) >= limit:
                        break
                        
        return playlist
