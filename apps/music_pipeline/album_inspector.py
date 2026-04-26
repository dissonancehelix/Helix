from __future__ import annotations
from typing import Optional, List, Dict, Any

class Inspector:
    def __init__(self, db):
        self._db = db
    def inspect_album(self, album_id: str) -> Dict[str, Any]:
        return {"id": album_id, "status": "partial", "tracks": 0}
