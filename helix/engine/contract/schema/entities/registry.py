"""
Entity Registry — Helix SPEC-02
================================
Manages the unified Helix entity store.

Storage: atlas/entities/registry.json
Uniqueness: enforced by add() via upsert (last write wins for same id).
Validation: delegates to Entity.validate() before storing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.engine.kernel.schema.entities.schema import Entity

_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "codex" / "atlas" / "entities" / "registry.json"
)


class EntityRegistry:
    """
    In-memory entity store backed by atlas/entities/registry.json.

    Uniqueness is enforced per entity id — add() behaves as upsert:
    a later add() for the same id overwrites the prior entry.

    Schema validation is delegated to Entity.validate().
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add(self, entity: Entity) -> None:
        """Validate and upsert an entity. Enforces uniqueness by id."""
        entity.validate()
        self._entities[entity.id] = entity

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def remove(self, entity_id: str) -> bool:
        if entity_id in self._entities:
            del self._entities[entity_id]
            return True
        return False

    def list_by_type(self, type_str: str) -> list[Entity]:
        return [e for e in self._entities.values() if e.type == type_str]

    def all(self) -> list[Entity]:
        return list(self._entities.values())

    def __len__(self) -> int:
        return len(self._entities)

    def __contains__(self, entity_id: str) -> bool:
        return entity_id in self._entities

    # ── Relationships ─────────────────────────────────────────────────────────

    def link(
        self,
        source_id: str,
        relation: str,
        target_id: str,
        confidence: float = 1.0,
        **extra: Any,
    ) -> None:
        """
        Append a relationship to the source entity.
        Skips silently if source_id is not in the registry.
        Does not require target_id to be in the registry (cross-substrate links allowed).
        """
        entity = self._entities.get(source_id)
        if entity is None:
            return
        rel: dict[str, Any] = {
            "relation":  relation,
            "target_id": target_id,
            "confidence": confidence,
        }
        rel.update(extra)
        # Deduplicate: skip if identical relation+target already exists
        for existing in entity.relationships:
            if existing.get("relation") == relation and existing.get("target_id") == target_id:
                return
        entity.relationships.append(rel)

    # ── Persistence ───────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self._entities.values()],
            "_meta": {
                "entity_count": len(self._entities),
            },
        }

    def save(self, path: Path = _DEFAULT_REGISTRY_PATH) -> None:
        from core.validation import enforce_persistence
        enforce_persistence(self.to_dict(), path, is_atlas=True)

    @classmethod
    def load(cls, path: Path = _DEFAULT_REGISTRY_PATH) -> "EntityRegistry":
        reg = cls()
        if not path.exists():
            return reg
        data = json.loads(path.read_text())
        for ed in data.get("entities", []):
            try:
                entity = Entity.from_dict(ed)
                # Skip validate() on load to allow forward-compatible files
                reg._entities[entity.id] = entity
            except Exception:
                pass  # skip malformed entries
        return reg

    def summary(self) -> str:
        type_counts: dict[str, int] = {}
        for e in self._entities.values():
            type_counts[e.type] = type_counts.get(e.type, 0) + 1
        parts = ", ".join(f"{v} {k}" for k, v in sorted(type_counts.items()))
        return f"EntityRegistry: {len(self._entities)} entities — {parts or 'empty'}"
