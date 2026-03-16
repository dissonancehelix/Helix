"""
HIL AST Nodes
=============
Typed AST node classes produced by the HIL parser.
Every valid command produces a HILCommand; canonical() serializes it back.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TypedRef:
    """A typed object reference: prefix:name  e.g. invariant:decision_compression"""
    prefix: str
    name:   str

    def __str__(self) -> str:
        return f"{self.prefix}:{self.name}"

    def canonical(self) -> str:
        return f"{self.prefix}:{self.name}"


@dataclass
class RangeExpr:
    """A numeric range expression: low..high  e.g. 0..1"""
    low:  float
    high: float

    def __str__(self) -> str:
        lo = int(self.low)  if self.low  == int(self.low)  else self.low
        hi = int(self.high) if self.high == int(self.high) else self.high
        return f"{lo}..{hi}"

    def is_valid(self) -> bool:
        return self.low <= self.high

    def canonical(self) -> str:
        return str(self)


@dataclass
class HILCommand:
    """
    A fully parsed HIL command.

    Fields
    ------
    verb        Upper-cased command family: PROBE, RUN, SWEEP, ...
    subcommand  Optional subcommand word:  lookup, trace, check, ...
    targets     Ordered list of typed object references
    params      Key -> value parameter map (engine, range, steps, ...)
    raw         Original unmodified input string
    source      Always 'hil'
    version     Protocol version string
    """
    verb:       str
    subcommand: str | None
    targets:    list[TypedRef]
    params:     dict[str, Any]
    raw:        str
    source:     str = "hil"
    version:    str = "1.0"

    def primary_target(self) -> TypedRef | None:
        return self.targets[0] if self.targets else None

    def get_engine(self) -> str:
        ref = self.params.get("engine")
        if isinstance(ref, TypedRef):
            return ref.name
        if isinstance(ref, str):
            return ref
        return "python"

    def get_range(self) -> RangeExpr | None:
        r = self.params.get("range")
        return r if isinstance(r, RangeExpr) else None

    def canonical(self) -> str:
        """Produce the canonical normalized HIL string for this command."""
        parts: list[str] = [self.verb]
        if self.subcommand:
            parts.append(self.subcommand)
        for t in self.targets:
            parts.append(t.canonical())
        for k, v in self.params.items():
            if isinstance(v, RangeExpr):
                parts.append(f"range:{v}")
            elif isinstance(v, TypedRef):
                parts.append(f"{v.prefix}:{v.name}")
            elif v is not None:
                parts.append(f"{k}:{v}")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {
            "verb":       self.verb,
            "subcommand": self.subcommand,
            "targets":    [str(t) for t in self.targets],
            "params":     {k: str(v) for k, v in self.params.items()},
            "raw":        self.raw,
            "canonical":  self.canonical(),
            "source":     self.source,
            "version":    self.version,
        }
