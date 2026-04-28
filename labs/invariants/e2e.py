"""
Math End-to-End Path — core/probes/math/e2e.py
==========================================
One canonical, inspectable path through the math substrate:

  Simulation input
  → Kuramoto simulation
  → MathStructuralVector extraction
  → HelixEmbedding projection
  → Invariant candidate construction
  → Governance validation gate (structural rules only)
  → Persistence candidate output (NOT committed — enforcement layer required)

This is NOT a full pipeline. It is the minimal path that proves each stage
of the math substrate produces real, inspectable output at each step.

Persistence to the Atlas is intentionally NOT done here. This module
outputs a persistence CANDIDATE dict that would be submitted to
core/engine/store/compiler/atlas_compiler.py via enforce_persistence().
The calling code is responsible for that final step.

Usage:
    python -m helix.research.invariants.math.math.e2e
    python -m helix.research.invariants.math.math.e2e --K 2.5 --n 100 --steps 800
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "helix").exists() or (p / "README.md").exists()
)
sys.path.insert(0, str(ROOT))

from helix.research.invariants.math.math.simulation.kuramoto import KuramotoSystem
from helix.research.invariants.math.math.domain_analysis.math_structural_vector import MathStructuralVector
from helix.research.invariants.math.math.embedding.projection import (
    project, PROVISIONAL_CONFIDENCE_FLOOR, PROJECTION_SCHEMA_VERSION,
)
from core.validation.validation.rules import AtomicityRule, FalsifiabilityRule


def run_e2e(
    K: float = 2.0,
    n: int = 50,
    steps: int = 500,
    dt: float = 0.05,
    seed: int = 42,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Run one end-to-end math path.

    Args:
        K:       Kuramoto coupling strength.
        n:       Number of oscillators.
        steps:   Simulation steps.
        dt:      Time step.
        seed:    Random seed for reproducibility.
        verbose: Print stage output.

    Returns:
        A dict with stage outputs and a persistence_candidate dict.
        The persistence_candidate is NOT submitted to the Atlas here —
        it requires compiler-gated persistence via enforce_persistence().
    """

    def log(msg):
        if verbose:
            print(msg)

    # --- Stage 1: Simulation ---
    log(f"\n[STAGE 1] Running Kuramoto simulation (K={K}, n={n}, steps={steps})")
    rng = np.random.default_rng(seed)
    natural_freqs = rng.normal(0.0, 1.0, n)
    initial_phases = rng.uniform(0, 2 * math.pi, n)

    system = KuramotoSystem(n_oscillators=n, K=K, natural_freqs=natural_freqs)
    system.theta = initial_phases
    system.simulate(dt=dt, steps=steps)
    sim_results = system.get_results_summary()
    log(f"  sync_index: {sim_results['sync_index']:.4f}")

    # --- Stage 2: MathStructuralVector extraction ---
    log("\n[STAGE 2] Extracting MathStructuralVector")
    math_vec = MathStructuralVector.from_kuramoto_results(sim_results)
    log(f"  {math_vec.to_dict()}")

    # --- Stage 3: HelixEmbedding projection ---
    log("\n[STAGE 3] Projecting to HelixEmbedding")
    embedding = project(math_vec)
    confidence = embedding["confidence"]
    log(f"  confidence: {confidence:.4f}")
    if confidence < PROVISIONAL_CONFIDENCE_FLOOR:
        log(f"  [WARN] Confidence {confidence:.4f} below provisional floor {PROVISIONAL_CONFIDENCE_FLOOR}")
    log(f"  {json.dumps({k: round(v, 4) for k, v in embedding.items() if isinstance(v, float)})}")

    # --- Stage 4: Invariant candidate construction ---
    log("\n[STAGE 4] Constructing invariant candidate")
    sync_index = sim_results["sync_index"]
    candidate_status = "CANDIDATE" if sync_index > 0.6 else "EXPLORATORY"

    candidate = {
        # Identity
        "entity_id": f"math.invariant:oscillator-locking-K{K:.2f}-n{n}-s{seed}",
        "entity_type": "invariant",
        "domain": "math",
        "title": "Oscillator Locking",
        # Content
        "mechanism": (
            f"Kuramoto model with K={K} produces sync_index={sync_index:.4f}, "
            "indicating coherent phase synchronization above coupling threshold."
        ),
        "status": candidate_status,
        "predictions": (
            "Increasing K above K_c will increase sync_index monotonically. "
            "K=0 will produce sync_index < 0.3 (null model guard)."
        ),
        "falsifiers": (
            "A run with K>2.0 and n>=50 that produces sync_index < 0.5 would falsify "
            "the locking claim. A run with K=0 producing sync_index > 0.3 would indicate "
            "metric miscalibration."
        ),
        # Structural vectors
        "math_structural_vector": math_vec.to_dict(),
        "ccs_embedding": embedding,
        # Provenance
        "projection_schema": PROJECTION_SCHEMA_VERSION,
        "source": "math_domain_e2e",
        "simulation_params": {"K": K, "n": n, "steps": steps, "dt": dt, "seed": seed},
        # Calibration and validation state
        "confidence": confidence,
        "calibration_status": "provisional — confidence threshold not calibrated against null baseline",
        "validation_flags": {
            "null_baseline_used": False,
            "multi_domain_observed": False,
            "adversarial_validation_run": False,
        },
        # Persistence target (deferred — not committed here)
        "persistence_target": "codex/atlas/math/",
        "persistence_gate": "core/engine/store/compiler/atlas_compiler.py via enforce_persistence()",
    }
    log(f"  status: {candidate_status}")

    # --- Stage 5: Governance validation ---
    log("\n[STAGE 5] Running governance validation rules")
    gov_results = {}
    for rule in [AtomicityRule(), FalsifiabilityRule()]:
        passed, reason = rule.check(candidate)
        gov_results[rule.name] = {"passed": passed, "reason": reason}
        log(f"  {rule.name}: {'PASS' if passed else 'FAIL'} — {reason}")

    all_gov_passed = all(r["passed"] for r in gov_results.values())

    # --- Stage 6: Persistence candidate output ---
    log("\n[STAGE 6] Persistence candidate ready")
    if all_gov_passed and confidence >= PROVISIONAL_CONFIDENCE_FLOOR:
        log("  [OK] Would be eligible for compiler-gated Atlas submission")
        log("  [NOTE] Submission requires: enforce_persistence(candidate, atlas_path, is_atlas=True)")
    else:
        log("  [BLOCKED] Not eligible for Atlas submission:")
        if not all_gov_passed:
            log(f"    Governance failed: {[k for k, v in gov_results.items() if not v['passed']]}")
        if confidence < PROVISIONAL_CONFIDENCE_FLOOR:
            log(f"    Confidence {confidence:.4f} below floor {PROVISIONAL_CONFIDENCE_FLOOR}")

    return {
        "simulation_results": sim_results,
        "math_structural_vector": math_vec.to_dict(),
        "helix_embedding": embedding,
        "invariant_candidate": candidate,
        "governance_validation": gov_results,
        "persistence_eligible": all_gov_passed and confidence >= PROVISIONAL_CONFIDENCE_FLOOR,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Helix math substrate end-to-end path")
    parser.add_argument("--K", type=float, default=2.0, help="Coupling strength")
    parser.add_argument("--n", type=int, default=50, help="Number of oscillators")
    parser.add_argument("--steps", type=int, default=500, help="Simulation steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    result = run_e2e(K=args.K, n=args.n, steps=args.steps, seed=args.seed, verbose=not args.json)
    if args.json:
        print(json.dumps(result, indent=2))
    sys.exit(0 if result["persistence_eligible"] else 1)

