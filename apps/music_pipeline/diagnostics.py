from __future__ import annotations
from typing import Optional, List, Dict, Any

class MusicDiagnostics:
    def __init__(self, bridge_db, runtime):
        self._db = bridge_db
        self._runtime = runtime
    def get_status(self) -> Dict[str, Any]:
        return {"bridge_health": "OK", "runtime_plane": "Connected" if self._runtime.is_live() else "Offline"}
    def detect_context_split(self, np_id: Optional[str], sel_id: Optional[str]) -> Optional[str]:
        if np_id and sel_id and np_id != sel_id:
            return "Warning: browsed track differs from playing track (art-panel risk)."
        return None
