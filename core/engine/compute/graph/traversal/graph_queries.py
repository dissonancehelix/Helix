"""
Graph Queries — Helix Phase 10
================================
Query interface for the Atlas Knowledge Graph.

Queries:
  query_support(invariant_id)         — find supporting experiments
  query_cross_domain()                — invariants verified across domains
  query_unverified_models()           — models without verified invariant support
  query_clusters()                    — candidate invariant clusters (shared support)
  query_contradictions()              — CONTRADICTS edges
  query_missing_experiments(inv_id)   — invariants with no experiments
  query_node(node_id)                 — full neighborhood of a node
"""

from __future__ import annotations

from dataclasses import dataclass
from core.engine.kernel.graph.storage.atlas_graph import AtlasGraph, Node, Edge


@dataclass
class QueryResult:
    query:  str
    nodes:  list[Node]
    edges:  list[Edge]
    notes:  list[str]

    def report(self) -> str:
        lines = [f"Query: {self.query}", f"  {len(self.nodes)} nodes, {len(self.edges)} edges"]
        for note in self.notes:
            lines.append(f"  {note}")
        if self.nodes:
            lines.append("  Nodes:")
            for n in self.nodes:
                lines.append(f"    [{n.type}] {n.id} ({n.status})")
        return "\n".join(lines)


class GraphQuery:
    def __init__(self, graph: AtlasGraph) -> None:
        self.g = graph

    def query_support(self, invariant_id: str) -> QueryResult:
        """Find all experiments and operators that support an invariant."""
        support_nodes: list[Node] = []
        support_edges: list[Edge] = []
        notes = []

        target = self.g.node(invariant_id)
        if target is None:
            return QueryResult(
                query=f"query_support({invariant_id!r})",
                nodes=[], edges=[],
                notes=[f"Node not found: {invariant_id!r}"],
            )

        for e in self.g.edges:
            if e.target == invariant_id and e.type in ("SUPPORTED_BY", "TESTED_BY", "IMPLEMENTS"):
                n = self.g.node(e.source)
                if n:
                    support_nodes.append(n)
                    support_edges.append(e)

        if not support_nodes:
            notes.append(f"No supporting entries found for {invariant_id!r}")
        else:
            notes.append(f"Found {len(support_nodes)} supporting entries")

        return QueryResult(
            query=f"query_support({invariant_id!r})",
            nodes=support_nodes,
            edges=support_edges,
            notes=notes,
        )

    def query_cross_domain(self) -> QueryResult:
        """Find invariants verified across 2+ distinct substrate domains."""
        multi_domain = []
        for n in self.g.nodes:
            if n.type == "INVARIANT" and len(n.domains) >= 2:
                multi_domain.append(n)

        return QueryResult(
            query="query_cross_domain()",
            nodes=multi_domain,
            edges=[],
            notes=[f"{len(multi_domain)} cross-domain invariants found"],
        )

    def query_unverified_models(self) -> QueryResult:
        """Find models that derive from unverified invariants or have no support."""
        unverified = []
        for n in self.g.nodes:
            if n.type != "MODEL":
                continue
            # Check if model derives from a verified invariant
            derives = [e for e in self.g.edges_from(n.id) if e.type == "DERIVES_FROM"]
            if not derives:
                unverified.append(n)
                continue
            all_verified = all(
                (self.g.node(e.target) or type("_", (), {"status": ""})()).status in ("verified", "Verified")
                for e in derives
            )
            if not all_verified:
                unverified.append(n)

        return QueryResult(
            query="query_unverified_models()",
            nodes=unverified,
            edges=[],
            notes=[f"{len(unverified)} model(s) without fully verified invariant support"],
        )

    def query_clusters(self) -> QueryResult:
        """
        Detect candidate invariant clusters — groups of invariants sharing
        experimental support or probe types (EMERGES_FROM edges).
        """
        cluster_edges = [e for e in self.g.edges if e.type == "EMERGES_FROM"]
        cluster_nodes_ids: set[str] = set()
        for e in cluster_edges:
            cluster_nodes_ids.add(e.source)
            cluster_nodes_ids.add(e.target)

        cluster_nodes = [n for n in self.g.nodes if n.id in cluster_nodes_ids]

        return QueryResult(
            query="query_clusters()",
            nodes=cluster_nodes,
            edges=cluster_edges,
            notes=[
                f"{len(cluster_nodes)} nodes in {len(cluster_edges)} cluster relationships",
                "Cluster = shared probe, experiment, or regime",
            ],
        )

    def query_contradictions(self) -> QueryResult:
        """Find all CONTRADICTS edges in the graph."""
        contra_edges = [e for e in self.g.edges if e.type == "CONTRADICTS"]
        contra_nodes_ids = set()
        for e in contra_edges:
            contra_nodes_ids.add(e.source)
            contra_nodes_ids.add(e.target)
        contra_nodes = [n for n in self.g.nodes if n.id in contra_nodes_ids]

        return QueryResult(
            query="query_contradictions()",
            nodes=contra_nodes,
            edges=contra_edges,
            notes=[f"{len(contra_edges)} contradiction(s) detected"],
        )

    def query_missing_experiments(self) -> QueryResult:
        """Find invariants with no supporting experiments at all."""
        missing = []
        for n in self.g.nodes:
            if n.type != "INVARIANT":
                continue
            support = [
                e for e in self.g.edges
                if e.target == n.id and e.type in ("SUPPORTED_BY", "TESTED_BY")
            ]
            if not support:
                missing.append(n)

        return QueryResult(
            query="query_missing_experiments()",
            nodes=missing,
            edges=[],
            notes=[f"{len(missing)} invariant(s) have no linked experiments"],
        )

    def query_node(self, node_id: str) -> QueryResult:
        """Return a node and its full one-hop neighborhood."""
        target = self.g.node(node_id)
        if target is None:
            return QueryResult(
                query=f"query_node({node_id!r})",
                nodes=[], edges=[],
                notes=[f"Node not found: {node_id!r}"],
            )

        neighbors_raw = self.g.neighbors(node_id)
        neighbor_nodes = [target]
        neighbor_edges = []
        seen_ids = {node_id}
        for nid, edge in neighbors_raw:
            neighbor_edges.append(edge)
            if nid not in seen_ids:
                n = self.g.node(nid)
                if n:
                    neighbor_nodes.append(n)
                    seen_ids.add(nid)

        return QueryResult(
            query=f"query_node({node_id!r})",
            nodes=neighbor_nodes,
            edges=neighbor_edges,
            notes=[f"Neighborhood: {len(neighbor_nodes)} nodes, {len(neighbor_edges)} edges"],
        )
