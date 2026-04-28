"""
Embedding Projection Adapter — core/probes/math/embedding/projection.py
====================================================================
Projects a MathStructuralVector into the shared HelixEmbedding format.

This adapter is the ONLY legal path from math-domain metrics into the
cross-domain representation used by the Atlas.

Design intent:
- MathStructuralVector is domain-local and simulation-specific.
- HelixEmbedding is system-wide and comparison-safe.
- The projection is explicit, deterministic, versioned, and documented.
- The axes do NOT map 1:1 by default — the mapping is intentional.

Axis projection mapping (math → shared)::
  attractor_stability   → structure
  generative_constraint → complexity
  recurrence_depth      → repetition
  structural_density    → density
  control_entropy       → variation
  basin_permeability    → expression

These mappings reflect semantic similarity, not mathematical equivalence.
They should be revisited if the shared embedding axes are redefined.
When the mapping changes, PROJECTION_SCHEMA_VERSION must be incremented.

Similarity vs Distance:
  similarity(a, b) ∈ [0, 1] — 1 means identical, 0 means maximally different.
  distance(a, b)   ∈ [0, 1] — 0 means identical, 1 means maximally different.
  distance(a, b) = 1 - similarity(a, b)

  Triangle inequality is a property of DISTANCE, not similarity:
    d(a, c) ≤ d(a, b) + d(b, c)
  This is validated in validate_triangle_inequality() on distance values.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

# Provisional confidence floor — NOT calibrated.
# Calibration procedure: run K=0 Kuramoto (null model) N>=100 times,
# compute mean and std of projected embedding L2 norms, set floor at
# mean + 2*std. Until this calibration is performed, treat any
# threshold-based promotion decision as provisional.
PROVISIONAL_CONFIDENCE_FLOOR = 0.30

# Schema version for this projection mapping.
# Increment when the axis→axis mapping changes so that artifacts produced
# under different versions are not silently compared as if equivalent.
PROJECTION_SCHEMA_VERSION = "math_v1"


def project(
    math_vec: "MathStructuralVector",  # noqa: F821
    *,
    confidence: float | None = None,
    source_label: str = "math_structural_vector",
) -> dict[str, Any]:
    """
    Project a MathStructuralVector into a HelixEmbedding dict.

    Returns a dict conforming to the shared HelixEmbedding schema.
    All output values are floats in [0.0, 1.0].

    Args:
        math_vec:     The domain-local math structural vector.
        confidence:   Override confidence value. If None, computed from
                      the embedding's L2 norm relative to the unit hypercube.
        source_label: Label identifying the source vector type; kept for
                      traceability.

    Returns:
        dict with keys: complexity, structure, repetition, density,
                        expression, variation, confidence, domain, source_vector
    """
    # Axis mapping — explicit and documented, not assumed
    embedding = {
        "complexity":  float(np.clip(math_vec.generative_constraint, 0.0, 1.0)),
        "structure":   float(np.clip(math_vec.attractor_stability,    0.0, 1.0)),
        "repetition":  float(np.clip(math_vec.recurrence_depth,       0.0, 1.0)),
        "density":     float(np.clip(math_vec.structural_density,      0.0, 1.0)),
        "expression":  float(np.clip(math_vec.basin_permeability,      0.0, 1.0)),
        "variation":   float(np.clip(math_vec.control_entropy,         0.0, 1.0)),
    }

    if confidence is None:
        # Confidence heuristic: L2 norm of the 6D vector normalized to [0,1].
        # sqrt(6) is the diagonal of the unit 6-cube (max possible L2 norm).
        vec = np.array(list(embedding.values()))
        l2 = float(np.linalg.norm(vec))
        confidence = float(np.clip(l2 / math.sqrt(6), 0.0, 1.0))

    # Flag if below the provisional floor — not a hard rejection here
    # (rejection happens in the enforcement/compiler layer)
    if confidence < PROVISIONAL_CONFIDENCE_FLOOR:
        embedding["_confidence_warning"] = (
            f"Confidence {confidence:.3f} is below provisional floor "
            f"{PROVISIONAL_CONFIDENCE_FLOOR}. Null-baseline calibration "
            "has not been performed. Treat as unreliable."
        )

    embedding["confidence"] = confidence
    embedding["domain"] = "math"
    embedding["source_vector"] = source_label
    embedding["projection_schema"] = PROJECTION_SCHEMA_VERSION

    return embedding


def similarity(embedding_a: dict, embedding_b: dict) -> float:
    """
    Compute similarity between two HelixEmbedding dicts using the
    Euclidean metric normalized by sqrt(6).

    similarity = 1 - (euclidean_distance / sqrt(6))

    Returns a float in [0.0, 1.0].
    """
    axes = ["complexity", "structure", "repetition", "density", "expression", "variation"]
    a = np.array([embedding_a.get(ax, 0.0) for ax in axes])
    b = np.array([embedding_b.get(ax, 0.0) for ax in axes])
    dist = float(np.linalg.norm(a - b))
    return float(np.clip(1.0 - (dist / math.sqrt(6)), 0.0, 1.0))


def distance(embedding_a: dict, embedding_b: dict) -> float:
    """
    Compute Euclidean distance between two HelixEmbedding dicts,
    normalized by sqrt(6) so the result is in [0.0, 1.0].

    distance(a, b) = euclidean(a, b) / sqrt(6)

    This is the dual of similarity():
        distance(a, b) = 1 - similarity(a, b)
    """
    axes = ["complexity", "structure", "repetition", "density", "expression", "variation"]
    a = np.array([embedding_a.get(ax, 0.0) for ax in axes])
    b = np.array([embedding_b.get(ax, 0.0) for ax in axes])
    dist = float(np.linalg.norm(a - b))
    return float(np.clip(dist / math.sqrt(6), 0.0, 1.0))


def validate_triangle_inequality(
    emb_a: dict,
    emb_b: dict,
    emb_c: dict,
) -> tuple[bool, str]:
    """
    Verify the triangle inequality holds for three embeddings.
    Triangle inequality is a property of DISTANCE, not similarity:

        d(a, c) ≤ d(a, b) + d(b, c)

    A violation indicates a structural failure in the metric space.
    Returns (passed, reason).
    """
    d_ab = distance(emb_a, emb_b)
    d_bc = distance(emb_b, emb_c)
    d_ac = distance(emb_a, emb_c)

    if d_ac > d_ab + d_bc + 1e-9:
        return False, (
            f"STRUCTURAL_FAILURE: triangle inequality violated — "
            f"d(a,c)={d_ac:.4f} > d(a,b)={d_ab:.4f} + d(b,c)={d_bc:.4f}"
        )
    return True, "ok"
