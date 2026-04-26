"""
Template family extractor — Phase 1.3.

Reads Phase 1.2 gold corpus artifacts and the embedded gold article corpus
definitions to produce:

  1. A priority-ranked ingest queue (template → family → tier → seen_in count)
  2. A family assignment map (template name → family_id)

Family assignment uses name-matching heuristics against the four families:

  nfl_biography  — NFL player / front-office / team infoboxes
  vg_infobox     — Video game infoboxes and reception helpers
  executive_bio  — Person / officeholder / executive biography templates
  venue_project  — Stadium / venue / project / infrastructure templates

Priority tiers:
  core           — infoboxes seen in 2+ gold articles (highest value)
  supporting     — navboxes / key helpers seen in 2+ gold articles
  helper         — any template seen once but name-matched to a known family
  low_priority   — navboxes / categories seen once
  deferred       — no family match, seen once only

Reads from: domains/language/tools/wikimedia/template_family_prep_report.json (if present).
Falls back to static gold corpus metadata if the artifact is absent.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_ARTIFACTS = (
    Path(__file__).resolve().parents[5]
    / "domains" / "language" / "wikipedia" / "data"
)

# ---------------------------------------------------------------------------
# Static family definitions
# ---------------------------------------------------------------------------

# Each entry: regex pattern to match template names → family_id
_FAMILY_PATTERNS: list[tuple[re.Pattern, str]] = [
    # NFL / football
    (re.compile(r"(?i)nfl|football|infobox\s+national\s+football"), "nfl_biography"),
    (re.compile(r"(?i)infobox\s+american\s+football"),               "nfl_biography"),
    (re.compile(r"(?i)nfl\s+team|football\s+player"),                "nfl_biography"),

    # Video game
    (re.compile(r"(?i)infobox\s+video\s+game"),                      "vg_infobox"),
    (re.compile(r"(?i)video\s+game\s+(release|ratings|reviews)"),    "vg_infobox"),
    (re.compile(r"(?i)game\s+(nav|navbox|sidebar)"),                  "vg_infobox"),

    # Person / executive biography
    (re.compile(r"(?i)infobox\s+(person|officeholder|politician|businessman|executive)"), "executive_bio"),
    (re.compile(r"(?i)birth\s+date|death\s+date|birth\s+year"),      "executive_bio"),
    (re.compile(r"(?i)short\s+description"),                          "executive_bio"),

    # Venue / project / infrastructure
    (re.compile(r"(?i)infobox\s+(stadium|venue|building|structure|arena)"), "venue_project"),
    (re.compile(r"(?i)stadium|venue|arena"),                          "venue_project"),
]

# Policy codes governing each family
_FAMILY_POLICIES: dict[str, list[str]] = {
    "nfl_biography":  ["WP:NFL", "WP:BLP", "MOS:Biography", "MOS"],
    "vg_infobox":     ["MOS:VG", "WP:GNG", "MOS"],
    "executive_bio":  ["MOS:Biography", "WP:BLP", "WP:GNG", "MOS"],
    "venue_project":  ["WP:NFL", "MOS"],
}

# Priority tier labels
TIER_CORE       = "core"
TIER_SUPPORTING = "supporting"
TIER_HELPER     = "helper"
TIER_LOW        = "low_priority"
TIER_DEFERRED   = "deferred"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assign_family(template_name: str) -> str | None:
    """
    Return the family_id for a template name, or None if no match.
    Uses pattern matching against _FAMILY_PATTERNS.
    """
    for pattern, family_id in _FAMILY_PATTERNS:
        if pattern.search(template_name):
            return family_id
    return None


def build_priority_queue(prep_data: dict[str, Any]) -> list[dict]:
    """
    Given `template_family_prep` data (from GoldCorpusReport or loaded JSON),
    return an ordered priority queue list.

    Each entry:
        {
            "template":    str,
            "family":      str | None,
            "tier":        str,
            "seen_in":     int,
            "articles":    list[str],
            "is_infobox":  bool,
        }
    """
    infobox_inv: dict[str, list[str]] = prep_data.get("infobox_inventory", {})
    navbox_inv:  dict[str, list[str]] = prep_data.get("navbox_inventory", {})
    common_inv:  dict[str, list[str]] = prep_data.get("common_templates", {})

    queue: list[dict] = []

    def _add(name: str, articles: list[str], is_infobox: bool) -> None:
        family = assign_family(name)
        seen = len(articles)

        if is_infobox and seen >= 2:
            tier = TIER_CORE
        elif is_infobox and seen == 1 and family:
            tier = TIER_HELPER
        elif not is_infobox and seen >= 2 and family:
            tier = TIER_SUPPORTING
        elif not is_infobox and seen >= 2:
            tier = TIER_LOW
        elif family:
            tier = TIER_HELPER
        else:
            tier = TIER_DEFERRED

        queue.append({
            "template":   name,
            "family":     family,
            "tier":       tier,
            "seen_in":    seen,
            "articles":   articles,
            "is_infobox": is_infobox,
        })

    for name, articles in infobox_inv.items():
        _add(name, articles, is_infobox=True)

    for name, articles in navbox_inv.items():
        if name not in infobox_inv:
            _add(name, articles, is_infobox=False)

    for name, articles in common_inv.items():
        if name not in infobox_inv and name not in navbox_inv:
            _add(name, articles, is_infobox=False)

    # Sort: core first, then supporting, then helper, then low_priority, deferred last;
    # within tier, sort by seen_in descending
    _tier_rank = {
        TIER_CORE: 0,
        TIER_SUPPORTING: 1,
        TIER_HELPER: 2,
        TIER_LOW: 3,
        TIER_DEFERRED: 4,
    }
    queue.sort(key=lambda e: (_tier_rank.get(e["tier"], 9), -e["seen_in"]))
    return queue


def load_prep_data() -> dict[str, Any]:
    """
    Load template_family_prep_report.json from the wikimedia artifacts dir.
    Returns an empty dict with blank inventories if the file is absent
    (the caller then falls back to static corpus metadata).
    """
    path = _ARTIFACTS / "template_family_prep_report.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # Graceful fallback — return minimal structure so the ingestor can still
    # work with the hard-coded gold corpus metadata.
    return {
        "infobox_inventory": {},
        "navbox_inventory": {},
        "common_templates": {},
        "priority_ingest_queue": [],
        "template_families_implied": [],
        "fragile_area_notes": [],
    }


def families_for_policy(policy_code: str) -> list[str]:
    """Return all family_ids that are governed by a given policy code."""
    return [fid for fid, codes in _FAMILY_POLICIES.items() if policy_code in codes]


def policies_for_family(family_id: str) -> list[str]:
    """Return policy codes that govern a given family."""
    return _FAMILY_POLICIES.get(family_id, [])


# Expose the full policy map for crosswalk building
FAMILY_POLICIES = _FAMILY_POLICIES
