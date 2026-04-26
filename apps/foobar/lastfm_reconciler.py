"""
lastfm_reconciler.py — Last.fm trace reconciliation for the Foobar tool.

Reconciles Last.fm scrobble history against:
  1. Live library files (corpus root)
  2. Foobar sidecar/tag metadata
  3. Codex mirror (TrackDB)

Produces match classifications, high-signal missing tracks,
priority cleanup targets, and active listening corpus manifests.

Authority rules:
  - Last.fm is a BEHAVIORAL trace — not a metadata authority
  - Never overwrite curated Foobar/library metadata with Last.fm strings
  - Use Last.fm as evidence for prioritization and coverage gaps only

Classification states:
  - matched_to_library          : scrobble matches a library file
  - matched_to_codex            : scrobble matches a codex record
  - unmatched_history_entry     : no match found anywhere
  - likely_alias_match          : fuzzy/normalized match suggests alias
  - missing_from_library_but_high_signal : many plays, not in library
  - missing_from_codex_but_in_library    : in library, not yet indexed
  - high_listen_low_metadata_confidence  : high plays but schema gaps
  - priority_cleanup_candidate           : high signal + known issues
  - priority_ingest_candidate            : high plays, missing codex record
  - ambiguous_match_manual_review        : multiple partial matches
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from domains.music.ingestion.adapters.lastfm import (
    DEFAULT_LASTFM_PATH, LastFmAdapter, Scrobble, _norm_key,
)
from .diff import _norm


# ---------------------------------------------------------------------------
# Match classification vocabulary
# ---------------------------------------------------------------------------

LASTFM_MATCH_STATES = {
    "matched_to_library",
    "matched_to_codex",
    "unmatched_history_entry",
    "likely_alias_match",
    "missing_from_library_but_high_signal",
    "missing_from_codex_but_in_library",
    "high_listen_low_metadata_confidence",
    "priority_cleanup_candidate",
    "priority_ingest_candidate",
    "ambiguous_match_manual_review",
}

# Thresholds
HIGH_SIGNAL_PLAY_COUNT = 5    # ≥ this many plays = "high signal"
PRIORITY_PLAY_COUNT    = 20   # ≥ this many plays = priority candidate


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

def _build_library_index(foobar_records: list[dict]) -> dict[tuple, dict]:
    """
    Build a normalized key index from Foobar/library records.
    Returns {(artist_key, album_key, track_key): record}.
    """
    idx: dict[tuple, dict] = {}
    artist_album_idx: dict[tuple, list[dict]] = defaultdict(list)

    for rec in foobar_records:
        artist = _norm_key(_norm(rec.get("artist")) or "")
        album  = _norm_key(_norm(rec.get("album")) or "")
        title  = _norm_key(_norm(rec.get("title")) or "")
        if artist or title:
            key = (artist, album, title)
            idx[key] = rec
            artist_album_idx[(artist, album)].append(rec)

    return idx, dict(artist_album_idx)


def _build_codex_index(codex_records: dict[str, dict]) -> dict[tuple, dict]:
    """
    Build a normalized key index from codex TrackDB records.
    Returns {(artist_key, album_key, title_key): record}.
    """
    idx: dict[tuple, dict] = {}
    for path, rec in codex_records.items():
        artist = _norm_key(rec.get("artist") or "")
        album  = _norm_key(rec.get("album") or "")
        title  = _norm_key(rec.get("title") or "")
        if artist or title:
            idx[(artist, album, title)] = rec
    return idx


# ---------------------------------------------------------------------------
# Core reconciliation
# ---------------------------------------------------------------------------

def reconcile_lastfm(
    adapter: LastFmAdapter,
    foobar_records: list[dict],
    codex_records: dict[str, dict],
    *,
    top_n_tracks: int = 500,
) -> dict:
    """
    Reconcile Last.fm scrobble history against library and codex.

    Parameters:
        adapter         : loaded LastFmAdapter
        foobar_records  : normalized Foobar/library track records
        codex_records   : {file_path: track_record} from TrackDB
        top_n_tracks    : how many top-play tracks to fully classify

    Returns a dict with:
        summary, matched, unmatched, high_signal_missing,
        priority_cleanup, priority_ingest, active_corpus
    """
    lib_idx, lib_album_idx = _build_library_index(foobar_records)
    codex_idx = _build_codex_index(codex_records)

    play_counts = adapter.play_counts_by_track()
    top_tracks  = adapter.top_tracks(n=max(top_n_tracks, 1000))

    matched_to_library   = []
    matched_to_codex     = []
    unmatched            = []
    alias_candidates     = []
    high_signal_missing  = []
    priority_cleanup     = []
    priority_ingest      = []
    ambiguous            = []

    # Track which library records were matched (for missing_from_codex detection)
    matched_library_paths: set[str] = set()

    for entry in top_tracks:
        a_key = entry["artist_key"]
        al_key = entry["album_key"]
        t_key  = entry["track_key"]
        plays  = entry["play_count"]
        key    = (a_key, al_key, t_key)

        lib_match  = lib_idx.get(key)
        codex_match = codex_idx.get(key)

        # Exact match in library
        if lib_match:
            matched_library_paths.add(lib_match.get("file_path", ""))

            has_codex = codex_match is not None
            has_schema_gap = not all([
                _norm(lib_match.get("sound_team")),
                _norm(lib_match.get("franchise")),
                _norm(lib_match.get("platform")),
            ])

            r = {**entry, "library_record": lib_match, "has_codex": has_codex}

            if not has_codex:
                r["state"] = "missing_from_codex_but_in_library"
                if plays >= PRIORITY_PLAY_COUNT:
                    r["state"] = "priority_ingest_candidate"
                    priority_ingest.append(r)
                else:
                    priority_ingest.append(r)
            elif has_schema_gap and plays >= HIGH_SIGNAL_PLAY_COUNT:
                r["state"] = "high_listen_low_metadata_confidence"
                if plays >= PRIORITY_PLAY_COUNT:
                    r["state"] = "priority_cleanup_candidate"
                    priority_cleanup.append(r)
                else:
                    matched_to_library.append(r)
            else:
                r["state"] = "matched_to_library"
                matched_to_library.append(r)

            if has_codex:
                matched_to_codex.append({**r, "codex_record": codex_match})

        # Codex-only match (not in library index by normalized key)
        elif codex_match:
            r = {**entry, "codex_record": codex_match, "state": "matched_to_codex"}
            matched_to_codex.append(r)

        else:
            # Try artist-album partial match for alias detection
            album_matches = lib_album_idx.get((a_key, al_key), [])
            if album_matches and len(album_matches) < 10:
                state = "likely_alias_match" if len(album_matches) == 1 else "ambiguous_match_manual_review"
                r = {**entry, "partial_matches": len(album_matches), "state": state}
                if state == "likely_alias_match":
                    alias_candidates.append(r)
                else:
                    ambiguous.append(r)
            else:
                # Completely unmatched
                state = "unmatched_history_entry"
                if plays >= HIGH_SIGNAL_PLAY_COUNT:
                    state = "missing_from_library_but_high_signal"
                r = {**entry, "state": state}
                if plays >= HIGH_SIGNAL_PLAY_COUNT:
                    high_signal_missing.append(r)
                else:
                    unmatched.append(r)

    # Overall stats
    total_unique = len(set(
        (s.artist_key, s.album_key, s.track_key) for s in adapter.scrobbles
    ))
    total_checked = len(top_tracks)

    # Top albums by plays (for active corpus manifest)
    top_albums = adapter.top_albums(n=100)
    active_corpus = _build_active_corpus(top_albums, lib_album_idx, codex_records)

    return {
        "source": str(adapter.json_path),
        "username": adapter.username,
        "total_scrobbles": len(adapter.scrobbles),
        "total_unique_tracks": total_unique,
        "tracks_analyzed": total_checked,
        "summary": {
            "matched_to_library":               len(matched_to_library),
            "matched_to_codex":                 len(matched_to_codex),
            "alias_candidates":                 len(alias_candidates),
            "ambiguous":                        len(ambiguous),
            "missing_from_library_high_signal": len(high_signal_missing),
            "priority_cleanup_candidates":      len(priority_cleanup),
            "priority_ingest_candidates":       len(priority_ingest),
            "unmatched":                        len(unmatched),
        },
        "matched_to_library":   matched_to_library[:200],
        "matched_to_codex":     matched_to_codex[:200],
        "alias_candidates":     alias_candidates[:100],
        "ambiguous":            ambiguous[:50],
        "high_signal_missing":  high_signal_missing,
        "priority_cleanup":     priority_cleanup,
        "priority_ingest":      priority_ingest,
        "unmatched_sample":     unmatched[:200],
        "active_corpus":        active_corpus,
    }


def _build_active_corpus(
    top_albums: list[dict],
    lib_album_idx: dict[tuple, list[dict]],
    codex_records: dict[str, dict],
) -> list[dict]:
    """
    Build the active listening corpus — albums with significant play history
    and their library/codex coverage status.
    """
    corpus = []
    codex_paths = set(codex_records.keys())

    for album in top_albums:
        a_key  = album["artist_key"]
        al_key = album["album_key"]
        plays  = album["play_count"]

        lib_tracks = lib_album_idx.get((a_key, al_key), [])
        in_library = len(lib_tracks) > 0

        codex_count = 0
        for rec in lib_tracks:
            path = rec.get("file_path", "")
            if path in codex_paths:
                codex_count += 1

        corpus.append({
            "artist":      album["artist"],
            "album":       album["album"],
            "play_count":  plays,
            "in_library":  in_library,
            "library_track_count": len(lib_tracks),
            "codex_track_count":   codex_count,
            "fully_indexed": codex_count == len(lib_tracks) and len(lib_tracks) > 0,
        })

    return corpus


# ---------------------------------------------------------------------------
# Report summary formatter (for embedding in audit_summary.md)
# ---------------------------------------------------------------------------

def format_lastfm_summary_section(reconciliation: dict) -> list[str]:
    """Return markdown lines for the Last.fm section of audit_summary.md."""
    s = reconciliation.get("summary", {})
    lines = [
        "",
        "---",
        "",
        "## Last.fm Trace Reconciliation",
        f"Source: `{reconciliation.get('source', 'unknown')}`  ",
        f"Username: @{reconciliation.get('username', '?')}  ",
        f"Total scrobbles: {reconciliation.get('total_scrobbles', 0):,}  ",
        f"Unique tracks: {reconciliation.get('total_unique_tracks', 0):,}  ",
        f"Top tracks analyzed: {reconciliation.get('tracks_analyzed', 0)}  ",
        "",
        "### Match Summary",
        "| State | Count |",
        "|-------|-------|",
    ]
    for k, v in sorted(s.items(), key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v} |")

    top_missing = reconciliation.get("high_signal_missing", [])[:10]
    if top_missing:
        lines += [
            "",
            "### High-Signal Missing from Library (top 10)",
            "| Artist | Album | Track | Plays |",
            "|--------|-------|-------|-------|",
        ]
        for t in top_missing:
            lines.append(
                f"| {t['artist']} | {t['album']} | {t['track']} | {t['play_count']} |"
            )

    top_cleanup = reconciliation.get("priority_cleanup", [])[:10]
    if top_cleanup:
        lines += [
            "",
            "### Priority Cleanup Candidates (top 10)",
            "| Artist | Album | Track | Plays |",
            "|--------|-------|-------|-------|",
        ]
        for t in top_cleanup:
            lines.append(
                f"| {t['artist']} | {t['album']} | {t['track']} | {t['play_count']} |"
            )

    return lines
