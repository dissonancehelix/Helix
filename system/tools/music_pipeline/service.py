"""
service.py — Music Operator Unified Facade.

The primary entry point for high-level music reasoning and retrieval.
Integrates Context, Explain, Retrieve, Canon, and Diagnostics.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any, Union
from .context import NowPlayingContext, BrowseContext, LibraryContext, get_partition_from_path
from .explain import Explainer
from .retrieve import Retriever
from .canon import CanonManager
from .album_inspector import Inspector
from .diagnostics import MusicDiagnostics
from .action_model import ActionRegistry, ActionItem
from .playlist_actions import PlaylistGenerator
from .repair_actions import RepairDetector, StagingManager
from .session import SessionManager
from .executor import ExecutionEngine

class MusicOperator:
    def __init__(self, bridge):
        self._bridge = bridge # The HelixBridge instance
        self._db = bridge.db
        self._runtime = bridge.runtime
        self._taste = bridge.taste
        
        # Components
        self.explainer = Explainer(self._db, bridge.metadata)
        self.retriever = Retriever(self._taste, self._db)
        self.canon = CanonManager(self._taste)
        self.inspector = Inspector(self._db)
        self.diagnostics = MusicDiagnostics(self._db, self._runtime)
        
        # Action Layer (Phase 15)
        self.action_registry = ActionRegistry()
        self.playlist_gen = PlaylistGenerator(self._taste, self._db)
        self.repair_detect = RepairDetector(self._db)
        self.staging = StagingManager(self._db)
        self.session = SessionManager(self.action_registry)
        self.executor = ExecutionEngine(bridge)

    def get_current_context(self, source: str = "playing") -> Union[NowPlayingContext, BrowseContext]:
        """Derive the active context from the bridge runtime."""
        if source == "playing":
            track = self._bridge.get_now_playing()
            partition = get_partition_from_path(track.runtime.file_path) if track else None
            return NowPlayingContext(track=track, partition=partition)
        else:
            # Selection/Browse context
            track = self._bridge.get_selection()
            partition = get_partition_from_path(track.runtime.file_path) if track else None
            return BrowseContext(track=track, partition=partition)

    def explain(self, context_source: str = "playing") -> Optional[Dict[str, Any]]:
        """Explain the significance of the current track/selection."""
        ctx = self.get_current_context(context_source)
        explanation = self.explainer.explain_track(ctx)
        return vars(explanation) if explanation else None

    def nearest(self, limit: int = 10, partition_mode: str = "all", context_source: str = "playing") -> List[Dict[str, Any]]:
        """Get context-aware neighbors."""
        ctx = self.get_current_context(context_source)
        return self.retriever.get_neighbors(ctx, limit=limit, partition_mode=partition_mode)

    def diagnose(self) -> Dict[str, Any]:
        """Perform system-wide music diagnostics."""
        # 1. Base status
        results = self.diagnostics.get_status()
        
        # 2. Context Split detection
        np = self._bridge.get_now_playing()
        sel = self._bridge.get_selection()
        
        np_id = np.helix_id if np else None
        sel_id = sel.helix_id if sel else None
        
        warning = self.diagnostics.detect_context_split(np_id, sel_id)
        results["mismatch_warning"] = warning
        
        # 3. Quick identities
        results["now_playing"] = {"resolved": np.resolved if np else False, "album": np.album if np else None, "id": np_id}
        results["selection"] = {"resolved": sel.resolved if sel else False, "album": sel.album if sel else None, "id": sel_id}
        
        return results

    # ── Phase 15: Action Layer API ───────────────────────────────────────────

    def get_contextual_actions(self, source: str = "playing") -> List[Dict[str, Any]]:
        """Identify actions relevant to the current context."""
        ctx = self.get_current_context(source)
        self.action_registry.clear()
        
        # 1. Repairs
        repairs = self.repair_detect.detect_repairs(ctx)
        for r in repairs: self.action_registry.add(r)
        
        # 2. Playlists (Adjacent & Canon)
        adjacent = self.playlist_gen.generate_candidates(ctx, mode="adjacent")
        for a in adjacent: self.action_registry.add(a)
        
        canon = self.playlist_gen.generate_candidates(ctx, mode="canon")
        for c in canon: self.action_registry.add(c)

        return [a.to_dict() for a in self.action_registry.get_all()]

    def stage_action(self, action_id: str):
        """Persist a session action to the staging table."""
        actions = self.action_registry.get_all()
        target = next((a for a in actions if a.id == action_id), None)
        if target:
            self.staging.stage_action(target)
            return True
        return False

    def get_session_summary(self, source: str = "playing") -> Dict[str, Any]:
        """Generate high-level Flight Deck summary."""
        ctx = self.get_current_context(source)
        # Ensure registry has some fresh suggestions
        self.get_contextual_actions(source)
        summary = self.session.get_summary(ctx)
        return summary.to_report()

    # ── Phase 16: Safe Execution & Review ───────────────────────────────────

    def list_staged_actions(self, status: str = "staged", priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """List staged actions by status and/or priority."""
        return self.staging.list_actions(status=status, priority=priority)

    def update_action_state(self, action_id: str, status: str, note: Optional[str] = None) -> bool:
        """Approve, reject, or defer a staged action."""
        valid_states = {"staged", "approved", "rejected", "deferred"}
        if status not in valid_states:
             return False
        return self.staging.update_status(action_id, status, operator_note=note)

    def execute_action(self, action_id: str) -> Dict[str, Any]:
        """Execute an approved action safely."""
        result = self.executor.execute(action_id)
        return {
            "success": result.success,
            "outcome": result.outcome,
            "message": result.message,
            "changes": result.changes
        }

    def get_execution_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch the history of action executions."""
        return self.executor.get_log(limit=limit)
