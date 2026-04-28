"""
Template family dossiers — Phase 1.3 data classes.

A "template family" is a named cluster of Wikipedia templates that operate together
across one or more article archetypes. Each family carries:

  - A live-ingested parameter inventory (from TemplateData)
  - Alias normalisation map (alias → canonical param name)
  - Fragile-param list (params where wrong format triggers known breakage patterns)
  - Per-family breakage patterns (drawn from anti_patterns + operator experience)
  - Article crosswalk (which gold articles use this family)
  - Policy crosswalk (which policies govern this family)

Families defined here:
  nfl_biography     — NFL player / personnel / team infoboxes
  vg_infobox        — Video game infoboxes and reception helpers
  executive_bio     — Person / officeholder / executive biography templates
  venue_project     — Stadium / venue / infrastructure article templates

All structures are JSON-serialisable via .to_dict().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Per-template member within a family
# ---------------------------------------------------------------------------

@dataclass
class TemplateFamilyMember:
    """One template within a family, post-ingest."""
    name: str                         # e.g. "Infobox NFL player"
    full_title: str                   # e.g. "Template:Infobox NFL player"
    family_id: str                    # e.g. "nfl_biography"
    priority_tier: str                # "core" | "supporting" | "helper" | "low_priority" | "deferred"

    # Ingest status
    fetch_ok: bool
    fetch_error: str | None

    # TemplateData-derived
    param_names: list[str]
    alias_map: dict[str, str]         # alias → canonical param name
    required_params: list[str]
    suggested_params: list[str]
    param_descriptions: dict[str, str]

    # Fragility analysis
    fragile_params: list[str]         # params most often involved in breakage
    fragility_notes: list[str]        # human-readable notes per fragile param

    # Source availability
    has_source: bool
    has_doc: bool
    has_templatedata: bool

    # Articles in gold corpus that use this template
    seen_in_articles: list[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "full_title": self.full_title,
            "family_id": self.family_id,
            "priority_tier": self.priority_tier,
            "fetch_ok": self.fetch_ok,
            "fetch_error": self.fetch_error,
            "param_names": self.param_names,
            "alias_map": self.alias_map,
            "required_params": self.required_params,
            "suggested_params": self.suggested_params,
            "fragile_params": self.fragile_params,
            "fragility_notes": self.fragility_notes,
            "has_source": self.has_source,
            "has_doc": self.has_doc,
            "has_templatedata": self.has_templatedata,
            "seen_in_articles": self.seen_in_articles,
        }


# ---------------------------------------------------------------------------
# Family-level dossier
# ---------------------------------------------------------------------------

@dataclass
class FamilyDossier:
    """
    Aggregated dossier for one template family.

    Combines per-member data into a family-level view:
    parameter union, alias normalisation, fragility map, policy links.
    """
    family_id: str                    # "nfl_biography" | "vg_infobox" | "executive_bio" | "venue_project"
    family_name: str                  # display name
    description: str

    member_templates: list[TemplateFamilyMember]

    # Aggregated param view across the family
    param_union: list[str]            # all unique param names across members
    alias_union: dict[str, str]       # alias → canonical, merged across members

    # Shared fragile params (appear in 2+ members or are known high-risk)
    shared_fragile_params: list[str]
    breakage_patterns: list[dict]     # [{id, name, description, severity, templates_affected}]

    # Policies that govern this family
    policy_codes: list[str]           # e.g. ["WP:NFL", "WP:BLP", "MOS:Biography"]

    # Gold corpus coverage
    articles_using_family: list[str]

    # Sandbox / validation notes
    sandbox_notes: list[str]

    def to_dict(self) -> dict:
        return {
            "family_id": self.family_id,
            "family_name": self.family_name,
            "description": self.description,
            "member_count": len(self.member_templates),
            "members": [m.to_dict() for m in self.member_templates],
            "param_union": self.param_union,
            "alias_union": self.alias_union,
            "shared_fragile_params": self.shared_fragile_params,
            "breakage_patterns": self.breakage_patterns,
            "policy_codes": self.policy_codes,
            "articles_using_family": self.articles_using_family,
            "sandbox_notes": self.sandbox_notes,
        }

    def display(self) -> str:
        lines = [
            f"Family: {self.family_name}  [{self.family_id}]",
            f"  {self.description}",
            f"  Members     : {len(self.member_templates)}",
            f"  Policies    : {', '.join(self.policy_codes)}",
            f"  Articles    : {', '.join(self.articles_using_family)}",
            f"  Params (union): {len(self.param_union)}",
            f"  Fragile params: {', '.join(self.shared_fragile_params) or 'none identified'}",
            "",
            "  Breakage patterns:",
        ]
        for bp in self.breakage_patterns:
            lines.append(f"    [{bp.get('severity','?').upper():6s}] {bp['name']}")
        lines.append("")
        lines.append("  Sandbox notes:")
        for note in self.sandbox_notes:
            lines.append(f"    - {note}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full report
# ---------------------------------------------------------------------------

@dataclass
class TemplateFamilyIngestReport:
    """
    Full output of Phase 1.3 template family ingest.
    Produced by TemplateFamilyIngestor.run().
    """
    families: dict[str, FamilyDossier]     # family_id → FamilyDossier
    priority_queue: list[dict]             # ordered list of {template, family, tier, seen_in}
    family_article_crosswalk: dict[str, list[str]]   # family_id → [article titles]
    family_policy_crosswalk: dict[str, list[str]]    # family_id → [policy_codes]
    article_family_crosswalk: dict[str, list[str]]   # article title → [family_ids]
    fetch_summary: dict[str, int]          # ok, errors, total_templates

    def to_dict(self) -> dict:
        return {
            "fetch_summary": self.fetch_summary,
            "families": {fid: d.to_dict() for fid, d in self.families.items()},
            "priority_queue": self.priority_queue,
            "family_article_crosswalk": self.family_article_crosswalk,
            "family_policy_crosswalk": self.family_policy_crosswalk,
            "article_family_crosswalk": self.article_family_crosswalk,
        }
