"""
Cognition Domain — Probe / Metric Proxy Functions
domains/self/model/analysis/probes.py

First-pass minimal probe functions for the cognition domain.

These are MEASUREMENT PROXIES — operational approximations of the
domain-local variables defined in domains/self/model/SPEC.md.

Each function is documented with:
- what it approximates
- the formula used
- known limitations / caveats

None of these are calibrated against a null corpus. All values are
provisional heuristics subject to revision as empirical data accumulates.

Design rules:
- All inputs and outputs use normalized [0, 1] ranges where applicable
- None inputs are handled gracefully (return None, not crash)
- These functions have no side effects — they are pure computations
- They do not own state; state is passed in from the fixture runner
"""
from __future__ import annotations

from typing import Optional
import math


# ---------------------------------------------------------------------------
# 1. Possibility-breadth estimate
# ---------------------------------------------------------------------------

def estimate_possibility_breadth(current: float, maximum: float) -> float:
    """
    Estimate possibility_breadth as a fraction of the maximum accessible space.

    Formula:
        breadth = current / maximum

    Interpretation:
        1.0 = fully unconstrained (all options available)
        0.0 = singular forced state (one option remaining)

    Args:
        current: current number/measure of accessible states or branches
        maximum: maximum number/measure at unconstrained state

    Returns:
        float in [0, 1]

    Limitations:
        Assumes accessible state measure is directly comparable to maximum.
        For discrete branching: use branch count. For continuous: use entropy.
    """
    if maximum <= 0:
        return 0.0
    return max(0.0, min(1.0, current / maximum))


# ---------------------------------------------------------------------------
# 2. Constraint-intensity estimate
# ---------------------------------------------------------------------------

def estimate_constraint_proxy(initial: float, current: float, maximum: float) -> float:
    """
    Estimate constraint_intensity as fractional reduction from initial breadth.

    Formula:
        constraint = (initial - current) / maximum

    Interpretation:
        0.0 = no constraint reduction has occurred
        1.0 = all space has been removed

    Args:
        initial: initial breadth measure (unconstrained baseline)
        current: current breadth measure
        maximum: total possible breadth measure

    Returns:
        float in [0, 1]

    Limitations:
        Does not measure rate of change (use a sliding window for that).
        Monotonically increases if constraint only tightens — captures
        accumulated constraint, not instantaneous intensity.
    """
    if maximum <= 0:
        return 0.0
    return max(0.0, min(1.0, (initial - current) / maximum))


# ---------------------------------------------------------------------------
# 3. Tension estimate
# ---------------------------------------------------------------------------

def estimate_tension(
    breadth_series: list[float],
    window: int = 10,
) -> float:
    """
    Estimate tension as accumulated unresolved constraint over a sliding window.

    Formula:
        tension = mean(constraint_delta) over last `window` steps
        where constraint_delta[t] = breadth[t-1] - breadth[t]  (positive = tightening)

    Normalized to [0, 1] by dividing by max possible per-step delta (1.0 / window).

    Interpretation:
        Rising tension indicates constraint is accumulating without collapse.
        High tension is a pre-collapse indicator candidate.

    Args:
        breadth_series: list of possibility_breadth values in time order
        window: number of steps to look back

    Returns:
        float in [0, 1]. Returns 0.0 if fewer than 2 steps available.

    Limitations:
        Window size is not calibrated. Current value (10) is a provisional default.
        Does not penalize tension that reverses (expansion after tightening).
    """
    if len(breadth_series) < 2:
        return 0.0

    recent = breadth_series[-window:]
    deltas = [max(0.0, recent[i - 1] - recent[i]) for i in range(1, len(recent))]
    if not deltas:
        return 0.0

    # Normalize: average per-step tightening as fraction of maximum possible
    mean_delta = sum(deltas) / len(deltas)
    return min(1.0, mean_delta * window)  # scale up so sustained tightening → high tension


# ---------------------------------------------------------------------------
# 4. Collapse detection
# ---------------------------------------------------------------------------

def detect_collapse(
    breadth_series: list[float],
    threshold: float = 0.20,
    min_magnitude: float = 0.20,
    lookback: int = 5,
) -> Optional[int]:
    """
    Detect the first collapse event in a breadth time series.

    A collapse is declared at step t if:
    1. breadth[t] < threshold  (crossed below floor)
    2. breadth drop from the mean of the prior `lookback` steps exceeds min_magnitude

    Returns the step index of the first qualifying collapse event, or None.

    Args:
        breadth_series: list of possibility_breadth values
        threshold: breadth floor below which a collapse is considered (provisional: 0.10)
        min_magnitude: minimum fractional drop required to count (provisional: 0.20)
        lookback: steps to use for pre-collapse baseline

    Returns:
        int: step index of first collapse, or None if no collapse detected

    Limitations:
        Threshold (0.10) and min_magnitude (0.20) are uncalibrated placeholders.
        Does not detect collapses in systems that never cross the threshold
        (DEFERRED_SUSPENDED goes undetected — by design; use tension for those).
    """
    for i in range(lookback, len(breadth_series)):
        current = breadth_series[i]
        if current >= threshold:
            continue
        pre_window = breadth_series[max(0, i - lookback): i]
        if not pre_window:
            continue
        pre_mean = sum(pre_window) / len(pre_window)
        magnitude = pre_mean - current
        if magnitude >= min_magnitude * pre_mean:
            return i
    return None


# ---------------------------------------------------------------------------
# 5. Post-collapse narrowing
# ---------------------------------------------------------------------------

def estimate_post_collapse_narrowing(
    breadth_series: list[float],
    collapse_step: int,
    post_window: int = 10,
) -> Optional[float]:
    """
    Estimate post_collapse_narrowing as fractional breadth reduction from
    pre-collapse mean to post-collapse mean.

    Formula:
        narrowing = (pre_mean - post_mean) / pre_mean

    Args:
        breadth_series: full breadth series
        collapse_step: step index of detected collapse
        post_window: how many steps after collapse to measure

    Returns:
        float in [0, 1], or None if collapse_step is out of range

    Limitations:
        Window size not calibrated. May overestimate for transient collapses.
    """
    if collapse_step is None or collapse_step >= len(breadth_series):
        return None

    lookback = 10
    pre = breadth_series[max(0, collapse_step - lookback): collapse_step]
    post = breadth_series[collapse_step: collapse_step + post_window]

    if not pre or not post:
        return None

    pre_mean = sum(pre) / len(pre)
    post_mean = sum(post) / len(post)

    if pre_mean <= 0:
        return None

    return max(0.0, min(1.0, (pre_mean - post_mean) / pre_mean))


# ---------------------------------------------------------------------------
# 6. Perturbation response
# ---------------------------------------------------------------------------

def estimate_perturbation_response(
    breadth_series: list[float],
    perturb_step: int,
    pre_window: int = 5,
    post_window: int = 10,
) -> Optional[float]:
    """
    Estimate signed perturbation_response as change in breadth from
    pre-perturbation mean to post-perturbation mean.

    Formula:
        response = post_mean - pre_mean
        (positive = expansion / recovery; negative = further constraint)

    Args:
        breadth_series: full breadth series
        perturb_step: step at which perturbation was injected
        pre_window: steps before perturbation for baseline
        post_window: steps after perturbation to measure

    Returns:
        float in [-1, 1], or None if perturb_step is out of range

    Limitations:
        Does not distinguish between perturbation-caused change and
        ongoing trend. Use with fixed pre/post windows to minimize confounding.
    """
    if perturb_step is None or perturb_step >= len(breadth_series):
        return None

    pre = breadth_series[max(0, perturb_step - pre_window): perturb_step]
    post = breadth_series[perturb_step: perturb_step + post_window]

    if not pre or not post:
        return None

    pre_mean = sum(pre) / len(pre)
    post_mean = sum(post) / len(post)

    return max(-1.0, min(1.0, post_mean - pre_mean))


# ---------------------------------------------------------------------------
# 7. DCP qualification status (mirrors DCPEvent.qualification_status)
# ---------------------------------------------------------------------------

def compute_qualification_status(
    has_possibility_proxy: bool,
    has_constraint_proxy: bool,
    has_tension_proxy: bool,
    has_collapse_proxy: bool,
    has_post_collapse: bool,
) -> str:
    """
    Compute the DCP qualification status for a run, mirroring DCPEvent logic.

    Returns:
        'FULL'         — all five components observable
        'UNCONFIRMED'  — missing tension only
        'INCOMPLETE'   — 3 or 4 components
        'INSUFFICIENT' — fewer than 3
    """
    components = [
        has_possibility_proxy,
        has_constraint_proxy,
        has_tension_proxy,
        has_collapse_proxy,
        has_post_collapse,
    ]
    present = sum(components)

    if present == 5:
        return "FULL"
    if present == 4 and not has_tension_proxy:
        return "UNCONFIRMED"
    if present >= 3:
        return "INCOMPLETE"
    return "INSUFFICIENT"


