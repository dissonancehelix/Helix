"""
DCP Metrics — core/invariants/dcp/metrics.py
============================================
First-pass metric definitions for Decision Compression event detection.

These are MEASUREMENT PROXIES, not the invariant itself.
They are domain-agnostic interfaces; each domain hook implements
the translation from domain signals into these metrics.

Rules:
- All inputs should be normalized to [0.0, 1.0] before calling these
- None inputs are permitted; will propagate gracefully
- These do not validate whether a DCP event is real — they compute
  metric values from already-extracted proxy signals

Cross-domain normalization: NOT YET IMPLEMENTED.
Each domain currently uses its own proxy formula. A cross-domain
normalization procedure is a known open question (see DCP doc §12).
"""
from __future__ import annotations

from typing import Optional
import numpy as np


# ---------------------------------------------------------------------------
# Individual component metrics
# ---------------------------------------------------------------------------

def possibility_space_entropy(state_probabilities: list[float]) -> float:
    """
    Shannon entropy of a reachable-state distribution, normalized to [0, 1].

    Higher = more open possibility space.
    H_norm = H / H_max = H / log2(N)

    Args:
        state_probabilities: list of probabilities summing to ~1.0

    Returns:
        Normalized entropy in [0.0, 1.0]. Returns 0.0 if degenerate input.
    """
    p = np.array(state_probabilities, dtype=float)
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    h = float(-np.sum(p * np.log2(p)))
    h_max = np.log2(len(p))
    if h_max < 1e-9:
        return 0.0
    return float(np.clip(h / h_max, 0.0, 1.0))


def collapse_sharpness(series: list[float], window: int = 5) -> float:
    """
    Estimate collapse sharpness from a time series of possibility-space values.

    Sharpness = max rate of decrease in the series over any window of `window` steps.
    Normalized to [0.0, 1.0] relative to the range of the series.

    Higher = sharper collapse.

    Args:
        series: time series of possibility-space proxy values (e.g. policy entropy over time)
        window: step window for rate estimation

    Returns:
        Sharpness score in [0.0, 1.0]. Returns 0.0 if insufficient data.
    """
    arr = np.array(series, dtype=float)
    if len(arr) < window + 1:
        return 0.0

    series_range = arr.max() - arr.min()
    if series_range < 1e-9:
        return 0.0

    max_decrease = 0.0
    for i in range(len(arr) - window):
        decrease = arr[i] - arr[i + window]
        if decrease > max_decrease:
            max_decrease = decrease

    return float(np.clip(max_decrease / series_range, 0.0, 1.0))


def tension_accumulation_index(series: list[float], pre_window_fraction: float = 0.3) -> float:
    """
    Estimate tension accumulation: how much the possibility-space proxy
    stays elevated (or rises) before collapsing.

    A high value means the system held tension before compressing.
    A low value means monotonic decrease (no detectable tension).

    Method: compare mean value in the first `pre_window_fraction` of the
    series to the overall mean. If the pre-window mean is lower than or
    equal to the overall mean, tension evidence is weak.

    Args:
        series: time series of possibility-space proxy values
        pre_window_fraction: fraction of series to consider as "pre-collapse"

    Returns:
        Tension index in [0.0, 1.0]. Returns 0.0 if series is too short.
    """
    arr = np.array(series, dtype=float)
    if len(arr) < 4:
        return 0.0

    split = max(1, int(len(arr) * pre_window_fraction))
    pre_mean = float(arr[:split].mean())
    overall_mean = float(arr.mean())
    series_range = arr.max() - arr.min()

    if series_range < 1e-9:
        return 0.0

    # Tension: pre-window is at or above overall mean (not already collapsing)
    delta = pre_mean - overall_mean
    return float(np.clip(delta / series_range, 0.0, 1.0))


def post_collapse_narrowing(pre_values: list[float], post_values: list[float]) -> float:
    """
    Measure reduction in trajectory diversity after a collapse event.

    Computed as: 1 - (std(post) / std(pre))
    Higher = more narrowing.

    Args:
        pre_values:  possibility-space proxy values before the event
        post_values: possibility-space proxy values after the event

    Returns:
        Narrowing score in [0.0, 1.0]. Returns 0.0 if input is degenerate.
    """
    if not pre_values or not post_values:
        return 0.0

    pre_std = float(np.std(pre_values))
    post_std = float(np.std(post_values))

    if pre_std < 1e-9:
        return 0.0

    return float(np.clip(1.0 - (post_std / pre_std), 0.0, 1.0))


def irreversibility_proxy(series: list[float], tail_fraction: float = 0.2) -> float:
    """
    Proxy for non-recoverability: how stable the post-collapse state is.

    Measures variance in the tail of the series normalized by the initial variance.
    Lower tail variance = more irreversible.

    Returns:
        Irreversibility in [0.0, 1.0]. 1.0 = completely locked (zero tail variance).
    """
    arr = np.array(series, dtype=float)
    if len(arr) < 4:
        return 0.0

    initial_var = float(np.var(arr[:max(1, int(len(arr) * 0.2))]))
    tail_var = float(np.var(arr[int(len(arr) * (1.0 - tail_fraction)):]))

    if initial_var < 1e-9:
        return 0.0

    return float(np.clip(1.0 - (tail_var / initial_var), 0.0, 1.0))


# ---------------------------------------------------------------------------
# Composite DCP score (provisional)
# ---------------------------------------------------------------------------

def compute_dcp_score(
    possibility_space: Optional[float],
    constraint: Optional[float],
    tension: Optional[float],
    collapse: Optional[float],
    post_narrowing: Optional[float],
    weights: Optional[dict[str, float]] = None,
) -> float:
    """
    Compute a provisional composite DCP score from component proxies.

    This is a weighted mean of available components. Missing (None) components
    are excluded from the mean — their absence reduces confidence in the score
    (tracked separately in DCPEvent.qualification_status()).

    Default weights are equal. These have NOT been calibrated and should
    be treated as provisional heuristics.

    Args:
        possibility_space: normalized proxy, or None
        constraint: normalized proxy, or None
        tension: normalized proxy, or None
        collapse: normalized proxy, or None
        post_narrowing: normalized proxy, or None
        weights: optional custom weights dict with keys matching component names

    Returns:
        Composite score in [0.0, 1.0]. Returns 0.0 if no components present.

    NOTE: This score is NOT a validated confidence score. It is a structural
    summary for inspection. Do not use as an Atlas promotion criterion alone.
    """
    default_weights = {
        "possibility_space": 1.0,
        "constraint": 1.0,
        "tension": 1.0,
        "collapse": 1.5,      # weighted higher — collapse is the core event
        "post_narrowing": 1.5,
    }
    w = weights or default_weights

    components_and_weights = [
        (possibility_space, w.get("possibility_space", 1.0)),
        (constraint,        w.get("constraint", 1.0)),
        (tension,           w.get("tension", 1.0)),
        (collapse,          w.get("collapse", 1.5)),
        (post_narrowing,    w.get("post_narrowing", 1.5)),
    ]

    total_weight = 0.0
    weighted_sum = 0.0
    for val, weight in components_and_weights:
        if val is not None:
            weighted_sum += val * weight
            total_weight += weight

    if total_weight < 1e-9:
        return 0.0

    return float(np.clip(weighted_sum / total_weight, 0.0, 1.0))
