"""
repair_plan.py — Patch plan generation for the Foobar tool.

Generates reviewable repair plans from audit and sync results.
Does NOT mutate Foobar metadata, SQLite internals, or external tags.
All output is opinionated but operator-approved before any action is taken.

Patch model (v0):
  ALLOWED:   write reports, write codex-side index refreshes (explicit only)
  NOT DEFAULT: mutate Foobar metadata, rewrite external tags, modify SQLite
"""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .diff import _norm, _norm_bool, _norm_int
from .reports import write_json, _now_str, ARTIFACTS_DIR

# ---------------------------------------------------------------------------
# Patch action types
# ---------------------------------------------------------------------------

# Safe patch actions in v0 (read/plan side only)
PATCH_ACTIONS_V0 = {
    "codex_mirror_update":   "Update codex mirror record to match Foobar metadata",
    "codex_field_patch":     "Patch a single field in the codex mirror",
    "codex_loved_sync":      "Sync loved/stats state from Foobar to codex",
    "reindex_affected":      "Rebuild field index for affected records",
    "flag_for_review":       "Flag track for manual operator review",
    "export_to_sidecar":     "(FUTURE) Export corrected fields to sidecar .tag file",
    "apply_to_foobar_db":    "(FUTURE) Apply patch to Foobar SQLite — not default in v0",
}

# Patch risk levels
RISK_LEVELS = {
    "codex_mirror_update": "low",
    "codex_field_patch":   "low",
    "codex_loved_sync":    "low",
    "reindex_affected":    "low",
    "flag_for_review":     "none",
    "export_to_sidecar":   "medium",    # writes to disk next to audio files
    "apply_to_foobar_db":  "high",      # mutates Foobar internals — not v0 default
}


# ---------------------------------------------------------------------------
# PatchAction dataclass
# ---------------------------------------------------------------------------

class PatchAction:
    """A single reviewable patch action."""

    def __init__(
        self,
        file_path: str,
        action: str,
        field: str | None,
        current_value: Any,
        proposed_value: Any,
        reason: str,
        source: str = "foobar_audit",
    ):
        self.file_path = file_path
        self.action = action
        self.field = field
        self.current_value = current_value
        self.proposed_value = proposed_value
        self.reason = reason
        self.source = source
        self.risk = RISK_LEVELS.get(action, "unknown")

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "action": self.action,
            "field": self.field,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "reason": self.reason,
            "source": self.source,
            "risk": self.risk,
        }


# ---------------------------------------------------------------------------
# Plan generators per audit type
# ---------------------------------------------------------------------------

def plan_from_metadata_drift(track_results: list[dict]) -> list[PatchAction]:
    """
    Generate codex patch actions for tracks with metadata drift.
    Proposes: codex_field_patch — updates codex mirror to match Foobar (Foobar is authoritative).
    """
    actions = []
    for tr in track_results:
        if "metadata_drift" not in tr.get("states", []):
            continue

        td = tr.get("diff")
        if not td:
            continue

        path = tr.get("file_path", "")
        for d in td.metadata_diffs:
            if not d.changed:
                continue
            actions.append(PatchAction(
                file_path=path,
                action="codex_field_patch",
                field=d.field,
                current_value=d.codex_value,
                proposed_value=d.foobar_value,
                reason="Foobar is authoritative for mutable metadata; codex mirror is stale",
            ))

    return actions


def plan_from_loved_drift(loved_audit: dict) -> list[PatchAction]:
    """
    Generate codex patch actions for loved/stats drift.
    Proposes: codex_loved_sync — updates codex loved/playcount to match Foobar.
    """
    actions = []

    for item in loved_audit.get("loved_drift", []):
        path = item.get("file_path", "")
        actions.append(PatchAction(
            file_path=path,
            action="codex_loved_sync",
            field="loved",
            current_value=None,  # codex value
            proposed_value=True,
            reason="Track is loved in Foobar but codex mirror does not reflect this",
        ))

    for item in loved_audit.get("stats_drift", []):
        path = item.get("file_path", "")
        fb_pc = item.get("foobar_playcount")
        cx_pc = item.get("codex_playcount")
        if fb_pc != cx_pc:
            actions.append(PatchAction(
                file_path=path,
                action="codex_loved_sync",
                field="play_count",
                current_value=cx_pc,
                proposed_value=fb_pc,
                reason="Playcount drifted between Foobar and codex",
            ))

    return actions


def plan_from_new_tracks(sync_result: dict) -> list[PatchAction]:
    """
    Generate codex mirror update actions for tracks new in Foobar.
    Proposes: codex_mirror_update — add track to codex.
    """
    actions = []
    for tr in sync_result.get("track_results", []):
        if "new_in_foobar" not in tr.get("states", []):
            continue
        fb = tr.get("foobar_record", {})
        path = fb.get("file_path", "")
        actions.append(PatchAction(
            file_path=path,
            action="codex_mirror_update",
            field=None,
            current_value=None,
            proposed_value=fb,
            reason="Track exists in Foobar library but is not yet indexed in codex",
        ))
    return actions


def plan_from_schema_gaps(track_results: list[dict]) -> list[PatchAction]:
    """
    Flag tracks with schema gaps for review.
    Does not propose automatic values — operator must supply missing custom fields.
    """
    actions = []
    for tr in track_results:
        if "schema_gap" not in tr.get("states", []):
            continue
        td = tr.get("diff")
        path = tr.get("file_path", "")
        missing = td.missing_schema_fields if td else []
        for f in missing:
            actions.append(PatchAction(
                file_path=path,
                action="flag_for_review",
                field=f,
                current_value=None,
                proposed_value=None,
                reason=f"Custom schema field '{f}' is missing — operator must supply value",
            ))
    return actions


def plan_from_corpus(corpus_result: dict) -> list[PatchAction]:
    """
    Generate patch actions from a research corpus integrity check.
    Flags drift and coverage gaps for review.
    """
    actions = []
    issues = corpus_result.get("issues", [])
    name = corpus_result.get("corpus_name", "corpus")

    for iss in issues:
        code = iss.get("issue_code", "")

        if code == "corpus_metadata_drift":
            for affected in iss.get("affected_tracks", []):
                for f in affected.get("drifted_fields", []):
                    actions.append(PatchAction(
                        file_path=affected.get("file_path", ""),
                        action="codex_field_patch",
                        field=f,
                        current_value=None,
                        proposed_value=None,
                        reason=f"[{name}] Analysis-critical field '{f}' drifted — "
                               "may affect downstream pipeline inputs",
                    ))

        elif code == "corpus_schema_gaps":
            for affected in iss.get("affected_tracks", []):
                for f in affected.get("missing_fields", []):
                    actions.append(PatchAction(
                        file_path=affected.get("file_path", ""),
                        action="flag_for_review",
                        field=f,
                        current_value=None,
                        proposed_value=None,
                        reason=f"[{name}] Custom schema field '{f}' missing in research corpus",
                    ))

        elif code == "corpus_partial_codex_coverage":
            actions.append(PatchAction(
                file_path="",
                action="reindex_affected",
                field=None,
                current_value=None,
                proposed_value=None,
                reason=f"[{name}] {iss.get('detail')} — run codex refresh for this corpus",
            ))

    return actions


# ---------------------------------------------------------------------------
# Full repair plan builder
# ---------------------------------------------------------------------------

def build_repair_plan(
    sync_result: dict,
    library_audit: dict,
    loved_audit: dict,
    corpus_results: list[dict] | None = None,
) -> list[PatchAction]:
    """
    Build the complete repair plan from all audit sources.
    Returns a list of PatchActions ordered by risk (low → high).
    """
    actions = []

    actions.extend(plan_from_new_tracks(sync_result))
    actions.extend(plan_from_metadata_drift(sync_result.get("track_results", [])))
    actions.extend(plan_from_loved_drift(loved_audit))
    actions.extend(plan_from_schema_gaps(sync_result.get("track_results", [])))

    if corpus_results:
        for cr in corpus_results:
            actions.extend(plan_from_corpus(cr))

    # Sort: low risk first, then medium, then high
    _risk_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "unknown": 4}
    actions.sort(key=lambda a: (_risk_order.get(a.risk, 9), a.file_path))

    return actions


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def write_repair_plan_csv(actions: list[PatchAction]) -> Path:
    """Write repair plan as CSV for operator review."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS_DIR / "repair_plan.csv"

    fieldnames = ["risk", "action", "field", "file_path",
                  "current_value", "proposed_value", "reason", "source"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in actions:
            d = a.to_dict()
            # Truncate long values for readability
            for key in ("current_value", "proposed_value"):
                val = d.get(key)
                if isinstance(val, dict):
                    d[key] = json.dumps(val)[:120]
                elif val is not None:
                    d[key] = str(val)[:120]
            writer.writerow(d)

    return path


def write_repair_plan_json(actions: list[PatchAction]) -> Path:
    """Write repair plan as JSON."""
    data = {
        "generated": _now_str(),
        "total_actions": len(actions),
        "by_action": {},
        "by_risk": {},
        "actions": [a.to_dict() for a in actions],
    }

    for a in actions:
        data["by_action"][a.action] = data["by_action"].get(a.action, 0) + 1
        data["by_risk"][a.risk] = data["by_risk"].get(a.risk, 0) + 1

    return write_json("repair_plan.json", data)


def print_repair_plan_summary(actions: list[PatchAction]) -> None:
    by_action: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for a in actions:
        by_action[a.action] = by_action.get(a.action, 0) + 1
        by_risk[a.risk] = by_risk.get(a.risk, 0) + 1

    print()
    print("=== Repair Plan Summary ===")
    print(f"  Total actions: {len(actions)}")
    print()
    print("  By risk:")
    for risk in ("none", "low", "medium", "high"):
        cnt = by_risk.get(risk, 0)
        if cnt:
            print(f"    {risk:<10} {cnt}")
    print()
    print("  By action type:")
    for action, cnt in sorted(by_action.items()):
        print(f"    {action:<35} {cnt}")
    print()
    print("  [!] Review repair_plan.csv before applying any changes.")
    print("  [!] v0 does NOT automatically apply patches to Foobar or external tags.")
