"""
Entity Graph — Helix SPEC-03
==============================
Knowledge graph for entity relationships.

STRICT SEPARATION from AtlasGraph:
  AtlasGraph handles: INVARIANT, EXPERIMENT, MODEL, REGIME, OPERATOR
  EntityGraph handles: COMPOSER, TRACK, GAME, PLATFORM, SOUND_CHIP, SOUND_TEAM

Do NOT mix node types between these graphs.
Both reside in core/graph but are independent systems.

Storage: codex/atlas/entities/entity_graph.json
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.paths import ATLAS_ROOT

if TYPE_CHECKING:
    from core.kernel.schema.entities.registry import EntityRegistry

_DEFAULT_GRAPH_PATH = ATLAS_ROOT / "entities" / "entity_graph.json"

# Entity node types — must not overlap with AtlasGraph NODE_TYPES
ENTITY_NODE_TYPES: frozenset[str] = frozenset({
    "COMPOSER",
    "TRACK",
    "GAME",
    "PLATFORM",
    "SOUND_CHIP",
    "SOUND_TEAM",
})

# Entity edge types — correspond to HIL semantic roles in core/hil/semantic_roles.py
ENTITY_EDGE_TYPES: frozenset[str] = frozenset({
    "COMPOSED",           # composer → track
    "APPEARS_IN",         # track → game
    "RUNS_ON",            # game → platform
    "USES_CHIP",          # game → sound_chip
    "MEMBER_OF",          # composer → sound_team
    "COLLABORATED_WITH",  # composer ↔ composer
})


@dataclass
class EntityNode:
    id:       str
    type:     str           # one of ENTITY_NODE_TYPES
    name:     str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id":       self.id,
            "type":     self.type,
            "name":     self.name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EntityNode":
        return cls(
            id=d["id"],
            type=d["type"],
            name=d.get("name", ""),
            metadata=d.get("metadata", {}),
        )


@dataclass
class EntityEdge:
    source:     str    # node id
    target:     str    # node id
    type:       str    # one of ENTITY_EDGE_TYPES
    confidence: float = 1.0
    notes:      str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source":     self.source,
            "target":     self.target,
            "type":       self.type,
            "confidence": self.confidence,
            "notes":      self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EntityEdge":
        return cls(
            source=d["source"],
            target=d["target"],
            type=d["type"],
            confidence=d.get("confidence", 1.0),
            notes=d.get("notes", ""),
        )


class EntityGraph:
    """
    In-memory entity relationship graph.
    Backed by codex/atlas/entities/entity_graph.json for persistence.

    Separate from AtlasGraph — handles entity-domain relationships only.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, EntityNode] = {}
        self._edges: list[EntityEdge] = []

    # ── Construction ──────────────────────────────────────────────────────────

    def add_node(self, node: EntityNode) -> None:
        node.type = node.type.upper()
        if node.type not in ENTITY_NODE_TYPES:
            raise ValueError(
                f"Unknown entity node type: {node.type!r}. "
                f"Valid types: {sorted(ENTITY_NODE_TYPES)}"
            )
        self._nodes[node.id] = node

    def add_edge(self, edge: EntityEdge) -> None:
        edge.type = edge.type.upper()
        if edge.type not in ENTITY_EDGE_TYPES:
            raise ValueError(
                f"Unknown entity edge type: {edge.type!r}. "
                f"Valid types: {sorted(ENTITY_EDGE_TYPES)}"
            )
        if edge.source not in self._nodes:
            raise KeyError(f"Source node not in entity graph: {edge.source!r}")
        if edge.target not in self._nodes:
            raise KeyError(f"Target node not in entity graph: {edge.target!r}")
        # Deduplicate
        for e in self._edges:
            if e.source == edge.source and e.target == edge.target and e.type == edge.type:
                return
        self._edges.append(edge)

    # ── Accessors ─────────────────────────────────────────────────────────────

    @property
    def nodes(self) -> list[EntityNode]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[EntityEdge]:
        return list(self._edges)

    def node(self, node_id: str) -> EntityNode | None:
        return self._nodes.get(node_id)

    def nodes_by_type(self, node_type: str) -> list[EntityNode]:
        t = node_type.upper()
        return [n for n in self._nodes.values() if n.type == t]

    def neighbors(
        self,
        node_id: str,
        edge_type: str | None = None,
    ) -> list[tuple[str, EntityEdge]]:
        result = []
        et = edge_type.upper() if edge_type else None
        for e in self._edges:
            if e.source == node_id:
                if et is None or e.type == et:
                    result.append((e.target, e))
            elif e.target == node_id:
                if et is None or e.type == et:
                    result.append((e.source, e))
        return result

    def edges_from(self, node_id: str) -> list[EntityEdge]:
        return [e for e in self._edges if e.source == node_id]

    def edges_to(self, node_id: str) -> list[EntityEdge]:
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

    def save(self, path: Path = _DEFAULT_GRAPH_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path = _DEFAULT_GRAPH_PATH) -> "EntityGraph":
        g = cls()
        if not path.exists():
            return g
        data = json.loads(path.read_text())
        for nd in data.get("nodes", []):
            try:
                g.add_node(EntityNode.from_dict(nd))
            except (ValueError, KeyError):
                pass
        for ed in data.get("edges", []):
            try:
                g.add_edge(EntityEdge.from_dict(ed))
            except (ValueError, KeyError):
                pass
        return g

    def summary(self) -> str:
        type_counts: dict[str, int] = {}
        for n in self._nodes.values():
            type_counts[n.type] = type_counts.get(n.type, 0) + 1
        edge_counts: dict[str, int] = {}
        for e in self._edges:
            edge_counts[e.type] = edge_counts.get(e.type, 0) + 1
        lines = [
            f"EntityGraph: {len(self._nodes)} nodes, {len(self._edges)} edges",
            "  Nodes: " + ", ".join(f"{v} {k}" for k, v in sorted(type_counts.items())),
            "  Edges: " + ", ".join(f"{v} {k}" for k, v in sorted(edge_counts.items())),
        ]
        return "\n".join(lines)


# ── Registry hydration ────────────────────────────────────────────────────────

# Relationship type → EntityGraph edge type mapping
_RELATION_TO_EDGE: dict[str, str] = {
    "composed":          "COMPOSED",
    "appears_in":        "APPEARS_IN",
    "runs_on":           "RUNS_ON",
    "uses_chip":         "USES_CHIP",
    "member_of":         "MEMBER_OF",
    "collaborated_with": "COLLABORATED_WITH",
}

# Entity type → EntityGraph node type mapping
_ENTITY_TYPE_TO_NODE: dict[str, str] = {
    "Composer":  "COMPOSER",
    "Track":     "TRACK",
    "Game":      "GAME",
    "Platform":  "PLATFORM",
    "SoundChip": "SOUND_CHIP",
    "SoundTeam": "SOUND_TEAM",
}


def build_from_registry(registry: "EntityRegistry") -> EntityGraph:
    """
    Hydrate an EntityGraph from an EntityRegistry.

    Only entities whose type maps to a known ENTITY_NODE_TYPE are included.
    Relationships are mapped via _RELATION_TO_EDGE; unknown relation types are skipped.
    """
    g = EntityGraph()

    # First pass: add all nodes
    for entity in registry.all():
        node_type = _ENTITY_TYPE_TO_NODE.get(entity.type)
        if node_type is None:
            continue  # reserved or unknown types skipped
        g.add_node(EntityNode(
            id=entity.id,
            type=node_type,
            name=entity.name,
            metadata=entity.metadata,
        ))

    # Second pass: add edges from relationships
    for entity in registry.all():
        if entity.id not in g._nodes:
            continue
        for rel in entity.relationships:
            edge_type = _RELATION_TO_EDGE.get(rel.get("relation", "").lower())
            target_id = rel.get("target_id", "")
            if not edge_type or target_id not in g._nodes:
                continue
            try:
                g.add_edge(EntityEdge(
                    source=entity.id,
                    target=target_id,
                    type=edge_type,
                    confidence=rel.get("confidence", 1.0),
                ))
            except (ValueError, KeyError):
                pass

    return g
