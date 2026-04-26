"""
core.engine.normalization — Helix Normalization Layer
===============================================
Converts raw input into canonical, validated form before semantic processing.

Pipeline position:  HIL input → [Normalization] → Semantics → Operators → Atlas

Public API:
  Normalizer          — full normalizer class (accepts registry for dedup checking)
  normalize(raw)      — convenience: normalize to canonical HIL string
  normalize_command() — convenience: normalize to legacy envelope dict
  enforce_id(id)      — validate entity ID against canonical pattern
  is_valid_id(id)     — boolean ID check
  NormalizationError  — base error
  InvalidIDError      — malformed entity ID
  DuplicateEntityError — entity ID already registered
"""
from core.engine.normalization.normalizer import Normalizer, normalize, normalize_command
from core.engine.normalization.id_enforcer import enforce_id, is_valid_id, id_namespace, id_type_slug, id_slug
from core.engine.normalization.errors import NormalizationError, InvalidIDError, DuplicateEntityError

__all__ = [
    "Normalizer",
    "normalize",
    "normalize_command",
    "enforce_id",
    "is_valid_id",
    "id_namespace",
    "id_type_slug",
    "id_slug",
    "NormalizationError",
    "InvalidIDError",
    "DuplicateEntityError",
]
