"""
Cognition Domain — End-to-End Demo
domains/cognition/e2e.py

One real vertical slice of the cognition domain pipeline:

    fixture → run → trajectory log → probe extraction
    → collapse detection → morphology assignment
    → structured artifact / result

Pattern follows core/probes/math/e2e.py.

This is a demonstration path, not production orchestration.
It exercises the full pipeline in one inspectable call and
returns a structured result suitable for later comparison.

Usage:
    python -m domains.self.e2e
    # or from code:
    from domains.self.e2e import run_e2e
    result = run_e2e()
"""
from __future__ import annotations

import json
import sys
from typing import Any

from domains.self.fixtures import branching, attractor
from domains.self.fixtures.branching import BranchingConfig
from domains.self.fixtures.attractor import AttractorConfig
from domains.self.analysis.morphology_classifier import morphology_summary
from core.invariants.dcp.morphology import CollapseMorphology, MORPHOLOGY_PROFILES


def run_e2e(verbose: bool = True) -> dict[str, Any]:
    """
    Run the full cognition-domain end-to-end demonstration.

    Executes four fixture runs:
        1. Branching / linear constraint (baseline DCP case)
        2. Branching / no constraint (null control)
        3. Branching / perturbation (recovery behavior)
        4. Attractor / strong pull + perturbation (circular / transformative contrast)

    Returns a structured result dictionary containing:
        - per-run summary dicts
        - morphology assignments and descriptions
        - qualification statuses
        - schema version

    Does NOT write to Atlas or HSL — this is a local demo path.
    """
    if verbose:
        _header("Cognition Domain — End-to-End Demo")
        print("Framework: trajectory dynamics → DCP events → collapse morphology")
        print("Status: first-pass heuristic fixtures, no Atlas integration")
        print()

    results: dict[str, Any] = {
        "schema_version": "cognition_e2e_v1",
        "runs": [],
    }

    # -----------------------------------------------------------------------
    # Run 1: Branching / linear constraint — canonical DCP case
    # -----------------------------------------------------------------------
    if verbose:
        _section("Run 1: Branching fixture / linear constraint")

    cfg1 = BranchingConfig(
        initial_branches     = 8,
        constraint_schedule  = "linear",
        n_steps              = 60,
        seed                 = 42,
    )
    log1 = branching.run(cfg1)
    _report_run(log1, verbose)
    results["runs"].append(_run_record("baseline_linear", log1))

    # -----------------------------------------------------------------------
    # Run 2: Branching / no constraint — null control
    # -----------------------------------------------------------------------
    if verbose:
        _section("Run 2: Branching fixture / null control (no constraint)")

    cfg2 = BranchingConfig(
        constraint_schedule = "none",
        n_steps             = 60,
        seed                = 42,
    )
    log2 = branching.run(cfg2)
    _report_run(log2, verbose)
    results["runs"].append(_run_record("null_control", log2))

    # -----------------------------------------------------------------------
    # Run 3: Branching / perturbation midway through constraint
    # -----------------------------------------------------------------------
    if verbose:
        _section("Run 3: Branching fixture / perturbation at step 20")

    cfg3 = BranchingConfig(
        initial_branches     = 8,
        constraint_schedule  = "linear",
        n_steps              = 60,
        perturbation_step    = 20,
        perturbation_magnitude = 0.50,
        seed                 = 42,
    )
    log3 = branching.run(cfg3)
    _report_run(log3, verbose)
    results["runs"].append(_run_record("perturbed_linear", log3))

    # -----------------------------------------------------------------------
    # Run 4: Attractor / strong pull + perturbation (circular vs transformative)
    # -----------------------------------------------------------------------
    if verbose:
        _section("Run 4: Attractor fixture / strong pull + perturbation at step 25")

    cfg4 = AttractorConfig(
        n_states             = 16,
        attractor_size       = 4,
        attractor_strength   = 0.12,
        n_steps              = 80,
        perturbation_step    = 25,
        perturbation_magnitude = 0.70,
        seed                 = 42,
    )
    log4 = attractor.run(cfg4)
    _report_run(log4, verbose)
    results["runs"].append(_run_record("attractor_perturbed", log4))

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    if verbose:
        _header("Summary")
        print(f"  {'Run':<22}  {'collapse_step':<14}  {'morphology':<22}  {'status'}")
        print(f"  {'-'*22}  {'-'*14}  {'-'*22}  {'-'*16}")
        for r in results["runs"]:
            print(
                f"  {r['label']:<22}  "
                f"{str(r['collapse_step']):<14}  "
                f"{str(r['final_morphology']):<22}  "
                f"{r['qualification_status']}"
            )
        print()
        print("NOTE: All morphology labels are provisional heuristics.")
        print("      No Atlas integration. No HSL in this path.")

    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_record(label: str, log: Any) -> dict[str, Any]:
    """Extract a compact, comparable record from a TrajectoryLog."""
    s = log.summary()
    s["label"] = label
    # Add morphology description from canonical profiles
    morphology = CollapseMorphology(log.final_morphology) if log.final_morphology else None
    if morphology and morphology in MORPHOLOGY_PROFILES:
        s["morphology_description"] = MORPHOLOGY_PROFILES[morphology].description
    else:
        s["morphology_description"] = None
    return s


def _report_run(log: Any, verbose: bool) -> None:
    if not verbose:
        return
    s = log.summary()
    morphology = CollapseMorphology(log.final_morphology) if log.final_morphology else None
    print(f"  fixture:              {s['fixture_id']}")
    print(f"  steps:                {s['n_steps']}")
    print(f"  initial_breadth:      {s['initial_breadth']:.4f}")
    print(f"  final_breadth:        {s['final_breadth']:.4f}")
    print(f"  min_breadth:          {s['min_breadth']:.4f}")
    print(f"  max_tension:          {s['max_tension']:.4f}")
    print(f"  collapse_step:        {s['collapse_step']}")
    print(f"  final_morphology:     {s['final_morphology']}")
    if morphology:
        print(f"  morphology_note:      {morphology_summary(morphology)}")
    print(f"  perturbation_step:    {s['perturbation_step']}")
    print(f"  perturbation_response:{s['perturbation_response']}")
    print(f"  qualification_status: {s['qualification_status']}")
    print()


def _header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def _section(text: str) -> None:
    print(f"\n--- {text} ---")


if __name__ == "__main__":
    result = run_e2e(verbose=True)
    # Optionally write result to JSON
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
