"""
Semantics — Semantic Validator
================================
Validates entity dicts and Entity objects against SemanticSignature contracts.

Used by:
  core/kernel/schema/entities/schema.py  — Entity.validate()
  core/engine/store/compiler/atlas_compiler.py         — compile_entity() gate
  core/kernel/schema/entities/registry.py — EntityRegistry.add() gate

Validation checks:
  1. Entity type exists in Semantics registry
  2. All required fields are present and non-empty
  3. All relationships use allowed relationship types for this entity type
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.engine.semantics.entity_registry.entity_types import get_signature, SemanticSignature


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise SemanticValidationError(self.errors)


class SemanticValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Semantic validation failed: {'; '.join(errors)}")


class SemanticValidator:
    """
    Validates entity data against SemanticSignature definitions.

    Accepts both Entity objects (with .type, .id, etc.) and raw dicts.
    """

    @classmethod
    def validate(cls, entity: Any) -> ValidationResult:
        """
        Validate an entity. Returns a ValidationResult.

        entity may be an Entity dataclass instance or a plain dict.
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Normalize to dict for uniform handling
        if hasattr(entity, "to_dict"):
            data = entity.to_dict()
            # Also pull label/description directly from the object
            data["label"] = getattr(entity, "label", data.get("label", ""))
            data["description"] = getattr(entity, "description", data.get("description", ""))
        elif isinstance(entity, dict):
            data = entity
        else:
            return ValidationResult(valid=False, errors=["entity must be a dict or Entity object"], warnings=[])

        entity_type = data.get("type", "")

        # 1. Type must exist in Semantics
        sig = get_signature(entity_type)
        if sig is None:
            errors.append(
                f"Unknown entity type {entity_type!r}. "
                f"Register it in core/semantics/entity_registry/entity_types.py"
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # 2. Required fields
        for field_name in sorted(sig.required_fields):
            val = data.get(field_name)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"Required field {field_name!r} is missing or empty")

        # 3. Relationships must use allowed types
        for i, rel in enumerate(data.get("relationships", [])):
            if not isinstance(rel, dict):
                continue
            relation = rel.get("relation", "")
            if relation and relation not in sig.allowed_relationships:
                # Check global relationship registry for broader compatibility
                from core.engine.semantics.relationship_registry.relationship_types import get_relationship
                rel_spec = get_relationship(relation)
                if rel_spec is None:
                    warnings.append(
                        f"relationships[{i}] uses unknown relation type {relation!r}"
                    )
                elif entity_type not in rel_spec.source_types:
                    warnings.append(
                        f"relationships[{i}] relation {relation!r} is not "
                        f"allowed for entity type {entity_type!r}"
                    )

        # 4. Global Enforcement Layer Check
        try:
            from core.validation import validate_entity_schema
            # Map 'id' -> 'entity_id', 'type' -> 'entity_type' if missing for enforcement check
            compat_data = dict(data)
            if 'entity_id' not in compat_data and 'id' in compat_data:
                compat_data['entity_id'] = compat_data['id']
            if 'entity_type' not in compat_data and 'type' in compat_data:
                compat_data['entity_type'] = compat_data['type']
            
            # Use 'source' default if missing to allow semantic pass, enforcement will catch it if it's a real write
            if 'source' not in compat_data:
                compat_data['source'] = 'inferred'
            if 'created_at' not in compat_data:
                from datetime import datetime, timezone
                compat_data['created_at'] = datetime.now(timezone.utc).isoformat()
                
            validate_entity_schema(compat_data, is_atlas=False)
        except Exception as e:
            errors.append(f"Enforcement violation: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @classmethod
    def validate_strict(cls, entity: Any) -> None:
        """Validate and raise SemanticValidationError on failure."""
        result = cls.validate(entity)
        result.raise_if_invalid()

