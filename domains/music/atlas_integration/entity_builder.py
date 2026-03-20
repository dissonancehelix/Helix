"""
Entity builder — music substrate
==================================
Creates Entity objects for tracks, composers, games, platforms,
and sound chips from DB track records.

Returns the updated EntityRegistry and the set of entity IDs
added in this batch (used for sub-graph construction).
"""
from __future__ import annotations

import re as _re
from typing import Any

_NON_ALNUM = _re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    return _NON_ALNUM.sub("_", text.lower().strip()).strip("_") or "unknown"


def build_entities(
    tracks: list[dict],
    registry: Any,               # EntityRegistry
    provenance: dict,
) -> tuple[Any, set[str]]:
    """
    Upsert Entity objects for every track record in *tracks*.

    Args:
        tracks:     list of track dicts from TrackDB.get_tracks_by_tier()
        registry:   EntityRegistry to add entities into
        provenance: dict of provenance metadata fields

    Returns:
        (registry, batch_entity_ids)  — updated registry + IDs added this run
    """
    from core.kernel.schema.entities import Entity

    batch_entity_ids: set[str] = set()

    composers_new: set[str] = set()
    games_new:     set[str] = set()
    platforms_new: set[str] = set()
    chips_new:     set[str] = set()

    for t in tracks:
        track_id   = t.get("id") or t.get("track_id", "")
        title      = t.get("title") or t.get("file_name") or track_id
        artist     = t.get("artist", "")
        album      = t.get("album", "")
        platform   = t.get("platform", "")
        sound_chip = t.get("sound_chip", "")

        if not track_id or not title:
            continue

        # ── Track ──────────────────────────────────────────────────────────
        track_eid = f"music.track:{_slugify(title)}"
        registry.add(Entity(
            id=track_eid,
            type="Track",
            name=title,
            metadata={**provenance, "source_artifact": str(t.get("file_path", ""))},
            external_ids={},
            relationships=[],
        ))
        batch_entity_ids.add(track_eid)

        # ── Composer ───────────────────────────────────────────────────────
        if artist:
            comp_eid = f"music.composer:{_slugify(artist)}"
            if comp_eid not in registry:
                registry.add(Entity(
                    id=comp_eid, type="Composer", name=artist,
                    metadata=provenance, external_ids={}, relationships=[],
                ))
                composers_new.add(comp_eid)
            batch_entity_ids.add(comp_eid)
            registry.link(comp_eid, "COMPOSED", track_eid, confidence=1.0)

        # ── Game ───────────────────────────────────────────────────────────
        if album:
            game_eid = f"music.game:{_slugify(album)}"
            if game_eid not in registry:
                registry.add(Entity(
                    id=game_eid, type="Game", name=album,
                    metadata=provenance, external_ids={}, relationships=[],
                ))
                games_new.add(game_eid)
            batch_entity_ids.add(game_eid)
            registry.link(track_eid, "APPEARS_IN", game_eid, confidence=1.0)

            # ── Platform ───────────────────────────────────────────────────
            if platform:
                plat_eid = f"music.platform:{_slugify(platform)}"
                if plat_eid not in registry:
                    registry.add(Entity(
                        id=plat_eid, type="Platform", name=platform,
                        metadata=provenance, external_ids={}, relationships=[],
                    ))
                    platforms_new.add(plat_eid)
                batch_entity_ids.add(plat_eid)
                registry.link(game_eid, "RUNS_ON", plat_eid, confidence=1.0)

            # ── Sound chips (APEv2 multi-value via \x00) ───────────────────
            if sound_chip:
                import re as _re2
                for chip_name in [c for c in _re2.split(r'[\x00\s]+', sound_chip) if c]:
                    chip_eid = f"music.sound_chip:{_slugify(chip_name)}"
                    if chip_eid not in registry:
                        registry.add(Entity(
                            id=chip_eid, type="SoundChip", name=chip_name,
                            metadata=provenance, external_ids={}, relationships=[],
                        ))
                        chips_new.add(chip_eid)
                    batch_entity_ids.add(chip_eid)
                    registry.link(game_eid, "USES_CHIP", chip_eid, confidence=1.0)

    print(
        f"    Entities: {len(registry)} total "
        f"({len(composers_new)} new composers, {len(games_new)} new games, "
        f"{len(platforms_new)} new platforms, {len(chips_new)} new chips)"
    )
    return registry, batch_entity_ids
