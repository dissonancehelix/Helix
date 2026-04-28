"""
bridge.py — HelixBridge: Unified Music Operator Interface.

Integrates Metadata, Runtime, and Alias planes into a formal Operator Layer.
Provides differentiated contexts (Now Playing vs Selection) and structural reasoning.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .metadata_adapter import MetadataAdapter, TrackMeta
from .runtime_adapter import RuntimeAdapter, RuntimeState, RuntimeTrack
from .identity_resolver import IdentityResolver, ResolvedTrack
from .alias_graph import AliasGraph
from domains.music.tools.music_pipeline.service import MusicOperator

@dataclass
class BridgeStatus:
    """Health snapshot of the Music Bridge and Operator Layer."""
    metadata_available: bool or None
    runtime_live: bool
    metadata_track_count: int
    alias_count: int
    semantic_tag_count: int
    taste_graph_size: int
    playback_state: str
    now_playing: Optional[ResolvedTrack]

    def describe(self) -> str:
        lines = [
            f"metadata plane : {'OK' if self.metadata_available else 'UNAVAILABLE'}"
            + (f" ({self.metadata_track_count:,} tracks)" if self.metadata_available else ""),
            f"alias graph    : {self.alias_count:,} entities",
            f"semantic plane : {self.semantic_tag_count:,} structural tags indexed",
            f"taste graph    : {self.taste_graph_size:,} nodes in structural space",
            f"runtime plane  : {'OK' if self.runtime_live else 'OFFLINE'}"
            + (f" [{self.playback_state}]" if self.runtime_live else ""),
        ]
        if self.now_playing:
            lines.append(f"now playing    : {self.now_playing.summary()}")
        return "\n".join(lines)

class HelixBridge:
    def __init__(
        self,
        beefweb_url: str = "http://localhost:8880",
        beefweb_timeout: float = 2.0,
        beefweb_username: str = None,
        beefweb_password: str = None,
    ) -> None:
        self._meta    = MetadataAdapter()
        self._runtime = RuntimeAdapter(base_url=beefweb_url, timeout=beefweb_timeout,
                                       username=beefweb_username, password=beefweb_password)
        self._aliases = AliasGraph()
        self._resolver = IdentityResolver(self._meta, self._aliases)
        
        from domains.music.tools.music_pipeline.track_db import TrackDB
        self._db = TrackDB()
        
        # operator service initialization
        self.operator = MusicOperator(self)

    # ── Core API ─────────────────────────────────────────────────────────────

    def status(self) -> BridgeStatus:
        runtime_state = self._runtime.state()
        now_playing = self.get_now_playing()
            
        with self._db._conn() as conn:
            tag_count = conn.execute("SELECT COUNT(DISTINCT tag_name) FROM semantic_tags").fetchone()[0]
            graph_nodes = conn.execute("SELECT COUNT(DISTINCT track_id) FROM semantic_tags").fetchone()[0]

        return BridgeStatus(
            metadata_available=self._meta.is_available(),
            runtime_live=runtime_state.is_live,
            metadata_track_count=self._meta.count() if self._meta.is_available() else 0,
            alias_count=self._aliases.entity_count,
            semantic_tag_count=tag_count,
            taste_graph_size=graph_nodes,
            playback_state=runtime_state.playback_state,
            now_playing=now_playing,
        )

    def resolve(self, file_uri: str) -> Optional[ResolvedTrack]:
        meta = self._meta.single(file_uri)
        if not meta: return None
        stub = RuntimeTrack(playback_state="stopped", file_uri=file_uri, file_path=meta.file_path,
                            title=meta.title, artist=meta.artist, album=meta.album)
        return ResolvedTrack(runtime=stub, meta=meta)

    def resolve_meta(self, file_uri: str) -> Optional[TrackMeta]:
        return self._meta.single(file_uri)

    # ── Context API ─────────────────────────────────────────────────────────

    def get_now_playing(self) -> Optional[ResolvedTrack]:
        rt = self._runtime.now_playing()
        return self._resolver.resolve(rt) if rt else None

    def get_selection(self) -> Optional[ResolvedTrack]:
        rt = self._runtime.get_selection()
        return self._resolver.resolve(rt) if rt else None

    def browse_context(self) -> list[ResolvedTrack]:
        tracks = self._runtime.get_active_playlist_tracks()
        return [self._resolver.resolve(rt) for rt in tracks]

    # ── Operator Delegation ──────────────────────────────────────────────────

    def explain(self, context: str = "playing") -> dict | None:
        return self.operator.explain(context_source=context)

    def nearest(self, limit: int = 10, partition: Optional[str] = None, context: str = "playing") -> list[dict]:
        return self.operator.nearest(limit=limit, partition_mode=partition or "all", context_source=context)

    def diagnose(self) -> dict:
        return self.operator.diagnose()

    # ── Phase 15: Action Layer ──────────────────────────────────────────────

    def get_actions(self, context: str = "playing") -> list[dict]:
        """Get identified actions for the given local context."""
        return self.operator.get_contextual_actions(source=context)

    def stage_action(self, action_id: str) -> bool:
        """Stage a session action for future execution/repair."""
        return self.operator.stage_action(action_id)

    def get_session_summary(self) -> Dict[str, Any]:
        """Operator level: Real-time context and action summary."""
        return self.operator.get_session_summary()

    # ── Phase 16: Safe Execution & Review ───────────────────────────────────

    def list_staged_actions(self, status: str = "staged") -> List[Dict[str, Any]]:
        """Operator level: List actions for review."""
        return self.operator.list_staged_actions(status=status)

    def approve_action(self, action_id: str, note: str = None) -> bool:
        """Operator level: Approve a staged action."""
        return self.operator.update_action_state(action_id, "approved", note=note)

    def reject_action(self, action_id: str, note: str = None) -> bool:
        """Operator level: Reject a staged action."""
        return self.operator.update_action_state(action_id, "rejected", note=note)

    def execute_action(self, action_id: str) -> Dict[str, Any]:
        """Operator level: Execute an approved action safely."""
        return self.operator.execute_action(action_id)

    def get_execution_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Operator level: Audit history of executed actions."""
        return self.operator.get_execution_log(limit=limit)

    def get_music_handoff(self) -> Dict[str, Any]:
        """Phase 16: Retrieve final music domain freeze summary."""
        # This will be used to generate the final artifact
        return {
            "status": "frozen",
            "bridge": "active",
            "capabilities": [
                "NowPlaying detection",
                "Context-aware neighbor retrieval",
                "Identity resolution (external-tags.db)",
                "Action staging",
                "Safe execution (playlists, repairs)",
                "Session logging"
            ],
            "stats": {
                "db_entries": self.db.track_count(),
                "execution_log_size": len(self.get_execution_log(limit=10000))
            }
        }

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def db(self): return self._db
    @property
    def runtime(self): return self._runtime
    @property
    def metadata(self): return self._meta
    @property
    def taste(self):
        if not hasattr(self, "_taste"):
            from domains.music.tools.music_pipeline.taste_engine import TasteEngine
            self._taste = TasteEngine()
        return self._taste
