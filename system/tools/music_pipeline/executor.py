"""
executor.py — Safe Execution Engine for Phase 16.

Governs the bounded mutation and export of approved Helix actions.
Includes provenance logging and safety policies.
"""
from __future__ import annotations
import json
import sqlite3
import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    success: bool
    outcome: str
    message: str
    changes: Optional[Dict[str, Any]] = None
    rollback_available: bool = False
    
class ExecutionEngine:
    def __init__(self, bridge):
        self._bridge = bridge
        self._db_path = bridge.db.db_path 
        self._runtime = bridge.runtime
        self._metadata = bridge.metadata
        
    def execute(self, action_id: str) -> ExecutionResult:
        """Fetch an approved action from the DB and route to the correct executor."""
        action = self._get_staged_action(action_id)
        if not action:
            return ExecutionResult(False, "failed", f"Action {action_id} not found in staging.")
            
        if action.get("status") != "approved":
            return ExecutionResult(False, "failed", f"Action {action_id} is not approved (current status: {action.get('status')}).")
            
        action_type = action.get("type")
        
        # Dispatch
        try:
            if action_type == "playlist_candidate":
                res = self._execute_playlist(action)
            elif action_type == "metadata_repair":
                res = self._execute_repair(action)
            elif action_type == "canon_suggest":
                res = self._execute_playlist(action) # Same logic as playlist
            else:
                return ExecutionResult(False, "failed", f"Executor for action type '{action_type}' not implemented or unsafe.")
                
            # Log the outcome
            self._log_execution(action_id, action_type, res)
            
            # Update staged action status
            self._update_staged_status(action_id, "executed" if res.success else "failed")
            
            return res
        except Exception as e:
            err_res = ExecutionResult(False, "failed", f"Execution error: {str(e)}")
            self._log_execution(action_id, action_type, err_res)
            self._update_staged_status(action_id, "failed")
            return err_res

    def _execute_playlist(self, action: Dict[str, Any]) -> ExecutionResult:
        """Create a foobar playlist from metadata."""
        meta = json.loads(action.get("metadata_json", "{}"))
        uris = meta.get("file_uris", [])
        title = meta.get("title", f"Helix Suggestion - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if not uris:
            return ExecutionResult(False, "failed", "No URIs found in playlist metadata.")
            
        if not self._runtime.is_live():
            return ExecutionResult(False, "failed", "Foobar/Beefweb not reachable for playlist creation.")
            
        pl_id = self._runtime.create_playlist(title)
        if pl_id:
            success = self._runtime.add_playlist_items(pl_id, uris)
            if success:
                return ExecutionResult(True, "success", f"Playlist '{title}' created with {len(uris)} tracks.", {"playlist_id": pl_id})
                
        return ExecutionResult(False, "failed", f"Failed to create or populate playlist '{title}'.")

    def _execute_repair(self, action: Dict[str, Any]) -> ExecutionResult:
        """Apply a metadata repair to external-tags.db."""
        meta = json.loads(action.get("metadata_json", "{}"))
        uri = meta.get("file_uri")
        proposed_tags = meta.get("proposed_tags", {})
        
        if not uri or not proposed_tags:
            return ExecutionResult(False, "failed", "Missing file_uri or proposed_tags in repair metadata.")
            
        # Safety: Narrow scope - one track at a time
        # Get 'before' state for logging/rollback
        current_meta = self._metadata.single(uri)
        before_tags = current_meta.raw if current_meta else {}
        
        # Merge repair into current tags
        new_tags = before_tags.copy()
        new_tags.update(proposed_tags)
        
        success = self._metadata.write(uri, new_tags)
        if success:
            return ExecutionResult(
                True, 
                "success", 
                f"Metadata repair applied to {uri}.",
                {"before": before_tags, "after": new_tags},
                rollback_available=True
            )
        else:
            return ExecutionResult(False, "failed", f"Failed to write metadata for {uri}.")

    def _get_staged_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM staged_actions WHERE id = ?", (action_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def _update_staged_status(self, action_id: str, status: str):
        conn = sqlite3.connect(self._db_path)
        conn.execute("UPDATE staged_actions SET status = ?, applied_ts = ? WHERE id = ?", 
                     (status, datetime.datetime.now().isoformat(), action_id))
        conn.commit()
        conn.close()

    def _log_execution(self, action_id: str, action_type: str, result: ExecutionResult):
        conn = sqlite3.connect(self._db_path)
        log_id = f"exec_{int(datetime.datetime.now().timestamp())}_{action_id[:8]}"
        
        changes_json = json.dumps(result.changes if result.changes else {})
        
        conn.execute("""
            INSERT INTO execution_log (
                id, action_id, action_type, timestamp, outcome, rationale, artifact_changes, rollback_available
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            action_id,
            action_type,
            datetime.datetime.now().isoformat(),
            result.outcome,
            result.message,
            changes_json,
            1 if result.rollback_available else 0
        ))
        
        # Also link back to staged action
        conn.execute("UPDATE staged_actions SET execution_id = ? WHERE id = ?", (log_id, action_id))
        
        conn.commit()
        conn.close()

    def get_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM execution_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        logs = [dict(row) for row in cur.fetchall()]
        conn.close()
        return logs
