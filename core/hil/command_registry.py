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
        subcommands=frozenset({"support", "trace", "cluster", "query", "export", "build"}),
        required_target_types=frozenset({
            "invariant", "experiment", "model", "graph", "graph_query",
        }),
        optional_params=frozenset({"depth", "format", "output"}),
        description="Query or export the Atlas Knowledge Graph.",
        example="GRAPH support invariant:decision_compression",
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
        subcommands=frozenset({"atlas", "wiki", "graph"}),
        required_target_types=frozenset({"atlas", "graph"}),
        optional_params=frozenset({"format", "output", "target"}),
        description="Export Helix discoveries into external formats.",
        example="EXPORT atlas format:wiki",
        allows_no_subcommand=False,
    ),
    "ANALYZE": CommandSpec(
        verb="ANALYZE",
        subcommands=frozenset({"atlas", "patterns", "features"}),
        required_target_types=frozenset({"atlas", "experiment"}),
        optional_params=frozenset({"verbose", "engine"}),
        description="Trigger post-hoc analysis of experiment artifacts.",
        example="ANALYZE atlas",
        allows_no_subcommand=True,
    ),
    "DISCOVER": CommandSpec(
        verb="DISCOVER",
        subcommands=frozenset({"invariants", "regimes", "probes"}),
        required_target_types=frozenset({"invariant", "domain"}),
        optional_params=frozenset({"domain", "threshold"}),
        description="Search for recurring patterns across validated experiments.",
        example="DISCOVER invariants domain:swarm",
        allows_no_subcommand=True,
    ),
    "SYSTEM": CommandSpec(
        verb="SYSTEM",
        subcommands=frozenset({
            "sync", "status", "diff", "log", "add", "commit", "push", "pull",
            "clean", "move", "rename", "delete", "mkdir", "list",
        }),
        required_target_types=frozenset(),
        optional_params=frozenset({"message", "verbose", "mode", "src", "dest", "path", "n"}),
        description="Git operations and file system tasks — no raw shell needed.",
        example="SYSTEM commit message:\"Enforce HIL execution pipeline\"",
        allows_no_subcommand=False,
    ),
    "OPERATOR": CommandSpec(
        verb="OPERATOR",
        subcommands=frozenset({"log", "status", "profile"}),
        required_target_types=frozenset(),
        optional_params=frozenset({"message", "context", "level"}),
        description="Manage operator context and logging.",
        example="OPERATOR log message:'Observed phase shift in Kuramoto trials'",
        allows_no_subcommand=False,
    ),
}

VALID_VERBS: frozenset[str] = frozenset(COMMAND_REGISTRY.keys())


def get_spec(verb: str) -> CommandSpec | None:
    return COMMAND_REGISTRY.get(verb.upper())


def list_verbs() -> list[str]:
    return sorted(COMMAND_REGISTRY.keys())
