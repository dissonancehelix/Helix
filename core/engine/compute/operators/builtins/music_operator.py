"""
music_operator.py — HSL implementation of the Music reasoning layer.
Routes HSL commands to the domains/music/model bridge and operator.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from core.engine.operators.base import BaseOperator

class MusicOperatorImpl(BaseOperator):
    """
    HSL Operator for Music reasoning and Beefweb interaction.
    
    Syntax:
        RUN operator:MUSIC subcommand:<now_playing|explain|neighbors|actions|approve|execute> [params...]
    """

    def __init__(self) -> None:
        # Lazy import to avoid circularities and ensure bridge state is fresh
        from domains.music.bridge.bridge import HelixBridge
        # Credentials from the operator session (hardcoded here for now as requested)
        self.bridge = HelixBridge(beefweb_username="dissonance", beefweb_password="Helix")

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sub = payload.get("subcommand", "").lower()
        
        def _to_json_safe(obj):
            if hasattr(obj, "to_dict"): return obj.to_dict()
            if hasattr(obj, "__dataclass_fields__"):
                from dataclasses import asdict
                return asdict(obj)
            return obj

        if sub == "now_playing":
            np = self.bridge.get_now_playing()
            return {
                "status": "ok",
                "summary": np.summary() if np else "Stopped",
                "track": _to_json_safe(np) if np else None
            }
        
        elif sub == "explain":
            source = payload.get("source", "playing")
            exp = self.bridge.explain(source)
            return {"status": "ok", "explanation": exp}
            
        elif sub == "neighbors":
            limit = int(payload.get("limit", 5))
            near = self.bridge.nearest(limit=limit)
            return {"status": "ok", "neighbors": near}
            
        elif sub == "actions":
            status = payload.get("status", "staged")
            actions = self.bridge.list_staged_actions(status=status)
            return {"status": "ok", "actions": actions}
            
        elif sub == "approve":
            action_id = payload.get("id")
            if not action_id:
                return {"status": "error", "error": "Approve requires id:<id>"}
            success = self.bridge.approve_action(action_id, note="Approved via HSL.")
            return {"status": "ok", "success": success}
            
        elif sub == "execute":
            action_id = payload.get("id")
            if not action_id:
                return {"status": "error", "error": "Execute requires id:<id>"}
            result = self.bridge.execute_action(action_id)
            return {"status": "ok", "result": result}
            
        return {"status": "error", "error": f"Unknown MUSIC subcommand: {sub}"}

