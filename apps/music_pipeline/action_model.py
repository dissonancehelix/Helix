"""
action_model.py — Phase 15: Action Layer Models.

Defines the structure for contextual actions and the session registry.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
import json
from typing import Optional, List, Dict, Any

@dataclass
class ActionItem:
    """A discrete actionable suggestion from Helix."""
    type: str           # e.g., "playlist_candidate", "repair_suggestion"
    category: str       # e.g., "Playlist", "Repair", "Canon"
    description: str
    target_id: str      # Helix ID or Album ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    confidence: float = 1.0
    context_type: str = "unknown"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    staged_ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "category": self.category,
            "description": self.description,
            "target_id": self.target_id,
            "metadata": self.metadata,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "context_type": self.context_type,
            "staged_ts": self.staged_ts
        }

class ActionRegistry:
    """In-memory registry for session-active actions."""
    def __init__(self):
        self._actions: Dict[str, ActionItem] = {}

    def add(self, action: ActionItem):
        self._actions[action.id] = action

    def clear(self):
        self._actions = {}

    def get_by_category(self, category: str) -> List[ActionItem]:
        return [a for a in self._actions.values() if a.category == category]

    def get_all(self) -> List[ActionItem]:
        return list(self._actions.values())
