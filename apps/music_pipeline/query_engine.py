"""
query_engine.py — Operator query workflows for the Phase 5 semantic layer.

High-level query patterns that combine entity_layer + credit_resolver
into the five canonical query types specified in Phase 5 Part E:

  1. featuring      — "show all tracks featuring <artist>"
  2. collaborations — "show all <artist A> + <artist B> collaborations"
  3. chip           — "show all <chip> tracks by <artist>"
  4. corpus         — "show full corpus for <artist> [+ filters]"
  5. unresolved     — "show all tracks with unresolved artist credits"

Each query returns a QueryResult with a structured result set and
a metadata block (what was matched, how many, from which source).

The engine is stateless — pass in a MusicEntityLayer, call a query.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .entity_layer import MusicEntityLayer
from .credit_resolver import resolve_credits, ParticipantSet, _norm
from .ambiguity import ResolutionState
from .glossary import resolve_chip, resolve_platform


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class QueryResult:
    """Structured result from a semantic query."""
    query_type:   str
    query_params: dict
    track_ids:    list[str]
    total:        int
    metadata:     dict = field(default_factory=dict)
    warnings:     list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query_type":   self.query_type,
            "query_params": self.query_params,
            "total":        self.total,
            "track_ids":    self.track_ids,
            "metadata":     self.metadata,
            "warnings":     self.warnings,
        }

    def print_summary(self) -> None:
        print(f"[{self.query_type}] {self.total} tracks")
        if self.warnings:
            for w in self.warnings:
                print(f"  WARN: {w}")
        params_str = ", ".join(f"{k}={v}" for k, v in self.query_params.items())
        print(f"  params: {params_str}")
        for key, val in self.metadata.items():
            print(f"  {key}: {val}")


# ── Normalization helpers ─────────────────────────────────────────────────────

def _artist_key(s: str) -> str:
    """Normalize artist string to field-index key format."""
    return re.sub(r"\s+", " ", s.strip().lower())


# ── Query engine ──────────────────────────────────────────────────────────────

class SemanticQueryEngine:
    """
    Operator query engine for the music semantic layer.

    Usage:
        layer   = MusicEntityLayer.load()
        engine  = SemanticQueryEngine(layer)
        result  = engine.featuring("Ashley Barrett")
    """

    def __init__(self, layer: MusicEntityLayer) -> None:
        self._layer = layer

    # ── 1. Featuring ──────────────────────────────────────────────────────────

    def featuring(self, artist: str) -> QueryResult:
        """
        Return all tracks featuring the given artist.
        Searches both the by_featuring index (Phase 5) and
        the by_artist index (for null-separated values).
        """
        key = _artist_key(artist)
        warnings: list[str] = []

        # Primary: by_featuring index (populated by Phase 5 pipeline extension)
        from_featuring = self._layer.tracks_by_featuring(key)

        # Secondary: by_artist index — the artist appears as one of multiple
        # credited artists (covers pre-Phase-5 data where FEATURING wasn't
        # indexed separately)
        from_artist = self._layer.tracks_by_artist(key)

        if not self._layer.has_featuring_data():
            warnings.append(
                "by_featuring index is empty — run library_pipeline.py to rebuild "
                "with FEATURING tag support (Phase 5)"
            )

        combined = sorted(set(from_featuring) | set(from_artist))

        return QueryResult(
            query_type="featuring",
            query_params={"artist": artist, "key": key},
            track_ids=combined,
            total=len(combined),
            metadata={
                "from_featuring_index": len(from_featuring),
                "from_artist_index":    len(from_artist),
            },
            warnings=warnings,
        )

    # ── 2. Collaborations ─────────────────────────────────────────────────────

    def collaborations(
        self,
        artist_a: str,
        artist_b: Optional[str] = None,
        *,
        min_tracks: int = 1,
    ) -> QueryResult:
        """
        Return tracks where artist_a collaborated with artist_b.
        If artist_b is None, return all collaborators of artist_a
        with their shared track counts.
        """
        key_a = _artist_key(artist_a)

        if artist_b:
            key_b = _artist_key(artist_b)
            tracks_a = set(self._layer.tracks_by_artist(key_a))
            tracks_b = set(self._layer.tracks_by_artist(key_b))
            shared = sorted(tracks_a & tracks_b)
            return QueryResult(
                query_type="collaborations",
                query_params={"artist_a": artist_a, "artist_b": artist_b},
                track_ids=shared,
                total=len(shared),
                metadata={
                    f"{key_a}_total": len(tracks_a),
                    f"{key_b}_total": len(tracks_b),
                    "overlap": len(shared),
                },
            )
        else:
            # All collaborators
            collabs = self._layer.collaborations_for_artist(key_a)
            collabs = {k: v for k, v in collabs.items() if len(v) >= min_tracks}
            all_collab_tracks = sorted({t for tracks in collabs.values() for t in tracks})
            return QueryResult(
                query_type="collaborations",
                query_params={"artist_a": artist_a, "artist_b": None, "min_tracks": min_tracks},
                track_ids=all_collab_tracks,
                total=len(all_collab_tracks),
                metadata={
                    "collaborator_count": len(collabs),
                    "collaborators": {k: len(v) for k, v in sorted(
                        collabs.items(), key=lambda x: -len(x[1])
                    )},
                },
            )

    # ── 3. Chip corpus ────────────────────────────────────────────────────────

    def chip_corpus(
        self,
        chip_raw: str,
        artist: Optional[str] = None,
    ) -> QueryResult:
        """
        Return all tracks that use the given sound chip.
        Optionally filter to a specific artist.

        Chip resolution is done via glossary.resolve_chip.
        Since the field index doesn't have a by_chip index yet,
        this falls back to format_category='hardware_log' as a
        conservative proxy (hardware log formats → chip-driven).
        """
        chip_entry = resolve_chip(chip_raw)
        warnings: list[str] = []

        if chip_entry:
            chip_id  = chip_entry.id
            chip_name = chip_entry.canonical_name
        else:
            chip_id   = None
            chip_name = chip_raw
            warnings.append(
                f"Chip '{chip_raw}' not found in glossary — "
                "using hardware_log format proxy"
            )

        # Proxy: hardware_log format tracks are chip-driven
        hw_tracks = set(self._layer.tracks_by_format_category("hardware_log"))

        if artist:
            key_a = _artist_key(artist)
            artist_tracks = set(self._layer.tracks_by_artist(key_a))
            result_tracks = sorted(hw_tracks & artist_tracks)
            meta = {
                "chip":          chip_name,
                "artist_key":    key_a,
                "hw_log_total":  len(hw_tracks),
                "artist_total":  len(artist_tracks),
                "overlap":       len(result_tracks),
                "note":          "chip filter is hardware_log proxy until by_chip index exists",
            }
        else:
            result_tracks = sorted(hw_tracks)
            meta = {
                "chip":         chip_name,
                "hw_log_total": len(hw_tracks),
                "note":         "chip filter is hardware_log proxy until by_chip index exists",
            }

        return QueryResult(
            query_type="chip_corpus",
            query_params={"chip": chip_raw, "artist": artist},
            track_ids=result_tracks,
            total=len(result_tracks),
            metadata=meta,
            warnings=warnings,
        )

    # ── 4. Artist corpus ──────────────────────────────────────────────────────

    def corpus(
        self,
        artist: str,
        *,
        loved_only:         bool = False,
        format_categories:  Optional[list[str]] = None,
        limit:              Optional[int] = None,
    ) -> QueryResult:
        """
        Return the full corpus for an artist with optional filters.
        """
        key = _artist_key(artist)
        tracks = self._layer.artist_corpus(
            key,
            include_loved_only=loved_only,
            format_categories=format_categories,
        )
        if limit:
            tracks = tracks[:limit]

        return QueryResult(
            query_type="corpus",
            query_params={
                "artist": artist,
                "loved_only": loved_only,
                "format_categories": format_categories,
                "limit": limit,
            },
            track_ids=tracks,
            total=len(tracks),
            metadata={
                "artist_key":       key,
                "format_filter":    format_categories,
                "loved_filter":     loved_only,
            },
        )

    # ── 5. Unresolved credits ─────────────────────────────────────────────────

    def unresolved(
        self,
        *,
        sample_size: int = 100,
        artist_filter: Optional[str] = None,
    ) -> QueryResult:
        """
        Return tracks with artist keys that don't resolve to codex entities.
        Uses credit_resolver to attempt resolution for each unique artist key.

        This is an expensive query — it loads the codex index and
        iterates all artist keys. Use sample_size to limit output.
        """
        from .credit_resolver import _load_codex_index, _norm

        codex = _load_codex_index()
        unresolved_artists: dict[str, list[str]] = {}  # artist_key -> [track_ids]

        artist_keys = self._layer.all_artist_keys()
        if artist_filter:
            af = _artist_key(artist_filter)
            artist_keys = [k for k in artist_keys if af in k]

        for key in artist_keys:
            # Multi-artist keys (null-sep) — split and check each token
            sub_keys = [k.strip() for k in key.split("\x00") if k.strip()]
            for sub in sub_keys:
                if sub not in codex:
                    if sub not in unresolved_artists:
                        unresolved_artists[sub] = self._layer.tracks_by_artist(key)

        # Sort by track count descending (most impactful unresolved artists first)
        sorted_unresolved = sorted(
            unresolved_artists.items(),
            key=lambda x: -len(x[1]),
        )

        sampled = sorted_unresolved[:sample_size]
        all_track_ids = sorted({t for _, tids in sampled for t in tids})

        return QueryResult(
            query_type="unresolved",
            query_params={"sample_size": sample_size, "artist_filter": artist_filter},
            track_ids=all_track_ids,
            total=len(unresolved_artists),
            metadata={
                "total_unresolved_artist_keys": len(unresolved_artists),
                "sample_shown":                 len(sampled),
                "top_unresolved": [
                    {"key": k, "track_count": len(v)}
                    for k, v in sampled[:20]
                ],
            },
        )

    # ── 6. Loved corpus ───────────────────────────────────────────────────────

    def loved(self, artist: Optional[str] = None) -> QueryResult:
        """Return all loved tracks, optionally filtered to an artist."""
        if artist:
            key = _artist_key(artist)
            tracks = self._layer.loved_tracks_by_artist(key)
            return QueryResult(
                query_type="loved",
                query_params={"artist": artist},
                track_ids=tracks,
                total=len(tracks),
                metadata={"artist_key": key},
            )
        else:
            tracks = self._layer.loved_tracks()
            return QueryResult(
                query_type="loved",
                query_params={"artist": None},
                track_ids=tracks,
                total=len(tracks),
            )
