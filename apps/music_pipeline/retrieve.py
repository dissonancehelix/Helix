from __future__ import annotations
from typing import Optional, List, Dict, Any
from .context import MusicContext

class Retriever:
    def __init__(self, taste_engine, bridge_db):
        self._taste = taste_engine
        self._db = bridge_db

    def get_neighbors(self, context: MusicContext, limit: int = 10, partition_mode: str = "all") -> List[Dict[str, Any]]:
        if not context.track or not context.track.helix_id:
            return []
        partition = context.partition if partition_mode == "same" else (partition_mode if partition_mode != "all" else None)
        neighbors = self._taste.get_neighbors(context.track.helix_id, limit=limit, partition=partition)
        results = []
        for n in neighbors:
            results.append({"id": n.track_id, "weight": n.weight, "traits": n.traits, "evidence": n.evidence})
        return results
