"""
Stage 3 — Synthesis architecture analysis
==========================================
Extracts chip-level features and synthesis profiles from VGM/VGZ files.

For YM2612 files this includes FM algorithm, operator ADSR envelopes,
instrument patches, channel allocation, DAC usage, and LFO state.

Uses synthesis_profiler.py for deep YM2612 operator extraction.
Stores results in the DB via upsert_chip_features() and writes a
synthesis_profiles artifact per track.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domains.music.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> int:
    """
    Stage 3: extract chip features and YM2612 synthesis profiles.

    Returns the number of tracks successfully processed.
    Falls back to legacy stage delegation if direct extraction yields 0.
    """
    db = pipeline._ensure_db()
    if db is None:
        print("    DB unavailable — falling back to legacy chip extraction")
        pipeline._delegate_to_legacy([4, 5])
        return 0

    vgm_paths = pipeline._get_vgm_paths_from_db()
    if not vgm_paths:
        print("    No VGM/VGZ files in DB — falling back to legacy chip extraction")
        pipeline._delegate_to_legacy([4, 5])
        return 0

    try:
        from domains.music.vgm_parser import parse_vgm_file
        from domains.music.feature_extractor import extract as _extract
        from domains.music.ingestion.config import TIER_A_STATIC
        from domains.music.analysis.synthesis_profiler import profile_vgm_track
    except ImportError as exc:
        print(f"    Chip analysis imports unavailable: {exc}")
        pipeline._delegate_to_legacy([4, 5])
        return 0

    # Artifact directory for synthesis profiles
    synth_dir: Path | None = None
    if pipeline.run_ctx and not pipeline.dry_run:
        synth_dir = pipeline.run_ctx.stage_dir(3, "synthesis_architecture")

    extracted = 0
    for path in vgm_paths:
        try:
            track    = parse_vgm_file(path)
            features = _extract(track)
            tid      = hashlib.sha1(str(path).encode()).hexdigest()

            # Standard chip features → DB
            if not pipeline.dry_run:
                db.upsert_chip_features(
                    tid, features.__dict__,
                    tier=TIER_A_STATIC, confidence=0.6,
                    provenance="chip_analysis:direct",
                )

            # YM2612 synthesis profile → artifact JSON
            if track.header.has_ym2612 and synth_dir is not None:
                profile = profile_vgm_track(track)
                _write_synthesis_profile(synth_dir, path.stem, tid, profile)

            extracted += 1
        except Exception:
            pass

    print(f"    Chip features: {extracted}/{len(vgm_paths)} tracks")
    return extracted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_synthesis_profile(out_dir: Path, stem: str, tid: str, profile: Any) -> None:
    """Write a per-track synthesis profile JSON to the artifact directory."""
    payload = {
        "track_id":   tid,
        "stem":       stem,
        "synthesis":  profile.to_dict(),
    }
    (out_dir / f"{stem}_synthesis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False)
    )
