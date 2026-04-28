"""
identity_resolver.py — Resolves a runtime track to its metadata identity.

The bridge operates across two independent planes:
  runtime plane   — what Beefweb reports is playing (file path + live fields)
  metadata plane  — what external-tags.db stores as canonical tags

The resolver connects them. Primary key: the file URI / file path.
Beefweb gives us %path%; external-tags.db is keyed on file:// URIs.
We normalize both sides and match on the path.

Resolution result carries both sides so callers never need to re-query.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .metadata_adapter import MetadataAdapter, TrackMeta, _normalize_uri
from .runtime_adapter import RuntimeTrack
from .alias_graph import AliasGraph


@dataclass
class ResolvedTrack:
    """
    A fully resolved track — runtime state plus canonical metadata.

    runtime is always present (we started from a live track).
    meta is None if the track is not found in external-tags.db
    (e.g. a file playing from outside the managed library).
    """
    runtime: RuntimeTrack
    meta: Optional[TrackMeta]
    helix_id: Optional[str] = None       # Phase 13: semantic slug from TrackDB
    alias_context: Optional[str] = None  # Canonical name from AliasGraph if matched

    @property
    def resolved(self) -> bool:
        """True if the track was found in the metadata plane."""
        return self.meta is not None

    @property
    def title(self) -> str:
        """Best available title: metadata first, runtime fallback."""
        if self.meta and self.meta.title:
            return self.meta.title
        return self.runtime.title

    @property
    def artist(self) -> str:
        if self.meta and self.meta.artist:
            return self.meta.artist
        return self.runtime.artist

    @property
    def display_artist(self) -> str:
        """Preferred display name: pivots to Sound Team for large ensembles (>3)."""
        raw_artist = self.artist
        # Split by both ; and , to be safe, but prioritize ; as per user format
        individuals = [a.strip() for a in raw_artist.split(';') if a.strip()]
        if len(individuals) <= 1:
            individuals = [a.strip() for a in raw_artist.split(',') if a.strip()]
            
        if len(individuals) > 3:
            if self.meta and self.meta.sound_team:
                return self.meta.sound_team
            if self.meta and self.meta.album_artist:
                return self.meta.album_artist
                
        return raw_artist

    @property
    def album(self) -> str:
        if self.meta and self.meta.album:
            return self.meta.album
        return self.runtime.album

    @property
    def is_vgm(self) -> bool:
        if self.meta:
            return self.meta.is_vgm
        VGM_EXTS = {".vgm", ".vgz", ".nsf", ".nsfe", ".spc", ".gbs",
                    ".hes", ".kss", ".ay", ".sap", ".sid", ".gym",
                    ".psf", ".psf2", ".usf", ".dsf", ".ssf"}
        return Path(self.runtime.file_path).suffix.lower() in VGM_EXTS

    def summary(self) -> str:
        parts = [f'"{self.title}"']
        if self.display_artist:
            parts.append(f"by {self.display_artist}")
        if self.album:
            parts.append(f"({self.album})")
        status = "resolved" if self.resolved else "unresolved"
        return f"{' '.join(parts)} [{status}]"


class IdentityResolver:
    """
    Resolves RuntimeTrack → ResolvedTrack by matching against external-tags.db.

    Matching strategy (in order):
      1. Exact URI match after normalization
      2. Normalized path match (handles slash/case variations)
      3. Alias match (handles translations/aliases via AliasGraph)
      4. Filename + album fuzzy match (fallback for renamed paths)
    """

    def __init__(self, metadata: MetadataAdapter, aliases: Optional[AliasGraph] = None) -> None:
        self._meta = metadata
        self._aliases = aliases or AliasGraph()
        # Seed aliases if graph is empty (basic Phase 1 behavior)
        if self._aliases.entity_count == 0:
            from .alias_graph import seed_from_codex
            seed_from_codex(self._aliases)
            
        # TrackDB for helix_id Resolution
        from system.tools.music_pipeline.track_db import TrackDB
        self._db = TrackDB()

    def resolve(self, runtime_track: RuntimeTrack) -> ResolvedTrack:
        """
        Resolve a RuntimeTrack to its metadata identity.
        Always returns a ResolvedTrack (meta may be None if not found).
        """
        meta, alias_ctx = self._lookup(runtime_track)
        
        # Phase 13: Bridge to Helix Identity
        helix_id = None
        if meta:
            # Try to get the semantic slug from TrackDB by path
            rec = self._db.get_track_by_path(meta.file_path)
            if rec:
                helix_id = rec.get("helix_id")
                
        return ResolvedTrack(runtime=runtime_track, meta=meta, helix_id=helix_id, alias_context=alias_ctx)

    def _lookup(self, rt: RuntimeTrack) -> tuple[Optional[TrackMeta], Optional[str]]:
        if not self._meta.is_available():
            return None, None

        # 1. Exact normalized URI match
        normalized = _normalize_uri(rt.file_uri)
        result = self._meta.single(normalized)
        if result:
            return result, None

        # 2. Try path variations (different slash counts in file://)
        for candidate in _uri_variants(rt.file_path):
            result = self._meta.single(candidate)
            if result:
                return result, None

        # 3. Alias lookup (check if title/artist are known aliases)
        alias_set = self._aliases.lookup(rt.title, entity_type="track")
        if alias_set:
             # If we have a canonical name, we could try to find it in the DB
             # but paths are still the primary key. For now, we report the context.
             return None, f"Alias: {alias_set.canonical}"

        # 4. Fuzzy: match by normalized filename within external-tags.db
        # Only used when path changed (e.g. library was moved)
        return self._fuzzy_fallback(rt.file_path), None

    def _fuzzy_fallback(self, file_path: str) -> Optional[TrackMeta]:
        """
        Last-resort: scan for a matching filename in the DB.
        Expensive — only fires when the exact path didn't match.
        """
        stem = Path(file_path).stem.lower()
        if not stem:
            return None
        try:
            import sqlite3
            con = sqlite3.connect(str(self._meta.db_path))
            # Use LIKE to find rows whose URI ends with the filename
            rows = con.execute(
                "SELECT path, meta FROM tags WHERE path LIKE ? LIMIT 5",
                (f"%{Path(file_path).name}",)
            ).fetchall()
            con.close()
            if len(rows) == 1:
                from .metadata_adapter import _row_to_meta
                return _row_to_meta(rows[0][0], rows[0][1])
            # Multiple matches — require stem similarity
            for path_uri, meta_blob in rows:
                if stem in path_uri.lower():
                    from .metadata_adapter import _row_to_meta
                    return _row_to_meta(path_uri, meta_blob)
        except Exception:
            pass
        return None


def _uri_variants(file_path: str) -> list[str]:
    """Generate candidate file:// URIs for a Windows path."""
    p = file_path.replace("\\", "/").lstrip("/")
    return [
        f"file:///{p}",
        f"file://{p}",
        f"file://///{p}",
    ]
