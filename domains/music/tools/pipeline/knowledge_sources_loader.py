"""
knowledge_sources_loader.py — Orchestrates all knowledge source ingesters
=========================================================================
Convenience wrapper that calls all available ingesters and enriches the graph.

API
---
load_all_sources(graph, enrich_online=False) -> dict[str, Any]
"""

from __future__ import annotations

import logging
from typing import Any

from model.domains.music.atlas_integration.composer_graph import ComposerGraph

log = logging.getLogger(__name__)


def load_all_sources(
    graph: ComposerGraph,
    enrich_online: bool = False,
) -> dict[str, Any]:
    """
    Run all available knowledge source ingesters against `graph`.

    Parameters
    ----------
    graph : ComposerGraph
        Target graph to populate.
    enrich_online : bool
        If True, also run network-dependent ingesters (Wikidata, VGMDB).
        Default False — offline HTML sources only.

    Returns
    -------
    dict with per-source result summaries.
    """
    summary: dict[str, Any] = {}

    # --- Sonic Retro HTML (offline, always available) ---
    try:
        from model.domains.music.atlas_integration.sources.sonic_retro_ingester import ingest_s3k_default
        result = ingest_s3k_default(graph)
        summary["sonic_retro"] = str(result)
        log.info("knowledge_sources: sonic_retro → %s", result)
    except Exception as exc:
        summary["sonic_retro_error"] = str(exc)
        log.warning("knowledge_sources: sonic_retro failed: %s", exc)

    if not enrich_online:
        return summary

    # --- Wikidata (online, requires network) ---
    try:
        from model.domains.music.atlas_integration.sources.wikidata_ingester import enrich_composer
        enriched = 0
        for c in graph.all_composers():
            wikidata_id = c.external_ids.get("wikidata")
            if wikidata_id:
                try:
                    enrich_composer(c)
                    enriched += 1
                except Exception as exc_inner:
                    log.debug("wikidata: %s failed: %s", c.composer_id, exc_inner)
        summary["wikidata"] = f"enriched {enriched} composers"
        log.info("knowledge_sources: wikidata enriched %d composers", enriched)
    except Exception as exc:
        summary["wikidata_error"] = str(exc)
        log.warning("knowledge_sources: wikidata failed: %s", exc)

    # --- VGMDB (online, requires network) ---
    try:
        from model.domains.music.atlas_integration.sources.vgmdb_ingester import enrich_composer as vgmdb_enrich
        enriched = 0
        for c in graph.all_composers():
            vgmdb_id = c.external_ids.get("vgmdb")
            if vgmdb_id:
                try:
                    vgmdb_enrich(c)
                    enriched += 1
                except Exception as exc_inner:
                    log.debug("vgmdb: %s failed: %s", c.composer_id, exc_inner)
        summary["vgmdb"] = f"enriched {enriched} composers"
        log.info("knowledge_sources: vgmdb enriched %d composers", enriched)
    except Exception as exc:
        summary["vgmdb_error"] = str(exc)
        log.warning("knowledge_sources: vgmdb failed: %s", exc)

    return summary

