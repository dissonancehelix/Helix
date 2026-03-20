"""
RunContext — run_id and artifact path management for the music substrate.
==========================================================================
Each pipeline invocation gets a unique run_id. Artifacts are written to:
  artifacts/music/{run_id}/stage{N:02d}_{name}/

This ensures every run is independently reproducible and non-destructive.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ARTIFACTS_ROOT = Path(__file__).parent.parent.parent / "artifacts" / "music"
_ATLAS_ROOT     = Path(__file__).parent.parent.parent / "atlas"


class RunContext:
    """Owns all path resolution for a single pipeline invocation."""

    def __init__(self, run_id: str | None = None) -> None:
        if run_id is None:
            ts  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            uid = uuid.uuid4().hex[:6]
            run_id = f"{ts}_{uid}"
        self.run_id = run_id
        self.root   = _ARTIFACTS_ROOT / run_id
        self.atlas  = _ATLAS_ROOT

    # ── Artifact paths ────────────────────────────────────────────────────────

    def stage_dir(self, stage_num: int, stage_name: str, *, create: bool = True) -> Path:
        """Return (and optionally create) the directory for a pipeline stage."""
        d = self.root / f"stage{stage_num:02d}_{stage_name}"
        if create:
            d.mkdir(parents=True, exist_ok=True)
        return d

    def write_json(
        self,
        stage_num: int,
        stage_name: str,
        filename: str,
        data: dict | list,
    ) -> Path:
        """Serialise *data* as JSON into the stage artifact directory."""
        path = self.stage_dir(stage_num, stage_name) / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    # ── Atlas paths ───────────────────────────────────────────────────────────

    def entity_file(self, entity_id: str) -> Path:
        """
        Return the path for an individual entity file.

        codex/atlas/entities/{namespace}/{type}/{slug}.json

        e.g. music.track:angel_island_zone_act_1
          →  codex/atlas/entities/music/track/angel_island_zone_act_1.json
        """
        # entity_id format: [namespace.]type:slug
        parts = entity_id.split(":", 1)
        if len(parts) != 2:
            return self.atlas / "entities" / "unknown" / f"{entity_id}.json"
        prefix, slug = parts
        segments = prefix.split(".")   # e.g. ["music", "track"]
        return self.atlas / "entities" / Path(*segments) / f"{slug}.json"

    def library_index_path(self) -> Path:
        """codex/atlas/music/library_index.json"""
        return self.atlas / "music" / "library_index.json"
