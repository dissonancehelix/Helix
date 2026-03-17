"""
Semantics — Entity Type Registry
=================================
Defines SemanticSignature for every entity type in ENTITY_ONTOLOGY.

A SemanticSignature declares:
  required_fields       — fields that MUST be present and non-empty
  optional_fields       — fields that may be absent
  allowed_relationships — relationship types valid for this entity

Any entity that fails signature constraints is rejected by SemanticValidator.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticSignature:
    """Semantic contract for one entity type."""
    entity_type: str
    required_fields: frozenset[str]
    optional_fields: frozenset[str]
    allowed_relationships: frozenset[str]


# ── Base required fields shared across all types ───────────────────────────
_BASE_REQUIRED: frozenset[str] = frozenset({"id", "type", "name", "label", "description"})
_BASE_OPTIONAL: frozenset[str] = frozenset({"metadata", "external_ids", "relationships"})

# ── Core entity type signatures ────────────────────────────────────────────

COMPOSER = SemanticSignature(
    entity_type="Composer",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "birth_year", "nationality", "active_years", "primary_chip",
    }),
    allowed_relationships=frozenset({
        "COMPOSED", "MEMBER_OF", "COLLABORATED_WITH",
    }),
)

TRACK = SemanticSignature(
    entity_type="Track",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "duration", "year", "genre", "chip", "bpm", "key",
        "attribution_type",     # solo, multi, inferred
        "artist_contributions", # list of {artist_id, confidence, source}
        "original_credit",      # original unparsed string
        "analysis_status",      # pending, analyzed, modeled
    }),
    allowed_relationships=frozenset({
        "APPEARS_IN", "COMPOSED_BY",
    }),
)

GAME = SemanticSignature(
    entity_type="Game",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "release_year", "publisher", "developer", "region",
    }),
    allowed_relationships=frozenset({
        "RUNS_ON", "USES_CHIP", "HAS_SOUNDTRACK",
    }),
)

PLATFORM = SemanticSignature(
    entity_type="Platform",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "manufacturer", "release_year", "cpu", "ram",
    }),
    allowed_relationships=frozenset({
        "HOSTS", "USES_CHIP",
    }),
)

SOUND_CHIP = SemanticSignature(
    entity_type="SoundChip",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "manufacturer", "channels", "clock_speed_hz", "chip_type",
    }),
    allowed_relationships=frozenset({
        "USED_BY",
    }),
)

SOUND_TEAM = SemanticSignature(
    entity_type="SoundTeam",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "active_years", "studio", "parent_company",
    }),
    allowed_relationships=frozenset({
        "MEMBER_OF",
    }),
)

SOUND_DRIVER = SemanticSignature(
    entity_type="SoundDriver",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "version", "manufacturer", "supported_chips",
    }),
    allowed_relationships=frozenset({
        "RUNS_ON", "EXECUTES_ON", "USED_BY",
    }),
)

CPU = SemanticSignature(
    entity_type="CPU",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "architecture", "manufacturer", "clock_speed_hz", "bits",
    }),
    allowed_relationships=frozenset({
        "HOSTS", "USED_BY",
    }),
)

KNOWLEDGE_SOURCE = SemanticSignature(
    entity_type="KnowledgeSource",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "format", "url", "publication_date", "author",
    }),
    allowed_relationships=frozenset({
        "DESCRIBES", "CONTEXT_FOR",
    }),
)

# ── Reserved entity type signatures ───────────────────────────────────────

SOUNDTRACK = SemanticSignature(
    entity_type="Soundtrack",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "game", "release_year", "track_count",
    }),
    allowed_relationships=frozenset({
        "COMPOSED_BY", "RELEASED_BY", "PART_OF",
    }),
)

STUDIO = SemanticSignature(
    entity_type="Studio",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "founded_year", "country", "parent_company",
    }),
    allowed_relationships=frozenset({
        "PUBLISHED", "DEVELOPED", "COLLABORATED_WITH",
    }),
)

DATASET = SemanticSignature(
    entity_type="Dataset",
    required_fields=_BASE_REQUIRED | frozenset({"source", "version"}),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "record_count", "format", "substrate",
    }),
    allowed_relationships=frozenset({
        "USED_BY", "DERIVED_FROM",
    }),
)

EXPERIMENT = SemanticSignature(
    entity_type="Experiment",
    required_fields=_BASE_REQUIRED | frozenset({"source"}),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "hypothesis", "result", "confidence", "run_count",
    }),
    allowed_relationships=frozenset({
        "TESTS", "SUPPORTS", "CONTRADICTS", "DERIVED_FROM",
    }),
)

MODEL = SemanticSignature(
    entity_type="Model",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "architecture", "parameters", "substrate",
    }),
    allowed_relationships=frozenset({
        "IMPLEMENTS", "TRAINED_ON", "EVALUATED_BY",
    }),
)

INVARIANT = SemanticSignature(
    entity_type="Invariant",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "status",              # proposed, measured, tested, falsified, refined, verified, retired
        "confidence_score",
        "dissonance_score",
        "evidence_entities",
        "counterexamples",
    }),
    allowed_relationships=frozenset({
        "SUPPORTED_BY", "CONTRADICTED_BY", "TESTED_BY",
        "SHARES_INVARIANT", "RELATES_TO",
    }),
)

MATH_MODEL = SemanticSignature(
    entity_type="MathModel",
    required_fields=_BASE_REQUIRED | frozenset({"formal_definition"}),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "equations", "parameters", "predicted_behavior", "applicable_substrates",
    }),
    allowed_relationships=frozenset({
        "EXPLAINS", "FORMALIZES", "APPLIED_TO",
    }),
)

CONJECTURE = SemanticSignature(
    entity_type="Conjecture",
    required_fields=_BASE_REQUIRED | frozenset({"statement"}),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "predicted_by_model", "evidence_count",
    }),
    allowed_relationships=frozenset({
        "PREDICTS", "PROVEN_BY",
    }),
)

PROOF = SemanticSignature(
    entity_type="Proof",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "derivation", "assumptions", "model_id",
    }),
    allowed_relationships=frozenset({
        "PROVES", "DERIVED_FROM",
    }),
)

RESEARCH_REPORT = SemanticSignature(
    entity_type="ResearchReport",
    required_fields=_BASE_REQUIRED | frozenset({"report_type", "findings"}),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "structural_deviation", "entropy_shift", "confidence_delta",
    }),
    allowed_relationships=frozenset({
        "DOCUMENTS", "FALSIFIES", "MAPS",
    }),
)

OPERATOR = SemanticSignature(
    entity_type="Operator",
    required_fields=_BASE_REQUIRED | frozenset({"version"}),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "input_types", "output_schema", "pipeline_stages",
    }),
    allowed_relationships=frozenset({
        "IMPLEMENTS", "USES", "PRODUCES",
    }),
)

DRIVER = SemanticSignature(
    entity_type="Driver",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "substrate", "protocol",
    }),
    allowed_relationships=frozenset({
        "DRIVES", "USED_BY",
    }),
)

INFRASUBSTRATE = SemanticSignature(
    entity_type="Infrasubstrate",
    required_fields=_BASE_REQUIRED,
    optional_fields=_BASE_OPTIONAL | frozenset({
        "layer", "dependencies",
    }),
    allowed_relationships=frozenset({
        "DEPENDS_ON", "PROVIDES",
    }),
)

# ── Music analysis entity type signatures ─────────────────────────────────
# These represent the artifact-level entities produced by the music operator
# pipeline. They live at:
#   artifacts/music/<track_id>/control_sequence.json
#   artifacts/music/<track_id>/symbolic_score.json
#   artifacts/music/<track_id>/signal_profile.json
#   artifacts/music/<composer_id>/artist_style_vector.json

CONTROL_SEQUENCE = SemanticSignature(
    entity_type="ControlSequence",
    required_fields=_BASE_REQUIRED | frozenset({
        "source_track", "chip_target", "format",
    }),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "event_count", "timing_data", "register_writes",
        "sample_rate", "bridge_mode", "adapter",
    }),
    allowed_relationships=frozenset({
        "DERIVED_FROM",  # → Track
        "TARGETS_CHIP",  # → SoundChip
    }),
)

SYMBOLIC_SCORE = SemanticSignature(
    entity_type="SymbolicScore",
    required_fields=_BASE_REQUIRED | frozenset({
        "source_track",
    }),
    optional_fields=_BASE_OPTIONAL | frozenset({
        "notes", "duration_total", "tempo_map",
        "key_estimates", "chord_progression", "phrase_segmentation",
        "interval_histogram", "melodic_contour", "time_signatures",
        "adapter",
    }),
    allowed_relationships=frozenset({
        "DERIVED_FROM",   # → Track or ControlSequence
        "REPRESENTS",     # → Track
    }),
)

SIGNAL_PROFILE = SemanticSignature(
    entity_type="SignalProfile",
    required_fields=_BASE_REQUIRED | frozenset({
        "source_track",
    }),
    optional_fields=_BASE_OPTIONAL | frozenset({
        # Spectral
        "spectral_centroid", "spectral_bandwidth", "spectral_rolloff",
        "brightness", "spectral_complexity", "dissonance", "hfc",
        # Rhythm
        "onset_density", "tempo", "bpm",
        # Dynamics
        "dynamic_envelope", "dynamic_complexity",
        # Timbral
        "mfcc_means", "chroma_means", "timbre_clusters",
        "zero_crossing_rate",
        # Tonal
        "key", "key_strength", "chord_histogram", "tonal_centroid",
        # Research Metrics
        "commitment_density",  # EIP Metric: how strongly a system collapses its decision space
        "entropy_collapse_rate",
        # Meta
        "duration", "sample_rate", "adapter",
    }),
    allowed_relationships=frozenset({
        "DERIVED_FROM",   # → Track or ControlSequence
        "REPRESENTS",     # → Track
    }),
)

ARTIST_STYLE_VECTOR = SemanticSignature(
    entity_type="ArtistStyleVector",
    required_fields=_BASE_REQUIRED | frozenset({
        "composer_id",
        # Musical cognition features (required — these define composer identity)
        "melodic_features",
        "harmonic_features",
        "rhythmic_features",
    }),
    optional_fields=_BASE_OPTIONAL | frozenset({
        # Extended musical features
        "structural_features", "timbral_features", "motivic_features",
        # Context metadata — NEVER overrides musical fingerprint
        # These explain differences, not identity
        "context_metadata",
        # Provenance
        "track_count", "track_ids", "era_range",
        "vector_version",
    }),
    allowed_relationships=frozenset({
        "ATTRIBUTED_TO",   # → Composer
        "DERIVED_FROM",    # → multiple Tracks or SignalProfiles
        "SIMILAR_TO",      # → other ArtistStyleVector
        "DIVERGES_FROM",   # → other ArtistStyleVector (hardware era difference)
    }),
)

# ── Registry lookup ────────────────────────────────────────────────────────

_SIGNATURES: dict[str, SemanticSignature] = {
    sig.entity_type: sig
    for sig in [
        COMPOSER, TRACK, GAME, PLATFORM, SOUND_CHIP, SOUND_TEAM,
        SOUND_DRIVER, CPU, KNOWLEDGE_SOURCE,
        SOUNDTRACK, STUDIO, DATASET, EXPERIMENT, MODEL,
        INVARIANT, OPERATOR, INFRASUBSTRATE,
        MATH_MODEL, CONJECTURE, PROOF, RESEARCH_REPORT,
        # Music analysis entities
        CONTROL_SEQUENCE, SYMBOLIC_SCORE, SIGNAL_PROFILE, ARTIST_STYLE_VECTOR,
    ]
}


def get_signature(entity_type: str) -> SemanticSignature | None:
    """Return the SemanticSignature for entity_type, or None if unknown."""
    return _SIGNATURES.get(entity_type)


def all_entity_types() -> frozenset[str]:
    return frozenset(_SIGNATURES.keys())
