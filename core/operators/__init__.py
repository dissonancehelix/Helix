"""
core.operators — Helix Operator System
========================================
Operators are the ONLY execution units in Helix runtime mode.

Each operator declares: accepted input types, output schema,
fixed pipeline stages, and failure conditions.

Operators dispatch predefined pipelines only. No arbitrary scripts.

Public API:
  OperatorSpec        — operator contract definition
  OperatorRegistry    — registry of all known operators
  get_registry()      — return the global operator registry singleton
"""
from core.operators.operator_spec import OperatorSpec
from core.operators.operator_registry import OperatorRegistry, get_registry, reset_registry

__all__ = [
    "OperatorSpec",
    "OperatorRegistry",
    "get_registry",
    "reset_registry",
]
