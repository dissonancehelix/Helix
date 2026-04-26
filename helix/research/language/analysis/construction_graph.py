"""
Construction graph builder for Spanish-first language fixtures.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any, Sequence

from domains.language.feature_extraction.structural_vector import (
    StructuralVectorExtractor,
    mean_vector,
    vector_distance,
)


class ConstructionGraphBuilder:
    def __init__(self, language: str = "spanish") -> None:
        self.language = language.lower()
        self.extractor = StructuralVectorExtractor(language=self.language)

    def build(self, records: Sequence[dict[str, Any]]) -> dict[str, Any]:
        if not records:
            return {
                "language": self.language,
                "node_count": 0,
                "edge_count": 0,
                "nodes": [],
                "edges": [],
                "families": {},
                "attractors": [],
                "bottlenecks": [],
            }

        summary = self.extractor.summarize(records)
        node_by_id = {
            vector["id"]: vector
            for vector in summary["vectors"]
            if vector.get("id") is not None
        }

        family_members: dict[str, list[str]] = defaultdict(list)
        for vector in summary["vectors"]:
            family = vector.get("family") or "ungrouped"
            family_members[family].append(vector["id"])

        edges: list[dict[str, Any]] = []
        for record in records:
            source_id = record.get("edge_from")
            target_id = record.get("id")
            if source_id and target_id and source_id in node_by_id and target_id in node_by_id:
                source = node_by_id[source_id]
                target = node_by_id[target_id]
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "label": record.get("transform", "transform"),
                    "distance": round(
                        vector_distance(source["axis_values"], target["axis_values"]),
                        4,
                    ),
                    "family": record.get("family"),
                })

        for family, ids in family_members.items():
            existing_pairs = {(edge["source"], edge["target"]) for edge in edges}
            for left, right in combinations(ids, 2):
                if (left, right) in existing_pairs or (right, left) in existing_pairs:
                    continue
                left_node = node_by_id[left]
                right_node = node_by_id[right]
                edges.append({
                    "source": left,
                    "target": right,
                    "label": "family_proximity",
                    "distance": round(
                        vector_distance(left_node["axis_values"], right_node["axis_values"]),
                        4,
                    ),
                    "family": family,
                })

        family_stats: dict[str, dict[str, Any]] = {}
        for family, ids in family_members.items():
            vectors = [node_by_id[item_id]["axis_values"] for item_id in ids if item_id in node_by_id]
            centroid = mean_vector(vectors)
            cohesion = 0.0
            if vectors:
                cohesion = round(
                    sum(vector_distance(vector, centroid) for vector in vectors) / len(vectors),
                    4,
                )
            family_stats[family] = {
                "count": len(vectors),
                "centroid": centroid,
                "cohesion": cohesion,
            }

        attractors = sorted(
            (
                {
                    "family": family,
                    "count": stats["count"],
                    "cohesion": stats["cohesion"],
                }
                for family, stats in family_stats.items()
            ),
            key=lambda item: (-item["count"], item["cohesion"]),
        )[:6]

        bottlenecks = sorted(
            (edge for edge in edges if edge["label"] != "family_proximity"),
            key=lambda item: item["distance"],
            reverse=True,
        )[:8]

        nodes = []
        for vector in summary["vectors"]:
            nodes.append({
                "id": vector["id"],
                "family": vector.get("family"),
                "label": vector.get("label"),
                "transform": vector.get("transform"),
                "text": vector.get("text"),
                "coordinates": vector["axis_values"],
            })

        return {
            "language": self.language,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "families": family_stats,
            "attractors": attractors,
            "bottlenecks": bottlenecks,
        }
