"""
HIL Command Context — Helix SPEC-08
=====================================
Execution state for a single HIL command.

CommandContext is passed through the interpreter to every command handler.
It bundles the resolved target entity (if any), the active substrate, free
params extracted from the command, and shared infrastructure handles.

Load the default context (backed by atlas paths) with CommandContext.default().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.kernel.schema.entities.registry import EntityRegistry
    from core.kernel.schema.entities.schema import Entity
    from core.kernel.graph.storage.entity_graph import EntityGraph


@dataclass
class CommandContext:
    """
    Execution context for a single HIL command dispatch.

    Fields
    ------
    target_entity     Resolved primary Entity (populated by interpreter before dispatch)
    active_substrate  Substrate namespace string, e.g. "music"
    params            Free parameter dict (engine, range, etc.) from HILCommand.params
    registry          EntityRegistry handle
    graph             EntityGraph handle
    """

    target_entity:    "Entity | None"         = None
    active_substrate: str | None              = None
    params:           dict[str, Any]          = field(default_factory=dict)
    registry:         "EntityRegistry | None" = None
    graph:            "EntityGraph | None"    = None

    @classmethod
    def default(cls) -> "CommandContext":
        """
        Load registry and graph from default atlas paths.

        Returns a fully-populated CommandContext backed by the on-disk state.
        If the atlas files do not exist, returns an empty context (no error).
        """
        from core.kernel.schema.entities.registry import EntityRegistry
        from core.kernel.graph.storage.entity_graph import EntityGraph

        registry = EntityRegistry.load()
        try:
            graph = EntityGraph.load()
        except Exception:
            graph = EntityGraph()

        return cls(registry=registry, graph=graph)
