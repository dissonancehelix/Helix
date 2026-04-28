"""
context.py — Music Operator Context Model.

Formalizes the distinction between Now-Playing, Browse/Search, and Library contexts.
Part of Phase 14: Music Operator Layer.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Any
from system.tools.music_bridge.identity_resolver import ResolvedTrack

@dataclass
class MusicContext:
    """Base class for all music reasoning contexts."""
    context_type: str
    track: Optional[ResolvedTrack] = None
    album_id: Optional[str] = None
    partition: Optional[str] = None  # "VGM", "Anime", "Film", "Others"
    confidence: float = 1.0
    notes: List[str] = field(default_factory=list)

    @property
    def has_identity(self) -> bool:
        return self.track is not None and self.track.resolved

@dataclass
class NowPlayingContext(MusicContext):
    """Context anchored to the live Beefweb telemetry."""
    context_type: str = "now_playing"
    playback_state: str = "playing"

@dataclass
class BrowseContext(MusicContext):
    """Context anchored to current search, filter, or selection in foobar."""
    context_type: str = "browse"
    selection_index: Optional[int] = None
    playlist_name: Optional[str] = None
    is_search_result: bool = False

@dataclass
class LibraryContext(MusicContext):
    """Context anchored to the global Helix-side music graph."""
    context_type: str = "library"
    search_query: Optional[str] = None
    tag_filter: Optional[str] = None

def get_partition_from_path(path: str) -> Optional[str]:
    """Extract partition (VGM, Anime, etc.) from standard Helix library path."""
    if not path:
        return None
    p = path.replace("\\", "/")
    for part in ["VGM", "Anime", "Film", "Others"]:
        if f"/{part}/" in p:
            return part
    return "Others" if "/Music/" in p else None
