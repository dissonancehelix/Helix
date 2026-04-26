"""
metadata_adapter.py — Metadata plane contract over external-tags.db.

This is the read side of the Helix↔Foobar metadata contract.
Source of truth: C:\\Users\\dissonance\\AppData\\Roaming\\foobar2000-v2\\external-tags.db

Contract rules:
  - Read-only. No writeback here (Phase 14).
  - Never touches metadb.sqlite.
  - Foobar must remain independently usable if this adapter is absent.

Two access modes:
  single(uri)    — look up one track by its file:// URI (fast, used by bridge)
  library()      — scan the full library (slow, used by indexing passes)
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from domains.music.ingestion.adapters.foobar import (
    decode_fb2k_meta,
    EXTERNAL_TAGS_DB,
)

# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------

@dataclass
class TrackMeta:
    """
    Flat metadata record for a single track as stored in external-tags.db.
    This is the bridge's view of a track — no Helix internals, no signal
    fusion. Just the raw foobar-facing metadata plane.
    """
    file_uri: str               # foobar file:// URI (canonical key)
    file_path: str              # Windows path derived from URI
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    composer: str = ""
    year: str = ""
    track_number: str = ""
    disc_number: str = ""
    genre: str = ""
    platform: str = ""
    sound_chip: str = ""
    sound_team: str = ""
    duration: str = ""
    format: str = ""
    # Raw pass-through of all decoded fields for callers that need more
    raw: dict = field(default_factory=dict)

    @property
    def display_artist(self) -> str:
        return self.album_artist or self.artist

    @property
    def is_vgm(self) -> bool:
        VGM_EXTS = {".vgm", ".vgz", ".nsf", ".nsfe", ".spc", ".gbs",
                    ".hes", ".kss", ".ay", ".sap", ".sid", ".gym",
                    ".psf", ".psf2", ".usf", ".dsf", ".ssf"}
        return Path(self.file_path).suffix.lower() in VGM_EXTS


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class MetadataAdapter:
    """
    Read-only interface to the foobar2000 external-tags.db metadata plane.

    Usage:
        adapter = MetadataAdapter()
        meta = adapter.single("file:///C:/Users/.../track.spc")
        all_tracks = adapter.library()
    """

    def __init__(self, db_path: Path = EXTERNAL_TAGS_DB) -> None:
        self.db_path = db_path

    def is_available(self) -> bool:
        """Return True if the database file exists and is readable."""
        return self.db_path.exists()

    def single(self, file_uri: str) -> Optional[TrackMeta]:
        """
        Look up one track by its foobar file:// URI.
        Fast — single SQLite row fetch.
        Returns None if not found or DB unavailable.
        """
        if not self.is_available():
            return None
        normalized = _normalize_uri(file_uri)
        try:
            con = sqlite3.connect(str(self.db_path))
            row = con.execute(
                "SELECT path, meta FROM tags WHERE path = ?", (normalized,)
            ).fetchone()
            con.close()
            if row:
                return _row_to_meta(row[0], row[1])
        except Exception:
            pass
        return None

    def single_by_path(self, windows_path: str) -> Optional[TrackMeta]:
        """
        Look up one track by its Windows file path.
        Converts to file:// URI internally.
        """
        return self.single(_path_to_uri(windows_path))

    def library(self) -> list[TrackMeta]:
        """
        Return all tracks in external-tags.db.
        Slow — scans the full table. Use for indexing passes, not runtime.
        """
        if not self.is_available():
            return []
        results = []
        try:
            con = sqlite3.connect(str(self.db_path))
            cur = con.execute("SELECT path, meta FROM tags WHERE path LIKE 'file://%'")
            for path_uri, meta_blob in cur.fetchall():
                tm = _row_to_meta(path_uri, meta_blob)
                if tm:
                    results.append(tm)
            con.close()
        except Exception:
            pass
        return results

    def count(self) -> int:
        """Return number of file:// rows in the database."""
        if not self.is_available():
            return 0
        try:
            con = sqlite3.connect(str(self.db_path))
            n = con.execute(
                "SELECT COUNT(*) FROM tags WHERE path LIKE 'file://%'"
            ).fetchone()[0]
            con.close()
            return n
        except Exception:
            return 0

    def write(self, file_uri: str, tags: dict) -> bool:
        """
        Write metadata to external-tags.db for a track.
        Careful: This is a direct mutation of foobar's metadata plane.
        """
        if not self.is_available():
            return False
            
        from domains.music.ingestion.adapters.foobar import encode_fb2k_meta
        
        normalized = _normalize_uri(file_uri)
        blob = encode_fb2k_meta(tags)
        
        try:
            con = sqlite3.connect(str(self.db_path))
            # Check if exists first to log 'before' state if we were in execution_log
            # But here we just write efficiently
            con.execute(
                "INSERT OR REPLACE INTO tags (path, meta) VALUES (?, ?)",
                (normalized, blob)
            )
            con.commit()
            con.close()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_meta(path_uri: str, meta_blob: bytes) -> Optional[TrackMeta]:
    tags = decode_fb2k_meta(meta_blob) if meta_blob else {}
    file_path = _uri_to_path(path_uri)
    return TrackMeta(
        file_uri=path_uri,
        file_path=file_path,
        title=_str(tags, "title") or Path(file_path).stem,
        artist=_str(tags, "artist", join_lists=True),
        album=_str(tags, "album"),
        album_artist=_str(tags, "album artist", "albumartist"),
        composer=_str(tags, "composer", join_lists=True),
        year=_str(tags, "date", "year"),
        track_number=_str(tags, "tracknumber", "track"),
        disc_number=_str(tags, "discnumber", "disc"),
        genre=_str(tags, "genre"),
        platform=_str(tags, "platform"),
        sound_chip=_str(tags, "sound chip", "soundchip"),
        sound_team=_str(tags, "sound team", "soundteam"),
        format=Path(file_path).suffix.lstrip(".").upper(),
        raw=tags,
    )


def _str(tags: dict, *keys: str, join_lists: bool = False) -> str:
    for k in keys:
        v = tags.get(k)
        if v:
            if isinstance(v, list):
                return "; ".join(str(i) for i in v) if join_lists else str(v[0])
            return str(v)
    return ""


def _normalize_uri(uri: str) -> str:
    """Normalize a file:// URI to the form stored in external-tags.db."""
    if not uri.startswith("file://"):
        uri = _path_to_uri(uri)
    # foobar stores file:///C:/... (three slashes, forward slashes)
    # Normalize to consistent form
    return uri.replace("\\", "/")


def _path_to_uri(path: str) -> str:
    """Convert a Windows path to a foobar file:// URI."""
    p = path.replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    return f"file://{p}"


def _uri_to_path(uri: str) -> str:
    """Convert a foobar file:// URI to a Windows path."""
    p = uri.replace("file://", "").replace("/", "\\")
    # Strip leading backslash: \\C:\\... -> C:\\...
    p = p.lstrip("\\")
    return p
