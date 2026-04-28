"""
sync.py — Codex sync audit for the Foobar tool.

Compares the live Foobar library scan against the existing codex mirror state.
Classifies every track and album into sync states.
Codex-aware: never assumes a full rebuild is needed.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Generator, Iterator

# Resolve repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .diff import (
    CUSTOM_SCHEMA_FIELDS, MUTABLE_METADATA_FIELDS, STATS_FIELDS,
    TrackDiff, diff_album_tracks, diff_track, _norm, _norm_bool, _norm_int,
)


# ---------------------------------------------------------------------------
# Path resolution (reuses ingestion config)
# ---------------------------------------------------------------------------

try:
    from domains.music.tools.music_pipeline.config import (
        DB_PATH, FOOBAR_APPDATA, LIBRARY_ROOT,
    )
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    DB_PATH = _REPO_ROOT / "domains" / "music" / "ingestion" / "data" / "helix_music.db"
    FOOBAR_APPDATA = Path("C:/Users/dissonance/AppData/Roaming/foobar2000-v2")
    LIBRARY_ROOT = Path("C:/Users/dissonance/Music")

FIELD_INDEX_PATH = _REPO_ROOT / "codex" / "library" / "music" / ".field_index.json"
CODEX_MUSIC_ROOT = _REPO_ROOT / "codex" / "library" / "music"


# ---------------------------------------------------------------------------
# Track ID (matches TrackDB._track_id)
# ---------------------------------------------------------------------------

def _track_id(file_path: str) -> str:
    return hashlib.sha1(file_path.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Sync state vocabulary
# ---------------------------------------------------------------------------

TRACK_STATES = {
    "in_sync",
    "new_in_foobar",
    "missing_from_codex",
    "missing_from_foobar",
    "codex_orphan",
    "metadata_drift",
    "stats_drift",
    "path_drift",
    "schema_gap",
    "stale_analysis_candidate",
    "duplicate_candidate",
    "alias_candidate",
    "manual_review_required",
}

ALBUM_STATES = {
    "album_in_sync",
    "album_numbering_issue",
    "album_disc_issue",
    "album_mixed_album_artist",
    "album_partial_codex_coverage",
    "album_platform_chip_gap",
    "album_franchise_gap",
    "album_sound_team_gap",
    "album_manual_review_required",
}


# ---------------------------------------------------------------------------
# Foobar library scan (delegates to FoobarAdapter + MetadbSqliteReader)
# ---------------------------------------------------------------------------

def scan_foobar_library(library_root: Path = LIBRARY_ROOT) -> list[dict]:
    """
    Scan the live Foobar library and return normalized track records.
    Uses MetadbSqliteReader for Foobar metadb.sqlite if available,
    falls back to FoobarAdapter filesystem scan.
    """
    records = []

    # Try metadb.sqlite first (richest source)
    metadb_path = FOOBAR_APPDATA / "metadb.sqlite"
    if metadb_path.exists():
        try:
            from domains.music.tools.music_pipeline.adapters.metadb_sqlite import MetadbSqliteReader
            reader = MetadbSqliteReader(str(metadb_path))
            raw = reader.read_all()
            records = [reader.normalize(r) for r in raw]
            print(f"[sync] metadb.sqlite: {len(records)} tracks loaded from Foobar DB")
            return records
        except Exception as e:
            print(f"[sync] metadb.sqlite unavailable ({e}), falling back to filesystem scan")

    # Filesystem scan fallback
    try:
        from domains.music.tools.music_pipeline.adapters.foobar import FoobarAdapter
        adapter = FoobarAdapter(str(library_root))
        tracks = adapter.scan()
        for t in tracks:
            records.append({
                "file_path": t.file_paths[0] if t.file_paths else None,
                "title": t.canonical_title,
                "artist": t.canonical_artist,
                "album": t.album,
                "platform": t.platform,
                "format": t.format_type,
                "loved": getattr(t, "is_love", False),
            })
        print(f"[sync] filesystem scan: {len(records)} tracks")
    except Exception as e:
        print(f"[sync] ERROR: could not scan library: {e}")

    return records


# ---------------------------------------------------------------------------
# Codex mirror read
# ---------------------------------------------------------------------------

def load_codex_tracks(db_path: Path = DB_PATH) -> dict[str, dict]:
    """
    Load all tracks from TrackDB into a path-keyed dict.
    Returns {file_path: track_record}.
    """
    if not db_path.exists():
        print(f"[sync] TrackDB not found at {db_path}")
        return {}

    try:
        from domains.music.tools.music_pipeline.track_db import TrackDB
        db = TrackDB(db_path)
        count = db.track_count()
        print(f"[sync] TrackDB: {count} records")

        # Query all tracks
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM tracks").fetchall()
        conn.close()

        return {row["file_path"]: dict(row) for row in rows if row["file_path"]}
    except Exception as e:
        print(f"[sync] ERROR loading TrackDB: {e}")
        return {}


def load_field_index(path: Path = FIELD_INDEX_PATH) -> dict:
    """Load the field index JSON if available."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[sync] Field index unavailable ({e})")
        return {}


# ---------------------------------------------------------------------------
# classify_track — assign sync state(s)
# ---------------------------------------------------------------------------

def classify_track(td: TrackDiff) -> list[str]:
    """
    Classify a TrackDiff into one or more sync states.
    A track can have multiple states (e.g., metadata_drift + schema_gap).
    """
    states = []

    if td.is_new_in_foobar:
        states.append("new_in_foobar")
        if td.has_schema_gap:
            states.append("schema_gap")
        return states

    if td.is_codex_orphan:
        states.append("codex_orphan")
        return states

    # Check path existence for path_drift
    if td.foobar_record and td.codex_record:
        fb_path = td.foobar_record.get("file_path", "")
        if fb_path and not Path(fb_path).exists():
            states.append("path_drift")

    if td.has_metadata_drift:
        states.append("metadata_drift")

    if td.has_stats_drift:
        states.append("stats_drift")

    if td.has_schema_gap:
        states.append("schema_gap")

    # Stale analysis candidate: metadata changed since last analysis
    if td.has_metadata_drift and td.codex_record:
        cx = td.codex_record
        if cx.get("analysis_tier") is not None:
            states.append("stale_analysis_candidate")

    if not states:
        states.append("in_sync")

    return states


def classify_album(album_tracks: list[dict], codex_tracks: dict[str, dict]) -> list[str]:
    """Classify an album group into album-level sync states."""
    if not album_tracks:
        return []

    states = []
    album_diff = diff_album_tracks(album_tracks)
    issues = album_diff.get("issues", [])

    # Map diff issues to album states
    for issue in issues:
        if "track_number" in issue or "gap" in issue or "mismatch" in issue:
            states.append("album_numbering_issue")
        if "disc" in issue:
            states.append("album_disc_issue")
        if "album_artist" in issue:
            states.append("album_mixed_album_artist")

    # Codex coverage
    paths = [t.get("file_path", "") for t in album_tracks]
    in_codex = sum(1 for p in paths if p in codex_tracks)
    if in_codex == 0:
        pass  # will be captured as new_in_foobar at track level
    elif in_codex < len(paths):
        states.append("album_partial_codex_coverage")

    # Custom schema gaps
    missing_platform = any(
        not _norm(t.get("platform")) and
        _norm(t.get("format", "")).lower() in {"vgm", "vgz", "spc", "nsf", "psf", "usf"}
        for t in album_tracks
    )
    if missing_platform:
        states.append("album_platform_chip_gap")

    missing_franchise = any(not _norm(t.get("franchise")) for t in album_tracks)
    if missing_franchise and len(album_tracks) > 3:
        states.append("album_franchise_gap")

    missing_sound_team = any(not _norm(t.get("sound_team")) for t in album_tracks)
    if missing_sound_team:
        states.append("album_sound_team_gap")

    if not states:
        states.append("album_in_sync")

    return list(set(states))  # dedupe


# ---------------------------------------------------------------------------
# Full sync computation
# ---------------------------------------------------------------------------

def compute_sync(
    foobar_records: list[dict],
    codex_records: dict[str, dict],
) -> dict:
    """
    Compute full sync state between Foobar and codex.

    Returns:
      {
        "track_results":  [{"file_path": ..., "states": [...], "diff": TrackDiff}],
        "album_results":  [{"album": ..., "states": [...], "track_count": N}],
        "summary":        {state: count, ...},
        "codex_orphans":  [track_dict, ...],
      }
    """
    foobar_by_path = {}
    for rec in foobar_records:
        path = rec.get("file_path")
        if path:
            foobar_by_path[path] = rec

    track_results = []
    seen_paths = set()

    # Process all Foobar-side tracks
    for path, fb_rec in foobar_by_path.items():
        seen_paths.add(path)
        cx_rec = codex_records.get(path)
        td = diff_track(fb_rec, cx_rec)
        states = classify_track(td)
        track_results.append({
            "file_path": path,
            "states": states,
            "diff": td,
            "foobar_record": fb_rec,
            "codex_record": cx_rec,
        })

    # Codex-only records (orphans)
    codex_orphans = []
    for path, cx_rec in codex_records.items():
        if path not in seen_paths:
            td = TrackDiff(
                file_path=path,
                foobar_record={},
                codex_record=cx_rec,
            )
            codex_orphans.append({
                "file_path": path,
                "states": ["codex_orphan"],
                "diff": td,
                "codex_record": cx_rec,
            })

    # Album grouping
    album_groups: dict[str, list[dict]] = defaultdict(list)
    for tr in track_results:
        fb = tr["foobar_record"]
        album = _norm(fb.get("album")) or "__no_album__"
        album_groups[album].append(fb)

    album_results = []
    for album, tracks in album_groups.items():
        states = classify_album(tracks, codex_records)
        album_results.append({
            "album": album,
            "states": states,
            "track_count": len(tracks),
            "artist": _norm(tracks[0].get("album_artist") or tracks[0].get("artist")),
            "platform": _norm(tracks[0].get("platform")),
            "franchise": _norm(tracks[0].get("franchise")),
        })

    # Summary counts
    summary: dict[str, int] = defaultdict(int)
    for tr in track_results:
        for s in tr["states"]:
            summary[s] += 1
    for orp in codex_orphans:
        summary["codex_orphan"] += 1

    return {
        "track_results": track_results,
        "album_results": album_results,
        "summary": dict(summary),
        "codex_orphans": codex_orphans,
        "total_foobar": len(foobar_records),
        "total_codex": len(codex_records),
    }


# ---------------------------------------------------------------------------
# Query helpers (franchise / platform / loved / schema filtered views)
# ---------------------------------------------------------------------------

def query_tracks(
    track_results: list[dict],
    *,
    franchise: str | None = None,
    platform: str | None = None,
    sound_chip: str | None = None,
    sound_team: str | None = None,
    loved: bool | None = None,
    states: list[str] | None = None,
    album: str | None = None,
) -> list[dict]:
    """
    Filter track_results by one or more criteria.
    All filters are AND-combined. None = no filter on that field.

    Examples:
      query_tracks(results, franchise="Sonic the Hedgehog")
      query_tracks(results, platform="Mega Drive", loved=True)
      query_tracks(results, sound_chip="YM2612")
      query_tracks(results, states=["schema_gap"])
      query_tracks(results, album="Sonic the Hedgehog 3 & Knuckles")
    """
    out = []
    for tr in track_results:
        fb = tr.get("foobar_record", {})

        if franchise is not None:
            val = _norm(fb.get("franchise")) or ""
            if franchise.lower() not in val.lower():
                continue

        if platform is not None:
            val = _norm(fb.get("platform")) or ""
            if platform.lower() not in val.lower():
                continue

        if sound_chip is not None:
            val = _norm(fb.get("sound_chip")) or ""
            if sound_chip.lower() not in val.lower():
                continue

        if sound_team is not None:
            val = _norm(fb.get("sound_team")) or ""
            if sound_team.lower() not in val.lower():
                continue

        if loved is not None:
            track_loved = _norm_bool(fb.get("loved"))
            if track_loved != loved:
                continue

        if states is not None:
            if not any(s in tr.get("states", []) for s in states):
                continue

        if album is not None:
            val = _norm(fb.get("album")) or ""
            if album.lower() not in val.lower():
                continue

        out.append(tr)
    return out

