"""
entity_layer.py — Lightweight semantic entity graph from .field_index.json.

Loads the field index once and exposes fast lookups by artist, chip,
platform, franchise, featuring, and loved status.

Does NOT modify or re-write the field index.
Does NOT call any pipeline operators.

Usage:
    from domains.music.semantic.entity_layer import MusicEntityLayer
    layer = MusicEntityLayer.load()
    tracks = layer.tracks_by_artist("masayuki nagao")
    featured = layer.tracks_by_featuring("ashley barrett")
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_FIELD_INDEX_PATH = _REPO_ROOT / "codex" / "library" / "music" / ".field_index.json"


# ── Track record (lightweight) ────────────────────────────────────────────────

@dataclass
class TrackRef:
    """Minimal track reference from the field index."""
    track_id:   str
    file_path:  Optional[str] = None
    loved:      bool = False


# ── Entity layer ──────────────────────────────────────────────────────────────

class MusicEntityLayer:
    """
    Semantic entity layer built from the Helix music field index.

    Provides O(1) lookups for common query patterns.
    Load once per session; the index is read-only.
    """

    def __init__(
        self,
        by_artist:   dict[str, list[str]],
        by_fmt_cat:  dict[str, list[str]],
        by_album:    dict[str, list[str]],
        by_loved:    list[str],
        by_featuring: dict[str, list[str]],
        source_map:  dict[str, str],
        meta:        dict,
    ) -> None:
        self._by_artist    = by_artist
        self._by_fmt_cat   = by_fmt_cat
        self._by_album     = by_album
        self._by_loved     = set(by_loved)
        self._by_featuring = by_featuring
        self._source_map   = source_map
        self._meta         = meta

    # ── Factories ─────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, index_path: Path = _FIELD_INDEX_PATH) -> "MusicEntityLayer":
        """Load the field index and return a ready entity layer."""
        if not index_path.exists():
            raise FileNotFoundError(f"Field index not found: {index_path}")
        raw = json.loads(index_path.read_text(encoding="utf-8"))
        return cls(
            by_artist   = raw.get("by_artist",    {}),
            by_fmt_cat  = raw.get("by_fmt_cat",   {}),
            by_album    = raw.get("by_album",      {}),
            by_loved    = raw.get("by_loved",      []),
            by_featuring= raw.get("by_featuring",  {}),
            source_map  = raw.get("source_map",    {}),
            meta        = raw.get("_meta",         {}),
        )

    # ── Meta ──────────────────────────────────────────────────────────────────

    @property
    def track_count(self) -> int:
        return self._meta.get("track_count", len(self._source_map))

    @property
    def loved_count(self) -> int:
        return self._meta.get("loved_count", len(self._by_loved))

    @property
    def built_at(self) -> Optional[str]:
        return self._meta.get("built_at")

    # ── Artist queries ────────────────────────────────────────────────────────

    def tracks_by_artist(self, artist_key: str) -> list[str]:
        """
        Return track IDs for an artist by normalized key.
        Key is lowercase, whitespace-collapsed — e.g. "masayuki nagao".
        """
        return list(self._by_artist.get(artist_key.lower().strip(), []))

    def tracks_by_artist_prefix(self, prefix: str) -> dict[str, list[str]]:
        """Return all artist keys that start with prefix → their track IDs."""
        pfx = prefix.lower().strip()
        return {k: list(v) for k, v in self._by_artist.items() if k.startswith(pfx)}

    def all_artist_keys(self) -> list[str]:
        return sorted(self._by_artist.keys())

    # ── Featuring queries ─────────────────────────────────────────────────────

    def tracks_by_featuring(self, artist_key: str) -> list[str]:
        """
        Return track IDs where this artist is credited in the FEATURING field.
        by_featuring is only populated if library_pipeline has been extended
        for Phase 5. Returns [] gracefully if the index has no featuring data.
        """
        return list(self._by_featuring.get(artist_key.lower().strip(), []))

    def all_featuring_keys(self) -> list[str]:
        return sorted(self._by_featuring.keys())

    def has_featuring_data(self) -> bool:
        return bool(self._by_featuring)

    # ── Collaboration queries ─────────────────────────────────────────────────

    def tracks_by_multi_artist(self, *artist_keys: str) -> list[str]:
        """
        Return track IDs where ALL given artists are credited (intersection).
        Uses null-byte multi-artist keys in the by_artist index.
        """
        if not artist_keys:
            return []
        sets = [set(self.tracks_by_artist(k)) for k in artist_keys]
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return sorted(result)

    def collaborations_for_artist(self, artist_key: str) -> dict[str, list[str]]:
        """
        Find all co-artists that share tracks with the given artist.
        Returns {co_artist_key: [track_ids]}.
        """
        my_tracks = set(self.tracks_by_artist(artist_key))
        if not my_tracks:
            return {}

        collabs: dict[str, list[str]] = {}
        for other_key, track_ids in self._by_artist.items():
            if other_key == artist_key.lower().strip():
                continue
            shared = my_tracks & set(track_ids)
            if shared:
                collabs[other_key] = sorted(shared)
        return collabs

    # ── Format / chip queries ─────────────────────────────────────────────────

    def tracks_by_format_category(self, fmt_cat: str) -> list[str]:
        """fmt_cat: 'audio' | 'hardware_log' | 'sequence' | 'waveform' | 'sampling'"""
        return list(self._by_fmt_cat.get(fmt_cat.lower(), []))

    def format_category_counts(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._by_fmt_cat.items()}

    # ── Album queries ─────────────────────────────────────────────────────────

    def tracks_by_album(self, album_key: str) -> list[str]:
        return list(self._by_album.get(album_key.lower().strip(), []))

    def all_album_keys(self) -> list[str]:
        return sorted(self._by_album.keys())

    # ── Loved queries ─────────────────────────────────────────────────────────

    def loved_tracks(self) -> list[str]:
        return sorted(self._by_loved)

    def is_loved(self, track_id: str) -> bool:
        return track_id in self._by_loved

    def loved_tracks_by_artist(self, artist_key: str) -> list[str]:
        return [t for t in self.tracks_by_artist(artist_key) if t in self._by_loved]

    # ── File path lookup ──────────────────────────────────────────────────────

    def file_path(self, track_id: str) -> Optional[str]:
        """Return the absolute file path for a track_id."""
        return self._source_map.get(track_id)

    # ── Cross-artist corpus ───────────────────────────────────────────────────

    def artist_corpus(
        self,
        artist_key: str,
        *,
        include_loved_only: bool = False,
        format_categories: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Return the full corpus for an artist with optional filters.
        Useful for feeding into analysis pipelines.
        """
        tracks = set(self.tracks_by_artist(artist_key))
        if include_loved_only:
            tracks &= self._by_loved
        if format_categories:
            allowed: set[str] = set()
            for fc in format_categories:
                allowed |= set(self._by_fmt_cat.get(fc.lower(), []))
            tracks &= allowed
        return sorted(tracks)

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "track_count":       self.track_count,
            "loved_count":       self.loved_count,
            "artist_count":      len(self._by_artist),
            "album_count":       len(self._by_album),
            "featuring_count":   len(self._by_featuring),
            "has_featuring_data": self.has_featuring_data(),
            "format_categories": self.format_category_counts(),
            "built_at":          self.built_at,
        }
