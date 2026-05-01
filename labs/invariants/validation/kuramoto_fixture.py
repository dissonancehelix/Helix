"""
Math Domain Validation Harness — labs/invariants/validation/kuramoto_fixture.py
=============================================================================
Canonical validation fixture for the Kuramoto model.

This is NOT a generic test suite. It is a Helix-native validation harness
that validates structural claims about the math domain using deterministic,
reproducible simulation fixtures and produces a structured, inspectable
validation artifact each run.

What this validates:
  A. Metric sanity — math-domain structural metrics behave in correct
     directions on deterministic inputs (not just "no crash").
  B. Canonical simulation — Kuramoto model behavior is structurally sound:
     - Low coupling (K≈0) does NOT produce false coherence
     - High coupling (K>>K_c) produces strong synchrony
     - Deterministic seeds produce stable outputs
     - Null (K=0) runs do not falsely promote invariants
  C. Projection consistency — math-local metrics project into HelixEmbedding
     deterministically, in valid ranges, with correct distance properties.
  D. Distance vs similarity — triangle inequality is validated on distance
     values, NOT on similarity scores.

Output:
  A structured validation report dict. When run from the command line,
  the report is written to stdout as JSON and optionally to a file.
  The report is designed to be persisted, compared over time, and
  consumed by governance or later automation.

Usage:
    python -m labs.invariants.validation.kuramoto_fixture
    python -m labs.invariants.validation.kuramoto_fixture --out report.json
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "README.md").exists())
sys.path.insert(0, str(ROOT))

from labs.invariants.simulation.kuramoto import KuramotoSystem
from labs.invariants.domain_analysis.math_structural_vector import MathStructuralVector
from labs.invariants.embedding.projection import (
    project, similarity, distance, validate_triangle_inequality,
    PROJECTION_SCHEMA_VERSION, PROVISIONAL_CONFIDENCE_FLOOR,
)

# ---------------------------------------------------------------------------
# Fixture parameters — deterministic, documented
# ---------------------------------------------------------------------------
SEED   = 42
N      = 50
STEPS  = 500
DT     = 0.05
K_NULL = 0.0   # null model: no coupling
K_MID  = 2.0   # moderate coupling
K_HIGH = 4.0   # strong coupling (well above K_c ≈ 1.6 for this N)


def _make_system(K: float, seed: int = SEED) -> KuramotoSystem:
    rng = np.random.default_rng(seed)
    freqs = rng.normal(0.0, 1.0, N)
    phases = rng.uniform(0, 2 * math.pi, N)
    sys_ = KuramotoSystem(n_oscillators=N, K=K, natural_freqs=freqs)
    sys_.theta = phases
    return sys_


def _run(K: float, seed: int = SEED) -> dict[str, Any]:
    sys_ = _make_system(K, seed)
    sys_.simulate(dt=DT, steps=STEPS)
    results = sys_.get_results_summary()
    vec = MathStructuralVector.from_kuramoto_results(results)
    emb = project(vec)
    return {
        "K": K,
        "seed": seed,
        "sync_index": results["sync_index"],
        "n_oscillators": results["n_oscillators"],
        "math_structural_vector": vec.to_dict(),
        "helix_embedding": emb,
        "embedding_l2_norm": float(np.linalg.norm(vec.as_array())),
        "projection_schema": PROJECTION_SCHEMA_VERSION,
    }


# ---------------------------------------------------------------------------
# Section A: Metric Sanity
# ---------------------------------------------------------------------------

def _section_a(null: dict, high: dict) -> dict:
    """
    Structural metrics must move in the correct direction with coupling strength.
    """
    checks = {
        "high_K_has_higher_sync_index": (
            high["sync_index"] > null["sync_index"]
        ),
        "high_K_has_higher_attractor_stability": (
            high["math_structural_vector"]["attractor_stability"]
            > null["math_structural_vector"]["attractor_stability"]
        ),
        "null_K_has_higher_control_entropy": (
            null["math_structural_vector"]["control_entropy"]
            > high["math_structural_vector"]["control_entropy"]
        ),
    }
    return {
        "section": "A",
        "name": "Metric Sanity",
        "passed": all(checks.values()),
        "checks": {k: {"passed": v} for k, v in checks.items()},
        "metric_outputs": {
            "null_sync_index": null["sync_index"],
            "high_sync_index": high["sync_index"],
            "null_attractor_stability": null["math_structural_vector"]["attractor_stability"],
            "high_attractor_stability": high["math_structural_vector"]["attractor_stability"],
            "null_control_entropy": null["math_structural_vector"]["control_entropy"],
            "high_control_entropy": high["math_structural_vector"]["control_entropy"],
        },
    }


# ---------------------------------------------------------------------------
# Section B: Simulation Fixture
# ---------------------------------------------------------------------------

def _section_b(null: dict, high: dict, mid: dict, mid_b: dict) -> dict:
    """
    Canonical simulation guards. Determinism, null confusion, coupling effect.
    """
    deterministic = (
        mid["sync_index"] == mid_b["sync_index"]
    )
    checks = {
        "null_K0_sync_below_0.3": null["sync_index"] < 0.3,
        "strong_K4_sync_above_0.8": high["sync_index"] > 0.8,
        "seed_produces_deterministic_output": deterministic,
        "null_embedding_l2_not_falsely_high": null["embedding_l2_norm"] < 1.5,
    }
    return {
        "section": "B",
        "name": "Simulation Fixture",
        "passed": all(checks.values()),
        "checks": {k: {"passed": v} for k, v in checks.items()},
        "threshold_context": {
            "null_confusion_guard": "sync_index < 0.3 for K=0",
            "locking_signal_guard": "sync_index > 0.8 for K=4.0",
            "null_embedding_guard": "L2 norm of null vector < 1.5 (out of sqrt(6)≈2.449)",
            "threshold_calibration_status": "provisional — not calibrated against null baseline",
        },
        "metric_outputs": {
            "null_sync_index": null["sync_index"],
            "strong_sync_index": high["sync_index"],
            "null_embedding_l2": null["embedding_l2_norm"],
            "deterministic": deterministic,
        },
    }


# ---------------------------------------------------------------------------
# Section C: Projection Consistency
# ---------------------------------------------------------------------------

def _section_c(null: dict, mid: dict, high: dict) -> dict:
    """
    Projection must be range-valid, deterministic, self-similar, and
    satisfy the triangle inequality on DISTANCE (not similarity).
    """
    axes = ["complexity", "structure", "repetition", "density", "expression", "variation"]
    emb_null = null["helix_embedding"]
    emb_mid  = mid["helix_embedding"]
    emb_high = high["helix_embedding"]

    # Re-project null to check determinism
    sys_ = _make_system(K_NULL, SEED)
    sys_.simulate(dt=DT, steps=STEPS)
    results = sys_.get_results_summary()
    vec2 = MathStructuralVector.from_kuramoto_results(results)
    emb_null2 = project(vec2)

    in_range = all(0.0 <= emb_null.get(ax, -1) <= 1.0 for ax in axes)
    projection_deterministic = all(
        abs(emb_null.get(ax, 0) - emb_null2.get(ax, 0)) < 1e-9 for ax in axes
    )
    self_sim = similarity(emb_null, emb_null)

    # Triangle inequality on DISTANCE (d(a,c) ≤ d(a,b) + d(b,c))
    tri_ok, tri_reason = validate_triangle_inequality(emb_null, emb_mid, emb_high)

    # Spot check distance invariant: d = 1 - similarity
    d = distance(emb_null, emb_high)
    s = similarity(emb_null, emb_high)
    distance_similarity_dual = abs((1.0 - s) - d) < 1e-9

    checks = {
        "all_embedding_values_in_0_1": in_range,
        "projection_is_deterministic": projection_deterministic,
        "self_similarity_is_1": abs(self_sim - 1.0) < 1e-9,
        "triangle_inequality_holds_on_distance": tri_ok,
        "distance_equals_1_minus_similarity": distance_similarity_dual,
    }
    return {
        "section": "C",
        "name": "Projection Consistency",
        "passed": all(checks.values()),
        "checks": {k: {"passed": v} for k, v in checks.items()},
        "projection_outputs": {
            "projection_schema": PROJECTION_SCHEMA_VERSION,
            "null_embedding": {ax: emb_null.get(ax) for ax in axes},
            "triangle_inequality_reason": tri_reason,
            "spot_check_distance": d,
            "spot_check_similarity": s,
            "distance_similarity_dual_holds": distance_similarity_dual,
        },
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(out_path: str | None = None) -> dict:
    """
    Run all validation sections and return a structured validation report.

    The report is suitable for:
    - inspection and diff over time
    - governance consumption
    - future automation / artifact comparison
    """
    null = _run(K=K_NULL)
    mid  = _run(K=K_MID)
    mid_b = _run(K=K_MID, seed=SEED)   # same seed, used for determinism check
    high = _run(K=K_HIGH)

    sec_a = _section_a(null, high)
    sec_b = _section_b(null, high, mid, mid_b)
    sec_c = _section_c(null, mid, high)

    all_passed = all(s["passed"] for s in [sec_a, sec_b, sec_c])

    report = {
        "fixture": "kuramoto",
        "fixture_version": "1.0",
        "projection_schema": PROJECTION_SCHEMA_VERSION,
        "confidence_floor": PROVISIONAL_CONFIDENCE_FLOOR,
        "confidence_floor_calibration_status": "provisional",
        "parameters": {
            "n_oscillators": N,
            "steps": STEPS,
            "dt": DT,
            "seed": SEED,
            "K_null": K_NULL,
            "K_mid": K_MID,
            "K_high": K_HIGH,
        },
        "passed": all_passed,
        "sections": [sec_a, sec_b, sec_c],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if out_path:
        Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="Write report to JSON file")
    args = parser.parse_args()

    report = run_all(out_path=args.out)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["passed"] else 1)
