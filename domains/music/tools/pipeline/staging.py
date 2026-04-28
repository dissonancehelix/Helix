"""
staging.py — Source staging and normalization for Phase 4 trace fusion.

Normalizes records from all music trace sources into a comparable
StagedRecord format with provenance preserved.

Sources supported:
  library         C:\\Users\\dissonance\\Music files + sidecar .tag metadata
  foobar_runtime  metadb.sqlite or filesystem scan from FoobarAdapter
  lastfm          behavioral trace from LastFmAdapter
  spotify         Spotify favorites JSON (if present)
  codex           Existing codex mirror records (TrackDB or field_index)

Authority:
  foobar_runtime  → canonical for mutable metadata fields
  lastfm          → behavioral trace only (play count, listening signal)
  spotify         → preference trace only (popularity, taste signal)
  codex           → prior indexed mirror (stable IDs, prior normalization)
  library         → canonical for file/path presence and sidecar metadata
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SPOTIFY_PATH = (
    _REPO_ROOT / "domains" / "music" / "data" / "metadata"
    / "spotify.json"
)
_LASTFM_PATH = (
    _REPO_ROOT / "domains" / "music" / "data" / "metadata"
    / "lastfm_dissident93.json"
)

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

_ARTICLE_RE = re.compile(r"^(the |a |an )", re.I)
_NONALNUM_RE = re.compile(r"[^\w\s]")
_SPACE_RE    = re.compile(r"\s+")


def norm_key(s: str | None) -> str:
    """Lowercase, strip articles and punctuation for fuzzy matching."""
    if not s:
        return ""
    s = s.lower().strip()
    s = _ARTICLE_RE.sub("", s)
    s = _NONALNUM_RE.sub(" ", s)
    s = _SPACE_RE.sub(" ", s).strip()
    return s


def _track_num(s: Any) -> int | None:
    if s is None:
        return None
    try:
        return int(str(s).split("/")[0].strip())
    except (ValueError, TypeError):
        return None


def _stable_id(*parts: str) -> str:
    """Stable deterministic ID from normalized key parts."""
    joined = "\x00".join(p.lower().strip() for p in parts if p)
    return hashlib.sha1(joined.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# StagedRecord
# ---------------------------------------------------------------------------

@dataclass
class StagedRecord:
    """
    A normalized, source-tagged record ready for entity resolution.

    All values are from the source — not synthesized or inferred.
    Normalization is limited to key generation for matching.
    """

    # Provenance
    source:      str   # "library" | "foobar_runtime" | "lastfm" | "spotify" | "codex"
    source_id:   str   # file_path, scrobble_index, spotify_uri, codex_id, etc.
    snapshot_id: str   # run ID — links back to the staging run

    # Source strings (verbatim — not overwritten)
    title_raw:  str
    artist_raw: str
    album_raw:  str

    # Normalized match keys (generated, not editable)
    title_key:  str
    artist_key: str
    album_key:  str

    # Structured fields — present only if source has them
    track_number:   int | None = None
    disc_number:    int | None = None
    total_tracks:   int | None = None
    total_discs:    int | None = None
    duration_ms:    int | None = None
    date_str:       str | None = None
    genre:          str | None = None
    platform:       str | None = None
    sound_chip:     str | None = None
    sound_team:     str | None = None
    franchise:      str | None = None
    album_artist:   str | None = None
    album_artist_key: str | None = None
    loved:          bool | None = None
    play_count:     int | None = None    # Foobar playcount
    scrobble_count: int | None = None    # Last.fm aggregated count
    mbid:           str | None = None    # MusicBrainz album ID (from Last.fm)
    spotify_popularity: int | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @property
    def entity_key(self) -> tuple[str, str, str]:
        """Primary match key tuple."""
        return (self.artist_key, self.album_key, self.title_key)

    def stable_id(self) -> str:
        return _stable_id(self.artist_key, self.album_key, self.title_key)


# ---------------------------------------------------------------------------
# Source snapshot
# ---------------------------------------------------------------------------

@dataclass
class SourceSnapshot:
    snapshot_id:  str
    source:       str
    record_count: int
    records:      list[StagedRecord]
    meta:         dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Normalizers per source
# ---------------------------------------------------------------------------

def from_foobar_record(rec: dict, snapshot_id: str) -> StagedRecord:
    """Normalize a Foobar/library record (metadb.sqlite or filesystem)."""
    from applications.tools.foobar.diff import _norm
    title  = _norm(rec.get("title")) or ""
    artist = _norm(rec.get("artist")) or ""
    album  = _norm(rec.get("album")) or ""
    aa     = _norm(rec.get("album_artist"))
    return StagedRecord(
        source      = "foobar_runtime",
        source_id   = rec.get("file_path", ""),
        snapshot_id = snapshot_id,
        title_raw   = title,
        artist_raw  = artist,
        album_raw   = album,
        title_key   = norm_key(title),
        artist_key  = norm_key(artist),
        album_key   = norm_key(album),
        track_number  = _track_num(rec.get("track_number")),
        disc_number   = _track_num(rec.get("disc_number")),
        total_tracks  = _track_num(rec.get("total_tracks")),
        total_discs   = _track_num(rec.get("total_discs")),
        date_str      = rec.get("date"),
        genre         = rec.get("genre"),
        platform      = rec.get("platform"),
        sound_chip    = rec.get("sound_chip"),
        sound_team    = rec.get("sound_team"),
        franchise     = rec.get("franchise"),
        album_artist  = aa,
        album_artist_key = norm_key(aa) if aa else None,
        loved       = bool(rec.get("loved")) if rec.get("loved") is not None else None,
        play_count  = rec.get("play_count"),
    )


def from_lastfm_scrobble(s: "Scrobble", snapshot_id: str, scrobble_count: int = 1) -> StagedRecord:
    """Normalize a Last.fm Scrobble into a StagedRecord."""
    return StagedRecord(
        source      = "lastfm",
        source_id   = f"lfm:{s.artist_key[:8]}:{s.album_key[:8]}:{s.track_key[:8]}",
        snapshot_id = snapshot_id,
        title_raw   = s.track,
        artist_raw  = s.artist,
        album_raw   = s.album,
        title_key   = s.track_key,
        artist_key  = s.artist_key,
        album_key   = s.album_key,
        mbid          = s.album_id or None,
        scrobble_count = scrobble_count,
    )


def from_spotify_record(rec: dict, snapshot_id: str) -> StagedRecord:
    """Normalize a Spotify favorites record."""
    title  = rec.get("Track Name") or ""
    artist = (rec.get("Artist Name(s)") or "").split(",")[0].strip()
    album  = rec.get("Album Name") or ""
    return StagedRecord(
        source      = "spotify",
        source_id   = rec.get("Track URI", ""),
        snapshot_id = snapshot_id,
        title_raw   = title,
        artist_raw  = artist,
        album_raw   = album,
        title_key   = norm_key(title),
        artist_key  = norm_key(artist),
        album_key   = norm_key(album),
        duration_ms = rec.get("Duration (ms)"),
        date_str    = str(rec.get("Release Date") or ""),
        spotify_popularity = rec.get("Popularity"),
        extra = {
            "duration_ms": rec.get("Duration (ms)"),
            "danceability": rec.get("Danceability"),
            "energy": rec.get("Energy"),
            "valence": rec.get("Valence"),
            "tempo": rec.get("Tempo"),
        },
    )


def from_codex_record(rec: dict, path: str, snapshot_id: str) -> StagedRecord:
    """Normalize an existing codex TrackDB record."""
    title  = rec.get("title") or ""
    artist = rec.get("artist") or ""
    album  = rec.get("album") or ""
    aa     = rec.get("album_artist")
    return StagedRecord(
        source      = "codex",
        source_id   = path,
        snapshot_id = snapshot_id,
        title_raw   = title,
        artist_raw  = artist,
        album_raw   = album,
        title_key   = norm_key(title),
        artist_key  = norm_key(artist),
        album_key   = norm_key(album),
        track_number  = _track_num(rec.get("track_number")),
        disc_number   = _track_num(rec.get("disc_number")),
        platform      = rec.get("platform"),
        sound_chip    = rec.get("sound_chip"),
        sound_team    = rec.get("sound_team"),
        franchise     = rec.get("franchise"),
        album_artist  = aa,
        album_artist_key = norm_key(aa) if aa else None,
        loved         = rec.get("loved"),
        play_count    = rec.get("play_count"),
        extra         = {"codex_id": rec.get("id"), "ingested_ts": rec.get("ingested_ts")},
    )


# ---------------------------------------------------------------------------
# Snapshot builders per source
# ---------------------------------------------------------------------------

def snapshot_foobar(foobar_records: list[dict], snapshot_id: str) -> SourceSnapshot:
    records = [from_foobar_record(r, snapshot_id) for r in foobar_records]
    return SourceSnapshot(
        snapshot_id  = snapshot_id,
        source       = "foobar_runtime",
        record_count = len(records),
        records      = records,
        meta         = {"field_schema_version": "v1"},
    )


def snapshot_lastfm(snapshot_id: str, json_path: Path = _LASTFM_PATH) -> SourceSnapshot:
    """Load and aggregate Last.fm scrobbles into unique track records."""
    from domains.music.tools.pipeline.adapters.lastfm import LastFmAdapter
    adapter = LastFmAdapter(json_path)
    if not adapter.available:
        return SourceSnapshot(snapshot_id, "lastfm", 0, [], {"available": False})
    adapter.load()

    # Aggregate: one record per unique (artist_key, album_key, track_key)
    from collections import defaultdict
    agg: dict[tuple, list] = defaultdict(list)
    for s in adapter.scrobbles:
        agg[s.entity_key].append(s)

    records = []
    for key, scrobbles in agg.items():
        # Use most recent scrobble as the representative
        rep = max(scrobbles, key=lambda s: s.timestamp_ms)
        records.append(from_lastfm_scrobble(rep, snapshot_id, len(scrobbles)))

    return SourceSnapshot(
        snapshot_id  = snapshot_id,
        source       = "lastfm",
        record_count = len(records),
        records      = records,
        meta = {
            "username": adapter.username,
            "total_scrobbles": len(adapter.scrobbles),
            "unique_tracks": len(records),
            "source_path": str(json_path),
        },
    )


def snapshot_spotify(snapshot_id: str, json_path: Path = _SPOTIFY_PATH) -> SourceSnapshot:
    """Load Spotify favorites JSON."""
    if not json_path.exists():
        return SourceSnapshot(snapshot_id, "spotify", 0, [], {"available": False})
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("tracks", raw.get("items", [raw]))
    records = [from_spotify_record(r, snapshot_id) for r in raw if isinstance(r, dict)]
    return SourceSnapshot(
        snapshot_id  = snapshot_id,
        source       = "spotify",
        record_count = len(records),
        records      = records,
        meta         = {"source_path": str(json_path)},
    )


def snapshot_codex(codex_records: dict[str, dict], snapshot_id: str) -> SourceSnapshot:
    """Snapshot existing codex records."""
    records = [from_codex_record(rec, path, snapshot_id)
               for path, rec in codex_records.items()]
    return SourceSnapshot(
        snapshot_id  = snapshot_id,
        source       = "codex",
        record_count = len(records),
        records      = records,
    )


def stage_all_sources(
    foobar_records: list[dict],
    codex_records: dict[str, dict],
    snapshot_id: str,
    *,
    lastfm_path: Path = _LASTFM_PATH,
    spotify_path: Path = _SPOTIFY_PATH,
    include_lastfm: bool = True,
    include_spotify: bool = True,
) -> dict[str, SourceSnapshot]:
    """
    Stage all available sources. Returns {source_name: SourceSnapshot}.
    Always includes foobar and codex.
    Last.fm and Spotify are included if files are available.
    """
    snaps: dict[str, SourceSnapshot] = {}

    print(f"[staging] Snapshotting foobar_runtime ({len(foobar_records)} records)...")
    snaps["foobar_runtime"] = snapshot_foobar(foobar_records, snapshot_id)

    print(f"[staging] Snapshotting codex ({len(codex_records)} records)...")
    snaps["codex"] = snapshot_codex(codex_records, snapshot_id)

    if include_lastfm:
        print("[staging] Snapshotting Last.fm...")
        snaps["lastfm"] = snapshot_lastfm(snapshot_id, lastfm_path)
        print(f"[staging] Last.fm: {snaps['lastfm'].record_count:,} unique tracks")

    if include_spotify:
        print("[staging] Snapshotting Spotify...")
        snaps["spotify"] = snapshot_spotify(snapshot_id, spotify_path)
        print(f"[staging] Spotify: {snaps['spotify'].record_count:,} tracks")

    return snaps

