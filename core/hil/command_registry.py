"""
HIL Command Registry
====================
Formal specification of every HIL command family.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommandSpec:
    """Specification for one HIL command family."""
    verb:                   str
    subcommands:            frozenset[str]
    required_target_types:  frozenset[str]
    optional_params:        frozenset[str]
    description:            str
    example:                str
    allows_no_subcommand:   bool = True   # True = subcommand optional

    def has_subcommands(self) -> bool:
        return bool(self.subcommands)

    def requires_subcommand(self) -> bool:
        return bool(self.subcommands) and not self.allows_no_subcommand


COMMAND_REGISTRY: dict[str, CommandSpec] = {
    "PROBE": CommandSpec(
        verb="PROBE",
        subcommands=frozenset(),
        required_target_types=frozenset({"invariant", "experiment", "operator"}),
        optional_params=frozenset({"engine", "verbose"}),
        description="Run a targeted probe against an invariant, experiment, or operator.",
        example="PROBE invariant:decision_compression",
        allows_no_subcommand=True,
    ),
    "RUN": CommandSpec(
        verb="RUN",
        subcommands=frozenset(),
        required_target_types=frozenset({"experiment", "operator", "model"}),
        optional_params=frozenset({"engine", "verbose", "seed", "repeat"}),
        description="Execute an experiment, operator, or model.",
        example="RUN experiment:decision_compression_probe engine:python repeat:5",
        allows_no_subcommand=True,
    ),
    "SWEEP": CommandSpec(
        verb="SWEEP",
        subcommands=frozenset(),
        required_target_types=frozenset({"parameter"}),
        optional_params=frozenset({"range", "engine", "steps", "seed", "experiment"}),
        description="Sweep a parameter across a numeric range.",
        example="SWEEP parameter:coupling_strength range:0..1 steps:10 experiment:oscillator_lock_probe",
        allows_no_subcommand=True,
    ),
    "COMPILE": CommandSpec(
        verb="COMPILE",
        subcommands=frozenset({"atlas", "graph", "entries"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"overwrite", "quiet", "no_graph"}),
        description="Compile atlas entries, graph, or full pipeline.",
        example="COMPILE atlas",
        allows_no_subcommand=False,
    ),
    "INTEGRITY": CommandSpec(
        verb="INTEGRITY",
        subcommands=frozenset({"check", "report", "gate"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"verbose"}),
        description="Run the environment integrity verification suite.",
        example="INTEGRITY check",
        allows_no_subcommand=False,
    ),
    "ATLAS": CommandSpec(
        verb="ATLAS",
        subcommands=frozenset({"lookup", "list", "status", "verify"}),
        required_target_types=frozenset({
            "invariant", "experiment", "model", "regime", "operator", "atlas",
        }),
        optional_params=frozenset({"format", "verbose"}),
        description="Look up, list, or verify atlas entries.",
        example="ATLAS lookup invariant:decision_compression",
        allows_no_subcommand=False,
    ),
    "GRAPH": CommandSpec(
        verb="GRAPH",
        subcommands=frozenset({"support", "trace", "cluster", "query", "export", "build", "similarity", "motif", "composer_styles", "neighbors", "path", "edges"}),
        required_target_types=frozenset({
            "invariant", "experiment", "model", "graph", "graph_query", "composer", "soundtrack", "track", "entity",
        }),
        optional_params=frozenset({"depth", "format", "output", "composer", "soundtrack"}),
        description="Query or export the Atlas Knowledge Graph or music similarity/motif networks.",
        example="GRAPH similarity composer:jun_senoue",
        allows_no_subcommand=False,
    ),
    "VALIDATE": CommandSpec(
        verb="VALIDATE",
        subcommands=frozenset({
            "atlas", "entry", "invariant", "experiment", "operator", "model",
        }),
        required_target_types=frozenset({
            "invariant", "experiment", "model", "regime", "operator",
            "atlas", "atlas_entry", "graph", "graph_query"
        }),
        optional_params=frozenset({"strict", "verbose", "engine"}),
        description="Validate experiments or atlas entries against structural invariants.",
        example="VALIDATE experiment:decision_compression_probe",
        allows_no_subcommand=True,
    ),
    "TRACE": CommandSpec(
        verb="TRACE",
        subcommands=frozenset(),
        required_target_types=frozenset({"experiment", "operator", "artifact"}),
        optional_params=frozenset({"depth", "format", "verbose"}),
        description="Trace the execution history of an experiment or artifact.",
        example="TRACE experiment:decision_compression_probe",
        allows_no_subcommand=True,
    ),
    "OBSERVE": CommandSpec(
        verb="OBSERVE",
        subcommands=frozenset(),
        required_target_types=frozenset({"invariant", "experiment", "parameter"}),
        optional_params=frozenset({"window", "engine", "format"}),
        description="Passively observe an invariant or experiment.",
        example="OBSERVE invariant:decision_compression",
        allows_no_subcommand=True,
    ),
    "REPORT": CommandSpec(
        verb="REPORT",
        subcommands=frozenset({"summary", "full", "graph", "status"}),
        required_target_types=frozenset({
            "invariant", "experiment", "model", "atlas", "graph",
        }),
        optional_params=frozenset({"format", "output", "verbose"}),
        description="Generate a report on atlas objects or the knowledge graph.",
        example="REPORT summary invariant:decision_compression",
        allows_no_subcommand=True,
    ),
    "EXPORT": CommandSpec(
        verb="EXPORT",
        subcommands=frozenset({"atlas", "wiki", "graph", "composer_report"}),
        required_target_types=frozenset({"atlas", "graph"}),
        optional_params=frozenset({"format", "output", "target", "domain"}),
        description="Export Helix discoveries into external formats.",
        example="EXPORT atlas format:wiki domain:music",
        allows_no_subcommand=False,
    ),
    "ANALYZE": CommandSpec(
        verb="ANALYZE",
        subcommands=frozenset({"atlas", "patterns", "features", "music", "track", "composer", "soundtrack"}),
        required_target_types=frozenset({"atlas", "experiment", "music", "track", "composer", "soundtrack"}),
        optional_params=frozenset({"verbose", "engine", "track", "artist", "composers", "soundtrack"}),
        description="Trigger post-hoc analysis of experiment artifacts or music tracks/composers.",
        example="ANALYZE music:track track:\"Angel Island Zone\"",
        allows_no_subcommand=True,
    ),
    "DISCOVER": CommandSpec(
        verb="DISCOVER",
        subcommands=frozenset({"invariants", "experiments", "crossdomain", "execute"}),
        required_target_types=frozenset({"invariant", "domain"}),
        optional_params=frozenset({"domain", "threshold", "verbose"}),
        description="Search for or execute Atlas-driven discovery patterns.",
        example="DISCOVER experiments invariant:decision_compression",
        allows_no_subcommand=False,
    ),
    "SCAN": CommandSpec(
        verb="SCAN",
        subcommands=frozenset({"filesystem", "music_library"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"path"}),
        description="Scan directory or music library.",
        example="SCAN filesystem path:\"~/Music/VGM\"",
        allows_no_subcommand=False,
    ),
    "INDEX": CommandSpec(
        verb="INDEX",
        subcommands=frozenset({"music_library"}),
        required_target_types=frozenset(),
        optional_params=frozenset(),
        description="Build music library index.",
        example="INDEX music_library",
        allows_no_subcommand=False,
    ),
    "INGEST": CommandSpec(
        verb="INGEST",
        subcommands=frozenset({"music_library", "composer_dataset"}),
        required_target_types=frozenset(),
        optional_params=frozenset(),
        description="Ingest tracks or composer data.",
        example="INGEST music_library",
        allows_no_subcommand=False,
    ),
    "LIST": CommandSpec(
        verb="LIST",
        subcommands=frozenset({"tracks", "composers", "franchises"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"composer", "franchise"}),
        description="List tracks, composers, or franchises.",
        example="LIST tracks composer:\"Jun Senoue\"",
        allows_no_subcommand=False,
    ),
    "TRAIN": CommandSpec(
        verb="TRAIN",
        subcommands=frozenset({"composer_vectors"}),
        required_target_types=frozenset(),
        optional_params=frozenset(),
        description="Train composer style vectors.",
        example="TRAIN composer_vectors",
        allows_no_subcommand=False,
    ),
    "ATTRIBUTION": CommandSpec(
        verb="ATTRIBUTION",
        subcommands=frozenset({"soundtrack"}),
        required_target_types=frozenset({"soundtrack"}),
        optional_params=frozenset({"soundtrack"}),
        description="Perform composer attribution on a soundtrack.",
        example="ATTRIBUTION soundtrack soundtrack:\"Sonic 3 & Knuckles\"",
        allows_no_subcommand=False,
    ),
    "SYSTEM": CommandSpec(
        verb="SYSTEM",
        subcommands=frozenset({
            "sync", "status", "diff", "log", "add", "commit", "push", "pull",
            "clean", "move", "rename", "delete", "mkdir", "list", "create"
        }),
        required_target_types=frozenset(),
        optional_params=frozenset({"message", "verbose", "mode", "src", "dest", "path", "n"}),
        description="Git operations and file system tasks — no raw shell needed.",
        example="SYSTEM commit message:\"Enforce HIL execution pipeline\"",
        allows_no_subcommand=False,
    ),
    "OPERATOR": CommandSpec(
        verb="OPERATOR",
        subcommands=frozenset({"log", "status", "profile", "list", "registry"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"message", "context", "level"}),
        description="Manage and introspect the operator registry.",
        example="OPERATOR list",
        allows_no_subcommand=False,
    ),
    "ENTITY": CommandSpec(
        verb="ENTITY",
        subcommands=frozenset({"add", "get", "list", "link", "export"}),
        # required_target_types is empty: entity IDs span all entity types
        # (composer:, track:, game:, platform:, etc.). The HIL parser validates
        # entity id prefixes using is_entity_type() from core.hil.ontology.
        required_target_types=frozenset(),
        optional_params=frozenset({"type", "name", "relation", "target", "format"}),
        description="Add, retrieve, list, or link entities in the Helix entity registry.",
        example="ENTITY get music.composer:jun_senoue",
        allows_no_subcommand=False,
    ),
    "SUBSTRATE": CommandSpec(
        verb="SUBSTRATE",
        subcommands=frozenset({"list", "info", "run"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"name", "stages", "stage", "verbose", "soundtrack", "resume"}),
        description="List, inspect, or run a Helix substrate pipeline.",
        example="SUBSTRATE list",
        allows_no_subcommand=False,
    ),
}

VALID_VERBS: frozenset[str] = frozenset(COMMAND_REGISTRY.keys())


def get_spec(verb: str) -> CommandSpec | None:
    return COMMAND_REGISTRY.get(verb.upper())


def list_verbs() -> list[str]:
    return sorted(COMMAND_REGISTRY.keys())
