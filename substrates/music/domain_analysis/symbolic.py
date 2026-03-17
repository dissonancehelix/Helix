"""
Stage 4 — Symbolic music extraction
=====================================
Reconstructs note events from chip register streams (VGM/VGZ).

Produces a SymbolicScore per track containing note onset/offset times,
pitch values, channel assignments, and basic velocity proxies derived
from YM2612 total-level writes.

Scores are saved as JSON to the stage artifact directory and to the
legacy labs/music_lab/artifacts/symbolic_scores/ for compatibility.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from substrates.music.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Stage 4: reconstruct note events from VGM register streams."""
    db = pipeline._ensure_db()
    if db is None:
        print("    DB unavailable — skipping symbolic reconstruction")
        return

    vgm_paths = pipeline._get_vgm_paths_from_db()
    if not vgm_paths:
        print("    No VGM/VGZ files for symbolic reconstruction")
        return

    try:
        from substrates.music.vgm_parser import parse_vgm_file
        from substrates.music.analysis.symbolic_music.vgm_note_reconstructor import reconstruct
        from substrates.music.ingestion.config import ARTIFACTS, VGM_ROOT, LIBRARY_ROOT
    except ImportError as exc:
        print(f"    Symbolic reconstruction unavailable: {exc}")
        return

    # Legacy output dir (for theory stage compatibility)
    legacy_dir = ARTIFACTS / "symbolic_scores"
    if not pipeline.dry_run:
        legacy_dir.mkdir(parents=True, exist_ok=True)

    # Stage artifact dir
    stage_dir: Path | None = None
    if pipeline.run_ctx and not pipeline.dry_run:
        stage_dir = pipeline.run_ctx.stage_dir(4, "symbolic_extraction")

    done = 0
    for path in vgm_paths:
        try:
            track = parse_vgm_file(path)
            score = reconstruct(track)

            # Resolve relative source path
            for root in (VGM_ROOT, LIBRARY_ROOT):
                try:
                    score.metadata["source"] = str(path.relative_to(root))
                    break
                except ValueError:
                    pass
            else:
                score.metadata["source"] = path.name

            if not pipeline.dry_run:
                score.save(legacy_dir / f"{path.stem}.json")
                if stage_dir is not None:
                    score.save(stage_dir / f"{path.stem}.json")
            done += 1
        except Exception:
            pass

    print(f"    Symbolic reconstruction: {done}/{len(vgm_paths)} tracks")
