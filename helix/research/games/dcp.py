"""
Games Domain — DCP Hook
domains/games/analysis/dcp.py

Translates a games-domain TrajectoryLog into a DCPEvent (schema: dcp_event_v2).

This is the games-domain counterpart to core/probes/math/analysis/dcp.py.
It takes the output of any fixture in domains/games/fixtures/ (pursuit, resource,
or null) and extracts the five DCP component proxies plus the v2 fields.

DESIGN:
    The games fixtures already compute per-step breadth/constraint/tension using
    the cognition domain probe functions. This adapter aggregates those per-step
    values into the event-level proxies that DCPEvent expects.

PROXIES:
    possibility_space_proxy  — initial breadth (always 1.0 for these fixtures; games
                                start with a fully open action set)
    constraint_proxy         — max constraint value observed across all steps
    tension_proxy            — peak tension value from the TrajectoryLog events
    collapse_proxy           — collapse sharpness from the breadth series
                                (using core.invariants.dcp.metrics.collapse_sharpness)
    post_collapse_narrowing  — from TrajectoryLog.collapse_step (probe-computed)

CONSTRAINT CLASS:
    pursuit fixture → 'external' (adversarial pursuer = external agent)
    resource fixture → 'internal' (budget depletion = self-imposed limit)
    null fixture → None (no constraint)

MORPHOLOGY:
    Taken directly from TrajectoryLog.final_morphology (cognition classifier).
    Labeled as 'provisional heuristic — not calibrated'.

CONFIDENCE CAP:
    Null fixture:     cap 0.10 (no meaningful signal)
    INCOMPLETE/UNCONFIRMED: cap 0.50
    FULL:             cap 0.75 (games domain is not yet calibrated against null corpus)

Layer relationships:
    domains/games/fixtures/sequential_decision.py  → fixture runners → TrajectoryLog
    domains/games/analysis/dcp.py     ← THIS FILE → DCPEvent (dcp_event_v2)
    core/invariants/dcp/event.py                   → DCPEvent schema
    core/invariants/dcp/metrics.py                 → collapse_sharpness, compute_dcp_score
    core/invariants/dcp/morphology.py              → CollapseMorphology enum
    domains/games/godot_engine/                    → real game data adapter (future)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists()
)
sys.path.insert(0, str(ROOT))

from core.invariants.dcp.event import DCPEvent
from core.invariants.dcp.metrics import collapse_sharpness, compute_dcp_score
from domains.self.analysis.trajectory import TrajectoryLog


def extract_dcp_event(log: TrajectoryLog) -> DCPEvent:
    """
    Build a DCPEvent (dcp_event_v2) from a games-domain TrajectoryLog.

    Args:
        log: TrajectoryLog produced by a games fixture runner
             (run_pursuit, run_resource, or run_null from sequential_decision.py)

    Returns:
        DCPEvent with:
            source_domain = 'games'
            qualification_status mirroring log.qualification_status
            collapse_proxy = None for null fixture; computed otherwise
    """
    breadth_series = [e.possibility_breadth for e in log.events]
    tension_series = [e.tension_proxy       for e in log.events]
    constraint_series = [e.constraint_proxy for e in log.events]

    # ── Possibility space ────────────────────────────────────────────────────
    # Initial breadth — always 1.0 for games fixtures (start fully open)
    possibility_space = breadth_series[0] if breadth_series else 1.0

    # ── Constraint proxy ─────────────────────────────────────────────────────
    # Max accumulated constraint across the run
    constraint = max(constraint_series) if constraint_series else 0.0

    # ── Tension proxy ────────────────────────────────────────────────────────
    # Peak tension from the per-step estimates
    tension = max(tension_series) if tension_series else 0.0

    # ── Collapse proxy ───────────────────────────────────────────────────────
    # Sharpness of the breadth drop — computed from the actual breadth time series.
    # Returns None for null fixture (no collapse, so sharpness ≈ 0 and uninformative).
    if log.collapse_step is not None and len(breadth_series) > 5:
        collapse = collapse_sharpness(breadth_series, window=5)
    else:
        collapse = None

    # ── Post-collapse narrowing ───────────────────────────────────────────────
    # Taken from the collapse step event (already computed by probe functions)
    post_narrowing: Optional[float] = None
    if log.collapse_step is not None:
        collapse_event = log.events[log.collapse_step]
        post_narrowing = collapse_event.post_collapse_narrowing

    # ── v2 fields ────────────────────────────────────────────────────────────
    morphology     = log.final_morphology
    constraint_class = _infer_constraint_class(log)

    # ── Composite score ───────────────────────────────────────────────────────
    dcp_score = compute_dcp_score(
        possibility_space=possibility_space,
        constraint=constraint,
        tension=tension,
        collapse=collapse,
        post_narrowing=post_narrowing,
    )

    # ── Confidence cap ────────────────────────────────────────────────────────
    is_null = log.fixture_id == "games_null"
    qual    = log.qualification_status

    if is_null:
        confidence = min(0.10, dcp_score * 0.15)
    elif qual == "FULL":
        confidence = min(0.75, dcp_score * 0.80)
    else:
        confidence = min(0.50, dcp_score * 0.60)

    # ── Build event ───────────────────────────────────────────────────────────
    return DCPEvent(
        source_domain           = "games",
        source_artifact         = log.run_id,
        event_id                = f"games.dcp.{log.fixture_id}.{log.run_id}",
        possibility_space_proxy = round(float(possibility_space), 4),
        constraint_proxy        = round(float(constraint), 4),
        tension_proxy           = round(float(tension), 4) if tension > 0 else None,
        collapse_proxy          = round(float(collapse), 4) if collapse is not None else None,
        post_collapse_narrowing = round(float(post_narrowing), 4) if post_narrowing is not None else None,
        collapse_morphology     = morphology,
        constraint_class        = constraint_class,
        confidence              = round(confidence, 4),
        calibration_status      = "provisional",
        notes=(
            f"Games fixture '{log.fixture_id}' run '{log.run_id}'. "
            f"Steps: {len(log.events)}. "
            f"Collapse at step: {log.collapse_step}. "
            f"qualification_status='{qual}'. "
            f"Morphology='{morphology}' (heuristic — cognition classifier). "
            f"constraint_class='{constraint_class}'. "
            f"Games domain not yet calibrated against null corpus. "
            f"Real game data path: domains/games/godot_engine/ (not yet wired)."
        ),
        domain_metadata={
            "fixture_id":        log.fixture_id,
            "fixture_type":      log.fixture_type,
            "run_id":            log.run_id,
            "n_steps":           len(log.events),
            "collapse_step":     log.collapse_step,
            "qualification":     qual,
            "initial_breadth":   breadth_series[0] if breadth_series else None,
            "final_breadth":     breadth_series[-1] if breadth_series else None,
            "max_tension":       max(tension_series) if tension_series else None,
            "max_constraint":    max(constraint_series) if constraint_series else None,
            "dcp_composite":     round(dcp_score, 4),
            "config":            log.config,
        },
    )


def _infer_constraint_class(log: TrajectoryLog) -> Optional[str]:
    """
    Infer constraint class from fixture metadata.
    Uses the state_summary of the first event if available.
    """
    if not log.events:
        return None
    summary = log.events[0].state_summary or {}
    cc = summary.get("constraint_class")
    if cc == "none" or cc is None:
        return None
    return cc
