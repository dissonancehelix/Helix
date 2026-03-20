"""
Music Substrate Pipeline — Helix SPEC-04
=========================================
Canonical 10-stage pipeline for the Helix Music Substrate.

This is the authoritative entrypoint for all music substrate processing.

ARCHITECTURE:
  /domains/music          — canonical Helix music substrate (SPEC-04)
  /domains/music/ingest/  — stages 1–2  (library scan, metadata normalisation)
  /domains/music/analysis/— stages 3–6  (chip, symbolic, MIR, musicology)
  /domains/music/models/  — stages 7–8  (feature fusion, style embedding)
  /domains/music/kg/      — stage  9    (knowledge graph integration)
  /labs/music_lab/           — legacy implementation delegated to for stages 1–2, 5, 7–8

Pipeline stages (SPEC-04 canonical order):
  1  library_ingestion              — scan library, ingest track metadata
  2  metadata_normalization         — chip register parse + APEv2 sidecar merge
  3  synthesis_architecture         — chip feature extraction + YM2612 synthesis profiles
  4  symbolic_music_extraction      — note reconstruction from register streams
  5  mir_audio_analysis             — MIR features (librosa or chip-proxy)
  6  musicology_analysis            — key, tempo, motif, harmonic analysis
  7  feature_synthesis              — 64-dim feature vector + FAISS + composer profiles
  8  style_space_embedding          — UMAP/PCA style space projection
  9  knowledge_graph_integration    — entity registry + graph + atlas entity files
  10 llm_interpretation             — LLM-assisted structural interpretation

Artifacts written to: artifacts/music/{run_id}/stage{N:02d}_{name}/
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domains.music.run_context import RunContext

# ── Stage metadata ────────────────────────────────────────────────────────────

STAGE_NAMES: dict[int, str] = {
    1:  "library_ingestion",
    2:  "metadata_normalization",
    3:  "synthesis_architecture",
    4:  "symbolic_music_extraction",
    5:  "mir_audio_analysis",
    6:  "musicology_analysis",
    7:  "feature_synthesis",
    8:  "style_space_embedding",
    9:  "knowledge_graph_integration",
    10: "llm_interpretation",
}


class MusicSubstratePipeline:
    """
    Canonical Helix Music Substrate pipeline (SPEC-04).

    Stages 3, 4, 6, 9 are implemented directly via the modular
    domains/music/ components.  All other stages delegate to
    domains.music.master_pipeline.MasterPipeline.

    Args:
        stages:            stage numbers to run (default: all 1–10)
        limit:             max tracks to process (0 = all)
        dry_run:           log only — no writes
        resume_from:       skip stages before this number
        workers:           parallel workers for legacy pipeline
        format_filter:     only process files with this extension
        track_filter:      filter by track name substring
        soundtrack_filter: filter by soundtrack/album name
        run_id:            explicit run ID (default: auto-generated timestamp)
    """

    def __init__(
        self,
        stages:            list[int] | None = None,
        limit:             int              = 0,
        dry_run:           bool             = False,
        resume_from:       int              = 1,
        workers:           int              = 4,
        format_filter:     str | None       = None,
        track_filter:      str | None       = None,
        soundtrack_filter: str | None       = None,
        run_id:            str | None       = None,
    ) -> None:
        self.stages            = stages or list(range(1, 11))
        self.limit             = limit
        self.dry_run           = dry_run
        self.resume_from       = resume_from
        self.workers           = workers
        self.format_filter     = format_filter
        self.track_filter      = track_filter
        self.soundtrack_filter = soundtrack_filter

        self.run_ctx: RunContext | None = None if dry_run else RunContext(run_id)

        self._legacy: Any = None   # MasterPipeline, lazily initialised

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> dict:
        ts_start = time.time()
        rid = self.run_ctx.run_id if self.run_ctx else "dry-run"
        print(f"\n{'='*62}")
        print(f"  Helix Music Substrate — SPEC-04 Pipeline")
        print(f"  {datetime.now(timezone.utc).isoformat()}")
        print(f"  Run ID : {rid}")
        print(f"  Stages : {self.stages}   Limit: {self.limit or 'all'}")
        print(f"  Dry-run: {self.dry_run}")
        print(f"{'='*62}\n")

        active = [s for s in self.stages if s >= self.resume_from]
        results: dict[int, str] = {}

        for stage_num in active:
            name = STAGE_NAMES.get(stage_num, f"stage_{stage_num}")
            print(f"  [stage {stage_num:02d}/{name}] Starting …")
            t0 = time.time()
            try:
                self._run_stage(stage_num)
                results[stage_num] = "ok"
            except Exception as exc:
                import traceback
                print(f"  [stage {stage_num:02d}/{name}] ERROR: {exc}")
                traceback.print_exc()
                results[stage_num] = f"error: {exc}"
            elapsed = time.time() - t0
            print(f"  [stage {stage_num:02d}/{name}] Done in {elapsed:.1f}s\n")

        total = time.time() - ts_start
        print(f"{'='*62}")
        print(f"  Pipeline complete in {total:.1f}s")
        if self.run_ctx:
            print(f"  Artifacts → artifacts/music/{self.run_ctx.run_id}/")
        print(f"{'='*62}\n")
        return {"run_id": rid, "stages": results, "elapsed": total}

    # ── Stage dispatcher ──────────────────────────────────────────────────────

    def _run_stage(self, stage_num: int) -> None:
        if stage_num == 1:
            from domains.music.ingest.library_scanner     import run
            run(self); return
        if stage_num == 2:
            from domains.music.ingest.metadata_normalizer import run
            run(self); return
        if stage_num == 3:
            from domains.music.analysis.chip import run
            run(self); return
        if stage_num == 4:
            from domains.music.analysis.symbolic import run
            run(self); return
        if stage_num == 5:
            from domains.music.analysis.mir import run
            run(self); return
        if stage_num == 6:
            from domains.music.analysis.musicology import run
            run(self); return
        if stage_num == 7:
            from domains.music.models.feature_fusion import run
            run(self); return
        if stage_num == 8:
            from domains.music.models.style_embedding import run
            run(self); return
        if stage_num == 9:
            from domains.music.kg.graph_integration import run
            run(self); return
        if stage_num == 10:
            self._stage_llm_interpretation(); return

        print(f"    No implementation for stage {stage_num} — skipping")

    # ── Legacy delegation ─────────────────────────────────────────────────────

    def _get_legacy(self) -> Any:
        if self._legacy is None:
            from domains.music.master_pipeline import MasterPipeline
            self._legacy = MasterPipeline(
                stages=list(range(1, 19)),
                limit=self.limit,
                dry_run=self.dry_run,
                resume_from=1,
                workers=self.workers,
                format_filter=self.format_filter,
                track_filter=self.track_filter,
                soundtrack_filter=self.soundtrack_filter,
            )
        return self._legacy

    def _delegate_to_legacy(self, legacy_stage_nums: list[int]) -> None:
        from domains.music.master_pipeline import STAGE_NAME as _LEGACY_STAGE_NAME
        mp = self._get_legacy()
        if mp._db is None and any(s > 1 for s in legacy_stage_nums):
            try:
                from domains.music.db.track_db import TrackDB
                from domains.music.config import DB_PATH
                mp._db = TrackDB(DB_PATH)
            except Exception as exc:
                print(f"    Warning: could not init legacy DB: {exc}")
        for sn in legacy_stage_nums:
            name    = _LEGACY_STAGE_NAME.get(sn, f"stage_{sn}")
            handler = getattr(mp, f"_stage_{name}", None)
            if handler is None:
                print(f"    [legacy {sn}/{name}] No handler — skipping")
                continue
            print(f"    → legacy stage {sn} ({name})")
            handler()

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _ensure_db(self) -> Any:
        """Return an initialised TrackDB, or None if unavailable."""
        mp = self._get_legacy()
        if mp._db is None:
            try:
                from domains.music.db.track_db import TrackDB
                from domains.music.config import DB_PATH
                mp._db = TrackDB(DB_PATH)
            except Exception:
                return None
        return mp._db

    def _get_vgm_paths_from_db(self) -> list[Path]:
        """Return VGM/VGZ paths from DB, filtered by soundtrack if set."""
        db = self._ensure_db()
        if db is None:
            return []
        tracks = db.get_tracks_by_tier(max_tier=1)
        paths  = []
        for t in tracks:
            fp = t.get("file_path", "")
            if not fp:
                continue
            p = Path(fp)
            if p.suffix.lower() not in {".vgm", ".vgz", ".gym"}:
                continue
            if self.soundtrack_filter and self.soundtrack_filter.lower() not in str(p).lower():
                continue
            paths.append(p)
        return paths

    # ── Stage 10: LLM interpretation ──────────────────────────────────────────

    def _stage_llm_interpretation(self) -> None:
        try:
            from domains.music.analysis import llm_interpreter
        except ImportError as exc:
            print(f"    LLM interpreter unavailable: {exc}")
            return

        db = self._ensure_db()
        if db is None:
            print("    DB not available — skipping LLM interpretation")
            return

        try:
            tracks = db.get_tracks_by_tier(max_tier=1)
            if not tracks:
                print("    No tracks — skipping LLM interpretation")
                return
            sample = tracks[:10]
            for t in sample:
                try:
                    llm_interpreter.interpret(t)
                except Exception:
                    pass
            print(f"    LLM interpretation: {len(sample)} tracks sampled")
        except Exception as exc:
            print(f"    LLM interpretation error: {exc}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Helix Music Substrate — SPEC-04 pipeline")
    p.add_argument("--stages",      default="", help="Comma-separated stage numbers")
    p.add_argument("--limit",       type=int,   default=0)
    p.add_argument("--dry-run",     action="store_true")
    p.add_argument("--resume-from", type=int,   default=1)
    p.add_argument("--workers",     type=int,   default=4)
    p.add_argument("--format",      default=None)
    p.add_argument("--soundtrack",  default=None)
    p.add_argument("--run-id",      default=None)
    args = p.parse_args()

    stages = [int(s.strip()) for s in args.stages.split(",") if s.strip()] if args.stages else None

    MusicSubstratePipeline(
        stages=stages,
        limit=args.limit,
        dry_run=args.dry_run,
        resume_from=args.resume_from,
        workers=args.workers,
        format_filter=args.format,
        soundtrack_filter=args.soundtrack,
        run_id=args.run_id,
    ).run()


if __name__ == "__main__":
    main()
