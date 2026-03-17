"""
Operators — Built-in Operators
================================
Registers all pre-defined Helix system operators into the OperatorRegistry.

Built-in operators are deterministic execution units that dispatch predefined
pipelines only. No arbitrary script execution.

Called once at registry initialization by operator_registry.get_registry().
"""
from __future__ import annotations

from core.operators.operator_spec import OperatorSpec
from core.operators.builtins.ingest_track import IngestTrackOperator
from core.operators.builtins.analyze_track import AnalyzeTrackOperator
from core.operators.builtins.falsify_invariant import FalsifyInvariantOperator
from core.operators.builtins.topology_map import TopologyMapOperator
from core.operators.builtins.discover_invariants import DiscoverInvariantsOperator
from core.operators.builtins.measure_knowledge_gain import MeasureKnowledgeGainOperator
from core.operators.builtins.discover import DiscoverOperator
from core.operators.builtins.query import QueryOperator


def register_builtins(registry: "OperatorRegistry") -> None:  # type: ignore[name-defined]
    """Register all built-in operators into registry."""
    for spec in _BUILTIN_SPECS:
        impl = None
        if spec.name == "INGEST_TRACK":
            impl = IngestTrackOperator
        elif spec.name == "ANALYZE_TRACK":
            impl = AnalyzeTrackOperator
        elif spec.name == "DISCOVER":
            impl = DiscoverOperator
        elif spec.name == "FALSIFY_INVARIANT":
            impl = FalsifyInvariantOperator
        elif spec.name == "TOPOLOGY_MAP":
            impl = TopologyMapOperator
        elif spec.name == "DISCOVER_INVARIANTS":
            impl = DiscoverInvariantsOperator
        elif spec.name == "MEASURE_KNOWLEDGE_GAIN":
            impl = MeasureKnowledgeGainOperator
        elif spec.name == "QUERY":
            impl = QueryOperator
        # COMPILE_ATLAS implementation is usually internal to the kernel, but registered here if needed
        registry.register(spec, implementation=impl)


# ── Core system operators ─────────────────────────────────────────

_BUILTIN_SPECS: list[OperatorSpec] = [

    OperatorSpec(
        name="INGEST_TRACK",
        accepted_input_types=frozenset({"Track", "*"}),
        output_schema={
            "track_id":         "str",
            "control_sequence": "dict",
            "artifact_path":    "str",
        },
        pipeline_stages=(
            "validate_source",
            "route_to_adapter",
            "render_control_sequence",
            "write_artifact",
        ),
        failure_conditions=("file_not_found", "adapter_unavailable"),
        description="Ingest music file and produce ControlSequence artifact.",
        version="2.0.0",
    ),

    OperatorSpec(
        name="ANALYZE_TRACK",
        accepted_input_types=frozenset({"Track", "ControlSequence", "Composer"}),
        output_schema={
            "track_id":           "str",
            "mir_features":       "dict",
            "motif_features":     "dict",
            "collapse_geometry":  "dict",
            "cause_effect_map":   "dict",
            "artist_style_vector": "dict",
        },
        pipeline_stages=(
            "load_artifacts",
            "extract_mir_features",       # SignalProfile → mir_features.json
            "extract_motif_features",     # SymbolicScore → motif_features.json
            "generate_collapse_geometry", # DCP analysis
            "generate_causal_map",        # dual timeline linking
            "compute_style_vector",       # ArtistStyleVector (if Composer provided)
            "write_research_artifacts",
        ),
        failure_conditions=("data_missing", "analysis_error"),
        description="Full structural analysis. Produces MIR, Motif, Geometry, and Causal artifacts.",
        version="2.0.0",
    ),

    OperatorSpec(
        name="DISCOVER",
        accepted_input_types=frozenset({"Invariant", "MathModel", "*"}),
        output_schema={
            "candidate_commands": "list",
            "model_match_report": "dict",
            "invariant_candidates": "list",
        },
        pipeline_stages=(
            "load_context",
            "pattern_search",             # data-driven mode
            "theory_search",              # target:model mode
            "generate_output",
        ),
        failure_conditions=("empty_atlas", "search_error"),
        description="Search for patterns (data-driven) or model instances (theory-driven).",
        version="2.0.0",
    ),

    OperatorSpec(
        name="DISCOVER_INVARIANTS",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "invariant_candidates": "list",
            "compression_score":    "float",
        },
        pipeline_stages=(
            "extract_patterns",
            "detect_compression",
            "validate_consistency",
            "align_with_math",
            "write_candidate_artifact",
        ),
        failure_conditions=("no_patterns_found"),
        description="Autonomously propose new structural invariants from Atlas data.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="FALSIFY_INVARIANT",
        accepted_input_types=frozenset({"Invariant"}),
        output_schema={
            "falsification_report": "dict",
            "confidence_score":     "float",
            "dissonance_score":     "float",
        },
        pipeline_stages=(
            "load_invariant",
            "detect_deviations",
            "calculate_scores",
            "write_report",
        ),
        failure_conditions=("invariant_not_found"),
        description="Search for counterexamples to update confidence and dissonance.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="TOPOLOGY_MAP",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "topology_mapping": "dict",
            "alignment_score":  "float",
        },
        pipeline_stages=(
            "extract_descriptors",
            "compare_structural_behavior",
            "write_mapping_artifact",
        ),
        failure_conditions=("incompatible_entities"),
        description="Compare structural topology across domains (entropy, compression, hierarchy).",
        version="1.0.0",
    ),

    OperatorSpec(
        name="MEASURE_KNOWLEDGE_GAIN",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "knowledge_gain_report": "dict",
            "dataset_status":        "str",
        },
        pipeline_stages=(
            "measure_variance_shift",
            "check_motif_expansion",
            "check_invariant_shift",
            "write_gain_report",
        ),
        failure_conditions=("computation_error"),
        description="Monitor redundancy. Tags datasets as saturated if novelty is low.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="QUERY",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "matching_entities": "list",
            "entity_type":        "str",
        },
        pipeline_stages=(
            "load_atlas_index",
            "apply_filters",
            "return_results",
        ),
        failure_conditions=("empty_atlas", "query_error"),
        description="Search Atlas for indexed entities. No analysis or mutation.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="COMPILE_ATLAS",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "entities_compiled": "int",
            "atlas_paths":       "list",
        },
        pipeline_stages=(
            "discover_artifacts",
            "normalize",
            "semantic_validate",
            "atlas_commit",
        ),
        failure_conditions=("validation_error", "write_blocked"),
        description="The ONLY authorized path for writing to Atlas. Compiles artifacts into entities.",
        version="2.0.0",
    ),
]
