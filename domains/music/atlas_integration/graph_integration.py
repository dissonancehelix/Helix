"""
Stage 9 — Knowledge graph integration
========================================
Populates the Helix entity registry and entity graph from music DB data,
then writes individual entity files to the atlas.

Output:
  codex/atlas/entities/registry.json             — full entity registry
  codex/atlas/entities/entity_graph.json         — entity relationship graph
  codex/atlas/entities/music/track/{slug}.json   — per-track entity files
  codex/atlas/entities/music/composer/{slug}.json
  codex/atlas/entities/music/game/{slug}.json
  codex/atlas/entities/music/platform/{slug}.json
  codex/atlas/entities/music/sound_chip/{slug}.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domains.music.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Stage 9: entity registry + graph population + atlas file writing."""
    from core.kernel.schema.entities import EntityRegistry
    from core.kernel.graph.storage.entity_graph import EntityGraph, build_from_registry
    from domains.music.kg.entity_builder import build_entities
    from domains.music.kg.library_index import build_library_index

    db = pipeline._ensure_db()
    if db is None:
        print("    DB unavailable — skipping knowledge graph integration")
        return

    registry = EntityRegistry.load()
    print(f"    Loaded registry: {registry.summary()}")

    try:
        all_tracks = db.get_tracks_by_tier(max_tier=1)
    except Exception as exc:
        print(f"    Could not load tracks: {exc}")
        return

    # Apply soundtrack filter
    if pipeline.soundtrack_filter:
        sf = pipeline.soundtrack_filter.lower()
        tracks = [
            t for t in all_tracks
            if sf in (t.get("album") or "").lower()
            or sf in (t.get("file_path") or "").lower()
        ]
        print(f"    Filtered to {len(tracks)} tracks for {pipeline.soundtrack_filter!r}")
    else:
        tracks = all_tracks

    provenance = {
        "source":            "music_substrate_pipeline",
        "source_stage":      "knowledge_graph_integration",
        "source_artifact":   "track_db",
        "extraction_method": "library_scan",
    }

    registry, batch_ids = build_entities(tracks, registry, provenance)

    if not pipeline.dry_run:
        registry.save()
        print("    Saved registry → codex/atlas/entities/registry.json")

        # Build sub-graph from current batch only (avoids serialising full library)
        batch_reg = EntityRegistry()
        for eid in batch_ids:
            e = registry.get(eid)
            if e:
                batch_reg.add(e)
        graph = build_from_registry(batch_reg)
        graph.save()
        print(f"    Saved entity graph → codex/atlas/entities/entity_graph.json")
        print(f"    {graph.summary()}")

        # Write individual entity files
        _write_entity_files(batch_reg, pipeline.run_ctx)

        # Build and write library index
        index_path = build_library_index(db, registry)
        if index_path:
            print(f"    Library index → {index_path}")


def _write_entity_files(registry: Any, run_ctx: Any) -> None:
    """
    Write one JSON file per entity under codex/atlas/entities/{ns}/{type}/{slug}.json.

    Entity ID format: music.track:angel_island_zone_act_1
    → codex/atlas/entities/music/track/angel_island_zone_act_1.json
    """
    if run_ctx is None:
        # Fallback: use default atlas root
        atlas_root = Path(__file__).parent.parent.parent.parent / "atlas"
    else:
        atlas_root = run_ctx.atlas

    written = 0
    for entity in registry.all():
        try:
            eid = entity.id                          # e.g. "music.track:angel_island_zone"
            colon = eid.index(":")
            prefix = eid[:colon]                     # "music.track"
            slug   = eid[colon + 1:]                 # "angel_island_zone"
            parts  = prefix.split(".")               # ["music", "track"]
            out    = atlas_root / "entities" / Path(*parts) / f"{slug}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(entity.to_dict(), indent=2, ensure_ascii=False))
            written += 1
        except Exception:
            pass

    print(f"    Written {written} individual entity files to codex/atlas/entities/")
