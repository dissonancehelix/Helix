"""
repair_actions.py — Phase 15: Targeted Repair and Staging.
"""
from __future__ import annotations
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .action_model import ActionItem
from .context import MusicContext

class RepairDetector:
    def __init__(self, bridge_db):
        self._db = bridge_db

    def detect_repairs(self, context: MusicContext) -> List[ActionItem]:
        """Scan context for repair opportunities."""
        actions = []
        
        # 1. Identity Weakness
        if context.track and not context.track.resolved:
            actions.append(ActionItem(
                type="repair_suggestion",
                category="Repair",
                description=f"Resolve missing Helix ID for '{context.track.title}'",
                target_id=context.track.file_path,
                metadata={"file_path": context.track.file_path},
                rationale="Track is active in session but lacks a canonical Helix identity.",
                confidence=0.8,
                context_type=context.context_type
            ))
            
        # 2. Metadata Suspicion (e.g., missing structural tags)
        if context.has_identity:
            tags = self._db.get_semantic_tags(context.track.helix_id)
            if not tags:
                actions.append(ActionItem(
                    type="repair_suggestion",
                    category="Repair",
                    description=f"Index structural tags for '{context.track.title}'",
                    target_id=context.track.helix_id,
                    metadata={"helix_id": context.track.helix_id},
                    rationale="Track is resolved but lacks structural tags in the taste graph.",
                    confidence=0.9,
                    context_type=context.context_type
                ))
                
        # 3. Playcount recovery (Hook for later phases)
        # If we see a track with 0 plays in foobar but it is 'loved', suggest audit
        if context.track and context.track.meta:
            if context.track.meta.loved and context.track.meta.play_count == 0:
                 actions.append(ActionItem(
                    type="repair_suggestion",
                    category="Repair",
                    description="Stage playcount recovery for loved track",
                    target_id=context.track.helix_id or context.track.file_path,
                    metadata={"play_count_current": 0, "loved": True},
                    rationale="Track is 'loved' but shows 0 plays. Potential Playcount 2003 recovery target.",
                    confidence=0.7,
                    context_type=context.context_type
                ))

        return actions

class StagingManager:
    """Handles persistence of staged actions in TrackDB."""
    def __init__(self, bridge_db):
        self._db = bridge_db

    def stage_action(self, action: ActionItem):
        """Persist an action to the database."""
        conn = sqlite3.connect(self._db.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO staged_actions (
                id, type, category, description, metadata_json, rationale, confidence, staged_ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action.id,
            action.type,
            action.category,
            action.description,
            json.dumps(action.metadata or {}),
            action.rationale,
            action.confidence,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    def list_actions(self, status: str = "staged", priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch staged actions filtered by status and priority."""
        conn = sqlite3.connect(self._db.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM staged_actions WHERE status = ?"
        params = [status]
        
        if priority:
            query += " AND priority = ?"
            params.append(priority)
            
        cur = conn.execute(query, params)
        actions = [dict(row) for row in cur.fetchall()]
        conn.close()
        return actions

    def update_status(self, action_id: str, status: str, operator_note: Optional[str] = None) -> bool:
        """Update the status/validity of a staged action."""
        conn = sqlite3.connect(self._db.db_path)
        try:
            if operator_note:
                conn.execute(
                    "UPDATE staged_actions SET status = ?, operator_note = ? WHERE id = ?",
                    (status, operator_note, action_id)
                )
            else:
                conn.execute(
                    "UPDATE staged_actions SET status = ? WHERE id = ?",
                    (status, action_id)
                )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_staged(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM staged_actions WHERE applied_ts IS NULL"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
            
        with self._db._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
