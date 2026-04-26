"""
energy_curve.py — Musical Energy Over Time
===========================================
Measures musical energy as a time series using symbolic features:

  - rhythmic density       (notes/sec per window)
  - harmonic tension       (chromatic density + chord entropy proxy)
  - arrangement density    (active channel count per window)

All three components are normalized [0,1] per track before combining.
Combined energy is a weighted sum (configurable weights).

Also computes:
  - energy_mean, energy_variance, energy_range (max–min)
  - energy_curve_stability   (1 – normalized variance)
  - energy_peak_time_sec     (when does energy peak?)
  - energy_ramp_type         "flat" | "build" | "drop" | "arch" | "valley"

API
---
analyze_energy(score, window_sec=2.0) -> EnergyCurveResult
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnergyCurveResult:
    window_sec:     float
    n_windows:      int = 0

    energy_series:  list[float] = field(default_factory=list)  # per-window 0–1
    rhythmic_series: list[float] = field(default_factory=list)
    harmonic_series: list[float] = field(default_factory=list)
    density_series:  list[float] = field(default_factory=list)

    energy_mean:      float = 0.0
    energy_variance:  float = 0.0
    energy_range:     float = 0.0
    energy_peak_time_sec: float | None = None
    energy_ramp_type: str = "flat"

    # Composite stability index (1 = perfectly flat energy = stable loop)
    energy_curve_stability: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_sec":           self.window_sec,
            "n_windows":            self.n_windows,
            "energy_mean":          round(self.energy_mean, 3),
            "energy_variance":      round(self.energy_variance, 3),
            "energy_range":         round(self.energy_range, 3),
            "energy_ramp_type":     self.energy_ramp_type,
            "energy_peak_time_sec": self.energy_peak_time_sec,
            "energy_curve_stability": round(self.energy_curve_stability, 3),
            # Downsample to 16 points for JSON compactness
            "energy_curve_16pt":    _downsample(self.energy_series, 16),
        }


def analyze_energy(
    score:       Any,
    window_sec:  float = 2.0,
    rhy_weight:  float = 0.40,
    harm_weight: float = 0.35,
    dens_weight: float = 0.25,
) -> EnergyCurveResult:
    """
    Compute musical energy time series from SymbolicScore.

    score: SymbolicScore with .notes, .channels (optional), .duration_sec (optional)
    """
    result = EnergyCurveResult(window_sec=window_sec)

    if not hasattr(score, "notes") or not score.notes:
        return result

    notes = score.notes
    total_dur = getattr(score, "duration_sec", None)
    if not total_dur:
        total_dur = max((n.start + n.duration for n in notes), default=0.0)

    if total_dur < window_sec:
        return result

    n_windows = max(1, int(total_dur / window_sec))
    result.n_windows = n_windows

    rhy_series: list[float] = []
    harm_series: list[float] = []
    dens_series: list[float] = []

    max_density    = 0.0
    max_chrom      = 0.0
    max_active_ch  = 0

    # First pass: raw values
    raw_rhy:  list[float] = []
    raw_harm: list[float] = []
    raw_dens: list[float] = []

    for w in range(n_windows):
        t0 = w * window_sec
        t1 = t0 + window_sec
        w_notes = [n for n in notes if t0 <= n.start < t1]

        # Rhythmic density
        density = len(w_notes) / window_sec
        raw_rhy.append(density)
        max_density = max(max_density, density)

        # Harmonic tension: chromatic density (fraction of 12 PCs present)
        pcs = set(n.note % 12 for n in w_notes)
        chrom = len(pcs) / 12.0
        raw_harm.append(chrom)
        max_chrom = max(max_chrom, chrom)

        # Arrangement density: unique channels active
        channels = set(getattr(n, "channel", 0) for n in w_notes)
        active_ch = len(channels)
        raw_dens.append(float(active_ch))
        max_active_ch = max(max_active_ch, active_ch)

    # Normalize to [0,1]
    def norm_series(s: list[float], mx: float) -> list[float]:
        if mx == 0:
            return [0.0] * len(s)
        return [v / mx for v in s]

    rhy_series  = norm_series(raw_rhy,  max_density)
    harm_series = norm_series(raw_harm, max_chrom)
    dens_series = norm_series(raw_dens, float(max_active_ch) if max_active_ch else 1.0)

    # Weighted sum
    energy_series = [
        rhy_weight  * rhy_series[i]
        + harm_weight * harm_series[i]
        + dens_weight * dens_series[i]
        for i in range(n_windows)
    ]

    result.rhythmic_series = [round(x, 3) for x in rhy_series]
    result.harmonic_series = [round(x, 3) for x in harm_series]
    result.density_series  = [round(x, 3) for x in dens_series]
    result.energy_series   = [round(x, 3) for x in energy_series]

    if energy_series:
        result.energy_mean     = round(sum(energy_series) / len(energy_series), 3)
        result.energy_range    = round(max(energy_series) - min(energy_series), 3)
        var = sum((e - result.energy_mean) ** 2 for e in energy_series) / len(energy_series)
        result.energy_variance = round(var, 3)

        peak_idx = energy_series.index(max(energy_series))
        result.energy_peak_time_sec = round(peak_idx * window_sec, 1)

        # Curve stability: 1 - normalized variance (variance normalized by mean²)
        if result.energy_mean > 0:
            norm_var = var / (result.energy_mean ** 2)
            result.energy_curve_stability = round(max(0.0, 1.0 - min(norm_var, 1.0)), 3)

        result.energy_ramp_type = _classify_ramp(energy_series)

    return result


def _classify_ramp(series: list[float]) -> str:
    """Classify the overall energy shape."""
    if len(series) < 3:
        return "flat"

    n = len(series)
    first_third = series[:n // 3]
    last_third  = series[n - n // 3:]
    mid_third   = series[n // 3: n - n // 3]

    start_mean = sum(first_third) / len(first_third)
    end_mean   = sum(last_third)  / len(last_third)
    mid_mean   = sum(mid_third)   / len(mid_third)  if mid_third else (start_mean + end_mean) / 2

    spread = max(series) - min(series)
    if spread < 0.1:
        return "flat"
    if end_mean > start_mean + 0.1 and mid_mean >= start_mean:
        return "build"
    if start_mean > end_mean + 0.1:
        return "drop"
    if mid_mean > start_mean + 0.1 and mid_mean > end_mean + 0.1:
        return "arch"
    if mid_mean < start_mean - 0.1 and mid_mean < end_mean - 0.1:
        return "valley"
    return "flat"


def _downsample(series: list[float], target: int) -> list[float]:
    if not series:
        return []
    if len(series) <= target:
        return [round(x, 3) for x in series]
    step = len(series) / target
    return [round(series[int(i * step)], 3) for i in range(target)]
