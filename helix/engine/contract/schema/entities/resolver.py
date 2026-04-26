"""
Entity Resolver — Helix SPEC-02
================================
HIL-facing lookup layer over EntityRegistry.

Provides a clean query interface for HIL commands without exposing
registry internals directly. All entity resolution in HIL must go
through this module.
"""
from __future__ import annotations

from pathlib import Path

from core.engine.kernel.schema.entities.registry import EntityRegistry
from core.engine.kernel.schema.entities.schema import Entity


class EntityNotFoundError(Exception):
    def __init__(self, entity_id: str) -> None:
        super().__init__(f"EntityNotFoundError: {entity_id}")
        self.entity_id = entity_id


_DEFAULT_REGISTRY_PATH = (
    Path(__file__).parent.parent.parent / "atlas" / "entities" / "registry.json"
)


class EntityResolver:
    """
    HIL-facing lookup layer over EntityRegistry.

    Load from the default atlas path with EntityResolver.default().
    """

    def __init__(self, registry: EntityRegistry) -> None:
        self._registry = registry

    @classmethod
    def default(cls) -> "EntityResolver":
        """Load registry from atlas/entities/registry.json."""
        return cls(EntityRegistry.load(_DEFAULT_REGISTRY_PATH))

    # ── Query ─────────────────────────────────────────────────────────────────

    def resolve(self, entity_id: str) -> Entity:
        """Return the entity for entity_id. Raises EntityNotFoundError if missing."""
        entity = self._registry.get(entity_id)
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return entity

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._registry

    def get_type(self, entity_id: str) -> str:
        """Return the type string for entity_id. Raises EntityNotFoundError if missing."""
        return self.resolve(entity_id).type

    def get_namespace(self, entity_id: str) -> str:
        """Return the namespace segment of entity_id. Raises EntityNotFoundError if missing."""
        return self.resolve(entity_id).namespace

    def list_by_type(self, type_str: str) -> list[Entity]:
        return self._registry.list_by_type(type_str)

    def list_by_namespace(self, namespace: str) -> list[Entity]:
        return [e for e in self._registry.all() if e.namespace == namespace]

    def all(self) -> list[Entity]:
        return self._registry.all()

    @property
    def registry(self) -> EntityRegistry:
        return self._registry
