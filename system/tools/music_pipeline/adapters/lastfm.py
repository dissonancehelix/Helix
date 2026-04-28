"""
lastfm.py — Last.fm play-history adapter for Helix music domain.

Reads the operator's Last.fm scrobble export JSON and exposes it as
a normalized behavioral trace source.

Source:
    model/domains/music/data/music/metadata/lastfm_dissident93.json
    (copied from: C:\\Users\\dissonance\\Downloads\\lastfmstats-dissident93.json)

Actual JSON schema (verified from source 2026-03-29):
    {
        "username": "dissident93",
        "scrobbles": [
            {
                "track":   str,
                "artist":  str,
                "album":   str,
                "albumId": str,   # MusicBrainz album MBID — empty on ~75% of entries
                "date":    int    # Unix timestamp in milliseconds
            },
            ...
        ]
    }

Stats (2026-03-29 snapshot):
    - 201,368 scrobbles
    - Date range: 2012-05-31 → 2026-03-30
    - ~75% of entries have empty albumId (older VGM scrobbles particularly)
    - 5 fields per entry: track, artist, album, albumId, date

Authority rule:
    Last.fm play history is a BEHAVIORAL TRACE source — not a metadata authority.
    It answers "what has been important in use over time."
    It does NOT override curated Foobar tag metadata.
    Never write Last.fm strings back to canonical library fields.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Default path — mirrors Spotify JSON location convention
DEFAULT_LASTFM_PATH = (
    _REPO_ROOT / "domains" / "music" / "data" / "metadata"
    / "lastfm_dissident93.json"
)


# ---------------------------------------------------------------------------
# Normalized scrobble record
# ---------------------------------------------------------------------------

class Scrobble:
    """A single normalized Last.fm scrobble."""

    __slots__ = (
        "track", "artist", "album", "album_id",
        "timestamp_ms", "dt",
        "track_key", "artist_key", "album_key",
    )

    def __init__(self, raw: dict):
        self.track    = (raw.get("track") or "").strip()
        self.artist   = (raw.get("artist") or "").strip()
        self.album    = (raw.get("album") or "").strip()
        self.album_id = (raw.get("albumId") or "").strip()  # MusicBrainz MBID, often empty

        ts_ms = raw.get("date", 0)
        self.timestamp_ms = ts_ms
        try:
            self.dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            self.dt = None

        # Normalized keys for fuzzy matching
        self.track_key  = _norm_key(self.track)
        self.artist_key = _norm_key(self.artist)
        self.album_key  = _norm_key(self.album)

    def to_dict(self) -> dict:
        return {
            "track":      self.track,
            "artist":     self.artist,
            "album":      self.album,
            "album_id":   self.album_id,
            "timestamp":  self.dt.isoformat() if self.dt else None,
            "track_key":  self.track_key,
            "artist_key": self.artist_key,
            "album_key":  self.album_key,
        }


def _norm_key(s: str) -> str:
    """Lowercase, strip punctuation/articles for fuzzy matching."""
    if not s:
        return ""
    s = s.lower().strip()
    # Remove leading articles
    s = re.sub(r"^(the |a |an )", "", s)
    # Collapse whitespace, strip non-alphanumeric except spaces
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------------------
# LastFmAdapter
# ---------------------------------------------------------------------------

class LastFmAdapter:
    """
    Reads and normalizes the operator's Last.fm scrobble export.

    This is a read-only behavioral trace adapter.
    It does not write to any source file.
    It does not overwrite library metadata.
    """

    def __init__(self, json_path: Path = DEFAULT_LASTFM_PATH):
        self.json_path = Path(json_path)
        self._scrobbles: list[Scrobble] | None = None
        self._username: str = ""

    @property
    def available(self) -> bool:
        return self.json_path.exists()

    def load(self) -> "LastFmAdapter":
        """Load and parse the scrobble JSON. Returns self for chaining."""
        if not self.json_path.exists():
            print(f"[lastfm] WARNING: file not found at {self.json_path}")
            self._scrobbles = []
            return self

        print(f"[lastfm] Loading {self.json_path.name} ...")
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._username = data.get("username", "unknown")
        raw_scrobbles = data.get("scrobbles", [])
        self._scrobbles = [Scrobble(r) for r in raw_scrobbles]

        # Date range
        dates = [s.dt for s in self._scrobbles if s.dt is not None]
        earliest = min(dates) if dates else None
        latest   = max(dates) if dates else None

        print(f"[lastfm] Loaded {len(self._scrobbles):,} scrobbles "
              f"for @{self._username}")
        if earliest and latest:
            print(f"[lastfm] Range: {earliest.date()} → {latest.date()}")
        return self

    @property
    def scrobbles(self) -> list[Scrobble]:
        if self._scrobbles is None:
            self.load()
        return self._scrobbles

    @property
    def username(self) -> str:
        return self._username

    # -----------------------------------------------------------------------
    # Aggregated views
    # -----------------------------------------------------------------------

    def play_counts_by_track(self) -> dict[tuple[str, str, str], int]:
        """
        Returns {(artist_key, album_key, track_key): play_count}.
        Keyed on normalized strings for fuzzy-tolerant matching.
        """
        counts: dict[tuple, int] = defaultdict(int)
        for s in self.scrobbles:
            key = (s.artist_key, s.album_key, s.track_key)
            counts[key] += 1
        return dict(counts)

    def play_counts_by_artist(self) -> dict[str, int]:
        """Returns {artist_key: total_plays}."""
        counts: dict[str, int] = defaultdict(int)
        for s in self.scrobbles:
            counts[s.artist_key] += 1
        return dict(counts)

    def play_counts_by_album(self) -> dict[tuple[str, str], int]:
        """Returns {(artist_key, album_key): total_plays}."""
        counts: dict[tuple, int] = defaultdict(int)
        for s in self.scrobbles:
            counts[(s.artist_key, s.album_key)] += 1
        return dict(counts)

    def top_tracks(self, n: int = 100) -> list[dict]:
        """Return top N tracks by play count."""
        counts = self.play_counts_by_track()
        sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
        results = []
        # Build readable output from most recent matching scrobble
        last_seen: dict[tuple, Scrobble] = {}
        for s in reversed(self.scrobbles):
            key = (s.artist_key, s.album_key, s.track_key)
            if key not in last_seen:
                last_seen[key] = s
        for key, count in sorted_counts[:n]:
            s = last_seen.get(key)
            results.append({
                "track":      s.track if s else key[2],
                "artist":     s.artist if s else key[0],
                "album":      s.album if s else key[1],
                "play_count": count,
                "artist_key": key[0],
                "album_key":  key[1],
                "track_key":  key[2],
            })
        return results

    def top_albums(self, n: int = 50) -> list[dict]:
        """Return top N albums by play count."""
        counts = self.play_counts_by_album()
        sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
        # Recover canonical strings from raw scrobbles
        album_strs: dict[tuple, tuple[str, str]] = {}
        for s in self.scrobbles:
            key = (s.artist_key, s.album_key)
            if key not in album_strs:
                album_strs[key] = (s.artist, s.album)
        results = []
        for key, count in sorted_counts[:n]:
            artist, album = album_strs.get(key, (key[0], key[1]))
            results.append({
                "artist":      artist,
                "album":       album,
                "play_count":  count,
                "artist_key":  key[0],
                "album_key":   key[1],
            })
        return results

    def stats(self) -> dict:
        """Return summary statistics."""
        dates = [s.dt for s in self.scrobbles if s.dt is not None]
        no_album_id = sum(1 for s in self.scrobbles if not s.album_id)
        unique_artists = len(set(s.artist_key for s in self.scrobbles))
        unique_albums  = len(set((s.artist_key, s.album_key) for s in self.scrobbles))
        unique_tracks  = len(set((s.artist_key, s.album_key, s.track_key) for s in self.scrobbles))
        return {
            "username":        self._username,
            "total_scrobbles": len(self.scrobbles),
            "unique_artists":  unique_artists,
            "unique_albums":   unique_albums,
            "unique_tracks":   unique_tracks,
            "date_range": {
                "earliest": min(dates).isoformat() if dates else None,
                "latest":   max(dates).isoformat() if dates else None,
            },
            "no_album_id_count": no_album_id,
            "no_album_id_pct": round(100 * no_album_id / max(1, len(self.scrobbles)), 1),
            "source_path": str(self.json_path),
        }

