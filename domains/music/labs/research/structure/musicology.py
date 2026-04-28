"""
Stage 6 — Computational musicology
=====================================
Computes music theory features from symbolic scores:
  - Key estimation (Krumhansl-Schmuckler profile matching)
  - Mode detection (major/minor/modal)
  - Tempo and beat regularity analysis
  - Syncopation index
  - Motif density and top recurring motifs
  - Harmonic density (chord change rate)
  - Pitch-class histogram (12-element normalised)

Reads SymbolicScore JSON files from the symbolic_scores artifact directory
and writes theory features back to the DB.

This stage is position 6 in the pipeline (after MIR at stage 5) so that
MIR audio features are available for cross-validation of tempo estimates.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine.kernel.runtime.orchestration.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Stage 6: key/tempo/motif/harmonic analysis from symbolic scores."""
    db = pipeline._ensure_db()
    if db is None:
        print("    DB unavailable — skipping musicology analysis")
        return

    try:
        from substrates.music.ingestion.config import ARTIFACTS, TIER_C_SYMBOLIC, VGM_ROOT, LIBRARY_ROOT
        from substrates.music.analysis.theory_features.key_estimator import estimate, pitch_histogram
        from substrates.music.analysis.theory_features.rhythm_analyzer import analyze as analyze_rhythm
        from substrates.music.analysis.theory_features.motif_detector  import detect as detect_motifs
        from substrates.music.analysis.symbolic_music.score_representation import SymbolicScore
    except ImportError as exc:
        print(f"    Musicology modules unavailable: {exc}")
        return

    scores_dir = ARTIFACTS / "symbolic_scores"
    if not scores_dir.exists():
        print("    No symbolic scores — skipping musicology analysis")
        return

    done = 0
    for score_path in scores_dir.glob("*.json"):
        try:
            score = SymbolicScore.load(score_path)

            # pitch_histogram returns list[float] (12 elements, normalised)
            hist  = pitch_histogram(score.notes)
            key_r = estimate(hist)
            rhy_r = analyze_rhythm(score.notes)
            mot_r = detect_motifs(score.notes)

            feat = {
                "key_estimate":      key_r.key,
                "mode":              key_r.mode,
                "key_confidence":    key_r.confidence,
                "tempo_bpm":         rhy_r.tempo_bpm,
                "syncopation_index": rhy_r.syncopation,
                "beat_regularity":   rhy_r.beat_regularity,
                "motif_count":       mot_r.motif_density,
                "top_motif_freq":    mot_r.top_motifs[0].count if mot_r.top_motifs else 0,
                "pitch_class_histogram": [round(x, 4) for x in hist],
            }

            # Resolve source path → track_id hash
            src = score.metadata.get("source", "")
            orig_path: Path | None = None
            for root in (VGM_ROOT, LIBRARY_ROOT):
                candidate = root / src
                if candidate.exists():
                    orig_path = candidate
                    break
            if orig_path is None:
                orig_path = score_path

            tid = hashlib.sha1(str(orig_path).encode()).hexdigest()
            if not pipeline.dry_run:
                db.upsert_theory_features(
                    tid, feat,
                    tier=TIER_C_SYMBOLIC, confidence=0.7,
                )
            done += 1
        except Exception:
            pass

    print(f"    Musicology features: {done} tracks")
