"""
Operators — OperatorSpec
=========================
Defines the contract for a Helix operator.

Operators are the ONLY execution units in runtime mode.
Each operator declares exactly what it accepts, what it produces,
which fixed pipeline stages it runs, and how it fails.

Operators must be deterministic. No dynamic script generation allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OperatorSpec:
    """
    Formal specification for a Helix operator.

    Fields:
      name                — unique operator name (uppercase, e.g. "PROBE")
      accepted_input_types — entity types this operator accepts as input
      output_schema       — expected output fields and their types
      pipeline_stages     — ordered, fixed execution stages
      failure_conditions  — named failure modes (for diagnostics)
      description         — human-readable operator description
      version             — semantic version string
    """
    name: str
    accepted_input_types: frozenset[str]
    output_schema: dict[str, str]           # field_name → type_string
    pipeline_stages: tuple[str, ...]
    failure_conditions: tuple[str, ...]
    description: str
    version: str

    def accepts(self, entity_type: str) -> bool:
        """Return True if this operator accepts the given entity type."""
        return entity_type in self.accepted_input_types or "*" in self.accepted_input_types

    def to_dict(self) -> dict[str, Any]:
        return {
            "name":                 self.name,
            "accepted_input_types": sorted(self.accepted_input_types),
            "output_schema":        self.output_schema,
            "pipeline_stages":      list(self.pipeline_stages),
            "failure_conditions":   list(self.failure_conditions),
            "description":          self.description,
            "version":              self.version,
        }
