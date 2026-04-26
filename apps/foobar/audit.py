"""
audit.py — Library audit checks for the Foobar tool.

Runs structured checks against Foobar-facing data and codex mirror state.
Returns structured issue lists, not opinions. Does not write to Atlas.

Workflows:
  1. Library audit (full health)
  2. Structural metadata audit (custom schema coverage)
  3. Numbering and release structure audit
  4. Loved and stats reconciliation
  5. Research corpus integrity (project-linked corpus checks, e.g. S3K)
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .diff import (
    CUSTOM_SCHEMA_FIELDS, REQUIRED_FIELDS, RELEASE_STRUCTURE_FIELDS,
    _norm, _norm_bool, _norm_int,
)
from .sync import query_tracks


# ---------------------------------------------------------------------------
# Issue record helpers
# ---------------------------------------------------------------------------

def _issue(track: dict, code: str, detail: str = "") -> dict:
    fb = track.get("foobar_record", track)
    return {
        "file_path": fb.get("file_path", ""),
        "title": _norm(fb.get("title")),
        "album": _norm(fb.get("album")),
        "artist": _norm(fb.get("artist")),
        "issue_code": code,
        "detail": detail,
    }


def _album_issue(album: str, code: str, tracks: list[dict], detail: str = "") -> dict:
    artist = None
    franchise = None
    if tracks:
        fb = tracks[0].get("foobar_record", tracks[0])
        artist = _norm(fb.get("album_artist") or fb.get("artist"))
        franchise = _norm(fb.get("franchise"))
    return {
        "album": album,
        "artist": artist,
        "franchise": franchise,
        "track_count": len(tracks),
        "issue_code": code,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# 1. Library audit — full health check
# ---------------------------------------------------------------------------

def audit_library(track_results: list[dict]) -> dict:
    """
    Full health check across all tracks.
    Checks required fields, empty custom fields, duplicates, and casing anomalies.
    """
    issues = []
    seen_paths: dict[str, list] = defaultdict(list)
    seen_titles: dict[str, list] = defaultdict(list)

    for tr in track_results:
        fb = tr.get("foobar_record", {})
        path = fb.get("file_path", "")

        # Required fields
        for f in REQUIRED_FIELDS:
            if not _norm(fb.get(f)):
                issues.append(_issue(tr, "missing_required_field",
                                     f"field={f}"))

        # Empty custom fields
        for f in CUSTOM_SCHEMA_FIELDS:
            if not _norm(fb.get(f)):
                issues.append(_issue(tr, "empty_custom_field", f"field={f}"))

        # Duplicate path detection
        if path:
            seen_paths[path.lower()].append(tr)

        # Title + artist duplicate
        title_key = (
            (_norm(fb.get("title")) or "").lower(),
            (_norm(fb.get("artist")) or "").lower(),
        )
        if all(title_key):
            seen_titles[str(title_key)].append(tr)

        # Codex orphan check
        if "codex_orphan" in tr.get("states", []):
            issues.append(_issue(tr, "codex_orphan",
                                 "codex has record but no Foobar/library source"))

        # Missing from codex
        if tr.get("codex_record") is None and "new_in_foobar" not in tr.get("states", []):
            issues.append(_issue(tr, "missing_from_codex",
                                 "file exists in Foobar but not indexed in codex"))

    # Duplicate paths
    for path, trs in seen_paths.items():
        if len(trs) > 1:
            for tr in trs:
                issues.append(_issue(tr, "duplicate_path",
                                     f"seen {len(trs)} times"))

    # Duplicate title+artist
    for key, trs in seen_titles.items():
        if len(trs) > 1:
            for tr in trs:
                issues.append(_issue(tr, "duplicate_candidate",
                                     f"title+artist match across {len(trs)} records"))

    return {
        "total_checked": len(track_results),
        "total_issues": len(issues),
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# 2. Structural metadata audit — custom schema coverage
# ---------------------------------------------------------------------------

def audit_custom_schema(track_results: list[dict]) -> dict:
    """
    Check SOUND TEAM, FRANCHISE, PLATFORM, SOUND CHIP coverage and consistency.
    Identifies suspicious chip/platform combinations and alias candidates.
    """
    issues = []
    sound_team_aliases: dict[str, list] = defaultdict(list)
    franchise_by_album: dict[str, set] = defaultdict(set)
    platform_chip_pairs: dict[tuple, int] = defaultdict(int)

    # Known suspicious chip/platform combos
    EXPECTED_CHIP_PLATFORM = {
        "YM2612": {"Mega Drive", "Genesis", "Sega Mega Drive"},
        "SN76489": {"Mega Drive", "Genesis", "Sega Mega Drive", "Master System", "Game Gear"},
        "SPC700": {"SNES", "Super Famicom"},
        "2A03": {"NES", "Famicom"},
        "OPL2": {"FM Towns", "PC-88", "PC-98", "Arcade"},
        "OPN": {"PC-88", "PC-98", "Arcade"},
        "OPM": {"X68000", "Arcade"},
    }

    for tr in track_results:
        fb = tr.get("foobar_record", {})
        platform = _norm(fb.get("platform"))
        chip = _norm(fb.get("sound_chip"))
        team = _norm(fb.get("sound_team"))
        franchise = _norm(fb.get("franchise"))
        album = _norm(fb.get("album")) or ""

        # Check platform present but franchise absent (for game music)
        if platform and not franchise and album:
            issues.append(_issue(tr, "platform_without_franchise",
                                 f"platform={platform} but no franchise set"))

        # Check franchise present but platform absent
        if franchise and not platform:
            issues.append(_issue(tr, "franchise_without_platform",
                                 f"franchise={franchise} but no platform set"))

        # Check chip/platform consistency
        if chip and platform:
            known_platforms = EXPECTED_CHIP_PLATFORM.get(chip)
            if known_platforms and not any(p.lower() in platform.lower()
                                           for p in known_platforms):
                issues.append(_issue(tr, "suspicious_chip_platform",
                                     f"chip={chip} but platform={platform}"))
            platform_chip_pairs[(platform, chip)] += 1

        # Sound team alias tracking
        if team:
            normalized = re.sub(r"\s+", " ", team.lower().strip())
            sound_team_aliases[normalized].append(team)

        # Franchise consistency within album
        if franchise and album:
            franchise_by_album[album].add(franchise)

    # Multiple franchises within same album — likely an alias or error
    for album, franchises in franchise_by_album.items():
        if len(franchises) > 1:
            issues.append({
                "album": album,
                "issue_code": "mixed_franchise_in_album",
                "detail": f"franchises: {sorted(franchises)}",
                "file_path": None,
            })

    # Sound team alias candidates
    alias_candidates = []
    seen_teams: dict[str, set] = defaultdict(set)
    for norm_key, originals in sound_team_aliases.items():
        unique = set(originals)
        if len(unique) > 1:
            alias_candidates.append({
                "normalized": norm_key,
                "variants": sorted(unique),
            })

    return {
        "total_checked": len(track_results),
        "total_issues": len(issues),
        "issues": issues,
        "alias_candidates": alias_candidates,
        "platform_chip_distribution": {
            f"{p}/{c}": count
            for (p, c), count in sorted(platform_chip_pairs.items(),
                                         key=lambda x: -x[1])
        },
    }


# ---------------------------------------------------------------------------
# 3. Numbering and release structure audit
# ---------------------------------------------------------------------------

def audit_release_structure(track_results: list[dict]) -> dict:
    """
    Check track/disc numbering and release structure integrity per album.
    """
    album_groups: dict[str, list[dict]] = defaultdict(list)
    for tr in track_results:
        fb = tr.get("foobar_record", {})
        album = _norm(fb.get("album")) or "__no_album__"
        album_groups[album].append(tr)

    issues = []
    album_reports = []

    for album, tracks in album_groups.items():
        album_issues = []
        track_nums = []

        for tr in tracks:
            fb = tr.get("foobar_record", {})
            tn = _norm_int(fb.get("track_number"))
            tt = _norm_int(fb.get("total_tracks"))
            dn = _norm_int(fb.get("disc_number"))
            td = _norm_int(fb.get("total_discs"))

            if tn is None:
                album_issues.append("missing_track_number")
                issues.append(_issue(tr, "missing_track_number",
                                     f"album={album!r}"))
            else:
                track_nums.append(tn)

            if tt is None:
                issues.append(_issue(tr, "missing_total_tracks",
                                     f"album={album!r}"))

        if track_nums:
            # Duplicate numbers
            dupes = [n for n in track_nums if track_nums.count(n) > 1]
            if dupes:
                album_issues.append(f"duplicate_track_numbers:{sorted(set(dupes))}")
                issues.append(_album_issue(album, "duplicate_track_numbers",
                                           tracks,
                                           f"duplicates={sorted(set(dupes))}"))

            # Gaps
            expected = set(range(min(track_nums), max(track_nums) + 1))
            gaps = sorted(expected - set(track_nums))
            if gaps:
                album_issues.append(f"track_gaps:{gaps}")
                issues.append(_album_issue(album, "track_number_gap",
                                           tracks,
                                           f"gaps={gaps}"))

        if album_issues:
            album_reports.append({
                "album": album,
                "track_count": len(tracks),
                "issues": album_issues,
            })

    return {
        "total_albums": len(album_groups),
        "albums_with_issues": len(album_reports),
        "total_issues": len(issues),
        "issues": issues,
        "album_reports": album_reports,
    }


# ---------------------------------------------------------------------------
# 4. Loved and stats reconciliation
# ---------------------------------------------------------------------------

def audit_loved_stats(track_results: list[dict]) -> dict:
    """
    Check loved/rating/playcount drift between Foobar-side and codex mirror.
    Surfaces newly loved tracks and priority refresh candidates.
    """
    loved_drift = []
    stats_drift = []
    newly_loved = []      # loved in Foobar but not in codex
    priority_refresh = [] # loved + stale analysis

    for tr in track_results:
        fb = tr.get("foobar_record", {})
        cx = tr.get("codex_record")
        states = tr.get("states", [])

        fb_loved = _norm_bool(fb.get("loved"))
        cx_loved = _norm_bool(cx.get("loved")) if cx else None

        if fb_loved and cx_loved is False:
            newly_loved.append({
                "file_path": fb.get("file_path"),
                "title": _norm(fb.get("title")),
                "album": _norm(fb.get("album")),
                "artist": _norm(fb.get("artist")),
            })
            loved_drift.append(_issue(tr, "loved_not_mirrored",
                                      "loved in Foobar but codex says not loved"))

        elif not fb_loved and cx_loved:
            loved_drift.append(_issue(tr, "loved_state_reversed",
                                      "codex says loved but Foobar says not"))

        if "stats_drift" in states:
            fb_pc = _norm_int(fb.get("play_count"))
            cx_pc = _norm_int(cx.get("play_count")) if cx else None
            stats_drift.append({
                "file_path": fb.get("file_path"),
                "title": _norm(fb.get("title")),
                "foobar_playcount": fb_pc,
                "codex_playcount": cx_pc,
                "foobar_loved": fb_loved,
                "codex_loved": cx_loved,
            })

        # Priority refresh: loved + stale analysis candidate
        if fb_loved and "stale_analysis_candidate" in states:
            priority_refresh.append({
                "file_path": fb.get("file_path"),
                "title": _norm(fb.get("title")),
                "album": _norm(fb.get("album")),
            })

    return {
        "total_loved_foobar": sum(
            1 for tr in track_results
            if _norm_bool(tr.get("foobar_record", {}).get("loved"))
        ),
        "loved_drift_count": len(loved_drift),
        "newly_loved_count": len(newly_loved),
        "stats_drift_count": len(stats_drift),
        "priority_refresh_count": len(priority_refresh),
        "loved_drift": loved_drift,
        "newly_loved": newly_loved,
        "stats_drift": stats_drift,
        "priority_refresh": priority_refresh,
    }


# ---------------------------------------------------------------------------
# 5. Research corpus integrity checker
# ---------------------------------------------------------------------------

def audit_corpus(
    track_results: list[dict],
    *,
    franchise: str | None = None,
    album: str | None = None,
    expected_track_count: int | None = None,
    corpus_name: str = "corpus",
) -> dict:
    """
    Verify structural integrity of a project-linked research corpus.

    This checks that a specific corpus (identified by franchise and/or album name)
    is complete, correctly tagged, and ready for downstream analysis pipelines.

    Checks:
    - All expected tracks present in Foobar and codex
    - No metadata drift on key fields that would affect analysis inputs
    - Sound team / franchise / platform / sound chip all populated
    - Track numbering complete and correct
    - No codex orphans within the corpus
    - Exports a manifest of current corpus state

    Does NOT check DCP values, axis vectors, or Atlas data —
    those are validated structural knowledge, not library metadata.

    Parameters:
      franchise:            Filter by franchise name (partial match)
      album:                Filter by album name (partial match)
      expected_track_count: If known, verify exact count
      corpus_name:          Label for reports
    """
    # Filter to corpus
    corpus_tracks = query_tracks(
        track_results,
        franchise=franchise,
        album=album,
    )

    if not corpus_tracks:
        return {
            "corpus_name": corpus_name,
            "status": "empty",
            "detail": f"No tracks found for franchise={franchise!r} album={album!r}",
            "issues": [],
        }

    issues = []
    warnings = []

    # Count check
    actual_count = len(corpus_tracks)
    if expected_track_count is not None:
        if actual_count != expected_track_count:
            issues.append({
                "issue_code": "corpus_count_mismatch",
                "detail": f"expected={expected_track_count}, actual={actual_count}",
            })

    # Codex coverage
    in_codex = sum(1 for tr in corpus_tracks if tr.get("codex_record") is not None)
    not_in_codex = actual_count - in_codex
    if not_in_codex > 0:
        issues.append({
            "issue_code": "corpus_partial_codex_coverage",
            "detail": f"{not_in_codex} of {actual_count} tracks not yet in codex",
        })

    # Metadata drift (fields that affect analysis inputs)
    ANALYSIS_CRITICAL_FIELDS = ["title", "artist", "album_artist", "sound_team",
                                 "franchise", "platform", "sound_chip"]
    tracks_with_drift = []
    for tr in corpus_tracks:
        td = tr.get("diff")
        if td and td.has_metadata_drift:
            drifted_fields = [d.field for d in td.metadata_diffs
                              if d.changed and d.field in ANALYSIS_CRITICAL_FIELDS]
            if drifted_fields:
                fb = tr.get("foobar_record", {})
                tracks_with_drift.append({
                    "file_path": fb.get("file_path"),
                    "title": _norm(fb.get("title")),
                    "drifted_fields": drifted_fields,
                })

    if tracks_with_drift:
        issues.append({
            "issue_code": "corpus_metadata_drift",
            "detail": f"{len(tracks_with_drift)} tracks with analysis-critical field drift",
            "affected_tracks": tracks_with_drift,
        })

    # Schema completeness
    schema_gaps = []
    for tr in corpus_tracks:
        fb = tr.get("foobar_record", {})
        missing = [f for f in CUSTOM_SCHEMA_FIELDS if not _norm(fb.get(f))]
        if missing:
            schema_gaps.append({
                "file_path": fb.get("file_path"),
                "title": _norm(fb.get("title")),
                "missing_fields": missing,
            })

    if schema_gaps:
        issues.append({
            "issue_code": "corpus_schema_gaps",
            "detail": f"{len(schema_gaps)} tracks with missing custom schema fields",
            "affected_tracks": schema_gaps,
        })

    # Numbering audit on corpus subset
    from .diff import diff_album_tracks
    # Group by album within corpus
    album_groups: dict[str, list[dict]] = defaultdict(list)
    for tr in corpus_tracks:
        fb = tr.get("foobar_record", {})
        alb = _norm(fb.get("album")) or "__no_album__"
        album_groups[alb].append(fb)

    for alb, atracks in album_groups.items():
        album_diff = diff_album_tracks(atracks)
        if album_diff.get("issue_count", 0) > 0:
            issues.append({
                "issue_code": "corpus_numbering_issues",
                "detail": f"album={alb!r}: {album_diff['issues']}",
            })

    # Build corpus manifest
    manifest = []
    for tr in corpus_tracks:
        fb = tr.get("foobar_record", {})
        manifest.append({
            "file_path": fb.get("file_path"),
            "title": _norm(fb.get("title")),
            "track_number": _norm_int(fb.get("track_number")),
            "disc_number": _norm_int(fb.get("disc_number")),
            "album": _norm(fb.get("album")),
            "artist": _norm(fb.get("artist")),
            "album_artist": _norm(fb.get("album_artist")),
            "sound_team": _norm(fb.get("sound_team")),
            "franchise": _norm(fb.get("franchise")),
            "platform": _norm(fb.get("platform")),
            "sound_chip": _norm(fb.get("sound_chip")),
            "loved": _norm_bool(fb.get("loved")),
            "in_codex": tr.get("codex_record") is not None,
            "sync_states": tr.get("states", []),
        })

    # Sort manifest by disc then track number
    manifest.sort(key=lambda x: (x.get("disc_number") or 0, x.get("track_number") or 0))

    status = "healthy" if not issues else "issues_found"

    return {
        "corpus_name": corpus_name,
        "status": status,
        "track_count": actual_count,
        "in_codex": in_codex,
        "issue_count": len(issues),
        "issues": issues,
        "manifest": manifest,
    }
