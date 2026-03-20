"""
Atlas Graph — Helix Phase 10
=============================
Data model for the Atlas Knowledge Graph.

Each Atlas entry becomes a node.
Relationships between entries become typed edges.

Node types:   INVARIANT, EXPERIMENT, MODEL, REGIME, OPERATOR
Edge types:   TESTED_BY, SUPPORTED_BY, CONTRADICTS, EMERGES_FROM,
              IMPLEMENTS, TRANSITIONS_TO, DERIVES_FROM, PRODUCES
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ATLAS_GRAPH_JSON = Path(__file__).parent.parent.parent / "atlas" / "atlas_graph.json"

# Valid node and edge types
NODE_TYPES = frozenset({
    "INVARIANT", "EXPERIMENT", "MODEL", "REGIME", "OPERATOR",
})

EDGE_TYPES = frozenset({
    "TESTED_BY",       # invariant TESTED_BY experiment
    "SUPPORTED_BY",    # invariant SUPPORTED_BY experiment
    "CONTRADICTS",     # invariant CONTRADICTS invariant
    "EMERGES_FROM",    # regime EMERGES_FROM experiment
    "IMPLEMENTS",      # operator IMPLEMENTS invariant
    "TRANSITIONS_TO",  # regime TRANSITIONS_TO regime
    "DERIVES_FROM",    # model DERIVES_FROM invariant
    "PRODUCES",        # experiment PRODUCES artifact
})


@dataclass
class Node:
    id:       str
    type:     str          # one of NODE_TYPES
    status:   str = "unknown"
    domains:  list[str] = field(default_factory=list)
    path:     str = ""     # relative path to atlas entry
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id":       self.id,
            "type":     self.type,
            "status":   self.status,
            "domains":  self.domains,
            "path":     self.path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        return cls(
            id=d["id"], type=d["type"],
            status=d.get("status", "unknown"),
            domains=d.get("domains", []),
            path=d.get("path", ""),
            metadata=d.get("metadata", {}),
        )


@dataclass
class Edge:
    source: str    # node id
    target: str    # node id
    type:   str    # one of EDGE_TYPES
    weight: float = 1.0
    notes:  str = ""

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type":   self.type,
            "weight": self.weight,
            "notes":  self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Edge":
        return cls(
            source=d["source"], target=d["target"], type=d["type"],
            weight=d.get("weight", 1.0), notes=d.get("notes", ""),
        )


class AtlasGraph:
    """
    In-memory Atlas Knowledge Graph.
    Backed by codex/atlas/atlas_graph.json for persistence.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    # ── Construction ───────────────────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        node.type = node.type.upper()
        if node.type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {node.type!r}")
        self._nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        edge.type = edge.type.upper()
        if edge.type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type: {edge.type!r}")
        if edge.source not in self._nodes:
            raise KeyError(f"Source node not in graph: {edge.source!r}")
        if edge.target not in self._nodes:
            raise KeyError(f"Target node not in graph: {edge.target!r}")
        # Deduplicate
        for e in self._edges:
            if e.source == edge.source and e.target == edge.target and e.type == edge.type:
                return
        self._edges.append(edge)

    # ── Accessors ──────────────────────────────────────────────────────────────

    @property
    def nodes(self) -> list[Node]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[Edge]:
        return list(self._edges)

    def node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def neighbors(self, node_id: str, edge_type: str | None = None) -> list[tuple[str, Edge]]:
        result = []
        for e in self._edges:
            if e.source == node_id:
                if edge_type is None or e.type == edge_type:
                    result.append((e.target, e))
            elif e.target == node_id:
                if edge_type is None or e.type == edge_type:
                    result.append((e.source, e))
        return result

    def edges_from(self, node_id: str) -> list[Edge]:
        return [e for e in self._edges if e.source == node_id]

    def edges_to(self, node_id: str) -> list[Edge]:
        return [e for e in self._edges if e.target == node_id]

    # ── Persistence ───────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
            "_meta": {
                "node_count": len(self._nodes),
                "edge_count": len(self._edges),
            },
        }

    def save(self, path: Path = ATLAS_GRAPH_JSON) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path = ATLAS_GRAPH_JSON) -> "AtlasGraph":
        g = cls()
        if not path.exists():
            return g
        data = json.loads(path.read_text())
        for nd in data.get("nodes", []):
            g.add_node(Node.from_dict(nd))
        for ed in data.get("edges", []):
            try:
                g.add_edge(Edge.from_dict(ed))
            except (ValueError, KeyError):
                pass  # skip stale edges referencing removed nodes
        return g

    def summary(self) -> str:
        type_counts: dict[str, int] = {}
        for n in self._nodes.values():
            type_counts[n.type] = type_counts.get(n.type, 0) + 1
        edge_counts: dict[str, int] = {}
        for e in self._edges:
            edge_counts[e.type] = edge_counts.get(e.type, 0) + 1
        lines = [
            f"Atlas Graph: {len(self._nodes)} nodes, {len(self._edges)} edges",
            "  Nodes: " + ", ".join(f"{v} {k}" for k, v in sorted(type_counts.items())),
            "  Edges: " + ", ".join(f"{v} {k}" for k, v in sorted(edge_counts.items())),
        ]
        return "\n".join(lines)
