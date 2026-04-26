"""
Helix Enforcement — Failure States
=================================
Defines the formal failure state registry for Helix system violations.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class FailureState:
    code: str
    meaning: str
    detection_condition: str
    recommended_action: str
    severity: Severity

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

FAILURE_STATES = {
    "INVALID_SCHEMA": FailureState(
        code="INVALID_SCHEMA",
        meaning="Persisted entity does not validate against canonical schema.",
        detection_condition="Entity missing required core fields or containing invalid data types.",
        recommended_action="Validate entity against ENTITY_SCHEMA.md before persistence.",
        severity=Severity.HIGH,
    ),
    "INVALID_ID": FailureState(
        code="INVALID_ID",
        meaning="Entity ID does not conform to 'domain.type:slug' format.",
        detection_condition="ID contains forbidden characters, uppercase letters, or missing components.",
        recommended_action="Use core.engine.normalization.id_enforcer to canonicalize the ID.",
        severity=Severity.HIGH,
    ),
    "CROSS_LAYER_VIOLATION": FailureState(
        code="CROSS_LAYER_VIOLATION",
        meaning="Illegal dependency across architectural layers.",
        detection_condition="Core depending on Codex as mutable state, or Apps writing to Atlas directly.",
        recommended_action="Refactor logic to use canonical core interfaces (e.g. AtlasCompiler).",
        severity=Severity.CRITICAL,
    ),
    "ILLEGAL_ATLAS_WRITE": FailureState(
        code="ILLEGAL_ATLAS_WRITE",
        meaning="Unauthorized direct write to the atlas/ directory.",
        detection_condition="Filesystem write detected to atlas/ bypassing the AtlasCompiler.",
        recommended_action="Route all data persistence through the compile_and_commit pipeline.",
        severity=Severity.CRITICAL,
    ),
    "ORPHAN_ENTITY": FailureState(
        code="ORPHAN_ENTITY",
        meaning="Entity exists in the Atlas but is unreachable in the knowledge graph.",
        detection_condition="Entity not linked to any other node or root index.",
        recommended_action="Establish explicit relationships in the entity definition.",
        severity=Severity.MEDIUM,
    ),
    "IMPLICIT_RELATIONSHIP": FailureState(
        code="IMPLICIT_RELATIONSHIP",
        meaning="Relationship exists in knowledge but is not declared in schema.",
        detection_condition="Found reference to entity ID not present in 'links' or 'relationships'.",
        recommended_action="Formalize the relationship in the entity's JSON definition.",
        severity=Severity.MEDIUM,
    ),
    "UNLOGGED_MUTATION": FailureState(
        code="UNLOGGED_MUTATION",
        meaning="Persistence occurred without an associated mutation log entry.",
        detection_condition="Atlas state change detected without corresponding provenance metadata.",
        recommended_action="Ensure all write paths include 'compiled_by' and 'source' metadata.",
        severity=Severity.HIGH,
    ),
    "NONDETERMINISTIC_OUTPUT": FailureState(
        code="NONDETERMINISTIC_OUTPUT",
        meaning="Compiler output varies between identical runs.",
        detection_condition="Checksum mismatch for identical input artifact.",
        recommended_action="Ensure all transformation logic is pure and ID generation is deterministic.",
        severity=Severity.HIGH,
    ),
    "INVALID_PIPELINE_TRANSITION": FailureState(
        code="INVALID_PIPELINE_TRANSITION",
        meaning="Pipeline entered an unauthorized state or skipped required validation.",
        detection_condition="atlas_commit attempted on non-validated compile buffer.",
        recommended_action="Use high-level pipeline helpers that enforce ordering.",
        severity=Severity.CRITICAL,
    ),
}

def get_failure_state(code: str) -> Optional[FailureState]:
    return FAILURE_STATES.get(code)
