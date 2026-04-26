"""
Entity Ontology
===============
Single-source entity type definitions for the Helix entity system.

Consumed by:
  core/entities/schema.py  — validation
  core/entities/registry.py — type filtering
  core.hsl/ontology.py      — HIL parser entity type recognition
"""
from __future__ import annotations

# Core entity types: fully supported, used by existing domains
ENTITY_CORE_TYPES: frozenset[str] = frozenset({
    "Artist",       # phase 5: general music performer/contributor (broader than Composer)
    "Composer",
    "Track",
    "Game",
    "Platform",
    "SoundChip",
    "SoundDriver",
    "SoundTeam",
    "KnowledgeSource",
})

# Reserved entity types: defined in ontology but not yet required by active domains
ENTITY_RESERVED_TYPES: frozenset[str] = frozenset({
    "Soundtrack",
    "Studio",
    "Dataset",
    "Corpus",
    "Text",
    "Experiment",
    "Model",
    "Invariant",
    "Operator",
    "Infrasubstrate",
    "MathModel",           # formal mathematical model
    "Conjecture",          # formal conjecture statement
    "Proof",               # mathematical proof or derivation
    "CriticalThreshold",   # critical parameter value (math)
    "PhaseTransition",     # identified phase transition
    "InvariantCandidate",  # proposed invariant from theory
    "ResearchReport",      # high-level research output (falsification, mapping, etc.)
})

# HSL structural entity types: produced by substrate translation pipelines
# (e.g. INGEST_TRACK → ANALYZE_TRACK → STYLE_VECTOR → COMPILE_ATLAS)
ENTITY_HSL_STRUCTURAL_TYPES: frozenset[str] = frozenset({
    "ControlSequence",    # chip_control dialect artifact
    "SymbolicScore",      # symbolic_music dialect artifact
    "SignalProfile",      # perceptual_audio dialect artifact
    "ArtistStyleVector",  # style_space invariant representation
})

# Full ontology: all recognized entity types
ENTITY_ONTOLOGY: frozenset[str] = (
    ENTITY_CORE_TYPES | ENTITY_RESERVED_TYPES | ENTITY_HSL_STRUCTURAL_TYPES
)


def is_core_entity_type(type_str: str) -> bool:
    return type_str in ENTITY_CORE_TYPES


def is_reserved_entity_type(type_str: str) -> bool:
    return type_str in ENTITY_RESERVED_TYPES


def is_music_analysis_entity_type(type_str: str) -> bool:
    return type_str in ENTITY_HSL_STRUCTURAL_TYPES


def is_known_entity_type(type_str: str) -> bool:
    return type_str in ENTITY_ONTOLOGY
