"""
Helix Enforcement — Final MISSING LAYER
=======================================
Centralized enforcement authority for the Helix repository.
This layer maintains the architectural integrity of the system
at runtime by preventing illegal states and layer violations.
"""
from core.validation.failure_states import FAILURE_STATES, Severity
from core.validation.rules import Law, Layer, LAYER_PATHS
from core.validation.validators import (
    validate_id,
    validate_entity_schema,
    EnforcementError,
    ValidationError,
    IDError
)
from core.validation.runtime_checks import (
    authorize_atlas_write,
    pre_persistence_check,
    enforce_persistence,
    require_canonical_provenance,
    IllegalWriteError,
    LayerViolationError,
    NonCanonicalExecutionError,
)
from core.validation.audit import audit_system_state

__all__ = [
    "FAILURE_STATES", "Severity",
    "Law", "Layer", "LAYER_PATHS",
    "validate_id", "validate_entity_schema",
    "EnforcementError", "ValidationError", "IDError",
    "authorize_atlas_write", "pre_persistence_check", "enforce_persistence",
    "require_canonical_provenance",
    "IllegalWriteError", "LayerViolationError", "NonCanonicalExecutionError",
    "audit_system_state",
]
