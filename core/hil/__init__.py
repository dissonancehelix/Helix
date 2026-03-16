"""
HIL — Helix Interface Language
================================
Phase 11: Full formal HIL package.

Public API (new):
  parse(raw)           -> HILCommand AST
  validate(cmd)        -> HILCommand (validated)
  normalize(raw)       -> str (canonical HIL string)
  dispatch(raw, ...)   -> dict (result)

Compat API (legacy callers):
  parse_command(raw)     -> dict
  validate_command(cmd)  -> {"valid": bool, "error": str | None}
  normalize_command(raw) -> dict
"""

# New API
from .parser            import parse
from .validator         import validate
from .normalizer        import normalize
from .dispatch_interface import dispatch

# Compat API
from .grammar    import parse_command
from .validator  import validate_command
from .normalizer import normalize_command

# Core types
from .ast_nodes import HILCommand, TypedRef, RangeExpr
from .errors    import (
    HILError, HILSyntaxError, HILValidationError,
    HILUnknownCommandError, HILUnknownTargetError,
    HILUnsafeCommandError, HILAmbiguityError,
)
from .ontology       import OBJECT_TYPES, VALID_ENGINES
from .command_registry import VALID_VERBS, list_verbs, get_spec
from .command_logger   import CommandLogger
from .aliases          import resolve_alias, list_aliases

__all__ = [
    # New API
    "parse", "validate", "normalize", "dispatch",
    # Compat API
    "parse_command", "validate_command", "normalize_command",
    # Types
    "HILCommand", "TypedRef", "RangeExpr",
    # Errors
    "HILError", "HILSyntaxError", "HILValidationError",
    "HILUnknownCommandError", "HILUnknownTargetError",
    "HILUnsafeCommandError", "HILAmbiguityError",
    # Registry & ontology
    "OBJECT_TYPES", "VALID_ENGINES", "VALID_VERBS",
    "list_verbs", "get_spec",
    # Utilities
    "CommandLogger", "resolve_alias", "list_aliases",
]
