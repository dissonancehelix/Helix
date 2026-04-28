"""
pipeline_core.py — Helix Music Substrate Pipeline Core
=========================================================
Exposes the 18-stage music translation pipeline as callable stage functions
that Helix operators can invoke deterministically.

This module is the internal orchestration layer. It must NOT be called
directly as a standalone script in production — operators call stage
functions through the Helix execution pipeline:

    HSL → Operator → pipeline_core translation → Adapter → Toolkit → Artifact

Architecture:
    INGEST_TRACK operator  → stages: scan, ingest, tier_a_parse, chip_features
    ANALYZE_TRACK operator → stages: tier_b_trace, symbolic, theory, mir, feature_vec
    STYLE_VECTOR operator  → stages: composer_fp, attributions, style_space
    COMPILE_ATLAS operator → stages: graph (then Atlas Compiler)

Operators MUST NOT write to Atlas directly. All Atlas writes go through
the Atlas Compiler gate:
    artifacts/music/<track_id>/ → COMPILE_ATLAS → atlas/music/

Stages (Dialect Translations):
    1  scan           — walk library, build file list
    2  ingest         — translate raw metadata to HSL entities
    3  chip_control   — translate to chip_control dialect (Tier A parse)
    4  chip_invariants — extract invariants from chip_control dialect
    5  emulation      — Tier B emulation trace (dialect refinement)
    6  symbolic       — translate to symbolic_music dialect (MIDI/note events)
    7  theory         — translate symbolic_music to high-level structures
    8  perceptual     — translate to perceptual_audio dialect (MIR)
    9  feature_vec    — mapping dialects to invariant feature space
    10 faiss          — build FAISS/KDTree similarity index
    11 composer_fp    — composer Gaussian fingerprinting
    12 attributions   — probabilistic composer attribution
    13 taste          — operator taste centroid
    14 recommend      — near_core + frontier recommendations
    15 graph          — knowledge graph construction (artifacts only)
    16 ludo           — ludomusicology (gameplay role, energy curve)
    17 training_sets  — composer/style training corpus generation
    18 style_space    — style vector space construction
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

# Stage definitions
STAGES: list[tuple[int, str]] = [
    (1,  "scan"),
    (2,  "ingest"),
    (3,  "chip_control"),
    (4,  "chip_invariants"),
    (5,  "emulation"),
    (6,  "symbolic"),
    (7,  "theory"),
    (8,  "perceptual"),
    (9,  "feature_vec"),
    (10, "faiss"),
    (11, "composer_fp"),
    (12, "attributions"),
    (13, "taste"),
    (14, "recommend"),
    (15, "graph"),
    (16, "ludo"),
    (17, "training_sets"),
    (18, "style_space"),
]

STAGE_NUM:  dict[str, int] = {name: num  for num, name in STAGES}
STAGE_NAME: dict[int, str] = {num:  name for num, name in STAGES}

# Stage groupings by operator
INGEST_TRACK_STAGES  = (1, 2, 3, 4)
ANALYZE_TRACK_STAGES = (5, 6, 7, 8, 9)
STYLE_VECTOR_STAGES  = (10, 11, 12, 13, 18)
GRAPH_STAGES         = (15,)
LUDO_STAGES          = (16,)
TRAINING_STAGES      = (14, 17)


# ---------------------------------------------------------------------------
# PipelineCore — operator-callable interface
# ---------------------------------------------------------------------------

class PipelineCore:
    """
    Callable stage interface for music pipeline operators.

    Operators use this class to invoke specific pipeline stages:

        core = PipelineCore(config)
        result = core.run_stages([1, 2, 3], tracks=track_list)

    This class never writes to Atlas. All outputs go to artifacts/.
    """

    def __init__(
        self,
        stages: list[int] | None = None,
        limit: int | None = None,
        dry_run: bool = False,
        resume_from: int = 1,
        workers: int | None = None,
        fmt_filter: str | None = None,
        artifact_dir: Path | None = None,
    ) -> None:
        self.stages       = stages or [s for s, _ in STAGES]
        self.limit        = limit
        self.dry_run      = dry_run
        self.resume_from  = resume_from
        self.workers      = workers
        self.fmt_filter   = fmt_filter
        self.artifact_dir = artifact_dir

    def run_stages(
        self,
        stage_nums: list[int],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run a specific subset of pipeline stages.

        Args:
            stage_nums: list of stage numbers to execute (e.g. [1, 2, 3])
            context: optional dict passed through stages (track lists, config, etc.)

        Returns:
            dict with status, stages_run, errors, duration_seconds, artifacts
        """
        ctx       = context or {}
        errors:   list[str] = []
        run_log:  list[dict] = []
        t_start   = time.monotonic()

        for num in sorted(stage_nums):
            name = STAGE_NAME.get(num)
            if name is None:
                errors.append(f"Unknown stage number: {num}")
                continue
            t0 = time.monotonic()
            try:
                stage_result = self._dispatch_stage(num, name, ctx)
                ctx.update(stage_result.get("context_updates", {}))
                run_log.append({
                    "stage":    num,
                    "name":     name,
                    "status":   "ok",
                    "duration": round(time.monotonic() - t0, 3),
                    "summary":  stage_result.get("summary", ""),
                })
            except Exception as exc:
                run_log.append({
                    "stage":    num,
                    "name":     name,
                    "status":   "error",
                    "error":    str(exc),
                    "duration": round(time.monotonic() - t0, 3),
                })
                errors.append(f"Stage {num} ({name}): {exc}")

        return {
            "status":           "ok" if not errors else "partial",
            "stages_run":       [r["stage"] for r in run_log],
            "run_log":          run_log,
            "errors":           errors,
            "duration_seconds": round(time.monotonic() - t_start, 3),
            "artifacts":        ctx.get("artifacts", []),
        }

    def _dispatch_stage(self, num: int, name: str, ctx: dict[str, Any]) -> dict[str, Any]:
        """Route stage execution to the appropriate substrate module."""
        # Import lazily to avoid circular dependencies
        if name == "scan":
            return self._stage_scan(ctx)
        elif name == "ingest":
            return self._stage_ingest(ctx)
        elif name == "chip_control": # formerly tier_a_parse
            return self._stage_chip_control(ctx)
        elif name == "chip_invariants": # formerly chip_features
            return self._stage_chip_invariants(ctx)
        elif name == "emulation": # formerly tier_b_trace
            return self._stage_emulation(ctx)
        elif name == "symbolic":
            return self._stage_symbolic(ctx)
        elif name == "theory":
            return self._stage_theory(ctx)
        elif name == "perceptual": # formerly mir
            return self._stage_perceptual(ctx)
        elif name == "feature_vec":
            return self._stage_feature_vec(ctx)
        elif name == "faiss":
            return self._stage_faiss(ctx)
        elif name == "composer_fp":
            return self._stage_composer_fp(ctx)
        elif name == "attributions":
            return self._stage_attributions(ctx)
        elif name == "taste":
            return self._stage_taste(ctx)
        elif name == "recommend":
            return self._stage_recommend(ctx)
        elif name == "graph":
            return self._stage_graph(ctx)
        elif name == "ludo":
            return self._stage_ludo(ctx)
        elif name == "training_sets":
            return self._stage_training_sets(ctx)
        elif name == "style_space":
            return self._stage_style_space(ctx)
        else:
            return {"summary": f"Stage {name} not implemented", "context_updates": {}}

    # ── Stage implementations (delegate to substrate modules) ──────────────

    def _stage_scan(self, ctx: dict) -> dict:
        from system.tools.music_pipeline.library_scanner import LibraryScanner
        scanner = LibraryScanner(fmt_filter=self.fmt_filter, limit=self.limit)
        tracks = scanner.scan()
        return {
            "summary": f"Scanned {len(tracks)} tracks",
            "context_updates": {"tracks": tracks},
        }

    def _stage_ingest(self, ctx: dict) -> dict:
        from system.tools.music_pipeline.metadata_processor import MetadataProcessor
        tracks = ctx.get("tracks", [])
        if not tracks:
            return {"summary": "No tracks to ingest", "context_updates": {}}
        proc = MetadataProcessor(dry_run=self.dry_run)
        count = proc.process(tracks)
        return {"summary": f"Ingested {count} tracks", "context_updates": {}}

    def _stage_chip_control(self, ctx: dict) -> dict:
        from model.domains.music.parsing.router import ParsingRouter
        tracks = ctx.get("tracks", [])
        router = ParsingRouter()
        results = router.parse_all(tracks, dry_run=self.dry_run)
        return {
            "summary": f"Translated to chip_control: {len(results)} tracks",
            "context_updates": {"chip_control_results": results},
        }

    def _stage_chip_invariants(self, ctx: dict) -> dict:
        from model.domains.music.feature_extraction.feature_extractor import FeatureExtractor
        chip_ctrl = ctx.get("chip_control_results", {})
        extractor = FeatureExtractor()
        features = extractor.extract_chip_features(chip_ctrl)
        return {
            "summary": f"Extracted chip invariants for {len(features)} tracks",
            "context_updates": {"chip_invariants": features},
        }

    def _stage_emulation(self, ctx: dict) -> dict:
        from model.domains.music.measurement_synthesis.measurement_engine import MeasurementEngine
        tracks = ctx.get("tracks", [])
        engine = MeasurementEngine()
        traces = engine.trace_all(tracks, dry_run=self.dry_run)
        return {
            "summary": f"Refined dialect via emulation: {len(traces)} tracks",
            "context_updates": {"emulation_traces": traces},
        }

    def _stage_symbolic(self, ctx: dict) -> dict:
        from model.domains.music.domain_analysis.symbolic import SymbolicAnalyzer
        traces = ctx.get("tier_b_traces", {})
        tier_a = ctx.get("tier_a_results", {})
        analyzer = SymbolicAnalyzer()
        symbolic = analyzer.analyze_all({**tier_a, **traces})
        return {
            "summary": f"Symbolic analysis for {len(symbolic)} tracks",
            "context_updates": {"symbolic": symbolic},
        }

    def _stage_theory(self, ctx: dict) -> dict:
        from model.domains.music.domain_analysis.musicology import MusicologyAnalyzer
        symbolic = ctx.get("symbolic", {})
        theory = MusicologyAnalyzer().analyze_all(symbolic)
        return {
            "summary": f"Theory analysis for {len(theory)} tracks",
            "context_updates": {"theory": theory},
        }

    def _stage_perceptual(self, ctx: dict) -> dict:
        from model.domains.music.domain_analysis.mir import MIRAnalyzer
        tracks = ctx.get("tracks", [])
        perceptual = MIRAnalyzer().analyze_all(tracks)
        return {
            "summary": f"Translated to perceptual_audio: {len(perceptual)} tracks",
            "context_updates": {"perceptual_audio": perceptual},
        }

    def _stage_feature_vec(self, ctx: dict) -> dict:
        from model.domains.music.feature_extraction.feature_vector import FeatureVectorBuilder
        builder = FeatureVectorBuilder()
        vectors = builder.build_all(ctx)
        return {
            "summary": f"Built {len(vectors)} feature vectors",
            "context_updates": {"feature_vectors": vectors},
        }

    def _stage_faiss(self, ctx: dict) -> dict:
        from model.domains.music.pattern_detection.faiss_index import FAISSIndexBuilder
        vectors = ctx.get("feature_vectors", {})
        builder = FAISSIndexBuilder()
        index = builder.build(vectors)
        return {
            "summary": f"FAISS index built ({len(vectors)} entries)",
            "context_updates": {"faiss_index": index},
        }

    def _stage_composer_fp(self, ctx: dict) -> dict:
        from model.domains.music.domain_analysis.composer_fingerprint import ComposerFingerprint
        vectors = ctx.get("feature_vectors", {})
        fp = ComposerFingerprint().compute_all(vectors)
        return {
            "summary": f"Composer fingerprints computed for {len(fp)} composers",
            "context_updates": {"composer_fingerprints": fp},
        }

    def _stage_attributions(self, ctx: dict) -> dict:
        from model.domains.music.pattern_detection.composer_attribution_engine import AttributionEngine
        vectors = ctx.get("feature_vectors", {})
        fps     = ctx.get("composer_fingerprints", {})
        attrs   = AttributionEngine().attribute_all(vectors, fps)
        return {
            "summary": f"Attribution computed for {len(attrs)} tracks",
            "context_updates": {"attributions": attrs},
        }

    def _stage_taste(self, ctx: dict) -> dict:
        from model.domains.music.interpretation.taste_vector import TasteVectorBuilder
        vectors = ctx.get("feature_vectors", {})
        taste   = TasteVectorBuilder().build(vectors)
        return {
            "summary": "Taste vector computed",
            "context_updates": {"taste_vector": taste},
        }

    def _stage_recommend(self, ctx: dict) -> dict:
        from model.domains.music.interpretation.recommender import Recommender
        rec = Recommender().recommend(ctx)
        return {
            "summary": f"Generated {len(rec.get('recommendations', []))} recommendations",
            "context_updates": {"recommendations": rec},
        }

    def _stage_graph(self, ctx: dict) -> dict:
        """
        Build knowledge graph artifacts.
        NOTE: Does NOT write to Atlas. Produces artifact JSON only.
        Atlas writes are handled by COMPILE_ATLAS operator.
        """
        from model.domains.music.atlas_integration.graph_integration import GraphIntegration
        gi     = GraphIntegration()
        result = gi.build_artifacts(ctx, dry_run=self.dry_run)
        return {
            "summary": "Graph artifacts produced (awaiting COMPILE_ATLAS)",
            "context_updates": {"graph_artifact": result},
        }

    def _stage_ludo(self, ctx: dict) -> dict:
        from model.domains.music.domain_analysis.ludomusicology.energy_curve import EnergyCurveAnalyzer
        tracks  = ctx.get("tracks", [])
        ludo    = EnergyCurveAnalyzer().analyze_all(tracks)
        return {
            "summary": f"Ludomusicology analysis for {len(ludo)} tracks",
            "context_updates": {"ludo": ludo},
        }

    def _stage_training_sets(self, ctx: dict) -> dict:
        from model.domains.music.atlas_integration.composer_store import ComposerStore
        fps  = ctx.get("composer_fingerprints", {})
        store = ComposerStore()
        store.update_all(fps, dry_run=self.dry_run)
        return {
            "summary": f"Training sets updated for {len(fps)} composers",
            "context_updates": {},
        }

    def _stage_style_space(self, ctx: dict) -> dict:
        from model.domains.music.embedding_generation.style_signal_generator import StyleSignalGenerator
        vectors = ctx.get("feature_vectors", {})
        fps     = ctx.get("composer_fingerprints", {})
        space   = StyleSignalGenerator().generate(vectors, fps)
        return {
            "summary": f"Style space built ({len(space.get('composers', []))} composers)",
            "context_updates": {"style_space": space},
        }


# ---------------------------------------------------------------------------
# Artifact writer — used by operators to store intermediate outputs
# ---------------------------------------------------------------------------

ARTIFACTS_ROOT = Path(__file__).parent.parent.parent / "artifacts" / "music"


def write_track_artifact(
    track_id: str,
    artifact_name: str,
    data: dict[str, Any],
    dry_run: bool = False,
) -> Path:
    """
    Write an intermediate artifact for a track.

    Artifacts are stored at: artifacts/music/<track_id>/<artifact_name>.json

    No Atlas writes. All Atlas writes go through the Atlas Compiler.
    """
    out_dir = ARTIFACTS_ROOT / track_id
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{artifact_name}.json"
    if not dry_run:
        out_path.write_text(json.dumps(data, indent=2, default=str))
    return out_path


def read_track_artifact(track_id: str, artifact_name: str) -> dict[str, Any] | None:
    """Read a previously written track artifact. Returns None if not found."""
    path = ARTIFACTS_ROOT / track_id / f"{artifact_name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_track_artifacts(track_id: str) -> list[str]:
    """List artifact names present for a given track_id."""
    track_dir = ARTIFACTS_ROOT / track_id
    if not track_dir.exists():
        return []
    return [p.stem for p in track_dir.glob("*.json")]

