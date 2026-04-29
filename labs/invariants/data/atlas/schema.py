"""
Pattern and Invariant Entity Schema
===================================
Cross-domain schemas for tracking discovered research invariants
across all Helix substrates (music, games, language, etc.).

Atlas becomes the knowledge engine of Helix by storing these
findings as first-class entities.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PatternNode:
    """A recurring structure or phenomenon observed in data."""
    pattern_id:         str
    pattern_name:       str
    description:        str
    substrate_origin:   str
    discovery_timestamp: str | None = None
    confidence_score:   float       = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PatternNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class InvariantNode:
    """A rigorously proven or hypothesized universal rule."""
    invariant_id:       str
    name:               str
    definition:         str
    discovery_context:  str
    validation_status:  str   # e.g., "UNTESTED", "FALSIFIED", "VERIFIED"

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "InvariantNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SupportingEvidenceNode:
    """Empirical data linking an invariant or pattern to a specific observation."""
    evidence_id:        str
    source_entity:      str   # ID of the track, game, text, etc.
    analysis_method:    str
    confidence_score:   float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SupportingEvidenceNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# Valid relationships for the Knowledge Graph:
INVARIANT_RELATIONS = {
    # Pattern -> X
    "instances",       # pattern -> entity
    "evidence_for",    # pattern -> invariant
    "originates_in",   # pattern -> substrate

    # Invariant -> X
    "exhibits",        # invariant -> pattern
    "supported_by",    # invariant -> supporting_evidence
    "applies_to",      # invariant -> substrate

    # Supporting Evidence -> X
    "validates",       # supporting_evidence -> invariant
    "derived_from",    # supporting_evidence -> artifact
    "found_in",        # supporting_evidence -> dataset
}
