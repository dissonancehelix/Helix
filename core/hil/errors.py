"""
HIL Error Hierarchy
===================
Structured error classes for the Helix Interface Language.
Parser errors and validator errors are always distinct.
"""
from __future__ import annotations


class HILError(Exception):
    """Base class for all HIL errors."""

    def __init__(self, message: str, raw: str = "", position: int = -1):
        super().__init__(message)
        self.raw      = raw
        self.position = position

    def to_dict(self) -> dict:
        return {
            "error_type": type(self).__name__,
            "message":    str(self),
            "raw":        self.raw,
            "position":   self.position,
        }


class HILSyntaxError(HILError):
    """Tokenizer or parser failed to parse the raw input."""


class HILValidationError(HILError):
    """Parsed command failed semantic validation."""


class HILUnknownCommandError(HILError):
    """Verb is not registered in the HIL command registry."""


class HILUnknownTargetError(HILError):
    """Typed reference names an object not present in the atlas registry."""


class HILUnsafeCommandError(HILError):
    """Command contains a pattern blocked by the HIL safety policy."""


class HILAmbiguityError(HILError):
    """Alias expansion is ambiguous — multiple valid expansions exist."""
