"""
HIL Validator
=============
Semantic validation of parsed HILCommand AST nodes.

Validator checks (in order):
  1.  Grammar validity      (parser already enforced)
  2.  Known command family  (verb in registry)
  3.  Subcommand required   (per CommandSpec)
  4.  Target type validity  (prefix in OBJECT_TYPES)
  5.  At least one target   (if spec.required_target_types non-empty)
  6.  Target type match     (prefix must be in required_target_types)
  7.  Engine name validity
  8.  Range validity        (low <= high, numeric)
  9.  Atlas registry lookup (if registry provided)
  10. No raw shell bypass   (enforced by parser, double-checked here)

Errors returned:
  HILValidationError, HILUnknownTargetError, HILUnsafeCommandError

Compat API:
  validate_command(cmd: dict) -> {"valid": bool, "error": str | None}
  Used by hil_probe and other pre-Phase-11 callers.
"""
from __future__ import annotations

from core.hil.ast_nodes import HILCommand
from core.hil.errors import (
    HILValidationError, HILUnknownTargetError,
)
from core.hil.ontology import (
    OBJECT_TYPES, VALID_ENGINES, is_atlas_backed, plural_key, is_entity_type,
)
from core.hil.command_registry import get_spec, VALID_VERBS

# Blocked shell patterns (defense-in-depth after parser)
_BLOCKED: tuple[str, ...] = (
    "rm ", "rm\t", "mkfs", "dd ", "sudo ",
    "curl ", "wget ", "exec(", "eval(",
    "DROP ", "DELETE FROM", "> /dev/",
)


def validate(cmd: HILCommand, registry: dict | None = None) -> HILCommand:
    """
    Validate a HILCommand AST node.
    Returns cmd unchanged if valid; raises on any violation.
    """
    spec = get_spec(cmd.verb)
    if spec is None:
        raise HILValidationError(
            f"Unknown verb: {cmd.verb!r}", raw=cmd.raw
        )

    # 1. Subcommand check
    if spec.requires_subcommand():
        if cmd.subcommand not in {s.lower() for s in spec.subcommands}:
            raise HILValidationError(
                f"{cmd.verb} requires subcommand, one of: {sorted(spec.subcommands)}",
                raw=cmd.raw,
            )

    # 2. Target type validity — accept OBJECT_TYPES and entity ontology types
    for t in cmd.targets:
        if t.prefix not in OBJECT_TYPES and not is_entity_type(t.prefix):
            raise HILValidationError(
                f"Unknown object type: {t.prefix!r}", raw=cmd.raw
            )

    # 3. At least one target required
    if spec.required_target_types and not cmd.targets:
        # Allow subcommand-only commands (COMPILE atlas, INTEGRITY check)
        if not cmd.subcommand:
            raise HILValidationError(
                f"{cmd.verb} requires a typed target "
                f"(one of: {sorted(spec.required_target_types)})",
                raw=cmd.raw,
            )

    # 4. Target type must be in required_target_types (if spec constrains it)
    #    Entity types (from entity ontology) bypass this check — they are valid
    #    targets for any command that accepts typed entity references.
    if spec.required_target_types and cmd.targets:
        for t in cmd.targets:
            _free = {"engine", "parameter", "artifact", "atlas", "graph",
                     "atlas_entry", "graph_query", "experiment"}
            if (t.prefix not in spec.required_target_types | _free
                    and not is_entity_type(t.prefix)):
                raise HILValidationError(
                    f"{cmd.verb} does not accept {t.prefix!r} targets. "
                    f"Expected: {sorted(spec.required_target_types)}",
                    raw=cmd.raw,
                )

    # 5. Engine check
    if "engine" in cmd.params:
        eng = cmd.get_engine()
        if eng not in VALID_ENGINES:
            raise HILValidationError(
                f"Unknown engine: {eng!r}. Valid: {sorted(VALID_ENGINES)}",
                raw=cmd.raw,
            )

    # 6. Range check
    rng = cmd.get_range()
    if rng is not None and not rng.is_valid():
        raise HILValidationError(
            f"Invalid range {rng}: low must be <= high", raw=cmd.raw
        )

    # 7. Atlas registry existence check
    if registry:
        for t in cmd.targets:
            if is_atlas_backed(t.prefix):
                section = registry.get(plural_key(t.prefix), [])
                known = {
                    e.get("id", "") for e in section
                    if isinstance(e, dict)
                }
                if t.name not in known:
                    raise HILUnknownTargetError(
                        f"Unknown {t.prefix}: {t.name!r} "
                        f"(not in atlas registry)",
                        raw=cmd.raw,
                    )

    # 8. Defense-in-depth: blocked patterns on canonical string
    import re as _re
    canonical = cmd.canonical().lower()
    for pat in _BLOCKED:
        stripped = pat.strip()
        # Use word-boundary matching for short alphabetic tokens to avoid
        # false positives (e.g. "dd" matching inside "add").
        if stripped.isalpha() and len(stripped) <= 5:
            if _re.search(rf"\b{_re.escape(stripped)}\b", canonical):
                from core.hil.errors import HILUnsafeCommandError
                raise HILUnsafeCommandError(
                    f"Blocked pattern in canonical command: {stripped!r}",
                    raw=cmd.raw,
                )
        else:
            if stripped.lower() in canonical:
                from core.hil.errors import HILUnsafeCommandError
                raise HILUnsafeCommandError(
                    f"Blocked pattern in canonical command: {stripped!r}",
                    raw=cmd.raw,
                )

    return cmd


def validate_command(cmd: dict | str) -> dict:
    """
    Compat API: validate a dict or raw string.
    Returns {"valid": bool, "error": str | None}.
    Used by hil_probe and other pre-Phase-11 callers.
    """
    try:
        if isinstance(cmd, str):
            from core.hil.parser import parse
            ast = parse(cmd)
        else:
            # cmd is a dict from normalize_command
            canonical = cmd.get("canonical", "")
            if not canonical:
                # Reconstruct from parts
                verb   = cmd.get("verb", "").upper()
                target = cmd.get("target", "")
                canonical = f"{verb} {target}".strip() if target else verb
            if not canonical:
                return {"valid": False, "error": "HIL_VALIDATION_ERROR: empty command"}
            from core.hil.parser import parse
            ast = parse(canonical)
        validate(ast)
        return {"valid": True, "error": None}
    except Exception as e:
        return {"valid": False, "error": str(e)}
