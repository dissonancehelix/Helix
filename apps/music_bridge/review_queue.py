"""
review_queue.py — Phase 12: Manual Review Queue Management.

Storage: codex/staging/music/review_queue.json
Purpose: Holds candidates requiring human judgment before auto-acceptance.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from .alias_graph import Candidate, Evidence, Contradiction

REVIEW_QUEUE_PATH = Path("C:/Users/dissonance/Desktop/Helix/codex/staging/music/review_queue.json")

class ReviewQueue:
    """Manages candidates needing human judgment."""
    
    def __init__(self, path: Path = REVIEW_QUEUE_PATH):
        self.path = path
        self.queue: List[Candidate] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.queue = []
                    for c_dict in data.get("queue", []):
                        # Extract nested objects
                        ev_data = c_dict.pop("evidence", {})
                        co_data = c_dict.pop("contradictions", {})
                        ev = Evidence(**ev_data)
                        co = Contradiction(**co_data)
                        c = Candidate(evidence=ev, contradictions=co, **c_dict)
                        self.queue.append(c)
            except Exception as e:
                print(f"Failed to load review queue: {e}")
                self.queue = []

    def add(self, candidate: Candidate):
        """Add a candidate to the queue if it's Tier B or C (uncertain/ambiguous)."""
        if candidate.tier in ("TIER_B", "TIER_C"):
            # Avoid duplicates by (local_id, external_id)
            if not any(c.local_id == candidate.local_id and c.external_id == candidate.external_id for c in self.queue):
                # Calculate priority & risk for Phase 12.5
                priority = self._calculate_priority(candidate)
                # Store extra metadata in a 'review_metadata' field if needed, or just notes
                candidate.provenance += f" | Priority: {priority}"
                self.queue.append(candidate)

    def _calculate_priority(self, c: Candidate) -> str:
        """Calculate manual review priority score (HIGH | MED | LOW)."""
        ev = c.evidence
        # HIGH: Strong evidence but maybe a slight year mismatch or manual preference
        if ev.alias_match == "exact" and (ev.artist_match and ev.track_count_overlap > 0.5):
            return "HIGH"
        # MED: Normalized match, moderate overlap
        if ev.alias_match in ("exact", "normalized") and ev.track_count_overlap > 0.3:
            return "MED"
        # LOW: Remote evidence (Fuzzy alias, low overlap)
        return "LOW"

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Sort queue by priority for the human operator
        prio_map = {"HIGH": 0, "MED": 1, "LOW": 2}
        sorted_queue = sorted(self.queue, key=lambda c: prio_map.get(c.provenance.split("Priority: ")[-1], 2))
        
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "count": len(sorted_queue),
            "tier_counts": {
                "TIER_B": len([c for c in sorted_queue if c.tier == "TIER_B"]),
                "TIER_C": len([c for c in sorted_queue if c.tier == "TIER_C"]),
            },
            "priority_counts": {
                "HIGH": len([c for c in sorted_queue if "Priority: HIGH" in c.provenance]),
                "MED":  len([c for c in sorted_queue if "Priority: MED" in c.provenance]),
                "LOW":  len([c for c in sorted_queue if "Priority: LOW" in c.provenance]),
            },
            "queue": [c.to_dict() for c in sorted_queue]
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Review queue saved (upgraded): {self.path}")

    @property
    def candidate_count(self) -> int:
        return len(self.queue)
