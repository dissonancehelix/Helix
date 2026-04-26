"""
Language-domain DCP and substrate analysis hooks.

This module translates construction-space fixtures into Helix-native substrate
and DCP artifacts. The mapping is heuristic but uses the shared DCP schemas
rather than a language-local ad hoc format.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from core.invariants.dcp.event import DCPEvent, DCPProbeOutput
from core.invariants.dcp.metrics import compute_dcp_score
from core.invariants.dcp.morphology import CollapseMorphology

SUBSTRATE_SCHEMA_VERSION = "language_substrate_v1"
TRAJECTORY_SCHEMA_VERSION = "language_trajectory_v1"
DCP_BLOCK_SCHEMA_VERSION = "language_dcp_block_v1"


def build_language_substrate_profile(
    *,
    language: str,
    structural_vector: dict[str, Any],
    construction_graph: dict[str, Any],
) -> dict[str, Any]:
    centroid = structural_vector.get("centroid", {})
    frame_concentration = structural_vector.get("frame_concentration", {})
    attractors = construction_graph.get("attractors", [])
    families = construction_graph.get("families", {})
    edges = [
        edge for edge in construction_graph.get("edges", [])
        if edge.get("label") != "family_proximity"
    ]

    mean_edge_distance = _mean(edge.get("distance", 0.0) for edge in edges)
    mean_attractor_cohesion = _mean(item.get("cohesion", 1.0) for item in attractors[:3]) if attractors else 1.0
    top_frames = list(frame_concentration.values())[:3]

    possibility_space = _clamp(
        (
            float(centroid.get("lexical_variation", 0.0))
            + min(len(families) / 8.0, 1.0)
            + (1.0 - float(centroid.get("frame_stability", 0.0)))
        ) / 3.0
    )
    constraint = _clamp(
        (
            float(centroid.get("inflectional_load", 0.0))
            + float(centroid.get("function_word_scaffolding", 0.0))
            + float(centroid.get("clause_subordination", 0.0))
        ) / 3.0
    )
    attractor_stability = _clamp(1.0 - mean_attractor_cohesion)
    basin_permeability = _clamp(1.0 - mean_edge_distance)
    recurrence_depth = _clamp(sum(top_frames) / len(top_frames)) if top_frames else 0.0

    return {
        "domain": "language",
        "language": language,
        "block": "substrate",
        "schema_version": SUBSTRATE_SCHEMA_VERSION,
        "possibility_space": round(possibility_space, 4),
        "constraint": round(constraint, 4),
        "attractor_stability": round(attractor_stability, 4),
        "basin_permeability": round(basin_permeability, 4),
        "recurrence_depth": round(recurrence_depth, 4),
        "source": "construction_space_fixture",
        "evidence": {
            "signals": [
                {
                    "name": "lexical_variation",
                    "value": round(float(centroid.get("lexical_variation", 0.0)), 4),
                    "axis": "possibility_space",
                },
                {
                    "name": "frame_stability_inverse",
                    "value": round(1.0 - float(centroid.get("frame_stability", 0.0)), 4),
                    "axis": "possibility_space",
                },
                {
                    "name": "inflectional_load",
                    "value": round(float(centroid.get("inflectional_load", 0.0)), 4),
                    "axis": "constraint",
                },
                {
                    "name": "function_word_scaffolding",
                    "value": round(float(centroid.get("function_word_scaffolding", 0.0)), 4),
                    "axis": "constraint",
                },
                {
                    "name": "clause_subordination",
                    "value": round(float(centroid.get("clause_subordination", 0.0)), 4),
                    "axis": "constraint",
                },
                {
                    "name": "mean_attractor_cohesion_inverse",
                    "value": round(1.0 - mean_attractor_cohesion, 4),
                    "axis": "attractor_stability",
                },
                {
                    "name": "mean_edge_distance_inverse",
                    "value": round(1.0 - mean_edge_distance, 4),
                    "axis": "basin_permeability",
                },
                {
                    "name": "top_frame_recurrence",
                    "value": round(recurrence_depth, 4),
                    "axis": "recurrence_depth",
                },
            ],
            "source_features": [
                f"construction_families: {len(families)}",
                f"transform_edges: {len(edges)}",
                f"top_attractors: {', '.join(item.get('family', '?') for item in attractors[:3]) or 'none'}",
            ],
            "notes": "Substrate axes are derived from centroid signals plus construction-family geometry.",
        },
        "notes": (
            "Heuristic grammar substrate profile derived from construction-space "
            "families, structural vector centroid, and attractor cohesion."
        ),
    }


def build_language_dcp_artifacts(
    *,
    language: str,
    corpus: str,
    structural_vector: dict[str, Any],
    construction_graph: dict[str, Any],
    null_model: dict[str, Any],
    source_artifact: str,
) -> dict[str, Any]:
    nodes = {node["id"]: node for node in construction_graph.get("nodes", [])}
    families = construction_graph.get("families", {})
    edges = [
        edge for edge in construction_graph.get("edges", [])
        if edge.get("label") != "family_proximity"
    ]
    if not edges:
        empty_probe = DCPProbeOutput(
            agent_id=f"{language}.{corpus}",
            source_domain="language",
            constraint_profile={"class": "internal", "intensity": 0.0, "notes": "no construction edges"},
            collapse_detected=False,
            confidence=0.0,
            notes="No construction-family transforms available.",
        )
        return {
            "trajectory_dynamics": {
                "schema_version": TRAJECTORY_SCHEMA_VERSION,
                "families": [],
                "process_model": "possibility→constraint→tension→collapse→trajectory",
                "family_count": 0,
                "morphology_histogram": {},
            },
            "dcp_events": [],
            "dcp_block": {
                "block": "dcp",
                "schema_version": DCP_BLOCK_SCHEMA_VERSION,
                "possibility_space": 0.0,
                "constraint": 0.0,
                "tension": 0.0,
                "collapse": 0.0,
                "post_narrowing": 0.0,
                "composite": 0.0,
                "qualification": "INSUFFICIENT",
                "event_count": 0,
                "dominant_morphology": None,
                "constraint_class": "internal",
                "source_artifact": source_artifact,
                "evidence": {
                    "signals": [],
                    "source_features": [],
                    "notes": "No construction-family transforms were available for language DCP extraction.",
                },
            },
            "probe_output": empty_probe.to_dict(),
        }

    max_edge_distance = max(float(edge.get("distance", 0.0)) for edge in edges) or 1.0
    trajectory_families: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    event_scores: list[tuple[str, float]] = []

    for index, edge in enumerate(edges, 1):
        source = nodes.get(edge["source"], {})
        target = nodes.get(edge["target"], {})
        source_coords = source.get("coordinates", {})
        target_coords = target.get("coordinates", {})
        family = str(edge.get("family", "ungrouped"))
        family_stats = families.get(family, {})
        family_cohesion = float(family_stats.get("cohesion", 1.0))

        axis_deltas = {
            axis: round(float(target_coords.get(axis, 0.0)) - float(source_coords.get(axis, 0.0)), 4)
            for axis in sorted(set(source_coords) | set(target_coords))
        }
        axis_change = _mean(abs(value) for value in axis_deltas.values())

        possibility = _clamp(
            (
                float(source_coords.get("lexical_variation", 0.0))
                + (1.0 - float(source_coords.get("frame_stability", 0.0)))
                + (1.0 - family_cohesion)
            ) / 3.0
        )
        constraint = _clamp(
            (
                float(source_coords.get("inflectional_load", 0.0))
                + float(source_coords.get("function_word_scaffolding", 0.0))
                + float(source_coords.get("clause_subordination", 0.0))
            ) / 3.0
        )
        tension = _clamp(
            (
                axis_change
                + abs(float(axis_deltas.get("subject_explicitness", 0.0)))
                + abs(float(axis_deltas.get("clause_subordination", 0.0)))
                + abs(float(axis_deltas.get("tense_aspect_marking", 0.0)))
            ) / 4.0
        )
        collapse = _clamp(float(edge.get("distance", 0.0)) / max_edge_distance)
        post_narrowing = _clamp(
            (
                (1.0 - family_cohesion)
                + float(target_coords.get("frame_stability", 0.0))
                + (1.0 - abs(float(axis_deltas.get("lexical_variation", 0.0))))
            ) / 3.0
        )
        morphology = _classify_morphology(
            collapse=collapse,
            post_narrowing=post_narrowing,
            tension=tension,
            source_coords=source_coords,
            target_coords=target_coords,
        )
        confidence = _clamp(
            compute_dcp_score(
                possibility,
                constraint,
                tension,
                collapse,
                post_narrowing,
            ) * 0.8 + float(null_model.get("confidence", 0.0)) * 0.2
        )

        event = DCPEvent(
            source_domain="language",
            source_artifact=source_artifact,
            event_id=f"{language}_{corpus}_{family}_{index:02d}",
            possibility_space_proxy=round(possibility, 4),
            constraint_proxy=round(constraint, 4),
            tension_proxy=round(tension, 4),
            collapse_proxy=round(collapse, 4),
            post_collapse_narrowing=round(post_narrowing, 4),
            collapse_morphology=morphology.value,
            constraint_class="internal",
            confidence=round(confidence, 4),
            calibration_status="null_baseline_run",
            notes=f"Construction transform '{edge.get('label')}' within family '{family}'.",
            domain_metadata={
                "language": language,
                "corpus": corpus,
                "family": family,
                "edge": edge,
                "source_text": source.get("text"),
                "target_text": target.get("text"),
                "axis_deltas": axis_deltas,
            },
        )
        event_dict = event.to_dict()
        event_score = compute_dcp_score(
            possibility,
            constraint,
            tension,
            collapse,
            post_narrowing,
        )
        event_scores.append((morphology.value, event_score))
        events.append(event_dict)

        trajectory_families.append({
            "family": family,
            "transform": edge.get("label"),
            "source_id": edge.get("source"),
            "target_id": edge.get("target"),
            "source_text": source.get("text"),
            "target_text": target.get("text"),
            "axis_deltas": axis_deltas,
            "pre_state": {
                "possibility_space": round(possibility, 4),
                "constraint": round(constraint, 4),
                "tension": round(tension, 4),
            },
            "collapse_event": {
                "collapse": round(collapse, 4),
                "post_narrowing": round(post_narrowing, 4),
                "morphology": morphology.value,
                "qualification": event_dict["qualification_status"],
            },
        })

    dominant_morphology = _dominant_morphology(event_scores)
    morphology_histogram = {
        label: count
        for label, count in Counter(label for label, _ in event_scores).most_common()
    }
    strongest_edge = max(events, key=lambda item: float(item.get("collapse_proxy", 0.0)))
    dcp_block = {
        "block": "dcp",
        "schema_version": DCP_BLOCK_SCHEMA_VERSION,
        "language": language,
        "corpus": corpus,
        "source_boundary": "construction_family_transform",
        "possibility_space": round(_mean(event["possibility_space_proxy"] for event in events), 4),
        "constraint": round(_mean(event["constraint_proxy"] for event in events), 4),
        "tension": round(_mean(event["tension_proxy"] for event in events), 4),
        "collapse": round(_mean(event["collapse_proxy"] for event in events), 4),
        "post_narrowing": round(_mean(event["post_collapse_narrowing"] for event in events), 4),
        "composite": round(_mean(score for _, score in event_scores), 4),
        "qualification": _aggregate_qualification(events),
        "event_count": len(events),
        "dominant_morphology": dominant_morphology,
        "constraint_class": "internal",
        "source_artifact": source_artifact,
        "null_calibration_status": "null_baseline_run",
        "evidence": {
            "signals": [
                {
                    "name": "event_composite_mean",
                    "value": round(_mean(score for _, score in event_scores), 4),
                    "axis": "composite",
                },
                {
                    "name": "null_model_confidence",
                    "value": round(float(null_model.get("confidence", 0.0)), 4),
                    "axis": "confidence",
                },
                {
                    "name": "mean_collapse_proxy",
                    "value": round(_mean(event["collapse_proxy"] for event in events), 4),
                    "axis": "collapse",
                },
                {
                    "name": "mean_post_narrowing",
                    "value": round(_mean(event["post_collapse_narrowing"] for event in events), 4),
                    "axis": "post_narrowing",
                },
            ],
            "source_features": [
                f"family_count: {len(families)}",
                f"dominant_morphology: {dominant_morphology}",
                (
                    "strongest_edge: "
                    f"{strongest_edge.get('domain_metadata', {}).get('family', 'unknown')}/"
                    f"{strongest_edge.get('domain_metadata', {}).get('edge', {}).get('label', 'transform')}"
                ),
            ],
            "notes": "DCP block aggregates family-local construction transforms into a corpus-level compression profile.",
        },
    }

    probe = DCPProbeOutput(
        agent_id=f"{language}.{corpus}",
        source_domain="language",
        constraint_profile={
            "class": "internal",
            "intensity": dcp_block["constraint"],
            "notes": "Language fixtures treat grammar and construction rules as internal constraint.",
        },
        possibility_breadth=dcp_block["possibility_space"],
        tension_estimate=dcp_block["tension"],
        collapse_detected=dcp_block["composite"] >= 0.3,
        collapse_morphology=dominant_morphology,
        post_collapse_class=dominant_morphology,
        confidence=round(
            _clamp((dcp_block["composite"] + float(null_model.get("confidence", 0.0))) / 2.0),
            4,
        ),
        notes="Language DCP probe derived from construction-family transforms.",
    )

    return {
        "trajectory_dynamics": {
            "schema_version": TRAJECTORY_SCHEMA_VERSION,
            "process_model": "possibility space → constraint → tension → collapse/commitment → new trajectory",
            "families": trajectory_families,
            "family_count": len(trajectory_families),
            "morphology_histogram": morphology_histogram,
            "qualification": dcp_block["qualification"],
        },
        "dcp_events": events,
        "dcp_block": dcp_block,
        "probe_output": probe.to_dict(),
    }


def _dominant_morphology(scores: list[tuple[str, float]]) -> str | None:
    if not scores:
        return None
    weighted = Counter()
    for label, score in scores:
        weighted[label] += score
    return weighted.most_common(1)[0][0]


def _aggregate_qualification(events: list[dict[str, Any]]) -> str:
    counts = Counter(event.get("qualification_status", "INSUFFICIENT") for event in events)
    return counts.most_common(1)[0][0] if counts else "INSUFFICIENT"


def _classify_morphology(
    *,
    collapse: float,
    post_narrowing: float,
    tension: float,
    source_coords: dict[str, float],
    target_coords: dict[str, float],
) -> CollapseMorphology:
    if collapse <= 0.1 and post_narrowing >= 0.3:
        return CollapseMorphology.CIRCULAR
    if collapse >= 0.45 and post_narrowing >= 0.45:
        return CollapseMorphology.TRANSFORMATIVE
    if tension >= 0.35 and collapse < 0.3:
        return CollapseMorphology.DEFERRED_SUSPENDED
    if float(target_coords.get("lexical_variation", 0.0)) < float(source_coords.get("lexical_variation", 0.0)) - 0.15:
        return CollapseMorphology.DISSOLUTIVE
    if float(target_coords.get("frame_stability", 0.0)) <= float(source_coords.get("frame_stability", 0.0)):
        return CollapseMorphology.CIRCULAR
    return CollapseMorphology.TRANSFORMATIVE


def _mean(values: Any) -> float:
    values = [float(value) for value in values]
    return sum(values) / len(values) if values else 0.0


def _clamp(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)
