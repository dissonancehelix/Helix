"""
session.py — Phase 15: Session Management and Flight Deck Summary.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from .action_model import ActionItem, ActionRegistry

class SessionSummary:
    """Consolidated report of the current foobar session."""
    def __init__(self, context, actions: List[ActionItem]):
        self.context = context
        self.actions = actions

    def to_report(self) -> Dict[str, Any]:
        """Generate a human-ready summary."""
        np = self.context if self.context.context_type == "now_playing" else None
        
        report = {
            "status": "Session Active",
            "now_playing": {
                "title": np.track.title if np and np.track else "Stopped",
                "resolved": np.track.resolved if np and np.track else False,
                "partition": np.partition if np else None
            },
            "active_actions_count": len(self.actions),
            "suggested_next": [a.description for a in self.actions[:3]],
            "rationale": [a.rationale for a in self.actions[:2]]
        }
        return report

class SessionManager:
    def __init__(self, action_registry: ActionRegistry):
        self.registry = action_registry
        self._history: List[str] = [] # Track Helix IDs played

    def record_play(self, helix_id: str):
        self._history.append(helix_id)
        if len(self._history) > 100:
            self._history.pop(0)

    def get_summary(self, context) -> SessionSummary:
        # Filter registry for current context relevance
        relevant_actions = self.registry.get_all()
        return SessionSummary(context, relevant_actions)
