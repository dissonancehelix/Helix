"""
Semantics — Property Type Registry
====================================
Defines typed property specifications used across entity types.

Each PropertySpec declares the expected value type and whether the property
is required. These definitions are referenced by SemanticSignature and used
during semantic validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PropertySpec:
    """Typed specification for a single entity property."""
    name: str
    value_type: str           # "str", "int", "float", "bool", "list", "dict"
    required: bool = False
    default: Any = None
    description: str = ""


# ── Universal properties ───────────────────────────────────────────────────

ID          = PropertySpec("id",          "str",  required=True,  description="Canonical entity ID: namespace.type:slug")
TYPE        = PropertySpec("type",        "str",  required=True,  description="Entity type from ENTITY_ONTOLOGY")
NAME        = PropertySpec("name",        "str",  required=True,  description="Human-readable display name")
LABEL       = PropertySpec("label",       "str",  required=True,  description="Short display label (may equal name)")
DESCRIPTION = PropertySpec("description", "str",  required=True,  description="One-sentence entity description")
METADATA    = PropertySpec("metadata",    "dict", required=False, description="Domain-specific provenance metadata")
EXTERNAL_IDS= PropertySpec("external_ids","dict", required=False, description="References to external knowledge bases")
RELATIONSHIPS=PropertySpec("relationships","list", required=False, description="Typed relationship list")

# ── Music domain properties ────────────────────────────────────────────────

BIRTH_YEAR   = PropertySpec("birth_year",   "int",   description="Year the composer was born")
NATIONALITY  = PropertySpec("nationality",  "str",   description="Composer's nationality")
ACTIVE_YEARS = PropertySpec("active_years", "str",   description="Range of active years, e.g. '1990-2005'")
PRIMARY_CHIP = PropertySpec("primary_chip", "str",   description="Preferred sound chip")

DURATION     = PropertySpec("duration",     "float", description="Track duration in seconds")
YEAR         = PropertySpec("year",         "int",   description="Release or composition year")
GENRE        = PropertySpec("genre",        "str",   description="Music genre")
CHIP         = PropertySpec("chip",         "str",   description="Sound chip used for this track")
BPM          = PropertySpec("bpm",          "float", description="Beats per minute")
KEY          = PropertySpec("key",          "str",   description="Musical key, e.g. 'C major'")

RELEASE_YEAR = PropertySpec("release_year", "int",   description="Year the game or album was released")
PUBLISHER    = PropertySpec("publisher",    "str",   description="Game or media publisher")
DEVELOPER    = PropertySpec("developer",    "str",   description="Game developer studio")
REGION       = PropertySpec("region",       "str",   description="Release region, e.g. 'JP', 'US'")

MANUFACTURER  = PropertySpec("manufacturer",   "str",   description="Hardware manufacturer")
CHANNELS      = PropertySpec("channels",       "int",   description="Number of audio channels")
CLOCK_SPEED   = PropertySpec("clock_speed_hz", "int",   description="Chip clock speed in Hz")
CHIP_TYPE     = PropertySpec("chip_type",      "str",   description="Chip family/type, e.g. 'FM', 'PSG'")

FOUNDED_YEAR  = PropertySpec("founded_year",   "int",   description="Year the studio or team was founded")
COUNTRY       = PropertySpec("country",        "str",   description="Country of origin")
PARENT_COMPANY= PropertySpec("parent_company", "str",   description="Parent company or organization")

# ── Research domain properties ─────────────────────────────────────────────

SOURCE        = PropertySpec("source",         "str",   required=True, description="Origin system or dataset")
VERSION       = PropertySpec("version",        "str",   required=True, description="Semantic version string, e.g. '1.0.0'")
CONFIDENCE    = PropertySpec("confidence",     "str",   description="Confidence class: Structural/Verified/Candidate/Exploratory")
DOMAINS       = PropertySpec("domains",        "list",  description="List of substrate domains where invariant holds")
PASS_RATE     = PropertySpec("pass_rate",      "float", description="Fraction of probes that passed [0.0, 1.0]")
FALSIFIERS    = PropertySpec("falsifiers",     "str",   description="Conditions under which this invariant would be falsified")
HYPOTHESIS    = PropertySpec("hypothesis",     "str",   description="Experiment hypothesis statement")
RESULT        = PropertySpec("result",         "str",   description="Experiment outcome summary")
RUN_COUNT     = PropertySpec("run_count",      "int",   description="Number of probe runs completed")
ARCHITECTURE  = PropertySpec("architecture",   "str",   description="Model architecture type")
PARAMETERS    = PropertySpec("parameters",     "dict",  description="Model parameter configuration")
INPUT_TYPES   = PropertySpec("input_types",    "list",  description="Accepted input entity types for an operator")
OUTPUT_SCHEMA = PropertySpec("output_schema",  "dict",  description="Expected output field schema")
PIPELINE_STAGES=PropertySpec("pipeline_stages","list",  description="Ordered execution stages")
RECORD_COUNT  = PropertySpec("record_count",   "int",   description="Number of records in dataset")
FORMAT        = PropertySpec("format",         "str",   description="Data format, e.g. 'json', 'csv'")
SUBSTRATE     = PropertySpec("substrate",      "str",   description="Helix substrate this entity belongs to")

# ── Registry ───────────────────────────────────────────────────────────────

_PROPERTIES: dict[str, PropertySpec] = {
    p.name: p
    for p in [
        ID, TYPE, NAME, LABEL, DESCRIPTION, METADATA, EXTERNAL_IDS, RELATIONSHIPS,
        BIRTH_YEAR, NATIONALITY, ACTIVE_YEARS, PRIMARY_CHIP,
        DURATION, YEAR, GENRE, CHIP, BPM, KEY,
        RELEASE_YEAR, PUBLISHER, DEVELOPER, REGION,
        MANUFACTURER, CHANNELS, CLOCK_SPEED, CHIP_TYPE,
        FOUNDED_YEAR, COUNTRY, PARENT_COMPANY,
        SOURCE, VERSION, CONFIDENCE, DOMAINS, PASS_RATE, FALSIFIERS,
        HYPOTHESIS, RESULT, RUN_COUNT, ARCHITECTURE, PARAMETERS,
        INPUT_TYPES, OUTPUT_SCHEMA, PIPELINE_STAGES,
        RECORD_COUNT, FORMAT, SUBSTRATE,
    ]
}


def get_property(name: str) -> PropertySpec | None:
    return _PROPERTIES.get(name)


def all_property_names() -> frozenset[str]:
    return frozenset(_PROPERTIES.keys())
