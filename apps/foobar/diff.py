"""
diff.py — Field-level comparison primitives for the Foobar tool.

Compares Foobar-side records against codex-side records.
Returns structured diffs used by sync.py to classify sync states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Schema — canonical Foobar field names
# ---------------------------------------------------------------------------

MUTABLE_METADATA_FIELDS = [
    "title", "artist", "album", "album_artist", "date", "genre",
    "featuring", "sound_team", "franchise", "track_number", "total_tracks",
    "disc_number", "total_discs", "comment", "platform", "sound_chip",
]

STATS_FIELDS = [
    "play_count", "rating", "loved",
]

CUSTOM_SCHEMA_FIELDS = [
    "sound_team", "franchise", "platform", "sound_chip",
]

RELEASE_STRUCTURE_FIELDS = [
    "track_number", "total_tracks", "disc_number", "total_discs", "album_artist",
]

REQUIRED_FIELDS = ["title", "artist", "album"]


# ---------------------------------------------------------------------------
# Field normalization helpers
# ---------------------------------------------------------------------------

def _norm(val: Any) -> str | None:
    """Normalize a field value for comparison."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _norm_int(val: Any) -> int | None:
    """Normalize a numeric field (track_number, play_count, etc.)."""
    if val is None:
        return None
    try:
        # Handle '3/12' format in track_number
        s = str(val).split("/")[0].strip()
        return int(s) if s else None
    except (ValueError, TypeError):
        return None


def _norm_bool(val: Any) -> bool:
    """Normalize a boolean (loved, etc.)."""
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes")
    return False


# ---------------------------------------------------------------------------
# FieldDiff dataclass
# ---------------------------------------------------------------------------

@dataclass
class FieldDiff:
    field: str
    foobar_value: Any
    codex_value: Any
    changed: bool

    def __repr__(self) -> str:
        if self.changed:
            return f"[DIFF] {self.field}: {self.foobar_value!r} → {self.codex_value!r}"
        return f"[OK]   {self.field}: {self.foobar_value!r}"


# ---------------------------------------------------------------------------
# TrackDiff dataclass
# ---------------------------------------------------------------------------

@dataclass
class TrackDiff:
    file_path: str
    foobar_record: dict
    codex_record: dict | None

    metadata_diffs: list[FieldDiff] = field(default_factory=list)
    stats_diffs: list[FieldDiff] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_schema_fields: list[str] = field(default_factory=list)

    @property
    def has_metadata_drift(self) -> bool:
        return any(d.changed for d in self.metadata_diffs)

    @property
    def has_stats_drift(self) -> bool:
        return any(d.changed for d in self.stats_diffs)

    @property
    def has_schema_gap(self) -> bool:
        return bool(self.missing_required or self.missing_schema_fields)

    @property
    def is_new_in_foobar(self) -> bool:
        return self.codex_record is None

    @property
    def is_codex_orphan(self) -> bool:
        return self.foobar_record is None and self.codex_record is not None


# ---------------------------------------------------------------------------
# Core diff function
# ---------------------------------------------------------------------------

def diff_track(foobar_rec: dict, codex_rec: dict | None) -> TrackDiff:
    """
    Compare a Foobar-side record against a codex-side record.
    Returns a TrackDiff with all detected differences.
    """
    path = foobar_rec.get("file_path", "")
    td = TrackDiff(
        file_path=path,
        foobar_record=foobar_rec,
        codex_record=codex_rec,
    )

    # Check required fields on Foobar side
    for f in REQUIRED_FIELDS:
        if not _norm(foobar_rec.get(f)):
            td.missing_required.append(f)

    # Check custom schema coverage on Foobar side
    for f in CUSTOM_SCHEMA_FIELDS:
        if not _norm(foobar_rec.get(f)):
            td.missing_schema_fields.append(f)

    if codex_rec is None:
        # No codex record — all diffs are against empty
        return td

    # Metadata field diffs
    for f in MUTABLE_METADATA_FIELDS:
        fb_val = _norm(foobar_rec.get(f))
        cx_val = _norm(codex_rec.get(f))
        changed = fb_val != cx_val
        td.metadata_diffs.append(FieldDiff(f, fb_val, cx_val, changed))

    # Stats field diffs
    for f in STATS_FIELDS:
        if f == "loved":
            fb_val = _norm_bool(foobar_rec.get(f))
            cx_val = _norm_bool(codex_rec.get(f))
        else:
            fb_val = _norm_int(foobar_rec.get(f))
            cx_val = _norm_int(codex_rec.get(f))
        changed = fb_val != cx_val
        td.stats_diffs.append(FieldDiff(f, fb_val, cx_val, changed))

    return td


def diff_album_tracks(tracks: list[dict]) -> dict:
    """
    Check release structure integrity for a group of tracks sharing an album.
    Returns a dict of per-album issues.
    """
    if not tracks:
        return {}

    issues = []

    # Track number checks
    track_nums = []
    for t in tracks:
        tn = _norm_int(t.get("track_number"))
        if tn is None:
            issues.append("missing_track_number")
        else:
            track_nums.append(tn)

    if track_nums:
        # Duplicate track numbers
        if len(track_nums) != len(set(track_nums)):
            issues.append("duplicate_track_numbers")

        # Gap detection
        expected = set(range(min(track_nums), max(track_nums) + 1))
        actual = set(track_nums)
        gaps = expected - actual
        if gaps:
            issues.append(f"track_number_gaps:{sorted(gaps)}")

    # Total tracks consistency
    total_tracks_vals = set()
    for t in tracks:
        tt = _norm_int(t.get("total_tracks"))
        if tt:
            total_tracks_vals.add(tt)
    if len(total_tracks_vals) > 1:
        issues.append(f"total_tracks_inconsistent:{total_tracks_vals}")
    elif total_tracks_vals:
        declared_total = list(total_tracks_vals)[0]
        if track_nums and declared_total != len(track_nums):
            issues.append(f"total_tracks_mismatch:declared={declared_total},actual={len(track_nums)}")

    # Disc number — check for multi-disc without disc_number
    disc_nums = [_norm_int(t.get("disc_number")) for t in tracks]
    if any(d is not None and d > 1 for d in disc_nums):
        if any(d is None for d in disc_nums):
            issues.append("multi_disc_missing_disc_number")

    # Album artist consistency
    album_artists = set(_norm(t.get("album_artist")) for t in tracks)
    album_artists.discard(None)
    if len(album_artists) > 1:
        issues.append(f"mixed_album_artist:{sorted(album_artists)}")

    # Platform / sound_chip gap for VGM formats
    vgm_formats = {"vgm", "vgz", "spc", "nsf", "psf", "psf2", "usf", "gsf"}
    for t in tracks:
        fmt = _norm(t.get("format") or t.get("codec", "")).lower()
        if fmt in vgm_formats:
            if not _norm(t.get("platform")):
                issues.append("missing_platform_on_vgm")
                break

    return {"issues": issues, "issue_count": len(issues)}
