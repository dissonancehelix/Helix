"""
Normalization layer for raw Wikimedia edit traces.
Converts raw API dicts into structure-preserving Helix dataclasses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WikiProjectSource:
    domain: str      # e.g. "en.wikipedia.org"
    shortcode: str   # e.g. "enwiki"
    api_endpoint: str


@dataclass
class PageEntityReference:
    page_id: int
    title: str
    namespace_id: int
    # 0 = Main, 1 = Talk, 2 = User, 4 = Wikipedia, etc.
    

@dataclass
class EditEvent:
    """A normalized Wikimedia contribution trace."""
    project: str             # e.g. "enwiki"
    username: str
    timestamp: str           # ISO 8601 string
    page: PageEntityReference
    revid: int
    parentid: int
    size: int
    sizediff: int
    comment: str
    is_minor: bool
    is_new: bool
    tags: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "username": self.username,
            "timestamp": self.timestamp,
            "page": {
                "page_id": self.page.page_id,
                "title": self.page.title,
                "namespace_id": self.page.namespace_id,
            },
            "revid": self.revid,
            "parentid": self.parentid,
            "size": self.size,
            "sizediff": self.sizediff,
            "comment": self.comment,
            "is_minor": self.is_minor,
            "is_new": self.is_new,
            "tags": self.tags,
        }


def normalize_contribution(
    raw: dict, 
    project_source: WikiProjectSource,
    username: str
) -> EditEvent:
    """Normalize a raw Wikipedia `usercontrib` dict into an EditEvent."""
    page = PageEntityReference(
        page_id=raw.get("pageid", 0),
        title=raw.get("title", ""),
        namespace_id=raw.get("ns", 0)
    )
    
    # Flags presence
    is_new = "new" in raw
    is_minor = "minor" in raw
    
    return EditEvent(
        project=project_source.shortcode,
        username=username,
        timestamp=raw.get("timestamp", ""),
        page=page,
        revid=raw.get("revid", 0),
        parentid=raw.get("parentid", 0),
        size=raw.get("size", 0),
        sizediff=raw.get("sizediff", 0),
        comment=raw.get("comment", ""),
        is_minor=is_minor,
        is_new=is_new,
        tags=raw.get("tags", []),
        raw_data=raw,
    )
