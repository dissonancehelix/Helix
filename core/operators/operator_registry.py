"""
Operators — OperatorRegistry
==============================
Singleton registry of all known Helix operators.

In runtime mode, only registered operators may be executed via RUN.
Any RUN targeting an unregistered operator raises HILValidationError.
"""
from __future__ import annotations

from core.operators.operator_spec import OperatorSpec


class OperatorRegistry:
    """
    Registry of Helix operators.

    Operators are registered at startup by builtin_operators.py.
    In dev mode, new operators may be registered dynamically.
    In runtime mode, the registry is immutable.
    """

    def __init__(self) -> None:
        self._operators: dict[str, OperatorSpec] = {}
        self._locked: bool = False

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, spec: OperatorSpec) -> None:
        """Register an operator. Raises RuntimeError if registry is locked."""
        if self._locked:
            raise RuntimeError(
                f"Cannot register operator {spec.name!r} — "
                f"registry is locked in runtime mode. "
                f"Set HELIX_MODE=dev to allow operator registration."
            )
        self._operators[spec.name.upper()] = spec

    def lock(self) -> None:
        """Lock the registry. Called when entering runtime mode."""
        self._locked = True

    # ── Lookup ────────────────────────────────────────────────────────────

    def get(self, name: str) -> OperatorSpec | None:
        """Return OperatorSpec by name (case-insensitive), or None if not found."""
        return self._operators.get(name.upper())

    def require(self, name: str) -> OperatorSpec:
        """
        Return OperatorSpec by name, or raise HILValidationError if not found.
        Used by interpreter._exec_run() to enforce closed-world assumption.
        """
        spec = self.get(name)
        if spec is None:
            from core.hil.errors import HILValidationError
            raise HILValidationError(
                f"Unknown operator {name!r}. "
                f"Registered operators: {', '.join(sorted(self._operators))}",
                raw=f"RUN operator:{name}",
            )
        return spec

    def all(self) -> list[OperatorSpec]:
        return list(self._operators.values())

    def names(self) -> list[str]:
        return sorted(self._operators.keys())

    def __contains__(self, name: str) -> bool:
        return name.upper() in self._operators

    def __len__(self) -> int:
        return len(self._operators)

    def to_dict(self) -> dict:
        return {
            "operators": [spec.to_dict() for spec in self._operators.values()],
            "count": len(self._operators),
            "locked": self._locked,
        }


# ── Module-level singleton ─────────────────────────────────────────────────

_registry: OperatorRegistry | None = None


def get_registry() -> OperatorRegistry:
    """Return the global operator registry, initializing it on first call."""
    global _registry
    if _registry is None:
        _registry = OperatorRegistry()
        from core.operators.builtin_operators import register_builtins
        register_builtins(_registry)
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing only)."""
    global _registry
    _registry = None
