"""
Template family crosswalk builders — Phase 1.3.

Three crosswalks are built from FamilyDossier data:

  family_article_crosswalk  : family_id → [article titles]
  family_policy_crosswalk   : family_id → [policy codes]
  article_family_crosswalk  : article title → [family_ids]

These are saved as standalone JSON artifacts and embedded inside
TemplateFamilyIngestReport for downstream use by the issue solver and
patch critic.
"""
from __future__ import annotations

from apps.language_pipeline.template_families.family_dossier import FamilyDossier


def build_family_article_crosswalk(
    families: dict[str, "FamilyDossier"],
) -> dict[str, list[str]]:
    """
    Return {family_id: [article_title, ...]} for every family that has
    at least one gold corpus article using it.
    """
    return {
        fid: sorted(d.articles_using_family)
        for fid, d in families.items()
        if d.articles_using_family
    }


def build_family_policy_crosswalk(
    families: dict[str, "FamilyDossier"],
) -> dict[str, list[str]]:
    """
    Return {family_id: [policy_code, ...]} for every family.
    """
    return {
        fid: d.policy_codes
        for fid, d in families.items()
    }


def build_article_family_crosswalk(
    families: dict[str, "FamilyDossier"],
) -> dict[str, list[str]]:
    """
    Invert family_article_crosswalk:
    Return {article_title: [family_id, ...]} so the issue solver can quickly
    look up which template families apply to any given article.
    """
    result: dict[str, list[str]] = {}
    for fid, d in families.items():
        for article in d.articles_using_family:
            result.setdefault(article, []).append(fid)
    # Sort family lists for determinism
    return {art: sorted(fids) for art, fids in sorted(result.items())}
