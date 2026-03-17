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


def register_builtins(registry: "OperatorRegistry") -> None:  # type: ignore[name-defined]
    """Register all built-in operators into registry."""
    for spec in _BUILTIN_SPECS:
        registry.register(spec)


# ── Built-in operator definitions ─────────────────────────────────────────

_BUILTIN_SPECS: list[OperatorSpec] = [

    # ── Music substrate operators ──────────────────────────────────────────

    OperatorSpec(
        name="INGEST_TRACK",
        accepted_input_types=frozenset({"Track", "*"}),
        output_schema={
            "track_id":         "str",
            "control_sequence": "dict",   # ControlSequence artifact
            "artifact_path":    "str",
            "bridge_used":      "str",    # libvgm | gme | vgmstream
            "bridge_mode":      "str",    # emulated | fallback | unavailable
        },
        pipeline_stages=(
            "validate_source_file",
            "route_to_adapter",        # libvgm | gme | vgmstream based on format
            "render_control_sequence",
            "write_artifact",          # → artifacts/music/<track_id>/control_sequence.json
        ),
        failure_conditions=(
            "file_not_found",
            "format_unsupported",
            "adapter_unavailable",
            "artifact_write_error",
        ),
        description=(
            "Ingest a chip music or audio file through the appropriate adapter "
            "(libvgm → gme → vgmstream) and produce a ControlSequence artifact. "
            "Supports VGM/VGZ, SPC, NSF, GBS, HES, PSF, FLAC, MP3, OPUS, and more. "
            "Does NOT write to Atlas — use COMPILE_ATLAS after ingestion."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="ANALYZE_TRACK",
        accepted_input_types=frozenset({"Track", "ControlSequence"}),
        output_schema={
            "track_id":       "str",
            "symbolic_score": "dict",    # SymbolicScore artifact
            "signal_profile": "dict",    # SignalProfile artifact
            "artifact_paths": "list",
        },
        pipeline_stages=(
            "load_control_sequence_artifact",
            "symbolic_analysis",          # pretty_midi | music21 (if MIDI available)
            "signal_analysis",            # librosa | essentia | chip proxy
            "nuked_opn2_topology",        # YM2612 brightness proxy (if applicable)
            "write_symbolic_artifact",    # → artifacts/music/<track_id>/symbolic_score.json
            "write_signal_artifact",      # → artifacts/music/<track_id>/signal_profile.json
        ),
        failure_conditions=(
            "control_sequence_missing",
            "symbolic_analysis_error",
            "signal_analysis_error",
            "artifact_write_error",
        ),
        description=(
            "Analyze a track's ControlSequence artifact using symbolic (pretty_midi, music21) "
            "and signal (librosa, essentia) adapters. Produces SymbolicScore and SignalProfile "
            "artifacts. Musical cognition features dominate — hardware context is metadata. "
            "Does NOT write to Atlas."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="STYLE_VECTOR",
        accepted_input_types=frozenset({"Composer"}),
        output_schema={
            "composer_id":        "str",
            "artist_style_vector": "dict",   # ArtistStyleVector artifact
            "track_count":        "int",
            "artifact_path":      "str",
        },
        pipeline_stages=(
            "load_composer_tracks",
            "load_signal_profiles",         # from artifacts/music/*/signal_profile.json
            "load_symbolic_scores",         # from artifacts/music/*/symbolic_score.json
            "compute_melodic_features",     # interval distributions, leap frequency, phrase lengths
            "compute_harmonic_features",    # chord type distribution, modulation, chromaticism
            "compute_rhythmic_features",    # syncopation, note density, tempo variance
            "compute_structural_features",  # loop lengths, section transitions
            "compute_timbral_features",     # spectral centroid profile, brightness, timbre clusters
            "compute_motivic_features",     # motif repetition, motif entropy
            "aggregate_context_metadata",   # platforms_used, chips_used (CONTEXT ONLY)
            "write_style_vector_artifact",  # → artifacts/music/<composer_id>/artist_style_vector.json
        ),
        failure_conditions=(
            "composer_not_found",
            "insufficient_track_data",     # fewer than 3 analyzed tracks
            "feature_computation_error",
            "artifact_write_error",
        ),
        description=(
            "Aggregate multiple track analyses for a composer into an ArtistStyleVector. "
            "Musical cognition features (melodic, harmonic, rhythmic, structural, timbral, "
            "motivic) DOMINATE. Hardware context (chips, platforms) is stored as metadata "
            "and must never override the musical fingerprint. "
            "Supports cross-era composer reasoning: early YM2612 vs later orchestral works "
            "are compared on musical behavior, not hardware."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="COMPILE_ATLAS",
        accepted_input_types=frozenset({"Track", "Composer", "ControlSequence",
                                        "SymbolicScore", "SignalProfile",
                                        "ArtistStyleVector", "*"}),
        output_schema={
            "entities_compiled": "int",
            "entities_rejected": "int",
            "atlas_paths":       "list",
            "substrate":         "str",
        },
        pipeline_stages=(
            "discover_music_artifacts",    # scan artifacts/music/
            "normalize_entities",          # Normalization gate
            "semantic_validate",           # Semantics gate
            "compile_to_substrate_dir",    # → atlas/music/<type_plural>/
            "atlas_commit",                # ONLY authorized Atlas write path
            "update_registry",             # update atlas/entities/registry.json
        ),
        failure_conditions=(
            "artifact_not_found",
            "normalization_error",
            "semantic_validation_error",
            "atlas_write_blocked",         # raised in runtime mode for direct writes
            "index_update_error",
        ),
        description=(
            "Compile music substrate artifacts into Atlas entities. "
            "This is the ONLY authorized path for writing music data to Atlas. "
            "Enforces: normalize → semantic_validate → compile → atlas_commit. "
            "Writes to atlas/music/composers/, atlas/music/tracks/, etc."
        ),
        version="1.0.0",
    ),



    OperatorSpec(
        name="PROBE",
        accepted_input_types=frozenset({"Invariant"}),
        output_schema={
            "probe_name":   "str",
            "domain":       "str",
            "signal":       "float",
            "confidence":   "str",
            "passed":       "bool",
            "run_id":       "str",
            "artifact_dir": "str",
        },
        pipeline_stages=(
            "load_dataset",
            "execute_probe",
            "collect_signal",
            "write_artifact",
            "update_atlas",
        ),
        failure_conditions=(
            "invariant_not_found",
            "dataset_missing",
            "probe_timeout",
            "signal_below_threshold",
            "artifact_write_error",
        ),
        description="Run a falsification probe against an invariant across one or more domains.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="INGEST",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "entities_created": "int",
            "entities_updated": "int",
            "artifact_path":    "str",
        },
        pipeline_stages=(
            "validate_source",
            "parse_records",
            "normalize_entities",
            "write_artifacts",
        ),
        failure_conditions=(
            "source_unreachable",
            "parse_error",
            "normalization_error",
            "artifact_write_error",
        ),
        description=(
            "Ingest structured data from a source into Helix artifacts. "
            "Substrates use INGEST to produce artifacts — never write Atlas directly."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="LINK",
        accepted_input_types=frozenset({
            "Composer", "Track", "Game", "Platform", "SoundChip", "SoundTeam",
            "Soundtrack", "Studio", "Dataset", "Experiment", "Model",
            "Invariant", "Operator",
        }),
        output_schema={
            "source_id": "str",
            "relation":  "str",
            "target_id": "str",
            "created":   "bool",
        },
        pipeline_stages=(
            "validate_source_entity",
            "validate_target_entity",
            "check_relationship_type",
            "write_relationship",
        ),
        failure_conditions=(
            "source_not_found",
            "target_not_found",
            "invalid_relationship_type",
            "duplicate_relationship",
        ),
        description="Create a typed relationship between two entities.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="COMPILE",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "entities_compiled": "int",
            "entities_rejected": "int",
            "atlas_paths":       "list",
        },
        pipeline_stages=(
            "discover_artifacts",
            "normalize_entities",
            "semantic_validate",
            "compile_entries",
            "atlas_commit",
            "update_index",
        ),
        failure_conditions=(
            "artifact_not_found",
            "normalization_error",
            "semantic_validation_error",
            "atlas_write_blocked",
            "index_update_error",
        ),
        description=(
            "Compile validated artifacts into Atlas entities. "
            "The only authorized path for writing to Atlas."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="SCAN",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "substrate":      "str",
            "entities_found": "int",
            "artifact_path":  "str",
        },
        pipeline_stages=(
            "enumerate_substrate",
            "extract_entities",
            "write_artifacts",
        ),
        failure_conditions=(
            "substrate_not_found",
            "extraction_error",
            "artifact_write_error",
        ),
        description=(
            "Scan a substrate and extract entity candidates into artifacts. "
            "Does not write to Atlas — use COMPILE after SCAN."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="ANALYZE",
        accepted_input_types=frozenset({
            "Composer", "Track", "Game", "Invariant", "Experiment",
        }),
        output_schema={
            "signals":       "dict",
            "artifact_path": "str",
        },
        pipeline_stages=(
            "load_entity",
            "extract_features",
            "compute_signals",
            "write_artifact",
        ),
        failure_conditions=(
            "entity_not_found",
            "feature_extraction_error",
            "signal_computation_error",
        ),
        description="Analyze an entity and produce a signal artifact.",
        version="1.0.0",
    ),

    OperatorSpec(
        name="DISCOVER",
        accepted_input_types=frozenset({"Invariant"}),
        output_schema={
            "candidate_commands": "list",
            "reasoning":          "list",
            "log_path":           "str",
        },
        pipeline_stages=(
            "load_atlas",
            "analyze_gaps",
            "generate_hil_candidates",
            "log_session",
        ),
        failure_conditions=(
            "invariant_not_found",
            "atlas_empty",
            "generation_error",
        ),
        description=(
            "Analyze Atlas and generate candidate HIL commands for further exploration. "
            "NEVER executes commands — all execution must go through HIL."
        ),
        version="1.0.0",
    ),

    OperatorSpec(
        name="MIGRATE",
        accepted_input_types=frozenset({"*"}),
        output_schema={
            "entities_migrated": "int",
            "entities_failed":   "int",
            "migration_log":     "str",
        },
        pipeline_stages=(
            "detect_legacy_entities",
            "convert_to_canonical_schema",
            "compile_entity",
            "mark_migration_metadata",
        ),
        failure_conditions=(
            "detection_error",
            "schema_conversion_error",
            "compilation_error",
        ),
        description=(
            "Migrate legacy Atlas entities to canonical schema. "
            "Legacy files are NOT deleted. Migration is additive."
        ),
        version="1.0.0",
    ),

]
