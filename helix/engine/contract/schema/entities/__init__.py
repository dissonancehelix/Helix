"""
core.engine.kernel.schema.entities — Helix Entity System (SPEC-02)
"""
from core.engine.kernel.schema.entities.ontology import (
    ENTITY_CORE_TYPES,
    ENTITY_RESERVED_TYPES,
    ENTITY_ONTOLOGY,
    is_core_entity_type,
    is_reserved_entity_type,
    is_known_entity_type,
)
from core.engine.kernel.schema.entities.schema import Entity, PROVENANCE_KEYS
from core.engine.kernel.schema.entities.registry import EntityRegistry

__all__ = [
    "Entity",
    "EntityRegistry",
    "PROVENANCE_KEYS",
    "ENTITY_CORE_TYPES",
    "ENTITY_RESERVED_TYPES",
    "ENTITY_ONTOLOGY",
    "is_core_entity_type",
    "is_reserved_entity_type",
    "is_known_entity_type",
]
