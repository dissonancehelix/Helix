"""
linker.py — Analysis Output → Knowledge Graph Linker
=====================================================
Bridges Helix analysis pipeline outputs (fingerprint vectors, cluster
memberships, motif stats, ludomusicology results) into the ComposerGraph.

After the analysis pipeline produces per-track result dicts and composer
profile clusters, this module:

  1. Attaches fingerprint vectors to ComposerNode objects
  2. Records cluster memberships on ComposerNode + TrackNode
  3. Adds style_traits from ludomusicology (gameplay_role, energy_ramp_type)
  4. Builds `wrote` relationships from attribution confidence scores
  5. Adds representative_tracks lists to ComposerNode based on clusters

API
---
linker = KnowledgeLinker(graph)
linker.link_track_result(track_id, track_result)
linker.link_composer_profiles(profiles)
linker.link_clusters(cluster_result)
linker.link_style_space(style_space_result)
linker.finalize()     → writes everything to graph and stores updated composer nodes
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from domains.music.atlas_integration.composer_graph import ComposerGraph, cid, tid

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# KnowledgeLinker
# ---------------------------------------------------------------------------

class KnowledgeLinker:
    """
    Links analysis results from the S3K pipeline into the ComposerGraph.

    Usage::

        linker = KnowledgeLinker(graph)
        for track_id, result in track_results.items():
            linker.link_track_result(track_id, result)
        linker.link_composer_profiles(composer_profiles)
        linker.link_clusters(pattern_discovery_dict)
        linker.finalize()

    """

    def __init__(self, graph: ComposerGraph) -> None:
        self.graph = graph
        self._pending_vectors:     dict[str, list[float]] = {}   # composer_id → vector
        self._pending_clusters:    dict[str, list[str]]   = {}   # composer_id → [cluster_ids]
        self._pending_rep_tracks:  dict[str, list[str]]   = {}   # composer_id → [track_ids]
        self._track_attributions:  dict[str, list[tuple[str, float]]] = {}  # track_id → [(composer_id, conf)]
        self._style_traits_buffer: dict[str, dict[str, Any]] = {} # composer_id → traits

    # -----------------------------------------------------------------------
    # Per-track result
    # -----------------------------------------------------------------------

    def link_track_result(
        self,
        track_id: str,
        result:   dict[str, Any],
    ) -> None:
        """
        Ingest a single track analysis result dict from s3k_analysis_pipeline.

        Reads:
          result["attribution"]["composerAttributions"]  — list of {composer_id, confidence}
          result["ludomusicology"]                        — gameplay_role, energy_ramp_type, etc.
          result["layer1"]["fingerprint"]                — optional per-track vector
        """
        # --- Attribution ---
        attribution = result.get("attribution", {}) or {}
        attribs = attribution.get("composerAttributions", []) or []
        if attribs:
            self._track_attributions[track_id] = [
                (a["composer_id"], float(a.get("confidence", 0.5)))
                for a in attribs
                if a.get("composer_id")
            ]

        # --- Ludomusicology traits → style_traits on composer nodes ---
        ludo = result.get("ludomusicology", {}) or {}
        if ludo:
            role      = ludo.get("gameplay_role")
            ramp_type = ludo.get("energy_ramp_type")
            loop_stab = ludo.get("loop_stability_index")
            energy_var = ludo.get("energy_variance")

            # Apply traits to each attributed composer with > 0.5 confidence
            for composer_id, conf in self._track_attributions.get(track_id, []):
                if conf < 0.5:
                    continue
                buf = self._style_traits_buffer.setdefault(composer_id, {})
                # Accumulate gameplay roles
                roles_seen = buf.setdefault("gameplay_roles_seen", [])
                if role and role != "unknown" and role not in roles_seen:
                    roles_seen.append(role)
                # Track ramp types
                ramps_seen = buf.setdefault("energy_ramp_types", [])
                if ramp_type and ramp_type not in ramps_seen:
                    ramps_seen.append(ramp_type)
                # Accumulate loop stability
                stab_list = buf.setdefault("loop_stability_samples", [])
                if loop_stab is not None:
                    stab_list.append(float(loop_stab))
                # Accumulate energy variance
                var_list = buf.setdefault("energy_variance_samples", [])
                if energy_var is not None:
                    var_list.append(float(energy_var))

        # --- Update TrackNode attribution confidence ---
        track_node = self.graph.get_track(track_id)
        if track_node and attribs:
            best = max(attribs, key=lambda a: a.get("confidence", 0), default=None)
            if best:
                track_node.attribution_confidence = float(best.get("confidence", 1.0))
                if best["composer_id"] not in track_node.composers:
                    track_node.composers.insert(0, best["composer_id"])

        # --- Add attributed_to relationships ---
        for composer_id, conf in self._track_attributions.get(track_id, []):
            # Only add if not already present
            existing_rels = self.graph.relationships_between(
                cid(composer_id), tid(track_id)
            )
            if not any(r.relation == "attributed_to" for r in existing_rels):
                self.graph.relate(
                    cid(composer_id), "attributed_to", tid(track_id),
                    confidence=conf, source_name="helix_analysis",
                )
                log.debug("linker: %s -attributed_to-> %s (%.2f)", composer_id, track_id, conf)

    # -----------------------------------------------------------------------
    # Composer profiles
    # -----------------------------------------------------------------------

    def link_composer_profiles(
        self,
        profiles: dict[str, Any],
    ) -> None:
        """
        Ingest composer profile dicts from analysis pipeline.

        profiles: { composer_id: { "fingerprint_vector": [...], "style_traits": {...}, ... } }
        """
        for composer_id, profile in profiles.items():
            node = self.graph.get_composer(composer_id)
            if not node:
                log.debug("linker: composer '%s' not in graph — skipping profile", composer_id)
                continue

            vec = profile.get("fingerprint_vector")
            if vec:
                self._pending_vectors[composer_id] = vec

            traits = profile.get("style_traits", {})
            if traits:
                buf = self._style_traits_buffer.setdefault(composer_id, {})
                buf.update(traits)

    # -----------------------------------------------------------------------
    # Cluster results
    # -----------------------------------------------------------------------

    def link_clusters(
        self,
        cluster_result: dict[str, Any],
    ) -> None:
        """
        Ingest cluster results from pattern_discovery.discover().

        Reads:
          cluster_result["clusters"]     — list of {cluster_id, track_ids}
          cluster_result["motif_families"] — list of {family_id, track_ids, ...}
        """
        clusters = cluster_result.get("clusters") or []
        for cluster in clusters:
            cluster_id = cluster.get("cluster_id", "")
            track_ids  = cluster.get("track_ids", [])

            for track_id in track_ids:
                # Update TrackNode cluster memberships via its composers
                for composer_id, conf in self._track_attributions.get(track_id, []):
                    if conf >= 0.5:
                        cl = self._pending_clusters.setdefault(composer_id, [])
                        if cluster_id not in cl:
                            cl.append(cluster_id)

        # Motif families → representative_tracks (top composers by motif coverage)
        motif_families = cluster_result.get("motif_families") or []
        for family in motif_families:
            family_id = family.get("family_id", "")
            track_ids = family.get("track_ids", [])
            for track_id in track_ids:
                for composer_id, conf in self._track_attributions.get(track_id, []):
                    if conf >= 0.6:
                        rep = self._pending_rep_tracks.setdefault(composer_id, [])
                        if track_id not in rep:
                            rep.append(track_id)

    # -----------------------------------------------------------------------
    # Style space
    # -----------------------------------------------------------------------

    def link_style_space(
        self,
        style_space: dict[str, Any],
    ) -> None:
        """
        Ingest style space projections.

        Reads:
          style_space["pca_2d"]  — {track_id: [x, y]}
          style_space["tools_used"]
        """
        pca = style_space.get("pca_2d", {})
        for track_id, coords in pca.items():
            for composer_id, conf in self._track_attributions.get(track_id, []):
                if conf >= 0.5:
                    buf = self._style_traits_buffer.setdefault(composer_id, {})
                    positions = buf.setdefault("style_space_positions", [])
                    positions.append({
                        "track_id": track_id,
                        "pca_2d":   [round(c, 4) for c in coords],
                    })

    # -----------------------------------------------------------------------
    # Finalize
    # -----------------------------------------------------------------------

    def finalize(self) -> dict[str, int]:
        """
        Flush all pending data into the graph.
        Returns summary counts.
        """
        updated_nodes = 0
        updated_traits = 0

        for composer_id, vec in self._pending_vectors.items():
            node = self.graph.get_composer(composer_id)
            if node:
                node.fingerprint_vector = [round(v, 4) for v in vec]
                updated_nodes += 1

        for composer_id, cl_ids in self._pending_clusters.items():
            node = self.graph.get_composer(composer_id)
            if node:
                existing = set(node.cluster_memberships)
                for cl in cl_ids:
                    if cl not in existing:
                        node.cluster_memberships.append(cl)
                        existing.add(cl)

        for composer_id, rep_tracks in self._pending_rep_tracks.items():
            node = self.graph.get_composer(composer_id)
            if node:
                existing = set(node.representative_tracks)
                for t in rep_tracks:
                    if t not in existing:
                        node.representative_tracks.append(t)
                        existing.add(t)

        for composer_id, buf_traits in self._style_traits_buffer.items():
            node = self.graph.get_composer(composer_id)
            if node:
                # Summarize sampled lists
                finalized = dict(node.style_traits)
                for key, val in buf_traits.items():
                    if isinstance(val, list) and "_samples" in key:
                        # Convert sample list to mean
                        base_key = key.replace("_samples", "_mean")
                        if val:
                            finalized[base_key] = round(sum(val) / len(val), 4)
                    else:
                        finalized[key] = val
                node.style_traits = finalized
                updated_traits += 1

        log.info(
            "linker.finalize: updated %d composer nodes, %d trait blocks",
            updated_nodes, updated_traits,
        )
        return {
            "updated_nodes":  updated_nodes,
            "updated_traits": updated_traits,
            "vectors_applied": len(self._pending_vectors),
            "clusters_applied": len(self._pending_clusters),
        }


# ---------------------------------------------------------------------------
# Convenience: link full pipeline output in one call
# ---------------------------------------------------------------------------

def link_pipeline_output(
    graph:           ComposerGraph,
    track_results:   dict[str, Any],
    composer_profiles: dict[str, Any] | None = None,
    cluster_result:  dict[str, Any] | None = None,
    style_space:     dict[str, Any] | None = None,
) -> dict[str, int]:
    """
    One-shot link of all pipeline outputs into the graph.

    Parameters
    ----------
    graph : ComposerGraph
    track_results : dict
        Mapping track_id → full analysis result dict (from pipeline run()).
    composer_profiles : dict, optional
        Composer profile dicts from analysis (fingerprint_vector, style_traits).
    cluster_result : dict, optional
        Output of pattern_discovery.discover().to_dict()
    style_space : dict, optional
        Output of style_space.compute().to_dict()
    """
    linker = KnowledgeLinker(graph)

    for track_id, result in track_results.items():
        try:
            linker.link_track_result(track_id, result)
        except Exception as exc:
            log.warning("linker: track '%s' error: %s", track_id, exc)

    if composer_profiles:
        try:
            linker.link_composer_profiles(composer_profiles)
        except Exception as exc:
            log.warning("linker: composer_profiles error: %s", exc)

    if cluster_result:
        try:
            linker.link_clusters(cluster_result)
        except Exception as exc:
            log.warning("linker: cluster_result error: %s", exc)

    if style_space:
        try:
            linker.link_style_space(style_space)
        except Exception as exc:
            log.warning("linker: style_space error: %s", exc)

    return linker.finalize()
