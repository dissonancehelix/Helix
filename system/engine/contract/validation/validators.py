"""
Helix Enforcement — Validators
==============================
Implements the core validation logic for Helix entities and IDs.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.validation.failure_states import FAILURE_STATES, Severity
from core.engine.normalization.id_enforcer import enforce_id as _enforce_id_canonical

# Pattern from ENTITY_SCHEMA.md and core.engine.normalization.id_enforcer
ID_PATTERN = re.compile(r"^[a-z_]+\.[a-z_]+:[a-z0-9_]+$")

# Required fields for all entities
CORE_FIELDS = {"entity_id", "entity_type", "created_at", "source"}

# Required Substrate Capability Vector axes for Atlas entities
SCV_AXES = {"attractor_stability", "generative_constraint", "recurrence_depth", "structural_density", "control_entropy", "basin_permeability"}

class EnforcementError(Exception):
    """Base exception for all Helix enforcement violations."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
        self.details = FAILURE_STATES.get(code)

class ValidationError(EnforcementError):
    """Raised when an entity fails structural or semantic validation."""
    pass

class IDError(EnforcementError):
    """Raised when an ID fails the canonical format check."""
    pass

# ---------------------------------------------------------------------------
# ID Validation
# ---------------------------------------------------------------------------

def validate_id(entity_id: str) -> str:
    """
    Enforce canonical ID format.
    Raises IDError on failure.
    """
    if not isinstance(entity_id, str) or not entity_id:
        raise IDError("Entity ID must be a non-empty string.", "INVALID_ID")
    
    if not ID_PATTERN.match(entity_id):
        raise IDError(
            f"ID '{entity_id}' violates canonical format ('domain.type:slug').",
            "INVALID_ID"
        )
    return entity_id

# ---------------------------------------------------------------------------
# Schema Validation
# ---------------------------------------------------------------------------

def validate_entity_schema(entity: dict[str, Any], is_atlas: bool = True) -> None:
    """
    Enforce the canonical Helix schema.
    Raises ValidationError on failure.
    """
    # 1. Core Fields
    missing = CORE_FIELDS - set(entity.keys())
    if missing:
        raise ValidationError(
            f"Entity missing mandatory core fields: {', '.join(missing)}",
            "INVALID_SCHEMA"
        )
    
    # 2. ID match
    try:
        validate_id(entity["entity_id"])
    except IDError as e:
        raise ValidationError(str(e), "INVALID_ID")
    
    # 3. Timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(entity["created_at"].replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid ISO 8601 timestamp: '{entity['created_at']}'",
            "INVALID_SCHEMA"
        )
    
    # 4. Atlas-specific requirements (Substrate Capability Vector)
    if is_atlas:
        _validate_substrate_embedding(entity)

def _validate_substrate_embedding(entity: dict[str, Any]) -> None:
    """Enforce the Substrate Capability Vector requirement for Atlas entities."""
    # Check if 'capability_vector' or equivalent exists.
    # New schema uses 'capability_vector'.
    embedding = entity.get("capability_vector", entity.get("substrate", entity.get("Substrate Capability Vector", {})))
    if not isinstance(embedding, dict):
        embedding = entity # fallback to flattened
    
    missing_axes = SCV_AXES - set(embedding.keys())
    if missing_axes:
        # Check if they are in the root entity (historical data)
        missing_root = SCV_AXES - set(entity.keys())
        if missing_axes and missing_root:
            raise ValidationError(
                f"Atlas entity missing Substrate Capability Vector coordinates: {', '.join(missing_axes)}",
                "INVALID_SCHEMA"
            )

    # Validate values are float [0.0, 1.0]
    for axis in SCV_AXES:
        val = embedding.get(axis, entity.get(axis))
        if val is None:
            continue
        try:
            f_val = float(val)
            if not (0.0 <= f_val <= 1.0):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValidationError(
                f"Substrate Capability Vector axis '{axis}' must be a float between 0.0 and 1.0.",
                "INVALID_SCHEMA"
            )
