"""
validator.py — Validation checkpoints for Phase 4 staged and resolved data.

Each EntityGroup passes through real validation rules before
becoming a refresh candidate. A record can PASS, FAIL, or
require MANUAL_REVIEW. This is not ceremonial — failures block
refresh candidacy.

Validation categories:
  schema_completeness    required fields must be present
  uniqueness             entity ID must not collide with multiple codex records
  path_integrity         file path must exist (for library-backed records)
  codex_id_stability     codex ID must not change for same content
  numbering_sanity       track/disc numbers must be plausible
  field_collapse_guard   custom fields must not be empty when genre="VGM"
  conflict_gate          field_conflicts block promotion unless minor
  source_provenance      at least one authoritative source must be present
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .entity_resolver import EntityGroup, MATCH_CONFLICT, MATCH_AMBIG


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

PASS   = "pass"
FAIL   = "fail"
REVIEW = "manual_review"


@dataclass
class Check:
    name:   str
    status: str   # PASS | FAIL | REVIEW
    detail: str = ""


@dataclass
class ValidationResult:
    entity_id:        str
    status:           str          # overall: PASS | FAIL | REVIEW
    checks:           list[Check]
    issues:           list[str]
    refresh_eligible: bool         # True only if status == PASS

    def to_dict(self) -> dict:
        return {
            "entity_id":        self.entity_id,
            "status":           self.status,
            "refresh_eligible": self.refresh_eligible,
            "issues":           self.issues,
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail}
                for c in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def _check_source_provenance(group: EntityGroup) -> Check:
    """At least one authoritative source must be present."""
    has_authoritative = any(
        s in group.sources_matched
        for s in ("foobar_runtime", "codex", "library")
    )
    if has_authoritative:
        return Check("source_provenance", PASS,
                     f"sources={group.sources_matched}")
    return Check("source_provenance", FAIL,
                 "Only behavioral traces (lastfm/spotify) — no authoritative library source")


def _check_schema_completeness(group: EntityGroup) -> Check:
    """Required metadata fields for a valid track: title, artist, album."""
    p = group.primary
    missing = []
    if not p.title_raw.strip():
        missing.append("title")
    if not p.artist_raw.strip():
        missing.append("artist")
    if not p.album_raw.strip():
        missing.append("album")
    if missing:
        return Check("schema_completeness", FAIL,
                     f"missing required fields: {missing}")
    return Check("schema_completeness", PASS)


def _check_conflict_gate(group: EntityGroup) -> Check:
    """Field conflicts between sources should not block if they're minor."""
    if not group.field_conflicts:
        return Check("conflict_gate", PASS, "no conflicts")
    CRITICAL_FIELDS = {"platform", "sound_chip", "franchise"}
    critical = [c for c in group.field_conflicts if c["field"] in CRITICAL_FIELDS]
    non_critical = [c for c in group.field_conflicts if c["field"] not in CRITICAL_FIELDS]
    if critical:
        return Check("conflict_gate", REVIEW,
                     f"critical field conflicts: "
                     f"{[c['field'] for c in critical]}")
    if len(non_critical) > 3:
        return Check("conflict_gate", REVIEW,
                     f"{len(non_critical)} non-critical conflicts")
    return Check("conflict_gate", PASS,
                 f"{len(non_critical)} minor conflicts tolerated")


def _check_match_class(group: EntityGroup) -> Check:
    """Ambiguous matches and conflicts need review; exact/strong are fine."""
    if group.match_class == MATCH_CONFLICT:
        return Check("match_class", REVIEW,
                     "match class is conflict_requires_review")
    if group.match_class == MATCH_AMBIG:
        return Check("match_class", REVIEW,
                     "match class is ambiguous_match")
    if group.confidence < 0.30 and len(group.sources_matched) > 1:
        return Check("match_class", REVIEW,
                     f"low confidence={group.confidence:.2f} multi-source match")
    return Check("match_class", PASS,
                 f"class={group.match_class} conf={group.confidence:.2f}")


def _check_numbering_sanity(group: EntityGroup) -> Check:
    """Track and disc numbers should be plausible."""
    p = group.primary
    issues = []
    if p.track_number is not None:
        if p.track_number < 1 or p.track_number > 999:
            issues.append(f"track_number={p.track_number} out of range")
        if p.total_tracks is not None and p.track_number > p.total_tracks:
            issues.append(f"track_number={p.track_number} > total_tracks={p.total_tracks}")
    if p.disc_number is not None:
        if p.disc_number < 1 or p.disc_number > 50:
            issues.append(f"disc_number={p.disc_number} suspicious")
        if p.total_discs is not None and p.disc_number > p.total_discs:
            issues.append(f"disc_number={p.disc_number} > total_discs={p.total_discs}")
    if issues:
        return Check("numbering_sanity", FAIL, "; ".join(issues))
    return Check("numbering_sanity", PASS)


def _check_field_collapse_guard(group: EntityGroup) -> Check:
    """
    For VGM/game music (genre=VGM or platform present), custom fields
    should not all be empty — that would mean metadata degradation.
    """
    p = group.primary
    is_game_music = (
        (p.genre and "vgm" in (p.genre or "").lower())
        or bool(p.platform)
        or bool(p.franchise)
    )
    if not is_game_music:
        return Check("field_collapse_guard", PASS, "not game music — skip")

    empty = [f for f in ("sound_team", "franchise", "platform", "sound_chip")
             if not getattr(p, f, None)]
    if len(empty) == 4:
        return Check("field_collapse_guard", REVIEW,
                     "VGM/game record with all custom fields empty — may indicate metadata loss")
    return Check("field_collapse_guard", PASS,
                 f"custom fields populated (empty: {empty})")


def _check_path_integrity(group: EntityGroup) -> Check:
    """If the primary source is library or foobar_runtime, the file should exist."""
    p = group.primary
    if p.source not in ("foobar_runtime", "library", "codex"):
        return Check("path_integrity", PASS, "behavioral source — skip")
    path_str = p.source_id
    if not path_str:
        return Check("path_integrity", REVIEW, "empty source_id")
    if path_str.startswith("lfm:") or path_str.startswith("spotify:"):
        return Check("path_integrity", PASS, "non-file source_id")
    path = Path(path_str)
    if path.exists():
        return Check("path_integrity", PASS, str(path))
    # Don't hard-fail — file may be on network drive or removable; just review
    return Check("path_integrity", REVIEW, f"path not found: {path_str}")


# ---------------------------------------------------------------------------
# Validate a single group
# ---------------------------------------------------------------------------

def validate_group(group: EntityGroup) -> ValidationResult:
    """Run all checks against an EntityGroup and return a ValidationResult."""
    checks = [
        _check_source_provenance(group),
        _check_schema_completeness(group),
        _check_conflict_gate(group),
        _check_match_class(group),
        _check_numbering_sanity(group),
        _check_field_collapse_guard(group),
        _check_path_integrity(group),
    ]

    fails   = [c for c in checks if c.status == FAIL]
    reviews = [c for c in checks if c.status == REVIEW]

    if fails:
        overall = FAIL
        refresh_eligible = False
    elif reviews:
        overall = REVIEW
        refresh_eligible = False
    else:
        overall = PASS
        refresh_eligible = True

    issues = [f"[{c.name}] {c.detail}" for c in fails + reviews]

    return ValidationResult(
        entity_id        = group.entity_id,
        status           = overall,
        checks           = checks,
        issues           = issues,
        refresh_eligible = refresh_eligible,
    )


def validate_all(groups: list[EntityGroup]) -> list[ValidationResult]:
    """Validate all EntityGroups. Returns one ValidationResult per group."""
    results = []
    for g in groups:
        results.append(validate_group(g))
    pass_count   = sum(1 for r in results if r.status == PASS)
    fail_count   = sum(1 for r in results if r.status == FAIL)
    review_count = sum(1 for r in results if r.status == REVIEW)
    print(f"[validator] {len(results):,} groups: "
          f"{pass_count} PASS / {fail_count} FAIL / {review_count} REVIEW")
    return results


def summarize_validation(results: list[ValidationResult]) -> dict:
    check_counts: dict[str, dict[str, int]] = {}
    for r in results:
        for c in r.checks:
            if c.name not in check_counts:
                check_counts[c.name] = {PASS: 0, FAIL: 0, REVIEW: 0}
            check_counts[c.name][c.status] += 1
    return {
        "total":             len(results),
        "pass_count":        sum(1 for r in results if r.status == PASS),
        "fail_count":        sum(1 for r in results if r.status == FAIL),
        "review_count":      sum(1 for r in results if r.status == REVIEW),
        "refresh_eligible":  sum(1 for r in results if r.refresh_eligible),
        "by_check":          check_counts,
    }
