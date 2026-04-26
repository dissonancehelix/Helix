"""
ambiguity.py — Resolution state model for Phase 5 credit resolution.

Tracks how confident Helix is that a credited string (from a Foobar tag)
maps to a known, unique semantic entity.

Resolution states (descending confidence):
  resolved              exact codex match — one entity, one identity
  likely_resolved       strong match by name normalization or alias
  alias_candidate       multiple plausible codex entities for same string
  ambiguous             string appears to be multiple people merged in one tag
  unresolved            no codex match found; entity placeholder created
  manual_review_required  conflicting signals across sources; needs human check

Provenance sources:
  derived_from_foobar_tags    primary tag read from library JSON
  supported_by_lastfm         Last.fm scrobble or artist metadata corroborates
  supported_by_spotify        Spotify artist match corroborates
  supported_by_codex          codex artist JSON explicitly names this form
  manual_override             a human set this explicitly; do not auto-update
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ResolutionState(str, Enum):
    RESOLVED               = "resolved"
    LIKELY_RESOLVED        = "likely_resolved"
    ALIAS_CANDIDATE        = "alias_candidate"
    AMBIGUOUS              = "ambiguous"
    UNRESOLVED             = "unresolved"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"

    def confidence_floor(self) -> float:
        """Minimum confidence score associated with this state."""
        _floors = {
            ResolutionState.RESOLVED:               0.95,
            ResolutionState.LIKELY_RESOLVED:        0.75,
            ResolutionState.ALIAS_CANDIDATE:        0.55,
            ResolutionState.AMBIGUOUS:              0.30,
            ResolutionState.UNRESOLVED:             0.10,
            ResolutionState.MANUAL_REVIEW_REQUIRED: 0.00,
        }
        return _floors[self]

    def is_usable(self) -> bool:
        """True if this resolution is good enough for analysis pipelines."""
        return self in (
            ResolutionState.RESOLVED,
            ResolutionState.LIKELY_RESOLVED,
        )


class ProvenanceSource(str, Enum):
    FOOBAR_TAGS      = "derived_from_foobar_tags"
    LASTFM           = "supported_by_lastfm"
    SPOTIFY          = "supported_by_spotify"
    CODEX            = "supported_by_codex"
    MANUAL_OVERRIDE  = "manual_override"


@dataclass
class ConfidenceRecord:
    """
    Tracks the confidence and provenance of a single entity resolution.

    Attached to Artist/Composer entities produced by credit_resolver.
    """
    resolution_state: ResolutionState
    confidence:       float                         # 0.0–1.0
    provenance:       list[ProvenanceSource] = field(default_factory=list)
    credited_forms:   list[str]             = field(default_factory=list)
    notes:            str                   = ""

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")

    def to_dict(self) -> dict:
        return {
            "resolution_state": self.resolution_state.value,
            "confidence":       self.confidence,
            "provenance":       [p.value for p in self.provenance],
            "credited_forms":   self.credited_forms,
            "notes":            self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConfidenceRecord":
        return cls(
            resolution_state=ResolutionState(d["resolution_state"]),
            confidence=d["confidence"],
            provenance=[ProvenanceSource(p) for p in d.get("provenance", [])],
            credited_forms=d.get("credited_forms", []),
            notes=d.get("notes", ""),
        )
