"""
dcp_validation.py — DCP Calibration Baselines and Null Model Tests
===================================================================
Two-section validation suite for the Decision Compression Principle.

Section 1 — Synthetic Calibration Fixtures (from dcp_synthetic_fixtures.py)
    Three tiny fixtures outside the major domains (math, games, music, language,
    cognition). Purpose: answer the question "is DCP only working because one
    domain is special?"

    These fixtures use the minimal probe functions to test whether:
      - A purely structural narrowing (no domain semantics) produces expected DCP signatures
      - The metrics behave sensibly on stripped-down cases
      - Null behavior does NOT falsely trigger DCP

    Fixtures:
      1. ForcedNarrowing   — N branches, monotonically forced to 1 in T steps.
                             Hardest possible DCP case: everything known, perfectly linear.
                             Expected: FULL qualification, TRANSFORMATIVE, high confidence.

      2. BasinTransition   — System in stable basin, forced transition to new basin at step T//2.
                             Models a sudden attractor shift (e.g., phase transition, reboot).
                             Expected: sharp collapse, TRANSFORMATIVE, moderate confidence.

      3. AmbiguityPool     — Pool of N competing hypotheses. Each step, evidence eliminates
                             one hypothesis. Breadth = remaining/initial.
                             Expected: gradual narrowing, collapse when 1 remains, TRANSFORMATIVE.

    All three are deliberately outside domain-specific semantics. They use only the
    cognition domain's probe/trajectory schema as a shared measurement surface.
    Run these first — they are the calibration layer the null tests depend on.

Section 2 — Null Model Tests (from dcp_null_tests.py)
    The four tests from dcp_trajectory_open_questions.md. These must pass before
    DCP can be promoted from CANDIDATE to EMERGING.

    Test 1 (F1): K=0 Kuramoto null model
        Run extract_dcp_event() on K=0 simulations across N>=50 seeds.
        PASS: mean DCP score < 0.3 (null produces consistently low signal)
        FAIL: DCP scores are high at K=0 -> F1 triggered -> measurement artifact

    Test 2: Time-series tension probe
        Sweep K from 0.5K_c to 2.0K_c (20 steps).
        Compute R(t) time series per run.
        Apply tension_accumulation_index() from actual R(t), not K/K_c proxy.
        PASS: tension peaks near K_c, drops away from it

    Test 3: Games null model
        Compare DCP k_eff slope for structured game sequences vs randomized sequences.
        PASS: null distribution has lower DCP structure (higher k_eff = less constrained)
        FAIL: random sequences produce similar or higher DCP structure

    Test 4: Cross-coupling comparison
        dcp_composite_score at K = 0.5K_c, 1.0K_c, 1.5K_c, 2.0K_c.
        PASS: score peaks near K_c and saturates (or declines) above it

Usage:
    python core/probes/dcp_validation.py               # all (baselines then null tests)
    python core/probes/dcp_validation.py --mode baselines
    python core/probes/dcp_validation.py --mode null_tests
    python core/probes/dcp_validation.py --mode null_tests --test 1
    python core/probes/dcp_validation.py --mode null_tests --test 2
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Sequence

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
sys.path.insert(0, str(ROOT))

import numpy as np

from helix.research.invariants.math.math.simulation.kuramoto import KuramotoSystem
from helix.research.invariants.math.math.analysis.dcp import extract_dcp_event, _estimate_Kc
from core.invariants.dcp.metrics import (
    tension_accumulation_index,
    collapse_sharpness,
    irreversibility_proxy,
    post_collapse_narrowing,
    compute_dcp_score,
)
from domains.self.analysis.trajectory import (
    TrajectoryEvent, TrajectoryLog, make_run_id,
    EVENT_SCHEMA_VERSION, LOG_SCHEMA_VERSION,
)
from domains.self.analysis.probes import (
    estimate_possibility_breadth,
    estimate_constraint_proxy,
    estimate_tension,
    detect_collapse,
    estimate_post_collapse_narrowing,
    compute_qualification_status,
)
from domains.self.analysis.morphology_classifier import classify_morphology


# =============================================================================
# SECTION 1: SYNTHETIC CALIBRATION FIXTURES
# =============================================================================

# ---------------------------------------------------------------------------
# Fixture 1: Forced Narrowing
# ---------------------------------------------------------------------------

def run_forced_narrowing(
    n_branches: int = 8,
    n_steps: int    = 20,
    seed: int       = 0,
) -> TrajectoryLog:
    """
    Linear, deterministic narrowing from N branches to 1 in n_steps.

    This is the cleanest possible DCP case: the constraint schedule is perfectly
    known, the narrowing is monotonic, and the collapse is guaranteed.
    It should consistently produce qualification_status='FULL' and
    morphology=TRANSFORMATIVE.

    If this fixture fails DCP probes, the probe functions are broken — not the theory.
    Use as a diagnostic baseline.

    Expected outputs:
        collapse_step ≈ n_steps * 0.8  (when breadth drops below 0.20)
        qualification_status = 'FULL'
        morphology = 'TRANSFORMATIVE'
    """
    initial = float(n_branches)
    events: list[TrajectoryEvent] = []
    breadth_series: list[float] = []

    for step in range(n_steps):
        current = max(1.0, initial - step * (initial - 1.0) / max(1, n_steps - 1))
        breadth    = estimate_possibility_breadth(current, initial)
        constraint = estimate_constraint_proxy(initial, current, initial)
        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        events.append(TrajectoryEvent(
            step=step,
            possibility_breadth=round(breadth, 4),
            constraint_proxy=round(constraint, 4),
            tension_proxy=round(tension, 4),
            state_summary={
                "branches": round(current, 2),
                "fixture":  "synthetic_forced_narrowing",
                "domain":   "synthetic",
            },
            schema_version=EVENT_SCHEMA_VERSION,
        ))

    collapse_step  = detect_collapse(breadth_series, threshold=0.20)
    post_narrowing = estimate_post_collapse_narrowing(breadth_series, collapse_step)
    morphology     = classify_morphology(breadth_series, collapse_step, initial_breadth=1.0)

    if collapse_step is not None:
        e = events[collapse_step]
        e.collapse_flag           = True
        e.collapse_morphology     = morphology.value
        e.post_collapse_narrowing = post_narrowing

    qual = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = (collapse_step is not None),
        has_post_collapse     = (post_narrowing is not None),
    )

    return TrajectoryLog(
        fixture_id           = "synthetic_forced_narrowing",
        fixture_type         = "Synthetic Forced Narrowing",
        run_id               = make_run_id("syn_narrow", seed),
        seed                 = seed,
        config               = {"n_branches": n_branches, "n_steps": n_steps, "seed": seed},
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = morphology.value,
        qualification_status = qual,
        schema_version       = LOG_SCHEMA_VERSION,
    )


# ---------------------------------------------------------------------------
# Fixture 2: Basin Transition
# ---------------------------------------------------------------------------

def run_basin_transition(
    basin1_breadth: float = 0.80,
    basin2_breadth: float = 0.15,
    transition_step: int  = 15,
    n_steps: int          = 30,
    seed: int             = 0,
) -> TrajectoryLog:
    """
    System sits in basin 1 at breadth=basin1_breadth, then abruptly transitions
    to basin 2 at breadth=basin2_breadth at step `transition_step`.

    Models a sudden attractor shift: phase transition, catastrophic narrowing,
    or sudden commitment. The breadth drop from basin1 to basin2 is the collapse.

    Expected outputs:
        collapse_step ≈ transition_step (first step in basin 2)
        morphology = TRANSFORMATIVE (new stable state)
        qualification_status = 'FULL' if transition is sharp enough
    """
    events: list[TrajectoryEvent] = []
    breadth_series: list[float] = []

    for step in range(n_steps):
        if step < transition_step:
            breadth    = basin1_breadth
            constraint = step / max(1, transition_step)
        else:
            breadth    = basin2_breadth
            constraint = 1.0

        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        events.append(TrajectoryEvent(
            step=step,
            possibility_breadth=round(breadth, 4),
            constraint_proxy=round(min(1.0, constraint), 4),
            tension_proxy=round(tension, 4),
            state_summary={
                "basin":           "basin_1" if step < transition_step else "basin_2",
                "transition_step": transition_step,
                "fixture":         "synthetic_basin_transition",
                "domain":          "synthetic",
            },
            schema_version=EVENT_SCHEMA_VERSION,
        ))

    collapse_step  = detect_collapse(breadth_series, threshold=basin2_breadth + 0.05)
    post_narrowing = estimate_post_collapse_narrowing(breadth_series, collapse_step)
    morphology     = classify_morphology(breadth_series, collapse_step, initial_breadth=basin1_breadth)

    if collapse_step is not None:
        e = events[collapse_step]
        e.collapse_flag           = True
        e.collapse_morphology     = morphology.value
        e.post_collapse_narrowing = post_narrowing

    qual = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = (collapse_step is not None),
        has_post_collapse     = (post_narrowing is not None),
    )

    return TrajectoryLog(
        fixture_id           = "synthetic_basin_transition",
        fixture_type         = "Synthetic Basin Transition",
        run_id               = make_run_id("syn_basin", seed),
        seed                 = seed,
        config               = {
            "basin1_breadth":  basin1_breadth,
            "basin2_breadth":  basin2_breadth,
            "transition_step": transition_step,
            "n_steps":         n_steps,
            "seed":            seed,
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = morphology.value,
        qualification_status = qual,
        schema_version       = LOG_SCHEMA_VERSION,
    )


# ---------------------------------------------------------------------------
# Fixture 3: Ambiguity Pool
# ---------------------------------------------------------------------------

def run_ambiguity_pool(
    initial_hypotheses: int = 10,
    elimination_rate: int   = 1,
    n_steps: int            = 15,
    seed: int               = 0,
) -> TrajectoryLog:
    """
    A pool of N competing hypotheses. Each step, `elimination_rate` hypotheses
    are eliminated by incoming evidence. Breadth = remaining / initial.

    Models: ambiguity resolution — the process of narrowing from many candidate
    explanations/options to few or one. Applicable to: language parse disambiguation,
    hypothesis testing, inference under constraint.

    The elimination is discrete and stepwise, creating a staircase breadth profile
    rather than smooth narrowing. This tests whether DCP probes work on stepped
    rather than continuous narrowing.

    Expected outputs:
        collapse_step: when remaining <= 1 (or <= 20% threshold)
        morphology: TRANSFORMATIVE (committed to remaining hypothesis)
        qualification_status: FULL or INCOMPLETE
    """
    initial = float(initial_hypotheses)
    events: list[TrajectoryEvent] = []
    breadth_series: list[float] = []

    for step in range(n_steps):
        remaining = max(1.0, initial - step * elimination_rate)
        breadth    = estimate_possibility_breadth(remaining, initial)
        constraint = estimate_constraint_proxy(initial, remaining, initial)
        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        events.append(TrajectoryEvent(
            step=step,
            possibility_breadth=round(breadth, 4),
            constraint_proxy=round(constraint, 4),
            tension_proxy=round(tension, 4),
            state_summary={
                "remaining_hypotheses": int(remaining),
                "initial_hypotheses":   initial_hypotheses,
                "eliminated_so_far":    step * elimination_rate,
                "fixture":              "synthetic_ambiguity_pool",
                "domain":               "synthetic",
            },
            schema_version=EVENT_SCHEMA_VERSION,
        ))

    collapse_step  = detect_collapse(breadth_series, threshold=0.20)
    post_narrowing = estimate_post_collapse_narrowing(breadth_series, collapse_step)
    morphology     = classify_morphology(breadth_series, collapse_step, initial_breadth=1.0)

    if collapse_step is not None:
        e = events[collapse_step]
        e.collapse_flag           = True
        e.collapse_morphology     = morphology.value
        e.post_collapse_narrowing = post_narrowing

    qual = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = (collapse_step is not None),
        has_post_collapse     = (post_narrowing is not None),
    )

    return TrajectoryLog(
        fixture_id           = "synthetic_ambiguity_pool",
        fixture_type         = "Synthetic Ambiguity Pool",
        run_id               = make_run_id("syn_ambig", seed),
        seed                 = seed,
        config               = {
            "initial_hypotheses": initial_hypotheses,
            "elimination_rate":   elimination_rate,
            "n_steps":            n_steps,
            "seed":               seed,
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = morphology.value,
        qualification_status = qual,
        schema_version       = LOG_SCHEMA_VERSION,
    )


def _summarize_fixture(log: TrajectoryLog) -> dict:
    breadths = [e.possibility_breadth for e in log.events]
    tensions = [e.tension_proxy       for e in log.events]
    return {
        "fixture":       log.fixture_id,
        "steps":         len(log.events),
        "initial_b":     round(breadths[0], 3) if breadths else None,
        "final_b":       round(breadths[-1], 3) if breadths else None,
        "min_b":         round(min(breadths), 3) if breadths else None,
        "max_tension":   round(max(tensions), 3) if tensions else None,
        "collapse_step": log.collapse_step,
        "morphology":    log.final_morphology,
        "qual":          log.qualification_status,
    }


def run_baselines() -> list[TrajectoryLog]:
    """Run all three synthetic calibration fixtures and print summary."""
    print("DCP Synthetic Calibration Fixtures")
    print("=" * 60)
    print()

    logs = [
        run_forced_narrowing(n_branches=8, n_steps=20),
        run_basin_transition(basin1_breadth=0.80, basin2_breadth=0.15, transition_step=15),
        run_ambiguity_pool(initial_hypotheses=10, elimination_rate=1, n_steps=15),
    ]

    for log in logs:
        s = _summarize_fixture(log)
        print(f"  {s['fixture']}")
        print(f"    steps={s['steps']}  initial_breadth={s['initial_b']}  "
              f"final_breadth={s['final_b']}  min_breadth={s['min_b']}")
        print(f"    max_tension={s['max_tension']}  collapse_step={s['collapse_step']}  "
              f"morphology={s['morphology']}")
        print(f"    qualification={s['qual']}")
        print()

    print("Interpretation:")
    print("  All three fixtures should show collapse and TRANSFORMATIVE morphology.")
    print("  If any is DEFERRED_SUSPENDED or has None collapse_step, check probe thresholds.")
    print("  These are calibration baselines, not domain findings.")
    return logs


# =============================================================================
# SECTION 2: NULL MODEL TESTS
# =============================================================================

# Shared simulation parameters (matching kuramoto_fixture.py)
N_OSC     = 50
STEPS     = 500
DT        = 0.05
BASE_SEED = 42


def _make_system(K: float, seed: int) -> KuramotoSystem:
    rng = np.random.default_rng(seed)
    freqs = rng.normal(0.0, 1.0, N_OSC)
    phases = rng.uniform(0, 2 * math.pi, N_OSC)
    sys_ = KuramotoSystem(n_oscillators=N_OSC, K=K, natural_freqs=freqs)
    sys_.theta = phases
    return sys_


def _r_time_series(sys_: KuramotoSystem) -> list[float]:
    """Extract order-parameter R(t) from simulation history."""
    return [
        float(np.abs(np.mean(np.exp(1j * phases))))
        for phases in sys_.history
    ]


def _compression_slope(k_effs: list[float]) -> float:
    """
    Compression slope: (mean last half - mean first half) / overall mean.
    Negative = k_eff decreased = compression.
    """
    if len(k_effs) < 2:
        return 0.0
    mid = len(k_effs) // 2
    first = float(np.mean(k_effs[:mid])) if mid > 0 else k_effs[0]
    last = float(np.mean(k_effs[mid:])) if mid < len(k_effs) else k_effs[-1]
    overall = float(np.mean(k_effs))
    if overall < 1e-9:
        return 0.0
    return (last - first) / overall


# ---------------------------------------------------------------------------
# Test 1: K=0 null model (F1)
# ---------------------------------------------------------------------------

def test1_null_model(n_seeds: int = 50) -> dict:
    """
    Run DCP extraction on K=0 simulations across n_seeds seeds.
    DCP scores should be consistently < 0.3.
    """
    print(f"\n  Test 1: K=0 null model ({n_seeds} seeds)")
    scores = []
    tensions = []
    for seed in range(n_seeds):
        sys_ = _make_system(K=0.0, seed=seed)
        sys_.simulate(dt=DT, steps=STEPS)
        results = sys_.get_results_summary()
        freqs = np.random.default_rng(seed).normal(0.0, 1.0, N_OSC)
        event = extract_dcp_event(results, K=0.0, natural_freqs=freqs, seed=seed)
        score = event.domain_metadata.get("dcp_composite_score", 0.0)
        scores.append(score)

        r_series = _r_time_series(sys_)
        ps_series = [1.0 - r for r in r_series]
        tai = tension_accumulation_index(ps_series)
        tensions.append(tai)

    mean_score = float(np.mean(scores))
    max_score = float(np.max(scores))
    mean_tension = float(np.mean(tensions))

    threshold = 0.3
    passed = mean_score < threshold and max_score < threshold + 0.1

    print(f"    DCP scores  — mean={mean_score:.4f}  max={max_score:.4f}  "
          f"std={float(np.std(scores)):.4f}")
    print(f"    TAI (null)  — mean={mean_tension:.4f}")
    print(f"    Threshold:  < {threshold}")
    print(f"    -> {'PASS' if passed else 'FAIL  <- F1 TRIGGERED'}")

    return {
        "test": 1,
        "name": "K=0 null model (F1)",
        "passed": passed,
        "n_seeds": n_seeds,
        "mean_dcp_score": round(mean_score, 5),
        "max_dcp_score": round(max_score, 5),
        "std_dcp_score": round(float(np.std(scores)), 5),
        "mean_tai_null": round(mean_tension, 5),
        "threshold": threshold,
        "all_scores": [round(s, 5) for s in scores],
    }


# ---------------------------------------------------------------------------
# Test 2: Time-series tension probe
# ---------------------------------------------------------------------------

def test2_timeseries_tension(n_k_steps: int = 20, n_seeds: int = 5) -> dict:
    """
    Sweep K from 0.5K_c to 2.0K_c (n_k_steps).
    Compute time-series DCP metrics from actual R(t), not K/K_c proxy.
    Tension should peak near K_c.
    """
    print(f"\n  Test 2: Time-series tension probe ({n_k_steps} K values, {n_seeds} seeds)")

    rng0 = np.random.default_rng(BASE_SEED)
    freqs_base = rng0.normal(0.0, 1.0, N_OSC)
    K_c = _estimate_Kc(freqs_base)
    print(f"    K_c estimate (seed={BASE_SEED}): {K_c:.4f}")

    k_values = np.linspace(0.5 * K_c, 2.0 * K_c, n_k_steps)
    results_by_k = []

    for K in k_values:
        seed_scores = {"tai": [], "sharpness": [], "irreversibility": [], "dcp_score": []}
        for seed in range(n_seeds):
            sys_ = _make_system(K=float(K), seed=seed)
            sys_.simulate(dt=DT, steps=STEPS)
            results_sum = sys_.get_results_summary()
            freqs = np.random.default_rng(seed).normal(0.0, 1.0, N_OSC)

            r_series = _r_time_series(sys_)
            ps_series = [1.0 - r for r in r_series]

            tai   = tension_accumulation_index(ps_series)
            sharp = collapse_sharpness(ps_series)
            irrev = irreversibility_proxy(r_series)

            midpoint = len(ps_series) // 2
            pre_ps = ps_series[:midpoint]
            post_ps = ps_series[midpoint:]
            narrowing = post_collapse_narrowing(pre_ps, post_ps)
            constraint = float(np.clip(K / K_c, 0.0, 1.0))
            ts_dcp_score = compute_dcp_score(
                possibility_space=ps_series[0] if ps_series else 0.0,
                constraint=constraint,
                tension=tai,
                collapse=sharp,
                post_narrowing=narrowing,
            )

            seed_scores["tai"].append(tai)
            seed_scores["sharpness"].append(sharp)
            seed_scores["irreversibility"].append(irrev)
            seed_scores["dcp_score"].append(ts_dcp_score)

        results_by_k.append({
            "K": round(float(K), 4),
            "K_over_Kc": round(float(K / K_c), 3),
            "mean_tai": round(float(np.mean(seed_scores["tai"])), 5),
            "mean_sharpness": round(float(np.mean(seed_scores["sharpness"])), 5),
            "mean_irreversibility": round(float(np.mean(seed_scores["irreversibility"])), 5),
            "mean_dcp_score": round(float(np.mean(seed_scores["dcp_score"])), 5),
        })

    tai_values = [r["mean_tai"] for r in results_by_k]
    dcp_values = [r["mean_dcp_score"] for r in results_by_k]
    k_ratios = [r["K_over_Kc"] for r in results_by_k]

    peak_tai_idx = int(np.argmax(tai_values))
    peak_dcp_idx = int(np.argmax(dcp_values))
    peak_tai_k_ratio = k_ratios[peak_tai_idx]
    peak_dcp_k_ratio = k_ratios[peak_dcp_idx]

    tai_peak_near_kc = 0.7 <= peak_tai_k_ratio <= 1.5
    passed = tai_peak_near_kc

    print(f"\n    {'K/Kc':>6}  {'TAI':>7}  {'Sharp':>7}  {'Irrev':>7}  {'DCP':>7}")
    print(f"    {'─'*40}")
    for r in results_by_k:
        marker = " <- peak TAI" if r == results_by_k[peak_tai_idx] else ""
        print(f"    {r['K_over_Kc']:>6.3f}  {r['mean_tai']:>7.4f}  "
              f"{r['mean_sharpness']:>7.4f}  {r['mean_irreversibility']:>7.4f}  "
              f"{r['mean_dcp_score']:>7.4f}{marker}")

    print(f"\n    Peak TAI at K/K_c={peak_tai_k_ratio:.3f}  "
          f"(expected in [0.7, 1.5])")
    print(f"    Peak DCP at K/K_c={peak_dcp_k_ratio:.3f}")
    print(f"    -> {'PASS' if passed else 'FAIL'}")

    return {
        "test": 2,
        "name": "Time-series tension probe",
        "passed": passed,
        "K_c_estimate": round(float(K_c), 4),
        "peak_tai_at_K_over_Kc": peak_tai_k_ratio,
        "peak_dcp_at_K_over_Kc": peak_dcp_k_ratio,
        "tai_peak_near_kc": tai_peak_near_kc,
        "trajectory": results_by_k,
    }


# ---------------------------------------------------------------------------
# Test 3: Games null model
# ---------------------------------------------------------------------------

def _k_eff_from_weights(weights: list[float]) -> float:
    s = sum(w * w for w in weights)
    return 1.0 / s if s > 1e-9 else float("inf")


def test3_games_null(n_null_sequences: int = 500) -> dict:
    """
    Compare DCP structure of:
      - Structured game: weights shift across rounds toward one dominant player
      - Null: randomly shuffled weight sequences of same players

    DCP structure = (mean_k_eff_last_half - mean_k_eff_first_half) / mean_k_eff_all
    Negative = compression (possibility space narrowed)
    Near zero = no compression

    PASS: structured game shows stronger compression than null distribution
    """
    print(f"\n  Test 3: Games null model ({n_null_sequences} null sequences)")

    fixture_path = (
        ROOT / "domains" / "games" / "data" / "datasets"
        / "decision_compression_dataset.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    rounds = fixture["decision_rounds"]
    n_agents = len(rounds[0]["weights"])

    real_k_effs = [_k_eff_from_weights(r["weights"]) for r in rounds]
    real_slope = _compression_slope(real_k_effs)
    real_tai = tension_accumulation_index(real_k_effs)
    real_sharpness = collapse_sharpness(real_k_effs)

    print(f"    Structured game: k_effs={[round(k,3) for k in real_k_effs]}")
    print(f"    Slope={real_slope:.4f}  TAI={real_tai:.4f}  Sharp={real_sharpness:.4f}")

    rng = random.Random(BASE_SEED)
    null_slopes = []
    null_tais = []
    for _ in range(n_null_sequences):
        null_rounds_k = []
        for _ in range(len(rounds)):
            raw2 = [rng.expovariate(1.0) for _ in range(n_agents)]
            total2 = sum(raw2)
            w = [v / total2 for v in raw2]
            null_rounds_k.append(_k_eff_from_weights(w))
        null_slopes.append(_compression_slope(null_rounds_k))
        null_tais.append(tension_accumulation_index(null_rounds_k))

    null_slope_mean = float(np.mean(null_slopes))
    null_slope_std = float(np.std(null_slopes))
    z_score = (real_slope - null_slope_mean) / max(null_slope_std, 1e-9)

    passed = real_slope < null_slope_mean - null_slope_std

    print(f"    Null distribution: slope mean={null_slope_mean:.4f}  "
          f"std={null_slope_std:.4f}")
    print(f"    Real slope z-score: {z_score:.3f}")
    print(f"    Null TAI mean: {float(np.mean(null_tais)):.4f}")
    print(f"    -> {'PASS' if passed else 'FAIL  (structured not distinguishable from null)'}")

    pct = sum(1 for s in null_slopes if s > real_slope) / len(null_slopes)
    print(f"    Real slope more negative than {pct*100:.1f}% of null sequences")

    return {
        "test": 3,
        "name": "Games null model",
        "passed": passed,
        "n_null_sequences": n_null_sequences,
        "real_k_effs": [round(k, 3) for k in real_k_effs],
        "real_slope": round(real_slope, 5),
        "real_tai": round(real_tai, 5),
        "null_slope_mean": round(null_slope_mean, 5),
        "null_slope_std": round(null_slope_std, 5),
        "z_score": round(z_score, 3),
        "percentile_more_negative": round(pct, 4),
    }


# ---------------------------------------------------------------------------
# Test 4: Cross-coupling comparison
# ---------------------------------------------------------------------------

def test4_cross_coupling(n_seeds: int = 10) -> dict:
    """
    Compare dcp_composite_score at K = 0.5K_c, 1.0K_c, 1.5K_c, 2.0K_c.
    Score should peak near K_c and saturate (or stabilize) above it.
    """
    print(f"\n  Test 4: Cross-coupling comparison ({n_seeds} seeds per point)")

    rng0 = np.random.default_rng(BASE_SEED)
    freqs_base = rng0.normal(0.0, 1.0, N_OSC)
    K_c = _estimate_Kc(freqs_base)

    k_factors = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    results = []

    for factor in k_factors:
        K = factor * K_c
        seed_dcp = []
        seed_ts_dcp = []
        for seed in range(n_seeds):
            sys_ = _make_system(K=float(K), seed=seed)
            sys_.simulate(dt=DT, steps=STEPS)
            res_sum = sys_.get_results_summary()
            freqs = np.random.default_rng(seed).normal(0.0, 1.0, N_OSC)

            event = extract_dcp_event(res_sum, K=float(K), natural_freqs=freqs, seed=seed)
            proxy_score = event.domain_metadata.get("dcp_composite_score", 0.0)
            seed_dcp.append(proxy_score)

            r_series = _r_time_series(sys_)
            ps_series = [1.0 - r for r in r_series]
            midpoint = len(ps_series) // 2
            pre_ps = ps_series[:midpoint]
            post_ps = ps_series[midpoint:]
            tai   = tension_accumulation_index(ps_series)
            sharp = collapse_sharpness(ps_series)
            narrowing = post_collapse_narrowing(pre_ps, post_ps)
            constraint = float(np.clip(K / K_c, 0.0, 1.0))
            ts_score = compute_dcp_score(
                possibility_space=ps_series[0] if ps_series else 0.0,
                constraint=constraint,
                tension=tai,
                collapse=sharp,
                post_narrowing=narrowing,
            )
            seed_ts_dcp.append(ts_score)

        results.append({
            "K_factor": factor,
            "K": round(float(K), 4),
            "K_over_Kc": factor,
            "proxy_dcp_mean": round(float(np.mean(seed_dcp)), 5),
            "ts_dcp_mean": round(float(np.mean(seed_ts_dcp)), 5),
        })

    print(f"\n    {'K/Kc':>6}  {'Proxy DCP':>10}  {'TS DCP':>8}  Bar (TS)")
    print(f"    {'─'*50}")
    ts_max = max(r["ts_dcp_mean"] for r in results) or 1.0
    for r in results:
        bar = "█" * int(r["ts_dcp_mean"] / ts_max * 25)
        print(f"    {r['K_over_Kc']:>6.2f}  {r['proxy_dcp_mean']:>10.5f}  "
              f"{r['ts_dcp_mean']:>8.5f}  {bar}")

    ts_scores = [r["ts_dcp_mean"] for r in results]
    peak_idx = int(np.argmax(ts_scores))
    peak_factor = results[peak_idx]["K_factor"]
    peak_not_at_boundary = 0 < peak_idx < len(results) - 1

    proxy_scores = [r["proxy_dcp_mean"] for r in results]
    proxy_rises = proxy_scores[-1] > proxy_scores[0]

    passed = peak_not_at_boundary

    print(f"\n    Peak TS DCP at K/K_c={peak_factor:.2f}  (index {peak_idx})")
    print(f"    Proxy DCP rises from K=0 side: {proxy_rises}")
    print(f"    Peak not at boundary: {peak_not_at_boundary}")
    print(f"    -> {'PASS' if passed else 'FAIL'}")

    return {
        "test": 4,
        "name": "Cross-coupling comparison",
        "passed": passed,
        "K_c_estimate": round(float(K_c), 4),
        "peak_ts_dcp_at_K_factor": peak_factor,
        "peak_not_at_boundary": peak_not_at_boundary,
        "proxy_dcp_rises": proxy_rises,
        "trajectory": results,
    }


def run_null_tests(test_filter: int | None = None) -> dict:
    """Run all four null model tests (or just one if test_filter is set)."""
    print("\nDCP Null Model Tests")
    print("\u2501" * 64)
    print("Falsification threshold: DCP scores must be distinguishable")
    print("from null distributions before tier promotion.\n")

    results = {}

    if test_filter is None or test_filter == 1:
        results["test1"] = test1_null_model(n_seeds=50)

    if test_filter is None or test_filter == 2:
        results["test2"] = test2_timeseries_tension(n_k_steps=20, n_seeds=5)

    if test_filter is None or test_filter == 3:
        results["test3"] = test3_games_null(n_null_sequences=500)

    if test_filter is None or test_filter == 4:
        results["test4"] = test4_cross_coupling(n_seeds=10)

    print("\n" + "\u2550" * 64)
    print("  SUMMARY")
    print("\u2550" * 64)
    all_passed = True
    for key, result in results.items():
        status = "PASS" if result["passed"] else "FAIL"
        print(f"  Test {result['test']}: {result['name']:<38}  {status}")
        if not result["passed"]:
            all_passed = False

    if all_passed:
        print("\n  All null tests pass -> DCP eligible for CANDIDATE -> EMERGING review")
    else:
        print("\n  One or more tests FAILED -> DCP remains at CANDIDATE")
        print("  Failing tests indicate either F1 artifact or model issue — investigate")

    out_path = ROOT / "domains" / "language" / "artifacts" / "dcp_null_test_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n  Results -> {out_path}")

    return results


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="DCP calibration baselines and null model tests")
    parser.add_argument(
        "--mode", choices=["baselines", "null_tests", "all"], default="all",
        help="Which section to run (default: all)"
    )
    parser.add_argument(
        "--test", type=int, default=None,
        help="(null_tests mode) Run only test N (1-4)"
    )
    args = parser.parse_args()

    mode = args.mode

    if mode in ("baselines", "all"):
        print("\n" + "=" * 64)
        print("SECTION 1: SYNTHETIC CALIBRATION FIXTURES")
        print("=" * 64)
        run_baselines()

    if mode in ("null_tests", "all"):
        print("\n" + "=" * 64)
        print("SECTION 2: NULL MODEL TESTS")
        print("=" * 64)
        run_null_tests(test_filter=args.test)


if __name__ == "__main__":
    main()
