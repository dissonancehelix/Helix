"""
playlist_actions.py — Phase 15: Playlist Candidate Generation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from .action_model import ActionItem
from .context import MusicContext

class PlaylistGenerator:
    def __init__(self, taste_engine, bridge_db):
        self._taste = taste_engine
        self._db = bridge_db

    def generate_candidates(self, context: MusicContext, mode: str = "adjacent", limit: int = 15, partition_mode: str = "same") -> List[ActionItem]:
        """
        Generate a set of playlist candidates based on context and mode.
        Modes: adjacent, canon, exploratory.
        """
        if not context.track or not context.track.helix_id:
            return []

        seed_id = context.track.helix_id
        partition = context.partition if partition_mode == "same" else (partition_mode if partition_mode != "all" else None)
        
        actions = []
        
        if mode == "adjacent":
            neighbors = self._taste.get_neighbors(seed_id, limit=limit, partition=partition)
            description = f"Adjacent tracks to '{context.track.title}'"
            actions.append(ActionItem(
                type="playlist_candidate",
                category="Playlist",
                description=description,
                target_id=seed_id,
                metadata={"tracks": [n.track_id for n in neighbors], "mode": "adjacent"},
                rationale=f"Helix found {len(neighbors)} tracks sharing structural traits with the current seed.",
                context_type=context.context_type
            ))
            
        elif mode == "canon":
            # For each tag in seed, get canon
            tags = self._taste._db.get_semantic_tags(context.track.helix_id)
            for tag in tags[:2]: # Top 2 tags to avoid clutter
                canon = self._taste.extract_canon(tag, limit=5, partition=partition)
                if canon:
                    actions.append(ActionItem(
                        type="canon_candidate",
                        category="Canon",
                        description=f"Canon tracks for structural role: {tag}",
                        target_id=seed_id,
                        metadata={"tracks": canon, "tag": tag},
                        rationale=f"'{tag}' is a key structural component of the current context. These are its hallmarks.",
                        context_type=context.context_type
                    ))

        elif mode == "exploratory":
            # BFS expansion
            exploratory = self._taste.generate_playlist(seed_id, depth=2, limit=limit)
            actions.append(ActionItem(
                type="playlist_candidate",
                category="Playlist",
                description=f"Exploratory set starting from '{context.track.title}'",
                target_id=seed_id,
                metadata={"tracks": exploratory, "mode": "exploratory"},
                rationale="Breadth-first search across the taste-graph to find less obvious structural neighbors.",
                context_type=context.context_type
            ))

        return actions
