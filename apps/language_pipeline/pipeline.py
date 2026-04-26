"""
Language Substrate Pipeline — Helix
===================================

Spanish-first runtime for the language domain. This is a pragmatic, fixture-led
implementation that exposes a real stack instead of a target-state stub.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.compiler.atlas_compiler import compile_and_commit
from domains.language.analysis.dcp import (
    build_language_dcp_artifacts,
    build_language_substrate_profile,
)
from domains.language.analysis.parser_trace import build_parser_traces
from domains.language.feature_extraction.comprehension_metrics import ComprehenMetrics
from domains.language.feature_extraction.structural_vector import (
    StructuralVectorExtractor,
    project_helix_embedding,
)
from domains.language.ingestion.corpus_loader import CorpusLoader
from domains.language.pattern_detection.construction_graph import ConstructionGraphBuilder
from domains.language.pattern_detection.grammar_patterns import GrammarPatterns
from domains.language.research.grammar_resolution import analyze_grammar_resolution
from domains.language.research.null_model import NullModelProbe
from domains.language.research.register_profile import analyze_label_profiles
from domains.language.research.translation_alignment import analyze_translation_alignment
from domains.language.structural_analysis.structure_analysis import StructureAnalyzer

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "domains" / "language" / "data" / "datasets"
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "language"


class LanguageSubstratePipeline:
    """
    Runnable Helix language pipeline.

    Focus:
        - Spanish structural vector
        - construction-space graph
        - grammar-resolution DCP fixture
        - null-model confidence guard
        - EN↔ES preservation fixture
        - register identity probe
    """

    def __init__(
        self,
        language: str = "spanish",
        corpus: str | None = None,
        max_samples: int | None = None,
        compile_to_atlas: bool = False,
        output_name: str | None = None,
        seed: int = 42,
    ) -> None:
        self.language = language.lower()
        self.corpus = (corpus or f"{self.language}_construction_map").lower()
        self.max_samples = max_samples
        self.compile_to_atlas = compile_to_atlas
        self.output_name = output_name
        self.seed = seed
        self.loader = CorpusLoader()

    def run(self) -> dict[str, Any]:
        records = self.loader.load_records(
            language=self.language,
            corpus=self.corpus,
            max_samples=self.max_samples,
        )
        texts = [record["text"] for record in records if record.get("text")]
        if not texts:
            raise ValueError(f"No texts loaded for language={self.language!r} corpus={self.corpus!r}")

        structure = StructureAnalyzer(language=self.language).analyze(texts)
        grammar = GrammarPatterns(language=self.language).extract(texts)
        structural_vector = StructuralVectorExtractor(language=self.language).summarize(records)
        construction_graph = ConstructionGraphBuilder(language=self.language).build(records)
        null_model = NullModelProbe(language=self.language, seed=self.seed).evaluate(records)
        parser_traces = build_parser_traces(
            language=self.language,
            records=records,
        )

        translation_alignment = analyze_translation_alignment(
            self._load_json_fixture("en_es_alignment.json")
        )
        register_profile = analyze_label_profiles(
            self._load_json_fixture(f"{self.language}_registers.json"),
            language=self.language,
            label_key="register",
        )
        grammar_resolution = analyze_grammar_resolution(
            self._load_language_fixture("grammar_resolution.json")
        )
        decision_compression = analyze_grammar_resolution(
            self._load_language_fixture("decision_compression_dataset.json")
        )

        comprehension = self._comprehension_proxy(texts)
        substrate_profile = build_language_substrate_profile(
            language=self.language,
            structural_vector=structural_vector,
            construction_graph=construction_graph,
        )
        dcp_artifacts = build_language_dcp_artifacts(
            language=self.language,
            corpus=self.corpus,
            structural_vector=structural_vector,
            construction_graph=construction_graph,
            null_model=null_model,
            source_artifact=self.corpus,
        )
        dcp_profile = self._build_dcp_profile(
            construction_graph=construction_graph,
            grammar_resolution=grammar_resolution,
            decision_compression=decision_compression,
            null_model=null_model,
            dcp_block=dcp_artifacts["dcp_block"],
        )
        embedding = project_helix_embedding(
            structural_vector["centroid"],
            null_signal=null_model,
            domain="language",
        )
        corpus_profile = self._build_corpus_profile(
            records=records,
            structural_vector=structural_vector,
            construction_graph=construction_graph,
        )
        structure_profile = self._build_structure_profile(
            structure=structure,
            grammar=grammar,
            construction_graph=construction_graph,
            dcp_artifacts=dcp_artifacts,
        )
        semantic_profile = self._build_semantic_profile(
            translation_alignment=translation_alignment,
            register_profile=register_profile,
            grammar_resolution=grammar_resolution,
            decision_compression=decision_compression,
            comprehension=comprehension,
            null_model=null_model,
            dcp_artifacts=dcp_artifacts,
        )

        summary = {
            "language": self.language,
            "corpus": self.corpus,
            "record_count": len(records),
            "structure_dispersion": structural_vector.get("dispersion", 0.0),
            "construction_nodes": construction_graph.get("node_count", 0),
            "construction_edges": construction_graph.get("edge_count", 0),
            "null_model_passes": bool(null_model.get("passes")),
            "translation_passes": bool(translation_alignment.get("passes")),
            "register_passes": bool(register_profile.get("passes")),
            "grammar_resolution_passes": bool(grammar_resolution.get("supports_dcp")),
            "decision_compression_passes": bool(decision_compression.get("supports_dcp")),
            "dcp_score": dcp_profile["compression_score"],
            "dcp_event_count": dcp_artifacts["dcp_block"]["event_count"],
            "dcp_qualification": dcp_artifacts["dcp_block"]["qualification"],
            "dominant_morphology": dcp_artifacts["dcp_block"]["dominant_morphology"],
            "translation_mean_score": translation_alignment.get("mean_score", 0.0),
            "register_accuracy": register_profile.get("nearest_centroid_accuracy", 0.0),
            "parser_trace_count": parser_traces.get("trace_count", 0),
        }

        payload = {
            "status": "ok",
            "language": self.language,
            "corpus": self.corpus,
            "records": len(records),
            "structure": structure,
            "grammar": grammar,
            "structural_vector": structural_vector,
            "construction_graph": construction_graph,
            "null_model": null_model,
            "parser_traces": parser_traces,
            "substrate_profile": substrate_profile,
            "corpus_profile": corpus_profile,
            "structure_profile": structure_profile,
            "semantic_profile": semantic_profile,
            "translation_alignment": translation_alignment,
            "register_profile": register_profile,
            "grammar_resolution": grammar_resolution,
            "decision_compression_fixture": decision_compression,
            "trajectory_dynamics": dcp_artifacts["trajectory_dynamics"],
            "dcp_events": dcp_artifacts["dcp_events"],
            "dcp_block": dcp_artifacts["dcp_block"],
            "dcp_probe_output": dcp_artifacts["probe_output"],
            "dcp_profile": dcp_profile,
            "comprehension_proxy": comprehension,
            "embedding": embedding,
            "summary": summary,
        }

        artifact_dir = self._write_artifacts(payload)
        payload["artifact_dir"] = str(artifact_dir)

        if self.compile_to_atlas:
            atlas_path = self._compile_corpus_entity(payload)
            payload["atlas_entity"] = str(atlas_path)
            payload["atlas_text_entities"] = self._compile_text_entities(payload)

        return payload

    def _artifact_dir(self) -> Path:
        slug = self.output_name or f"{self.language}_{self.corpus}"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return ARTIFACT_ROOT / f"{slug}_{timestamp}"

    def _write_artifacts(self, payload: dict[str, Any]) -> Path:
        artifact_dir = self._artifact_dir()
        artifact_dir.mkdir(parents=True, exist_ok=True)

        for name, value in (
            ("summary.json", payload["summary"]),
            ("structure.json", payload["structure"]),
            ("grammar.json", payload["grammar"]),
            ("structural_vector.json", payload["structural_vector"]),
            ("construction_graph.json", payload["construction_graph"]),
            ("null_model.json", payload["null_model"]),
            ("parser_traces.json", payload["parser_traces"]),
            ("substrate_profile.json", payload["substrate_profile"]),
            ("corpus_profile.json", payload["corpus_profile"]),
            ("structure_profile.json", payload["structure_profile"]),
            ("semantic_profile.json", payload["semantic_profile"]),
            ("translation_alignment.json", payload["translation_alignment"]),
            ("register_profile.json", payload["register_profile"]),
            ("grammar_resolution.json", payload["grammar_resolution"]),
            ("decision_compression_fixture.json", payload["decision_compression_fixture"]),
            ("trajectory_dynamics.json", payload["trajectory_dynamics"]),
            ("dcp_events.json", payload["dcp_events"]),
            ("dcp_block.json", payload["dcp_block"]),
            ("dcp_probe_output.json", payload["dcp_probe_output"]),
            ("dcp_profile.json", payload["dcp_profile"]),
            ("comprehension_proxy.json", payload["comprehension_proxy"]),
            ("embedding.json", payload["embedding"]),
        ):
            (artifact_dir / name).write_text(
                json.dumps(value, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return artifact_dir

    def _compile_corpus_entity(self, payload: dict[str, Any]) -> Path:
        embedding = dict(payload["embedding"])
        created_at = datetime.now(timezone.utc).isoformat()
        entity = {
            "id": f"language.corpus:{self.corpus}",
            "type": "Corpus",
            "entity_id": f"language.corpus:{self.corpus}",
            "entity_type": "Corpus",
            "name": self.corpus.replace("_", " ").title(),
            "label": self.corpus.replace("_", " ").title(),
            "description": (
                f"Language corpus run for {self.language} with substrate profile, "
                "construction-space DCP events, null model, translation, and register probes."
            ),
            "domain": "language",
            "source": "language_pipeline",
            "created_at": created_at,
            "confidence": embedding["confidence"],
            "language": self.language,
            "record_count": payload["summary"]["record_count"],
            "embedding": embedding,
            "summary": payload["summary"],
            "substrate": payload["substrate_profile"],
            "dcp": payload["dcp_block"],
            "corpus": payload["corpus_profile"],
            "structure": payload["structure_profile"],
            "semantic": payload["semantic_profile"],
            "evidence": {
                "signals": [
                    {
                        "name": "translation_alignment_mean",
                        "value": round(float(payload["translation_alignment"].get("mean_score", 0.0)), 4),
                        "block": "semantic",
                    },
                    {
                        "name": "register_accuracy",
                        "value": round(float(payload["register_profile"].get("nearest_centroid_accuracy", 0.0)), 4),
                        "block": "semantic",
                    },
                    {
                        "name": "null_model_confidence",
                        "value": round(float(payload["null_model"].get("confidence", 0.0)), 4),
                        "block": "semantic",
                    },
                    {
                        "name": "dcp_composite",
                        "value": round(float(payload["dcp_block"].get("composite", 0.0)), 4),
                        "block": "dcp",
                    },
                ],
                "source_features": [
                    f"language: {self.language}",
                    f"corpus: {self.corpus}",
                    f"families: {payload['structure_profile'].get('family_count', 0)}",
                    f"dominant_morphology: {payload['dcp_block'].get('dominant_morphology')}",
                ],
                "sources": [self.corpus],
                "artifacts": [str(payload.get("artifact_dir", ""))],
                "notes": "Corpus entity packages the canonical Helix runtime blocks for the language substrate.",
            },
            "ccs": {
                axis: embedding[axis]
                for axis in ("complexity", "structure", "repetition", "density", "expression", "variation")
            },
            "normalization": {
                "method": "heuristic_structural_pipeline",
                "reference": "language_v1",
            },
            "version": {
                "schema_version": "language_corpus_v1",
                "substrate_version": "1.2",
                "pipeline_version": "language_stack_v2_1",
            },
            "metadata": {
                "source": "language_pipeline",
                "source_stage": "pipeline_run",
                "source_artifact": str(payload.get("artifact_dir", "")),
                "extraction_method": "heuristic_structural_pipeline",
                "language": self.language,
                "summary": payload["summary"],
                "embedding": embedding,
                "substrate_schema": payload["substrate_profile"].get("schema_version"),
                "dcp_schema": payload["dcp_block"].get("schema_version"),
                "corpus_schema": payload["corpus_profile"].get("schema_version"),
                "structure_schema": payload["structure_profile"].get("schema_version"),
                "semantic_schema": payload["semantic_profile"].get("schema_version"),
                "parser_trace_schema": payload["parser_traces"].get("schema_version"),
                "dcp_probe_output": payload["dcp_probe_output"],
            },
            "relationships": [],
            "external_ids": {},
        }
        return compile_and_commit(entity)

    def _compile_text_entities(self, payload: dict[str, Any]) -> list[str]:
        text_entity_paths: list[str] = []
        dcp_index = self._index_text_dcp_events(payload["dcp_events"])

        for trace in payload["parser_traces"].get("traces", []):
            entity = self._build_text_entity(
                trace=trace,
                payload=payload,
                dcp_index=dcp_index,
            )
            path = compile_and_commit(entity)
            text_entity_paths.append(str(path))

        return text_entity_paths

    def _build_corpus_profile(
        self,
        *,
        records: list[dict[str, Any]],
        structural_vector: dict[str, Any],
        construction_graph: dict[str, Any],
    ) -> dict[str, Any]:
        family_counts = Counter(
            str(record.get("family", "ungrouped"))
            for record in records
        )
        transform_counts = Counter(
            str(record.get("transform", "base"))
            for record in records
            if record.get("transform")
        )
        token_counts = [
            int(vector.get("token_count", 0))
            for vector in structural_vector.get("vectors", [])
            if vector.get("token_count") is not None
        ]

        return {
            "block": "corpus",
            "schema_version": "language_corpus_block_v1",
            "language": self.language,
            "corpus": self.corpus,
            "record_count": len(records),
            "family_count": len(construction_graph.get("families", {})),
            "family_distribution": dict(family_counts),
            "transform_distribution": dict(transform_counts),
            "axes": list(structural_vector.get("axes", [])),
            "centroid": structural_vector.get("centroid", {}),
            "dispersion": structural_vector.get("dispersion", 0.0),
            "frame_concentration": structural_vector.get("frame_concentration", {}),
            "mean_token_count": round(sum(token_counts) / len(token_counts), 2) if token_counts else 0.0,
            "notes": "Corpus block summarizes the construction lattice used by the language runtime.",
        }

    def _build_structure_profile(
        self,
        *,
        structure: dict[str, Any],
        grammar: dict[str, Any],
        construction_graph: dict[str, Any],
        dcp_artifacts: dict[str, Any],
    ) -> dict[str, Any]:
        transform_edges = [
            edge for edge in construction_graph.get("edges", [])
            if edge.get("label") != "family_proximity"
        ]
        mean_transform_distance = 0.0
        if transform_edges:
            mean_transform_distance = round(
                sum(float(edge.get("distance", 0.0)) for edge in transform_edges) / len(transform_edges),
                4,
            )

        return {
            "block": "structure",
            "schema_version": "language_structure_block_v1",
            "language": self.language,
            "sample_count": structure.get("sample_count", 0),
            "sentence_lengths": structure.get("sentence_lengths", {}),
            "type_token_ratio": structure.get("type_token_ratio", 0.0),
            "word_order": structure.get("word_order", {}),
            "verb_morphology": structure.get("verb_morphology", {}),
            "top_frames": grammar.get("top_frames", []),
            "family_count": len(construction_graph.get("families", {})),
            "attractors": construction_graph.get("attractors", []),
            "bottlenecks": construction_graph.get("bottlenecks", []),
            "mean_transform_distance": mean_transform_distance,
            "dominant_morphology": dcp_artifacts["dcp_block"].get("dominant_morphology"),
            "notes": "Structure block captures the observable grammar geometry of the corpus lattice.",
        }

    def _build_semantic_profile(
        self,
        *,
        translation_alignment: dict[str, Any],
        register_profile: dict[str, Any],
        grammar_resolution: dict[str, Any],
        decision_compression: dict[str, Any],
        comprehension: dict[str, Any],
        null_model: dict[str, Any],
        dcp_artifacts: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "block": "semantic",
            "schema_version": "language_semantic_block_v1",
            "language": self.language,
            "translation_alignment": {
                "pair_count": translation_alignment.get("pair_count", 0),
                "mean_score": translation_alignment.get("mean_score", 0.0),
                "passes": bool(translation_alignment.get("passes")),
            },
            "register_identity": {
                "profile_count": register_profile.get("profile_count", 0),
                "nearest_centroid_accuracy": register_profile.get("nearest_centroid_accuracy", 0.0),
                "passes": bool(register_profile.get("passes")),
            },
            "grammar_resolution": {
                "dominant_mass_top2": grammar_resolution.get("dominant_mass_top2", 0.0),
                "collapse_sharpness": grammar_resolution.get("collapse_sharpness", 0.0),
                "supports_dcp": bool(grammar_resolution.get("supports_dcp")),
            },
            "decision_compression_fixture": {
                "dominant_mass_top2": decision_compression.get("dominant_mass_top2", 0.0),
                "collapse_sharpness": decision_compression.get("collapse_sharpness", 0.0),
                "supports_dcp": bool(decision_compression.get("supports_dcp")),
            },
            "null_model_guard": {
                "signal_gap": null_model.get("signal_gap", 0.0),
                "confidence": null_model.get("confidence", 0.0),
                "passes": bool(null_model.get("passes")),
            },
            "comprehension_proxy": comprehension,
            "probe_output": dcp_artifacts["probe_output"],
            "notes": (
                "Semantic block packages the cross-language preservation, register, "
                "and DCP support probes used by the fixture-led runtime."
            ),
        }

    def _build_text_entity(
        self,
        *,
        trace: dict[str, Any],
        payload: dict[str, Any],
        dcp_index: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        text_entity_id = self._text_entity_id(trace.get("record_id", "text"))
        record_embedding = project_helix_embedding(
            trace.get("axis_values", {}),
            null_signal=payload.get("null_model"),
            domain="language",
        )
        dcp_snapshot = self._build_text_dcp_snapshot(
            trace=trace,
            dcp_entries=dcp_index.get(str(trace.get("record_id", "")), []),
        )

        relationships = [
            {
                "relation": "PART_OF",
                "target_id": f"language.corpus:{self.corpus}",
                "confidence": 1.0,
            }
        ]
        if trace.get("edge_from"):
            relationships.append({
                "relation": "VARIANT_OF",
                "target_id": self._text_entity_id(str(trace["edge_from"])),
                "confidence": 1.0,
            })

        return {
            "id": text_entity_id,
            "type": "Text",
            "entity_id": text_entity_id,
            "entity_type": "Text",
            "name": str(trace.get("label") or trace.get("record_id") or "Text").replace("_", " ").title(),
            "label": str(trace.get("record_id") or trace.get("label") or "text"),
            "description": (
                f"{self.language.title()} text fixture '{trace.get('record_id')}' in corpus "
                f"'{self.corpus}', compiled with parser trace and construction metadata."
            ),
            "source": "language_pipeline",
            "created_at": created_at,
            "language": self.language,
            "text": trace.get("text"),
            "family": trace.get("family"),
            "transform": trace.get("transform"),
            "embedding": record_embedding,
            "summary": {
                "record_id": trace.get("record_id"),
                "family": trace.get("family"),
                "construction_role": trace.get("construction_role"),
                "sentence_type": trace.get("sentence_type"),
                "token_count": trace.get("token_count", 0),
            },
            "substrate": payload["substrate_profile"],
            "dcp": dcp_snapshot,
            "corpus": {
                "block": "corpus",
                "schema_version": "language_text_corpus_link_v1",
                "corpus_id": f"language.corpus:{self.corpus}",
                "family": trace.get("family"),
                "family_size": payload["corpus_profile"].get("family_distribution", {}).get(str(trace.get("family")), 1),
                "construction_role": trace.get("construction_role"),
                "transform": trace.get("transform"),
            },
            "structure": {
                "block": "structure",
                "schema_version": "language_text_structure_v1",
                "parser_backend": trace.get("backend"),
                "parser_trace_schema": trace.get("schema_version"),
                "sentence_type": trace.get("sentence_type"),
                "negation_present": trace.get("negation_present"),
                "pro_drop_likely": trace.get("pro_drop_likely"),
                "frame_anchor": trace.get("frame_anchor"),
                "axis_values": trace.get("axis_values", {}),
                "dependency_proxy": trace.get("dependency_proxy", {}),
            },
            "semantic": {
                "block": "semantic",
                "schema_version": "language_text_semantic_v1",
                "family": trace.get("family"),
                "label": trace.get("label"),
                "construction_role": trace.get("construction_role"),
                "transform": trace.get("transform"),
                "translation_reference_score": payload["translation_alignment"].get("mean_score", 0.0),
                "register_reference_accuracy": payload["register_profile"].get("nearest_centroid_accuracy", 0.0),
                "probe_reference": payload["dcp_probe_output"],
            },
            "evidence": {
                "signals": [
                    {
                        "name": "trace_confidence",
                        "value": round(float(trace.get("confidence", 0.0)), 4),
                        "block": "structure",
                    },
                    {
                        "name": "embedding_confidence",
                        "value": round(float(record_embedding.get("confidence", 0.0)), 4),
                        "block": "embedding",
                    },
                ],
                "source_features": [
                    f"record_id: {trace.get('record_id')}",
                    f"family: {trace.get('family')}",
                    f"construction_role: {trace.get('construction_role')}",
                ],
                "sources": [self.corpus, str(trace.get("record_id", ""))],
                "artifacts": [str(payload.get("artifact_dir", ""))],
                "notes": "Sentence-level text entity emitted from the canonical language substrate pipeline.",
            },
            "ccs": {
                axis: record_embedding[axis]
                for axis in ("complexity", "structure", "repetition", "density", "expression", "variation")
            },
            "metadata": {
                "source": "language_pipeline",
                "source_stage": "sentence_compile",
                "source_artifact": str(payload.get("artifact_dir", "")),
                "extraction_method": "heuristic_surface_parser",
                "corpus": self.corpus,
                "record_id": trace.get("record_id"),
                "parser_trace": trace,
                "corpus_entity_id": f"language.corpus:{self.corpus}",
            },
            "relationships": relationships,
            "external_ids": {},
        }

    def _build_text_dcp_snapshot(
        self,
        *,
        trace: dict[str, Any],
        dcp_entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not dcp_entries:
            return {
                "block": "dcp",
                "schema_version": "language_text_dcp_v1",
                "event_role": "background",
                "family": trace.get("family"),
                "transform": trace.get("transform"),
                "notes": "No direct construction-transform event targeted this text; corpus-level DCP still applies.",
            }

        primary = max(
            dcp_entries,
            key=lambda item: float(item["event"].get("confidence", 0.0)),
        )
        event = primary["event"]
        return {
            "block": "dcp",
            "schema_version": "language_text_dcp_v1",
            "event_role": primary["role"],
            "event_id": event.get("event_id"),
            "family": trace.get("family"),
            "transform": trace.get("transform"),
            "qualification": event.get("qualification_status"),
            "collapse_morphology": event.get("collapse_morphology"),
            "collapse": event.get("collapse_proxy"),
            "post_narrowing": event.get("post_collapse_narrowing"),
            "confidence": event.get("confidence"),
        }

    def _index_text_dcp_events(self, events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            edge = event.get("domain_metadata", {}).get("edge", {})
            source_id = str(edge.get("source", ""))
            target_id = str(edge.get("target", ""))
            if source_id:
                index.setdefault(source_id, []).append({"role": "pre_transform_source", "event": event})
            if target_id:
                index.setdefault(target_id, []).append({"role": "post_transform_target", "event": event})
        return index

    def _text_entity_id(self, record_id: str) -> str:
        normalized = "".join(
            character if character.isalnum() else "_"
            for character in f"{self.corpus}_{record_id}".lower()
        ).strip("_")
        return f"language.text:{normalized}"

    def _load_json_fixture(self, filename: str) -> dict[str, Any] | list[dict[str, Any]]:
        path = DATASET_ROOT / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing language fixture: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_language_fixture(self, filename: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Load a fixture, preferring a language-specific variant when available.

        Tries ``{stem}_{language}.{ext}`` first, falls back to ``{filename}``.
        Example: grammar_resolution.json → grammar_resolution_turkish.json
        """
        stem, dot, ext = filename.rpartition(".")
        lang_specific = DATASET_ROOT / f"{stem}_{self.language}{dot}{ext}"
        if lang_specific.exists():
            return json.loads(lang_specific.read_text(encoding="utf-8"))
        return self._load_json_fixture(filename)

    def _comprehension_proxy(self, texts: list[str]) -> dict[str, Any]:
        prompts: list[str] = []
        continuations: list[str] = []
        for text in texts:
            words = text.split()
            if len(words) < 4:
                continue
            midpoint = len(words) // 2
            prompts.append(" ".join(words[:midpoint]))
            continuations.append(" ".join(words[midpoint:]))

        if not prompts:
            return {"semantic_overlap": 0.0, "prediction_accuracy": 0.0}

        predictions = [
            continuation.split()[0] if continuation.split() else ""
            for continuation in continuations
        ]
        return {
            "semantic_overlap": ComprehenMetrics.batch_semantic_overlap(prompts, continuations),
            "prediction_accuracy": ComprehenMetrics.prediction_accuracy(
                predictions,
                continuations,
                partial=True,
            ),
        }

    def _build_dcp_profile(
        self,
        construction_graph: dict[str, Any],
        grammar_resolution: dict[str, Any],
        decision_compression: dict[str, Any],
        null_model: dict[str, Any],
        dcp_block: dict[str, Any],
    ) -> dict[str, Any]:
        bottlenecks = construction_graph.get("bottlenecks", [])
        mean_bottleneck = 0.0
        if bottlenecks:
            mean_bottleneck = round(
                sum(float(edge.get("distance", 0.0)) for edge in bottlenecks) / len(bottlenecks),
                4,
            )

        compression_score = round(
            (
                float(grammar_resolution.get("dominant_mass_top2", 0.0))
                + float(decision_compression.get("dominant_mass_top2", 0.0))
                + float(null_model.get("confidence", 0.0))
                + min(mean_bottleneck, 1.0)
                + float(dcp_block.get("composite", 0.0))
            ) / 5.0,
            4,
        )

        return {
            "profile": "expand_detect_prune_compress_reset",
            "compression_score": compression_score,
            "construction_bottleneck_mean": mean_bottleneck,
            "grammar_resolution_supports_dcp": bool(grammar_resolution.get("supports_dcp")),
            "decision_fixture_supports_dcp": bool(decision_compression.get("supports_dcp")),
            "null_model_confidence": float(null_model.get("confidence", 0.0)),
            "dominant_morphology": dcp_block.get("dominant_morphology"),
            "qualification": dcp_block.get("qualification"),
            "attractors": construction_graph.get("attractors", []),
        }
