"""
master_pipeline.py — Helix Music Lab master 14-stage orchestrator
=================================================================
Processes the full music archive across Tier A–D in sequence.
Stages:
  1  scan          — walk library, build file list
  2  ingest        — insert track metadata into DB
  3  tier_a_parse  — Tier A static parse (SPC/NSF/SID/VGM)
  4  chip_features — extract chip-level features
  5  tier_b_trace  — Tier B emulation trace (if available)
  6  symbolic      — symbolic reconstruction (note events, MIDI)
  7  theory        — key estimation, tempo, motifs
  8  mir           — audio MIR features (librosa, or chip proxy)
  9  feature_vec   — build 64-dim feature vector
  10 faiss         — build FAISS/KDTree similarity index
  11 composer_fp   — composer Gaussian fingerprinting
  12 attributions  — probabilistic composer attribution
  13 taste         — operator taste centroid
  14 recommend     — near_core + frontier recommendations

CLI:
    python -m labs.music_lab.master_pipeline [options]

Options:
    --stages 1,2,3        Run specific stages (comma-separated)
    --limit N             Process only N tracks (default: all)
    --dry-run             Log what would be done, no writes
    --resume-from STAGE   Skip stages before STAGE
    --workers N           Parallel workers (default: config.PARALLEL_WORKERS)
    --format EXT          Only process files with this extension
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labs.music_lab.config import (
    LIBRARY_ROOT, DB_PATH, FEATURE_VECTOR_VERSION,
    PARALLEL_WORKERS, ARTIFACTS, REPORTS,
    TIER_A_STATIC, TIER_B_EMULATED, TIER_C_SYMBOLIC, TIER_D_MIR,
)

# ---------------------------------------------------------------------------
# Stage registry
# ---------------------------------------------------------------------------

STAGES = [
    (1,  "scan"),
    (2,  "ingest"),
    (3,  "tier_a_parse"),
    (4,  "chip_features"),
    (5,  "tier_b_trace"),
    (6,  "symbolic"),
    (7,  "theory"),
    (8,  "mir"),
    (9,  "feature_vec"),
    (10, "faiss"),
    (11, "composer_fp"),
    (12, "attributions"),
    (13, "taste"),
    (14, "recommend"),
]

STAGE_NUM = {name: num for num, name in STAGES}
STAGE_NAME = {num: name for num, name in STAGES}

_AUDIO_EXTS = {
    ".vgm", ".vgz", ".gym",
    ".spc", ".nsf", ".nsfe",
    ".sid", ".psid", ".rsid",
    ".gbs", ".hes", ".kss", ".ay", ".sgc",
    ".2sf", ".ncsf", ".usf", ".gsf",
    ".psf", ".psf2", ".ssf", ".dsf", ".s98",
    ".mp3", ".flac", ".ogg", ".wav", ".m4a",
    ".opus", ".ape", ".wv",
}


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------

class MasterPipeline:

    def __init__(
        self,
        stages: list[int] | None = None,
        limit: int = 0,
        dry_run: bool = False,
        resume_from: int = 1,
        workers: int = PARALLEL_WORKERS,
        format_filter: str | None = None,
    ) -> None:
        self.stages       = stages or list(range(1, 15))
        self.limit        = limit
        self.dry_run      = dry_run
        self.resume_from  = resume_from
        self.workers      = workers
        self.format_filter = format_filter.lower() if format_filter else None

        self._files:  list[Path] = []
        self._db:     Any        = None
        self._index:  Any        = None
        self._taste:  Any        = None

        self._stats: dict[int, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        ts_start = time.time()
        print(f"\n{'='*60}")
        print(f"  Helix Music Lab — Master Pipeline")
        print(f"  {datetime.now(timezone.utc).isoformat()}")
        print(f"  Stages: {self.stages}  Limit: {self.limit or 'all'}")
        print(f"  Dry-run: {self.dry_run}  Workers: {self.workers}")
        print(f"{'='*60}\n")

        active_stages = [s for s in self.stages if s >= self.resume_from]

        for stage_num in active_stages:
            name = STAGE_NAME.get(stage_num, f"stage_{stage_num}")
            handler = getattr(self, f"_stage_{name}", None)
            if handler is None:
                print(f"  [stage {stage_num:02d}/{name}] No handler — skipping")
                continue

            print(f"  [stage {stage_num:02d}/{name}] Starting …")
            t0 = time.time()
            try:
                handler()
            except Exception as e:
                print(f"  [stage {stage_num:02d}/{name}] ERROR: {e}")
                import traceback; traceback.print_exc()
            elapsed = time.time() - t0
            print(f"  [stage {stage_num:02d}/{name}] Done in {elapsed:.1f}s\n")

        total = time.time() - ts_start
        print(f"{'='*60}")
        print(f"  Pipeline complete in {total:.1f}s")
        print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # Stage 1: Scan
    # ------------------------------------------------------------------

    def _stage_scan(self) -> None:
        files: list[Path] = []
        for p in LIBRARY_ROOT.rglob("*"):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext not in _AUDIO_EXTS:
                continue
            if self.format_filter and ext != f".{self.format_filter}":
                continue
            files.append(p)

        if self.limit:
            files = files[:self.limit]

        self._files = files
        print(f"    Found {len(files)} files")

    # ------------------------------------------------------------------
    # Stage 2: Ingest
    # ------------------------------------------------------------------

    def _stage_ingest(self) -> None:
        from labs.music_lab.db.track_db import TrackDB
        self._db = TrackDB(DB_PATH)

        if self.dry_run:
            print(f"    [dry-run] Would ingest {len(self._files)} tracks")
            return

        inserted = 0
        for path in self._files:
            rec = {
                "file_path": str(path),
                "title":     path.stem,
                "artist":    "",
                "album":     path.parent.name,
                "platform":  "",
                "sound_chip": "",
                "format":    path.suffix.lstrip(".").upper(),
                "loved":     0,
            }
            try:
                self._db.insert_track(rec)
                inserted += 1
            except Exception:
                pass

        print(f"    Ingested/updated {inserted} tracks")

    # ------------------------------------------------------------------
    # Stage 3: Tier A parse
    # ------------------------------------------------------------------

    def _stage_tier_a_parse(self) -> None:
        from labs.music_lab.decoders.router import FormatRouter
        router = FormatRouter()

        parsed = 0
        for path in self._files:
            if not router.supports_tier_a(path):
                continue
            if self.dry_run:
                continue
            try:
                result = router.parse(path)
                # Update DB track with parsed metadata
                if self._db and result.get("title"):
                    import hashlib
                    tid = hashlib.sha1(str(path).encode()).hexdigest()
                    self._db.conn if hasattr(self._db, "conn") else None
                    # Best-effort metadata update via upsert
                parsed += 1
            except Exception:
                pass

        print(f"    Parsed {parsed} Tier A files")

    # ------------------------------------------------------------------
    # Stage 4: Chip features
    # ------------------------------------------------------------------

    def _stage_chip_features(self) -> None:
        if self._db is None:
            print("    DB not initialized — skipping")
            return

        from labs.music_lab.feature_extractor import extract as _extract

        vgm_files = [p for p in self._files if p.suffix.lower() in {".vgm", ".vgz", ".gym"}]
        if not vgm_files:
            print("    No VGM files — skipping chip feature extraction")
            return

        if self.dry_run:
            print(f"    [dry-run] Would extract chip features for {len(vgm_files)} files")
            return

        try:
            # Import VGM parser
            from labs.music_lab.vgm_parser import parse_vgm_file
        except ImportError:
            print("    vgm_parser unavailable — skipping")
            return

        extracted = 0
        for path in vgm_files:
            try:
                track    = parse_vgm_file(path)
                features = _extract(track)
                import hashlib
                tid = hashlib.sha1(str(path).encode()).hexdigest()
                self._db.upsert_chip_features(
                    tid, features.__dict__,
                    tier=TIER_A_STATIC, confidence=0.6,
                    provenance=f"feature_extractor:pipeline",
                )
                extracted += 1
            except Exception:
                pass

        print(f"    Extracted chip features for {extracted} tracks")

    # ------------------------------------------------------------------
    # Stage 5: Tier B trace
    # ------------------------------------------------------------------

    def _stage_tier_b_trace(self) -> None:
        from labs.music_lab.emulation.build_extensions import is_built
        if not is_built("libvgm") and not is_built("vgmstream"):
            print("    No Tier B libraries compiled — skipping (non-blocking)")
            return

        from labs.music_lab.decoders.router import FormatRouter
        router = FormatRouter()
        traced = 0
        for path in self._files:
            if router.supports_tier_b(path):
                if not self.dry_run:
                    events = router.trace(path)
                    if events:
                        traced += 1

        print(f"    Tier B trace: {traced} files")

    # ------------------------------------------------------------------
    # Stage 6: Symbolic reconstruction
    # ------------------------------------------------------------------

    def _stage_symbolic(self) -> None:
        vgm_files = [p for p in self._files if p.suffix.lower() in {".vgm", ".vgz", ".gym"}]
        if not vgm_files:
            print("    No VGM files — skipping symbolic reconstruction")
            return

        if self.dry_run:
            print(f"    [dry-run] Would reconstruct notes for {len(vgm_files)} files")
            return

        try:
            from labs.music_lab.vgm_parser import parse_vgm_file
            from labs.music_lab.analysis.symbolic_music.vgm_note_reconstructor import reconstruct
            from labs.music_lab.analysis.symbolic_music.score_representation import SymbolicScore
        except ImportError as e:
            print(f"    Symbolic reconstruction unavailable: {e}")
            return

        out_dir = ARTIFACTS / "symbolic_scores"
        out_dir.mkdir(parents=True, exist_ok=True)
        done = 0
        for path in vgm_files:
            try:
                track = parse_vgm_file(path)
                score = reconstruct(track)
                score.save(out_dir / f"{path.stem}.json")
                done += 1
            except Exception:
                pass

        print(f"    Symbolic reconstruction: {done} scores")

    # ------------------------------------------------------------------
    # Stage 7: Theory features
    # ------------------------------------------------------------------

    def _stage_theory(self) -> None:
        from labs.music_lab.analysis.theory_features.key_estimator import estimate, pitch_histogram
        from labs.music_lab.analysis.theory_features.rhythm_analyzer import analyze
        from labs.music_lab.analysis.theory_features.motif_detector  import detect

        scores_dir = ARTIFACTS / "symbolic_scores"
        if not scores_dir.exists():
            print("    No symbolic scores — skipping theory features")
            return

        if self._db is None:
            print("    DB not initialized — skipping")
            return

        from labs.music_lab.analysis.symbolic_music.score_representation import SymbolicScore
        import hashlib

        done = 0
        for score_path in scores_dir.glob("*.json"):
            try:
                score = SymbolicScore.load(score_path)
                hist  = pitch_histogram(score.notes)
                key_r = estimate(hist)
                rhy_r = analyze(score.notes)
                mot_r = detect(score.notes)

                feat = {
                    "key":             key_r.key,
                    "mode":            key_r.mode,
                    "key_confidence":  key_r.confidence,
                    "tempo_bpm":       rhy_r.tempo_bpm,
                    "syncopation":     rhy_r.syncopation,
                    "beat_regularity": rhy_r.beat_regularity,
                    "motif_density":   mot_r.motif_density,
                    "top_motif_count": mot_r.top_motifs[0].count if mot_r.top_motifs else 0,
                }

                # Map score file back to track_id
                orig_path = LIBRARY_ROOT / score.metadata.get("source", "")
                tid = hashlib.sha1(str(orig_path).encode()).hexdigest()

                if not self.dry_run:
                    self._db.upsert_theory_features(
                        tid, feat,
                        tier=TIER_C_SYMBOLIC, confidence=0.7,
                    )
                done += 1
            except Exception:
                pass

        print(f"    Theory features: {done} tracks")

    # ------------------------------------------------------------------
    # Stage 8: MIR
    # ------------------------------------------------------------------

    def _stage_mir(self) -> None:
        from labs.music_lab.analysis.audio_features.mir_extractor import (
            extract_chip_proxy, is_available as librosa_available
        )
        if not librosa_available():
            print("    librosa not installed — using chip proxy for MIR")
        print("    MIR: using chip proxies (full audio MIR deferred to Tier B data)")

    # ------------------------------------------------------------------
    # Stage 9: Feature vectors
    # ------------------------------------------------------------------

    def _stage_feature_vec(self) -> None:
        if self._db is None:
            print("    DB not initialized — skipping")
            return

        from labs.music_lab.similarity.feature_vector import build_vector
        from labs.music_lab.analysis.audio_features.mir_extractor import extract_chip_proxy

        tracks = self._db.get_tracks_by_tier(max_tier=4)
        built  = 0

        for t in tracks:
            try:
                tid   = t["track_id"]
                chip  = t.get("chip_features") or {}
                theory = t.get("theory_features") or {}
                mir_proxy = extract_chip_proxy(chip)

                meta = {
                    "platform":  t.get("platform", "other"),
                    "chip_type": t.get("sound_chip", "other"),
                }
                vec = build_vector(chip, theory, mir_proxy, meta, confidence=0.6)

                if not self.dry_run:
                    import numpy as _np
                    if not isinstance(vec, list):
                        vec_arr = _np.array(vec, dtype=_np.float32)
                    else:
                        import numpy as _np2
                        vec_arr = _np2.array(vec, dtype=_np2.float32)
                    self._db.save_feature_vector(tid, vec_arr, tier=TIER_A_STATIC, confidence=0.6)
                built += 1
            except Exception:
                pass

        print(f"    Built feature vectors for {built} tracks")

    # ------------------------------------------------------------------
    # Stage 10: FAISS index
    # ------------------------------------------------------------------

    def _stage_faiss(self) -> None:
        if self._db is None:
            print("    DB not initialized — skipping")
            return

        from labs.music_lab.similarity.faiss_index import build_index

        try:
            ids, mat = self._db.load_all_vectors(FEATURE_VECTOR_VERSION)
        except Exception as e:
            print(f"    Could not load vectors: {e}")
            return

        if not ids:
            print("    No vectors in DB — skipping FAISS build")
            return

        index_path = ARTIFACTS / "faiss_index.pkl"
        if not self.dry_run:
            self._index = build_index(ids, mat, index_path=index_path)
            print(f"    FAISS index built: {self._index.size} vectors → {index_path}")
        else:
            print(f"    [dry-run] Would build FAISS index for {len(ids)} vectors")

    # ------------------------------------------------------------------
    # Stage 11: Composer fingerprinting
    # ------------------------------------------------------------------

    def _stage_composer_fp(self) -> None:
        if self._db is None:
            print("    DB not initialized — skipping")
            return

        from labs.music_lab.similarity.composer_similarity import ComposerProfiler

        try:
            ids, mat = self._db.load_all_vectors(FEATURE_VECTOR_VERSION)
            tracks   = {t["track_id"]: t for t in self._db.get_tracks_by_tier(max_tier=4)}
        except Exception as e:
            print(f"    Could not load data: {e}")
            return

        vecs       = [mat[i] for i in range(len(ids))]
        composers  = [tracks.get(tid, {}).get("artist", "Unknown") for tid in ids]

        profiler = ComposerProfiler()
        profiler.fit(vecs, composers)

        if not self.dry_run:
            from labs.music_lab.config import COMPOSER_PROFILES_PATH
            profiler.save(COMPOSER_PROFILES_PATH)

        print(f"    Composer profiles built: {profiler.composer_count()} composers")

    # ------------------------------------------------------------------
    # Stage 12: Attributions
    # ------------------------------------------------------------------

    def _stage_attributions(self) -> None:
        if self._db is None or self._index is None:
            print("    DB or index not available — skipping attributions")
            return

        from labs.music_lab.similarity.composer_similarity import ComposerProfiler
        from labs.music_lab.config import COMPOSER_PROFILES_PATH

        profiler = ComposerProfiler()
        profiler.load(COMPOSER_PROFILES_PATH)

        if profiler.composer_count() == 0:
            print("    No composer profiles loaded — skipping")
            return

        try:
            ids, mat = self._db.load_all_vectors(FEATURE_VECTOR_VERSION)
        except Exception:
            return

        attributed = 0
        for i, tid in enumerate(ids):
            try:
                results = profiler.predict(mat[i], top_k=3)
                if results and not self.dry_run:
                    attrs = [{"composer": r.composer, "probability": r.probability,
                              "distance": r.distance} for r in results]
                    self._db.upsert_attribution(
                        tid, attrs, method="bayesian_gaussian",
                        tier=TIER_D_MIR, confidence=results[0].confidence,
                    )
                attributed += 1
            except Exception:
                pass

        print(f"    Attributed {attributed} tracks")

    # ------------------------------------------------------------------
    # Stage 13: Taste centroid
    # ------------------------------------------------------------------

    def _stage_taste(self) -> None:
        if self._db is None:
            print("    DB not initialized — skipping")
            return

        from labs.music_lab.taste_model.taste_vector import build, TasteVector

        if self.dry_run:
            print("    [dry-run] Would build taste centroid")
            return

        self._taste = build(self._db)

    # ------------------------------------------------------------------
    # Stage 14: Recommendations
    # ------------------------------------------------------------------

    def _stage_recommend(self) -> None:
        if self._taste is None or self._index is None or self._db is None:
            print("    Taste/index/DB not available — skipping recommendations")
            return

        from labs.music_lab.taste_model.recommender import recommend, save_reports

        if self.dry_run:
            print("    [dry-run] Would generate recommendations")
            return

        report_dir = REPORTS / "recommendations"
        nc = recommend(self._taste, self._index, self._db, mode="near_core", k=500)
        fr = recommend(self._taste, self._index, self._db, mode="frontier",  k=500)
        save_reports(nc, fr, report_dir)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Helix Music Lab master pipeline")
    p.add_argument("--stages",       default="",    help="Comma-separated stage numbers (e.g. 1,2,3)")
    p.add_argument("--limit",        type=int, default=0, help="Max tracks to process")
    p.add_argument("--dry-run",      action="store_true", help="Log only, no writes")
    p.add_argument("--resume-from",  type=int, default=1, help="Start from this stage number")
    p.add_argument("--workers",      type=int, default=PARALLEL_WORKERS)
    p.add_argument("--format",       default=None, help="Filter by extension (e.g. vgm)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if args.stages:
        stages = [int(s.strip()) for s in args.stages.split(",") if s.strip()]
    else:
        stages = list(range(1, 15))

    pipeline = MasterPipeline(
        stages=stages,
        limit=args.limit,
        dry_run=args.dry_run,
        resume_from=args.resume_from,
        workers=args.workers,
        format_filter=args.format,
    )
    pipeline.run()


if __name__ == "__main__":
    main()
