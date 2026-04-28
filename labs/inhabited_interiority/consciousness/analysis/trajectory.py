"""
Cognition Domain — Trajectory Schema
core data structure for all cognition-domain runs.

This is the canonical log format for any fixture that exercises the
trajectory dynamics framework (constraint → tension → collapse → morphology).

Design rules:
- All fields use normalized [0, 1] proxies where applicable
- schema_version must be bumped if fields are added/removed/renamed
- to_dict() / to_json() are the canonical serialization paths
- This module has no dependency on fixture logic — fixtures import it, not vice versa
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import json
import uuid

EVENT_SCHEMA_VERSION = "cognition_traj_v1"
LOG_SCHEMA_VERSION   = "cognition_log_v1"


@dataclass
class TrajectoryEvent:
    """
    A single step in a cognition-domain fixture run.

    Produced at every time step by the fixture runner.
    All proxy values are [0, 1] normalized unless noted otherwise.
    """

    step: int
    """Time step index (0-indexed)."""

    possibility_breadth: float
    """
    Fraction of state space accessible at this step.
    1.0 = fully open; 0.0 = singular forced state.
    """

    constraint_proxy: float
    """
    Normalized constraint strength acting at this step.
    0.0 = unconstrained; 1.0 = maximally constrained.
    """

    tension_proxy: float
    """
    Accumulated unresolved constraint up to this step.
    Proxy: cumulative integral of constraint_proxy normalized by step count.
    """

    state_summary: dict[str, Any]
    """
    Fixture-specific state snapshot. Content is fixture-local.
    Not compared across fixture types.
    """

    collapse_flag: bool = False
    """True if a collapse event was detected at this step."""

    collapse_morphology: Optional[str] = None
    """
    Morphology label at this step (if collapse detected).
    Use values from CollapseMorphology enum (core/engine/compute/invariants/dcp/morphology.py).
    """

    perturbation_active: bool = False
    """True if a perturbation was injected at or just before this step."""

    post_collapse_narrowing: Optional[float] = None
    """
    Fractional narrowing from pre-collapse breadth to this step's breadth.
    Only meaningful after a collapse event.
    """

    notes: Optional[str] = None
    """Free-text annotation for this step."""

    schema_version: str = EVENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrajectoryLog:
    """
    Complete record of a single fixture run.

    Produced after a fixture completes execution.
    Carries provenance, all per-step events, and run-level summary fields.
    Designed for comparison across seeds, configurations, and fixture types.
    """

    fixture_id: str
    """Canonical fixture type identifier (e.g. 'branching', 'attractor')."""

    fixture_type: str
    """Human-readable fixture class name."""

    run_id: str
    """Unique run identifier (UUID or seed-derived)."""

    seed: int
    """Random seed used for this run."""

    config: dict[str, Any]
    """Full configuration snapshot for reproducibility."""

    events: list[TrajectoryEvent]
    """All per-step events in time order."""

    # --- Run-level summary fields ---

    collapse_step: Optional[int] = None
    """Step at which the first collapse event was detected. None if no collapse."""

    final_morphology: Optional[str] = None
    """Morphology label assigned at end of run. None if no collapse occurred."""

    perturbation_step: Optional[int] = None
    """Step at which perturbation was injected. None if no perturbation."""

    perturbation_response: Optional[float] = None
    """
    Signed change in possibility_breadth from pre-perturbation to post-perturbation.
    Positive = expansion (recovery); negative = further constraint.
    None if no perturbation.
    """

    qualification_status: str = "INSUFFICIENT"
    """
    DCP qualification status for this run.
    Mirrors DCPEvent.qualification_status() logic:
        'FULL'        — all five DCP components were observable
        'UNCONFIRMED' — tension was not observable (collapsed without tension plateau)
        'INCOMPLETE'  — 3-4 components observable
        'INSUFFICIENT' — fewer than 3 components
    """

    schema_version: str = LOG_SCHEMA_VERSION

    # --- Serialization ---

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # events are already dicts via asdict; no extra work needed
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> dict[str, Any]:
        """
        Compact run summary for comparison and reporting.
        Does not include per-step events.
        """
        breadths = [e.possibility_breadth for e in self.events]
        tensions = [e.tension_proxy for e in self.events]
        return {
            "fixture_id":           self.fixture_id,
            "run_id":               self.run_id,
            "seed":                 self.seed,
            "n_steps":              len(self.events),
            "initial_breadth":      breadths[0] if breadths else None,
            "final_breadth":        breadths[-1] if breadths else None,
            "min_breadth":          min(breadths) if breadths else None,
            "max_tension":          max(tensions) if tensions else None,
            "collapse_step":        self.collapse_step,
            "final_morphology":     self.final_morphology,
            "perturbation_step":    self.perturbation_step,
            "perturbation_response": self.perturbation_response,
            "qualification_status": self.qualification_status,
        }


def make_run_id(fixture_id: str, seed: int) -> str:
    """Generate a stable run ID from fixture type and seed."""
    return f"{fixture_id}-seed{seed}"

