"""
HIL Ontology
============
Object type categories recognised by HIL.
Legal type prefixes for typed references: prefix:name
"""
from __future__ import annotations

OBJECT_TYPES: frozenset[str] = frozenset({
    "invariant", "experiment", "model", "regime", "operator",
    "artifact", "engine", "parameter", "atlas", "graph",
    "atlas_entry", "graph_query",
})

ATLAS_BACKED_TYPES: frozenset[str] = frozenset({
    "invariant", "experiment", "model", "regime", "operator",
})

VALID_ENGINES: frozenset[str] = frozenset({"python", "godot"})

FREE_PARAM_TYPES: frozenset[str] = frozenset({
    "parameter", "artifact", "atlas", "graph", "atlas_entry", "graph_query",
})

_PLURAL: dict[str, str] = {
    "invariant":  "invariants",
    "experiment": "experiments",
    "model":      "models",
    "regime":     "regimes",
    "operator":   "operators",
}


def is_valid_type(prefix: str) -> bool:
    return prefix in OBJECT_TYPES

def is_atlas_backed(prefix: str) -> bool:
    return prefix in ATLAS_BACKED_TYPES

def is_free_param(prefix: str) -> bool:
    return prefix in FREE_PARAM_TYPES

def plural_key(prefix: str) -> str:
    """Return the atlas_index.yaml section key for this type prefix."""
    return _PLURAL.get(prefix, prefix + "s")
