"""
Semantics — Relationship Type Registry
========================================
Defines RelationshipSpec for every valid relationship between entity types.

A RelationshipSpec declares:
  name           — relationship name (uppercase, e.g. "COMPOSED")
  source_types   — entity types allowed as the relationship source
  target_types   — entity types allowed as the relationship target
  bidirectional  — if True, the reverse relationship is also semantically valid

Relationships not defined here are rejected by SemanticValidator.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationshipSpec:
    """Typed specification for a valid entity relationship."""
    name: str
    source_types: frozenset[str]
    target_types: frozenset[str]
    bidirectional: bool = False
    description: str = ""


# ── Music domain relationships ─────────────────────────────────────────────

APPEARED_ON = RelationshipSpec(
    name="APPEARED_ON",
    source_types=frozenset({"Artist", "Composer"}),
    target_types=frozenset({"Track"}),
    description="An artist or composer appears on this track (primary or any credited role)",
)

FEATURED_ON = RelationshipSpec(
    name="FEATURED_ON",
    source_types=frozenset({"Artist", "Composer"}),
    target_types=frozenset({"Track"}),
    description="An artist is featured on this track (derived from FEATURING tag)",
)

COMPOSED = RelationshipSpec(
    name="COMPOSED",
    source_types=frozenset({"Composer"}),
    target_types=frozenset({"Track", "Soundtrack"}),
    description="A composer created this track or soundtrack",
)

COMPOSED_BY = RelationshipSpec(
    name="COMPOSED_BY",
    source_types=frozenset({"Track", "Soundtrack"}),
    target_types=frozenset({"Composer"}),
    description="This track or soundtrack was composed by a composer (reverse of COMPOSED)",
)

APPEARS_IN = RelationshipSpec(
    name="APPEARS_IN",
    source_types=frozenset({"Track"}),
    target_types=frozenset({"Game", "Soundtrack"}),
    description="A track appears in a game or soundtrack",
)

HAS_SOUNDTRACK = RelationshipSpec(
    name="HAS_SOUNDTRACK",
    source_types=frozenset({"Game"}),
    target_types=frozenset({"Soundtrack"}),
    description="A game has a soundtrack",
)

RUNS_ON = RelationshipSpec(
    name="RUNS_ON",
    source_types=frozenset({"Game"}),
    target_types=frozenset({"Platform"}),
    description="A game runs on a hardware platform",
)

HOSTS = RelationshipSpec(
    name="HOSTS",
    source_types=frozenset({"Platform"}),
    target_types=frozenset({"Game"}),
    description="A platform hosts this game (reverse of RUNS_ON)",
)

USES_CHIP = RelationshipSpec(
    name="USES_CHIP",
    source_types=frozenset({"Game", "Platform"}),
    target_types=frozenset({"SoundChip"}),
    description="A game or platform uses this sound chip",
)

USED_BY = RelationshipSpec(
    name="USED_BY",
    source_types=frozenset({"SoundChip", "Dataset", "Driver"}),
    target_types=frozenset({"Game", "Platform", "Experiment", "Operator"}),
    description="This entity is used by another entity",
)

MEMBER_OF = RelationshipSpec(
    name="MEMBER_OF",
    source_types=frozenset({"Composer"}),
    target_types=frozenset({"SoundTeam", "Studio"}),
    description="A composer is a member of a sound team or studio",
)

COLLABORATED_WITH = RelationshipSpec(
    name="COLLABORATED_WITH",
    source_types=frozenset({"Composer", "Studio"}),
    target_types=frozenset({"Composer", "Studio"}),
    bidirectional=True,
    description="Two composers or studios collaborated",
)

PART_OF = RelationshipSpec(
    name="PART_OF",
    source_types=frozenset({"Track", "Soundtrack"}),
    target_types=frozenset({"Soundtrack", "Game"}),
    description="An entity is part of a larger collection",
)

RELEASED_BY = RelationshipSpec(
    name="RELEASED_BY",
    source_types=frozenset({"Soundtrack", "Game"}),
    target_types=frozenset({"Studio"}),
    description="A soundtrack or game was released by a studio",
)

PUBLISHED = RelationshipSpec(
    name="PUBLISHED",
    source_types=frozenset({"Studio"}),
    target_types=frozenset({"Game", "Soundtrack"}),
    description="A studio published this game or soundtrack",
)

DEVELOPED = RelationshipSpec(
    name="DEVELOPED",
    source_types=frozenset({"Studio"}),
    target_types=frozenset({"Game"}),
    description="A studio developed this game",
)

# ── Research domain relationships ──────────────────────────────────────────

SUPPORTS = RelationshipSpec(
    name="SUPPORTS",
    source_types=frozenset({"Experiment"}),
    target_types=frozenset({"Invariant", "Model"}),
    description="An experiment supports an invariant or model",
)

SUPPORTED_BY = RelationshipSpec(
    name="SUPPORTED_BY",
    source_types=frozenset({"Invariant", "Model"}),
    target_types=frozenset({"Experiment"}),
    description="An invariant or model is supported by an experiment",
)

CONTRADICTS = RelationshipSpec(
    name="CONTRADICTS",
    source_types=frozenset({"Experiment"}),
    target_types=frozenset({"Invariant", "Model"}),
    description="An experiment contradicts an invariant or model",
)

CONTRADICTED_BY = RelationshipSpec(
    name="CONTRADICTED_BY",
    source_types=frozenset({"Invariant", "Model"}),
    target_types=frozenset({"Experiment"}),
    description="An invariant or model is contradicted by an experiment",
)

TESTS = RelationshipSpec(
    name="TESTS",
    source_types=frozenset({"Experiment"}),
    target_types=frozenset({"Invariant", "Model"}),
    description="An experiment tests an invariant or model hypothesis",
)

TESTED_BY = RelationshipSpec(
    name="TESTED_BY",
    source_types=frozenset({"Invariant", "Model"}),
    target_types=frozenset({"Experiment"}),
    description="An invariant is tested by an experiment",
)

DERIVES_FROM = RelationshipSpec(
    name="DERIVED_FROM",
    source_types=frozenset({"Dataset", "Model", "Experiment"}),
    target_types=frozenset({"Dataset", "Experiment"}),
    description="This entity was derived from another",
)

IMPLEMENTS = RelationshipSpec(
    name="IMPLEMENTS",
    source_types=frozenset({"Operator", "Model"}),
    target_types=frozenset({"Invariant", "Model"}),
    description="An operator or model implements an invariant or model spec",
)

USES = RelationshipSpec(
    name="USES",
    source_types=frozenset({"Operator", "Experiment"}),
    target_types=frozenset({"Dataset", "Model"}),
    description="An operator or experiment uses a dataset or model",
)

PRODUCES = RelationshipSpec(
    name="PRODUCES",
    source_types=frozenset({"Operator"}),
    target_types=frozenset({"Dataset", "Experiment"}),
    description="An operator produces a dataset or experiment artifact",
)

TRAINED_ON = RelationshipSpec(
    name="TRAINED_ON",
    source_types=frozenset({"Model"}),
    target_types=frozenset({"Dataset"}),
    description="A model was trained on a dataset",
)

EVALUATED_BY = RelationshipSpec(
    name="EVALUATED_BY",
    source_types=frozenset({"Model"}),
    target_types=frozenset({"Experiment"}),
    description="A model was evaluated by an experiment",
)

DRIVES = RelationshipSpec(
    name="DRIVES",
    source_types=frozenset({"Driver"}),
    target_types=frozenset({"Infrasubstrate"}),
    description="A driver operates an infrasubstrate",
)

DEPENDS_ON = RelationshipSpec(
    name="DEPENDS_ON",
    source_types=frozenset({"Infrasubstrate"}),
    target_types=frozenset({"Infrasubstrate"}),
    description="An infrasubstrate depends on another",
)

PROVIDES = RelationshipSpec(
    name="PROVIDES",
    source_types=frozenset({"Infrasubstrate"}),
    target_types=frozenset({"Operator", "Driver"}),
    description="An infrasubstrate provides a capability",
)

# ── Registry ───────────────────────────────────────────────────────────────

_RELATIONSHIPS: dict[str, RelationshipSpec] = {
    r.name: r
    for r in [
        APPEARED_ON, FEATURED_ON,
        COMPOSED, COMPOSED_BY, APPEARS_IN, HAS_SOUNDTRACK, RUNS_ON, HOSTS,
        USES_CHIP, USED_BY, MEMBER_OF, COLLABORATED_WITH, PART_OF,
        RELEASED_BY, PUBLISHED, DEVELOPED,
        SUPPORTS, SUPPORTED_BY, CONTRADICTS, CONTRADICTED_BY,
        TESTS, TESTED_BY, DERIVES_FROM, IMPLEMENTS, USES, PRODUCES,
        TRAINED_ON, EVALUATED_BY, DRIVES, DEPENDS_ON, PROVIDES,
    ]
}


def get_relationship(name: str) -> RelationshipSpec | None:
    return _RELATIONSHIPS.get(name)


def all_relationship_names() -> frozenset[str]:
    return frozenset(_RELATIONSHIPS.keys())


def relationships_for_type(entity_type: str) -> list[RelationshipSpec]:
    """Return all RelationshipSpecs where entity_type is a valid source."""
    return [r for r in _RELATIONSHIPS.values() if entity_type in r.source_types]
