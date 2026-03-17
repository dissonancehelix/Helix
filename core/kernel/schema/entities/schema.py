"""
Entity Schema — Helix SPEC-02
==============================
Defines the canonical Entity dataclass for the Helix entity system.

All entities must:
  - have a globally unique id in format "namespace.type:slug"
  - declare a type that exists in ENTITY_ONTOLOGY
  - include name, label, description, metadata, external_ids, relationships

Canonical ID format:
  namespace.type:slug   e.g. "music.composer:jun_senoue"

  namespace — Helix substrate (music, games, math, language)
  type      — entity type slug from ENTITY_ONTOLOGY (lowercase)
  slug      — unique identifier within type (lowercase, underscores/digits)

Fields:
  id            — canonical ID (required)
  type          — entity type from ENTITY_ONTOLOGY (required)
  name          — human-readable display name (required)
  label         — short display label; defaults to name on load (required)
  description   — one-sentence description (required for new entities)
  metadata      — domain-specific extras; pipeline entities include provenance keys
  external_ids  — references to external knowledge bases
  relationships — list of {relation, target_id, confidence} dicts

Provenance keys required for pipeline-generated entities:
  source, source_stage, source_artifact, extraction_method
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import Any

from core.kernel.schema.entities.ontology import (
    ENTITY_ONTOLOGY,
    is_core_entity_type,
    is_reserved_entity_type,
    is_known_entity_type,
)

# Canonical format: namespace.type:slug  e.g. "music.composer:jun_senoue"
_ID_RE = re.compile(r"^[a-z_]+\.[a-z_]+:[a-z0-9_]+$")

# Provenance keys required for pipeline-generated entities
PROVENANCE_KEYS = ("source", "source_stage", "source_artifact", "extraction_method")


@dataclass
class Entity:
    """
    A Helix entity — a real-world or conceptual object referenced across substrates.

    Fields (SPEC-02 + Semantics Layer):
      id            globally unique, format "namespace.type:slug"
      type          entity type from ENTITY_ONTOLOGY
      name          human-readable display name
      label         short display label (defaults to name if absent on load)
      description   one-sentence description (required for new entities)
      metadata      domain-specific extras; pipeline entities include provenance keys
      external_ids  references to external knowledge bases
      relationships list of {relation, target_id, confidence} dicts
    """

    id:            str
    type:          str
    name:          str
    label:         str                      = field(default="")
    description:   str                     = field(default="")
    metadata:      dict[str, Any]          = field(default_factory=dict)
    external_ids:  dict[str, str]          = field(default_factory=dict)
    relationships: list[dict[str, Any]]    = field(default_factory=list)

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def namespace(self) -> str:
        """Return the substrate namespace from the id, e.g. 'music'."""
        part = self.id.split(":")[0]           # "music.composer"
        return part.split(".")[0] if "." in part else ""

    @property
    def type_slug(self) -> str:
        """Return the type portion of the id prefix, e.g. 'composer'."""
        part = self.id.split(":")[0]           # "music.composer"
        return part.split(".")[-1]             # "composer"

    @property
    def slug(self) -> str:
        """Return the entity slug, e.g. 'jun_senoue'."""
        return self.id.split(":", 1)[-1] if ":" in self.id else ""

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> None:
        """
        Validate schema correctness. Raises ValueError on hard errors.
        Emits warnings for reserved-type usage.

        Runs both structural checks (id format, type ontology) and
        semantic validation via SemanticValidator.

        Does NOT enforce registry uniqueness — that is EntityRegistry.add()'s job.
        """
        # Required structural fields
        if not self.id:
            raise ValueError("Entity.id must not be empty")
        if not self.type:
            raise ValueError("Entity.type must not be empty")
        if not self.name:
            raise ValueError("Entity.name must not be empty")

        # id format: "namespace.type:slug"
        if not _ID_RE.match(self.id):
            raise ValueError(
                f"Entity.id {self.id!r} does not match required format 'namespace.type:slug' "
                f"(lowercase letters/underscores only, e.g. 'music.composer:jun_senoue')"
            )

        # type portion of id must match declared type (lowercased, normalised)
        id_type_part = self.type_slug                            # "sound_chip"
        declared_type_slug = self.type.lower().replace(" ", "_")  # "soundchip"
        if id_type_part.replace("_", "") != declared_type_slug.replace("_", ""):
            raise ValueError(
                f"Entity.id type segment {id_type_part!r} does not match "
                f"declared type {self.type!r} (expected {declared_type_slug!r})"
            )

        # Type ontology check
        if is_reserved_entity_type(self.type):
            warnings.warn(
                f"Entity type {self.type!r} is in ENTITY_RESERVED_TYPES — "
                f"not yet required by active substrates",
                UserWarning,
                stacklevel=2,
            )
        elif not is_known_entity_type(self.type):
            raise ValueError(
                f"Entity type {self.type!r} is not in ENTITY_ONTOLOGY. "
                f"Known types: {sorted(ENTITY_ONTOLOGY)}"
            )

        # Relationship structure check
        for i, rel in enumerate(self.relationships):
            if not isinstance(rel, dict):
                raise ValueError(f"relationships[{i}] must be a dict")
            if "relation" not in rel or "target_id" not in rel:
                raise ValueError(
                    f"relationships[{i}] must contain 'relation' and 'target_id' keys"
                )

        # Semantic validation (label + description + field signatures)
        self._semantic_validate()

    def _semantic_validate(self) -> None:
        """
        Run SemanticValidator against this entity.
        Raises ValueError wrapping SemanticValidationError on failure.
        Emits warnings for semantic issues that don't block saving.
        """
        try:
            from core.semantics.validator import SemanticValidator
        except ImportError:
            return  # Semantics layer not yet available — skip gracefully

        result = SemanticValidator.validate(self)
        if result.warnings:
            for w in result.warnings:
                warnings.warn(f"Semantic warning for {self.id}: {w}", UserWarning, stacklevel=3)
        if not result.valid:
            raise ValueError(
                f"Semantic validation failed for entity {self.id!r}: "
                + "; ".join(result.errors)
            )

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "id":            self.id,
            "type":          self.type,
            "name":          self.name,
            "label":         self.label or self.name,
            "description":   self.description,
            "metadata":      self.metadata,
            "external_ids":  self.external_ids,
            "relationships": self.relationships,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Entity":
        name = d.get("name", "")
        return cls(
            id=d["id"],
            type=d["type"],
            name=name,
            # label defaults to name for backward compat with pre-label entities
            label=d.get("label", "") or name,
            # description flagged as missing in metadata if absent
            description=d.get("description", ""),
            metadata=d.get("metadata", {}),
            external_ids=d.get("external_ids", {}),
            relationships=d.get("relationships", []),
        )
