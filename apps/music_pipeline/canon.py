from __future__ import annotations
from typing import Optional, List, Dict, Any

class CanonManager:
    def __init__(self, taste_engine):
        self._taste = taste_engine
    def get_tag_canon(self, tag: str, limit: int = 5, partition: Optional[str] = None) -> List[str]:
        return self._taste.extract_canon(tag, limit=limit, partition=partition)
