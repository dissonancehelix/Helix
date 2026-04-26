"""
explain.py — Music Operator Explanation Flow.

Generates structural explanations for tracks and contexts.
Respects ALBUM ARTIST vs ARTIST composer overrides.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .context import MusicContext

@dataclass
class Explanation:
    """A human-friendly report of structural significance."""
    summary: str
    track_id: str
    composer: str
    traits: List[str]
    structural_role: str
    canon_rank: Optional[int] = None
    partition: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

class Explainer:
    def __init__(self, db, meta):
        self._db = db
        self._meta = meta

    def explain_track(self, context: MusicContext) -> Optional[Explanation]:
        """Explain the significance of the track in the given context."""
        track = context.track
        if not track:
            return None
            
        helix_id = track.helix_id
        tags = self._db.get_semantic_tags(helix_id) if helix_id else []
        
        # Composer semantic: ARTIST is true composer override if != ALBUM ARTIST
        # We check both the metadata adapter's version and the live runtime version.
        composer = "Unknown"
        if track.meta:
            album_artist = track.meta.album_artist
            artist = track.meta.artist
            
            if artist and album_artist and artist != album_artist:
                composer = artist
            elif album_artist:
                composer = album_artist
            elif artist:
                composer = artist
        
        # If still unknown or empty after metadata check, use live runtime
        if (not composer or composer == "Unknown") and track.runtime.artist:
            composer = track.runtime.artist
            
        # Determine Partition
        partition = context.partition or "Others"
        
        # Structural Role
        primary_role = tags[0] if tags else "unindexed"
        
        # Warnings
        warnings = []
        if not track.resolved:
            warnings.append("Identity is based on runtime metadata; external-tags bridge missing.")
        if not tags:
            warnings.append("No structural tags found in taste-space graph.")
            
        return Explanation(
            summary=f"'{track.title}' by {composer} in {partition}",
            track_id=track.helix_id,
            composer=composer,
            traits=tags,
            structural_role=primary_role,
            partition=partition,
            warnings=warnings
        )
