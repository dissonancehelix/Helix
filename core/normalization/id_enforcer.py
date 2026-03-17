"""
Normalization — ID Enforcer
============================
Validates and canonicalizes entity IDs.

Canonical ID format:  namespace.type:slug
Pattern:              ^[a-z_]+\\.[a-z_]+:[a-z0-9_]+$
Examples:
  music.composer:jun_senoue    ✓
  music.track:8aa0534f         ✓
  Music.Composer:Jun_Senoue    ✗  (uppercase not allowed)
  jun_senoue                   ✗  (missing namespace and type)
"""
from __future__ import annotations

import re

from core.normalization.errors import InvalidIDError

# Canonical ID pattern
_ID_RE = re.compile(r"^[a-z_]+\.[a-z_]+:[a-z0-9_]+$")

# Substrates recognized in canonical IDs
KNOWN_SUBSTRATES: frozenset[str] = frozenset({
    "music", "games", "language", "mathematics", "agents", "system",
})


def enforce_id(raw_id: str) -> str:
    """
    Validate that raw_id matches the canonical ID pattern.

    Returns the id unchanged if valid.
    Raises InvalidIDError if the id is malformed.

    Does NOT attempt to fix the id — callers must supply a valid id.
    """
    if not raw_id or not isinstance(raw_id, str):
        raise InvalidIDError("Entity ID must be a non-empty string", raw=str(raw_id))

    if not _ID_RE.match(raw_id):
        raise InvalidIDError(
            f"Entity ID {raw_id!r} does not match canonical format "
            f"'namespace.type:slug' (lowercase letters/underscores/digits only, "
            f"e.g. 'music.composer:jun_senoue')",
            raw=raw_id,
        )

    namespace = raw_id.split(".")[0]
    if namespace not in KNOWN_SUBSTRATES:
        # Warn but don't block — new substrates may be registered
        pass  # Future: emit warning via logger

    return raw_id


def is_valid_id(raw_id: str) -> bool:
    """Return True if raw_id is a valid canonical entity ID."""
    try:
        enforce_id(raw_id)
        return True
    except InvalidIDError:
        return False


def id_namespace(entity_id: str) -> str:
    """Extract the namespace from a canonical entity ID."""
    return entity_id.split(".")[0] if "." in entity_id else ""


def id_type_slug(entity_id: str) -> str:
    """Extract the type slug from a canonical entity ID (e.g. 'composer')."""
    prefix = entity_id.split(":")[0]   # "music.composer"
    return prefix.split(".")[-1] if "." in prefix else ""


def id_slug(entity_id: str) -> str:
    """Extract the entity slug from a canonical entity ID."""
    return entity_id.split(":", 1)[-1] if ":" in entity_id else ""
