"""
Cognition Domain — Collapse Morphology Classifier
model/model/domains/cognition/analysis/morphology_classifier.py

First-pass heuristic morphology assignment for the cognition domain.

This classifier assigns one of the four provisional CollapseMorphology labels
to a completed trajectory run based on observable post-collapse behavior.

IMPORTANT:
    - This is a first-pass heuristic implementation.
    - All thresholds are uncalibrated provisional values.
    - Classifications should be treated as working labels, not validated findings.
    - A null-corpus calibration pass is required before any Atlas promotion
      that cites morphology class as evidence.

Classification logic is based on:
    - Post-collapse breadth mean relative to pre-collapse mean
    - Post-collapse breadth variance relative to pre-collapse variance
    - Return tendency toward initial (pre-constraint) breadth level
    - Whether a collapse was detected at all

See also:
    system/engine/compute/invariants/dcp/morphology.py  — canonical enum + profile table
    docs/invariants/decision_compression_principle.md §7
"""
from __future__ import annotations

from typing import Optional
import statistics

from core.invariants.dcp.morphology import CollapseMorphology


# Heuristic thresholds — all provisional, subject to calibration
_TRANSFORMATIVE_COHERENCE_RATIO    = 0.65  # post_mean < this fraction of pre_mean → transformed
_TRANSFORMATIVE_VARIANCE_REDUCTION = 0.75  # post_var < this fraction of pre_var → coherence up
_CIRCULAR_RETURN_TOLERANCE         = 0.12  # post within this delta of initial → circular
_DISSOLUTIVE_VARIANCE_INCREASE     = 1.30  # post_var > this multiple of pre_var → dissolutive


def classify_morphology(
    breadth_series: list[float],
    collapse_step: Optional[int],
    initial_breadth: float,
    pre_window: int = 10,
    post_window: int = 15,
) -> CollapseMorphology:
    """
    Assign a provisional collapse morphology to a trajectory run.

    Decision rules (applied in order):
        1. No collapse detected → DEFERRED_SUSPENDED
        2. Post_var >> pre_var (dispersion) → DISSOLUTIVE
        3. Post_mean near initial_breadth (return to origin) → CIRCULAR
        4. Post_mean << pre_mean AND post_var < pre_var (new coherent state) → TRANSFORMATIVE
        5. Fallback → TRANSFORMATIVE (some narrowing occurred, even if noisy)

    Args:
        breadth_series: full possibility_breadth time series
        collapse_step: step index of detected collapse (None = no collapse)
        initial_breadth: breadth at step 0 (pre-constraint baseline)
        pre_window: steps before collapse used for pre-collapse baseline
        post_window: steps after collapse used for post-collapse measurement

    Returns:
        CollapseMorphology enum value

    NOTE: This function is heuristic. Do not treat outputs as validated findings.
    """
    # Rule 1: No collapse → DEFERRED
    if collapse_step is None:
        return CollapseMorphology.DEFERRED_SUSPENDED

    # Extract pre and post windows
    pre_start  = max(0, collapse_step - pre_window)
    pre_series  = breadth_series[pre_start: collapse_step]
    post_series = breadth_series[collapse_step: collapse_step + post_window]

    if not pre_series or not post_series:
        # Not enough data — default to TRANSFORMATIVE (something happened)
        return CollapseMorphology.TRANSFORMATIVE

    pre_mean = sum(pre_series) / len(pre_series)
    post_mean = sum(post_series) / len(post_series)

    pre_var = _safe_variance(pre_series)
    post_var = _safe_variance(post_series)

    # Rule 2: Dissolutive — post-collapse variance is larger (dispersion / breakdown)
    if pre_var > 0 and post_var > pre_var * _DISSOLUTIVE_VARIANCE_INCREASE:
        return CollapseMorphology.DISSOLUTIVE

    # Rule 3: Circular — post-collapse breadth returns near initial level
    if abs(post_mean - initial_breadth) < _CIRCULAR_RETURN_TOLERANCE:
        return CollapseMorphology.CIRCULAR

    # Rule 4: Transformative — breadth drops to new lower level with reduced variance
    if (
        post_mean < pre_mean * _TRANSFORMATIVE_COHERENCE_RATIO
        and (pre_var == 0 or post_var < pre_var * _TRANSFORMATIVE_VARIANCE_REDUCTION)
    ):
        return CollapseMorphology.TRANSFORMATIVE

    # Fallback — some narrowing occurred; label as transformative (working classification)
    return CollapseMorphology.TRANSFORMATIVE


def _safe_variance(series: list[float]) -> float:
    """Variance of a series; returns 0.0 for length < 2."""
    if len(series) < 2:
        return 0.0
    try:
        return statistics.variance(series)
    except statistics.StatisticsError:
        return 0.0


def morphology_summary(morphology: CollapseMorphology) -> str:
    """One-line summary of the assigned morphology for logging."""
    _SUMMARIES = {
        CollapseMorphology.TRANSFORMATIVE:     "→ new coherent structure (transformative)",
        CollapseMorphology.DISSOLUTIVE:        "→ coherence loss / dispersion (dissolutive)",
        CollapseMorphology.CIRCULAR:           "→ return toward prior basin (circular)",
        CollapseMorphology.DEFERRED_SUSPENDED: "→ no collapse; sustained tension (deferred)",
    }
    return _SUMMARIES.get(morphology, str(morphology))


