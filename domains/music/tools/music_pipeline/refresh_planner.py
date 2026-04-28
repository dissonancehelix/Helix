"""
refresh_planner.py — Dry-run codex refresh planning for Phase 4.

Takes validated EntityGroups and produces a codex refresh plan:
  leave_unchanged  — codex record current; no action needed
  patch            — narrow field update; only changed fields applied
  reindex          — record exists in codex but needs full re-normalization
  mark_stale       — codex record exists but source has moved/changed significantly
  mark_orphaned    — codex record exists but no library source found
  add_new          — not in codex; candidate for new mirror record
  hold_for_review  — validation uncertain; do not touch automatically

IMPORTANT: This planner produces a dry-run plan only.
No codex records are written until the operator explicitly applies the plan.
Stable codex IDs are preserved where possible.
Narrow patch actions are preferred over full rebuild.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .entity_resolver import (
    EntityGroup, MATCH_EXACT, MATCH_STRONG, MATCH_LIKELY,
    MATCH_ALIAS, MATCH_AMBIG, MATCH_NONE, MATCH_CONFLICT,
)
from .validator import ValidationResult, PASS, FAIL, REVIEW


# ---------------------------------------------------------------------------
# Refresh action constants
# ---------------------------------------------------------------------------

ACTION_UNCHANGED = "leave_unchanged"
ACTION_PATCH     = "patch"
ACTION_REINDEX   = "reindex"
ACTION_STALE     = "mark_stale"
ACTION_ORPHAN    = "mark_orphaned"
ACTION_ADD_NEW   = "add_new"
ACTION_REVIEW    = "hold_for_review"


# ---------------------------------------------------------------------------
# Patch field detection
# ---------------------------------------------------------------------------

_PATCHABLE_FIELDS = [
    "loved", "play_count", "genre", "date_str",
    "platform", "sound_chip", "sound_team", "franchise",
    "album_artist", "track_number", "disc_number",
    "total_tracks", "total_discs",
]

_IDENTITY_FIELDS = ["title_key", "artist_key", "album_key"]


def _compute_patch_fields(
    group: EntityGroup,
) -> dict[str, Any]:
    """
    Compute which fields differ between the primary (more authoritative)
    and codex records, and should be patched.

    Returns {field_name: new_value}.
    """
    codex_rec = group.all_records.get("codex")
    if not codex_rec:
        return {}

    primary = group.primary
    patches: dict[str, Any] = {}
    for f in _PATCHABLE_FIELDS:
        p_val = getattr(primary, f, None)
        c_val = getattr(codex_rec, f, None)
        # Patch if primary has a non-None value and it differs from codex
        if p_val is not None and p_val != c_val:
            patches[f] = p_val
    return patches


# ---------------------------------------------------------------------------
# RefreshCandidate
# ---------------------------------------------------------------------------

@dataclass
class RefreshCandidate:
    entity_id:          str
    action:             str
    confidence:         float
    validation_status:  str           # PASS | FAIL | REVIEW
    patch_fields:       dict           # non-empty only for ACTION_PATCH
    codex_record_id:    str | None     # existing codex ID if traceable
    source_provenance:  list[str]      # sources that justify this action
    detail:             str            # human-readable reason
    scrobble_count:     int = 0
    title_raw:          str = ""
    artist_raw:         str = ""
    album_raw:          str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Core planner
# ---------------------------------------------------------------------------

def plan_refresh(
    groups: list[EntityGroup],
    validation_results: list[ValidationResult],
) -> list[RefreshCandidate]:
    """
    Produce a refresh plan from resolved, validated EntityGroups.
    Returns one RefreshCandidate per group.
    """
    val_map: dict[str, ValidationResult] = {
        r.entity_id: r for r in validation_results
    }
    candidates: list[RefreshCandidate] = []

    for group in groups:
        val = val_map.get(group.entity_id)
        val_status = val.status if val else REVIEW
        p = group.primary

        # Extract existing codex ID if present
        codex_rec = group.all_records.get("codex")
        codex_id  = (codex_rec.extra.get("codex_id") if codex_rec else None)

        # Validation blocked
        if val_status == FAIL:
            candidates.append(RefreshCandidate(
                entity_id         = group.entity_id,
                action            = ACTION_REVIEW,
                confidence        = group.confidence,
                validation_status = val_status,
                patch_fields      = {},
                codex_record_id   = codex_id,
                source_provenance = group.sources_matched,
                detail            = "; ".join(val.issues) if val else "validation failed",
                scrobble_count    = group.scrobble_count,
                title_raw         = p.title_raw,
                artist_raw        = p.artist_raw,
                album_raw         = p.album_raw,
            ))
            continue

        # Determine action based on match class and source presence
        has_codex   = "codex" in group.sources_matched
        has_library = any(s in group.sources_matched
                          for s in ("foobar_runtime", "library"))

        if group.match_class in (MATCH_AMBIG, MATCH_CONFLICT):
            action = ACTION_REVIEW
            detail = f"match_class={group.match_class} — manual review required"

        elif not has_library and has_codex:
            # Codex record exists but no live source
            action = ACTION_ORPHAN
            detail = "codex record present but no library source found"

        elif has_library and not has_codex:
            # In library but not yet in codex
            if val_status == PASS:
                action = ACTION_ADD_NEW
                detail = "new library record, not yet in codex"
            else:
                action = ACTION_REVIEW
                detail = f"new candidate needs review: {'; '.join(val.issues) if val else ''}"

        elif has_library and has_codex:
            # Both exist — check if anything changed
            patch = _compute_patch_fields(group)
            if not patch:
                action = ACTION_UNCHANGED
                detail = "codex record current"
            elif len(patch) <= 4 and val_status == PASS:
                action = ACTION_PATCH
                detail = f"narrow field update: {list(patch.keys())}"
            elif val_status == REVIEW:
                action = ACTION_REVIEW
                detail = f"{len(patch)} fields differ, needs review"
            else:
                # Large drift or identity-level change
                action = ACTION_REINDEX
                detail = f"{len(patch)} fields changed — full re-normalization"

            patch_fields = patch if action == ACTION_PATCH else {}

        elif not has_library and not has_codex:
            # Behavioral trace only (Last.fm / Spotify)
            action = ACTION_REVIEW
            detail = "behavioral trace only — no library source"
            patch_fields = {}

        else:
            action = ACTION_REVIEW
            detail = "undetermined state"

        patch_fields = _compute_patch_fields(group) if action == ACTION_PATCH else {}

        candidates.append(RefreshCandidate(
            entity_id         = group.entity_id,
            action            = action,
            confidence        = group.confidence,
            validation_status = val_status,
            patch_fields      = patch_fields,
            codex_record_id   = codex_id,
            source_provenance = group.sources_matched,
            detail            = detail,
            scrobble_count    = group.scrobble_count,
            title_raw         = p.title_raw,
            artist_raw        = p.artist_raw,
            album_raw         = p.album_raw,
        ))

    # Summary
    from collections import Counter
    action_counts = Counter(c.action for c in candidates)
    print("[refresh_planner] Plan summary:")
    for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
        print(f"  {action:20s} : {count:,}")

    return candidates


def summarize_plan(candidates: list[RefreshCandidate]) -> dict:
    from collections import Counter, defaultdict
    action_counts = Counter(c.action for c in candidates)
    val_counts    = Counter(c.validation_status for c in candidates)
    patch_field_counts: dict[str, int] = defaultdict(int)
    for c in candidates:
        for f in c.patch_fields:
            patch_field_counts[f] += 1
    return {
        "total_candidates":  len(candidates),
        "by_action":         dict(action_counts),
        "by_validation_status": dict(val_counts),
        "patch_field_frequency": dict(
            sorted(patch_field_counts.items(), key=lambda x: -x[1])
        ),
        "safe_to_apply_count": sum(
            1 for c in candidates
            if c.action in (ACTION_PATCH, ACTION_ADD_NEW)
            and c.validation_status == PASS
            and c.confidence >= 0.85
        ),
    }


# ---------------------------------------------------------------------------
# Artifact writers — produce reviewable output, never auto-apply
# ---------------------------------------------------------------------------

def write_refresh_plan(
    candidates: list[RefreshCandidate],
    out_path: Path,
) -> Path:
    """Write the full refresh plan to JSON. Dry-run only."""
    summary = summarize_plan(candidates)
    data = {
        "dry_run": True,
        "note": (
            "This is a DRY-RUN plan. No codex records are changed until "
            "the operator explicitly applies individual candidates."
        ),
        "summary": summary,
        "candidates": [c.to_dict() for c in candidates],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return out_path


def write_patch_candidates(
    candidates: list[RefreshCandidate],
    out_path: Path,
) -> Path:
    """Write only the ACTION_PATCH candidates — safe narrow updates."""
    patches = [c for c in candidates if c.action == ACTION_PATCH]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(patches),
            "note":  "Narrow field patches — validated PASS, confidence ≥ threshold",
            "patches": [c.to_dict() for c in patches],
        }, f, indent=2, default=str)
    return out_path


def write_manual_review(
    candidates: list[RefreshCandidate],
    out_path: Path,
) -> Path:
    """Write records requiring manual review."""
    review = [c for c in candidates if c.action == ACTION_REVIEW]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(review),
            "note":  "Records requiring manual operator review before any action",
            "records": [c.to_dict() for c in review],
        }, f, indent=2, default=str)
    return out_path


def write_new_candidates(
    candidates: list[RefreshCandidate],
    out_path: Path,
) -> Path:
    """Write add_new candidates — library records not yet in codex."""
    new = [c for c in candidates if c.action == ACTION_ADD_NEW]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(new),
            "note":  "Library tracks not yet mirrored in codex",
            "records": [c.to_dict() for c in new],
        }, f, indent=2, default=str)
    return out_path
