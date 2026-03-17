"""
Normalization — Normalizer
===========================
Standalone normalization layer for the Helix execution pipeline.

Position in pipeline:
  HIL input → [Normalizer] → Semantics → Operators → Atlas

Responsibilities:
  1. Alias resolution       — human shorthand → canonical HIL
  2. Casing normalization   — verbs upper, slugs lower
  3. Canonical ID enforcement — entity IDs validated against pattern
  4. Typed reference resolution — prefix:name → registry entity (if registry provided)
  5. Deduplication detection — warn if entity ID already registered

This module is the authoritative normalization gate.
core/hil/normalizer.py delegates here.
"""
from __future__ import annotations

from typing import Any

from core.normalization.errors import NormalizationError, DuplicateEntityError
from core.normalization.id_enforcer import enforce_id, is_valid_id


class Normalizer:
    """
    Converts raw HIL input to canonical form and validates entity IDs.

    Usage:
        n = Normalizer()
        canonical_hil = n.normalize("probe decision compression")
        n.enforce_entity_id("music.composer:jun_senoue")
    """

    def __init__(self, registry: Any = None) -> None:
        """
        registry: optional EntityRegistry instance for typed-ref resolution
                  and deduplication checking.
        """
        self._registry = registry

    # ── HIL normalization ──────────────────────────────────────────────────

    def normalize(self, raw: str) -> str:
        """
        Normalize raw input to a canonical HIL string.

        Steps:
          1. Alias resolution
          2. Parse to AST
          3. AST → canonical string
        """
        from core.hil.aliases import resolve_alias
        from core.hil.parser import parse
        from core.hil.errors import HILSyntaxError

        tokens = raw.strip().split()
        if not tokens:
            raise NormalizationError("Empty input cannot be normalized", raw=raw)

        alias = resolve_alias(tokens)
        if alias:
            raw = alias

        cmd = parse(raw)
        return cmd.canonical()

    def normalize_command(self, raw: str) -> dict:
        """
        Normalize and return a legacy envelope dict.
        Backward-compatible with core/hil/normalizer.normalize_command().
        """
        from core.hil.aliases import resolve_alias
        from core.hil.parser import parse

        tokens = raw.strip().split()
        if not tokens:
            raise NormalizationError("Empty input cannot be normalized", raw=raw)

        alias = resolve_alias(tokens)
        if alias:
            raw = alias

        cmd = parse(raw)
        primary = cmd.primary_target()
        return {
            "verb":      cmd.verb.lower(),
            "target":    str(primary) if primary else (cmd.subcommand or ""),
            "params":    {k: str(v) for k, v in cmd.params.items()},
            "source":    "hil",
            "version":   "1.0",
            "canonical": cmd.canonical(),
            "ast":       cmd.to_dict(),
        }

    # ── Entity ID normalization ────────────────────────────────────────────

    def enforce_entity_id(self, entity_id: str) -> str:
        """
        Validate entity_id against canonical pattern.
        Returns the id if valid, raises InvalidIDError otherwise.
        """
        return enforce_id(entity_id)

    def check_duplicate(self, entity_id: str) -> bool:
        """
        Return True if entity_id is already registered.
        Raises DuplicateEntityError if registry is present and entity exists.
        """
        if self._registry is None:
            return False
        if entity_id in self._registry:
            return True
        return False

    def enforce_no_duplicate(self, entity_id: str) -> None:
        """Raise DuplicateEntityError if entity_id is already registered."""
        if self.check_duplicate(entity_id):
            raise DuplicateEntityError(
                f"Entity ID {entity_id!r} is already registered. "
                f"Use ENTITY get {entity_id} or provide a unique slug.",
                raw=entity_id,
            )

    # ── Typed reference resolution ─────────────────────────────────────────

    def resolve_typed_ref(self, ref: Any) -> dict | None:
        """
        Resolve a TypedRef to its registry entity dict.

        Returns the entity dict if found, None if registry unavailable,
        raises EntityNotFoundError if registry present but entity missing.
        """
        if self._registry is None:
            return None

        entity_id = ref.entity_id() if hasattr(ref, "entity_id") else str(ref)
        entity = self._registry.get(entity_id)
        if entity is None:
            from core.kernel.schema.entities.resolver import EntityNotFoundError
            raise EntityNotFoundError(entity_id)
        return entity.to_dict()


# ── Module-level convenience functions ────────────────────────────────────

_default_normalizer = Normalizer()


def normalize(raw: str) -> str:
    """Normalize raw input to canonical HIL string (no registry)."""
    return _default_normalizer.normalize(raw)


def normalize_command(raw: str) -> dict:
    """Normalize and return legacy envelope dict (no registry)."""
    return _default_normalizer.normalize_command(raw)
