"""
core.semantics — Helix Semantics Layer
========================================
Defines the meaning of all entities, properties, and relationships in Helix.

Subsystems:
  entity_registry/      — SemanticSignature per entity type
  property_registry/    — PropertySpec for typed properties
  relationship_registry/ — RelationshipSpec for valid relationships
  validator             — SemanticValidator: validates entities against signatures
"""
from core.semantics.validator import SemanticValidator, SemanticValidationError, ValidationResult
from core.semantics.entity_registry.entity_types import get_signature, all_entity_types, SemanticSignature
from core.semantics.property_registry.property_types import get_property, all_property_names, PropertySpec
from core.semantics.relationship_registry.relationship_types import (
    get_relationship, all_relationship_names, RelationshipSpec,
)

__all__ = [
    "SemanticValidator",
    "SemanticValidationError",
    "ValidationResult",
    "SemanticSignature",
    "PropertySpec",
    "RelationshipSpec",
    "get_signature",
    "get_property",
    "get_relationship",
    "all_entity_types",
    "all_property_names",
    "all_relationship_names",
]
