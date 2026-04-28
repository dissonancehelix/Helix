"""
Helix Enforcement — System Rules
===============================
Defines the authoritative laws that govern the Helix repository.
"""
from enum import Enum, auto

class Layer(Enum):
    CORE        = auto()
    CODEX       = auto()
    ATLAS       = auto()
    LIBRARY     = auto()
    DOCS        = auto()
    DOMAINS     = auto()

class Law(Enum):
    # -----------------------------------------------------------------------
    # Layer Separation Laws
    # -----------------------------------------------------------------------
    CORE_NO_CODEX_MUTATION = "core may not depend on codex/atlas as mutable state"
    DOMAINS_NO_ATLAS_WRITE = "domains may not write to codex/atlas directly except through compiler"
    DOMAINS_NO_COMPILER_BYPASS = "domains may not bypass core compiler paths"
    ATLAS_READ_ONLY_BY_CONVENTION = "atlas must remain read-only except through canonical compiler authority"

    # -----------------------------------------------------------------------
    # Identity Laws
    # -----------------------------------------------------------------------
    DETERMINISTIC_IDS = "all persisted entities must have deterministic IDs"
    ID_CANONICAL_FORMAT = "IDs must conform to 'domain.type:slug'"
    INVALID_IDS_FORBIDDEN = "malformed or missing IDs are invalid states"

    # -----------------------------------------------------------------------
    # Schema Laws
    # -----------------------------------------------------------------------
    SCHEMA_VALIDATION_REQUIRED = "persisted entities must validate against canonical schema"
    MISSING_CORE_FIELDS_ILLEGAL = "missing required fields (entity_id, entity_type, created_at, source) are invalid"
    UNKNOWN_CRITICAL_FIELDS_REJECTED = "unknown fields in schema-critical roles must be explicitly declared or rejected"

    # -----------------------------------------------------------------------
    # Relationship Laws
    # -----------------------------------------------------------------------
    EXPLICIT_LINKAGE_ONLY = "no implicit relationships in persisted knowledge"
    VALID_GRAPH_LINKS = "all graph links must be explicit and schema-valid"
    NO_ORPHAN_NODES = "orphan graph nodes must be flagged as unstable"

    # -----------------------------------------------------------------------
    # Mutation Laws
    # -----------------------------------------------------------------------
    OBSERVABLE_TRANSFORMATION = "all transformations must be observable and logged via metadata"
    NO_HIDDEN_MUTATION = "no hidden mutation of persistent state"
    PERSISTENCE_REQUIRES_VALIDATION = "persistence without validation is illegal"

# ---------------------------------------------------------------------------
# Canonical Path Maps (Determined by REPO_ROOT)
# ---------------------------------------------------------------------------
# These should be used by runtime checks to identify layer violations.
LAYER_PATHS = {
    Layer.CORE:    "core/",
    Layer.CODEX:   "codex/",
    Layer.ATLAS:   "codex/atlas/",
    Layer.LIBRARY: "codex/library/",
    Layer.DOCS:    "docs/",
    Layer.DOMAINS: "model/domains/",
}

