"""
domains/games/model/probes/gwt_phi_timing_probe.py

Helix — Path A: Φ Timing Prediction

Sweeps trust_build_rate (the rate at which new information is integrated)
and measures how the Φ integration gap changes.

The Φ gap = collapse_step - phi_peak_step:
  How many steps before ignition does peak integration occur?

Hypothesis: Φ_gap ∝ trust_build_rate^(-b)
  Slow integrators have proportionally longer pre-ignition windows.
  This is a power law — not linear, not exponential.

Neural translation:
  trust_build_rate → synaptic learning rate ε (Hebbian: ΔW = ε·pre·post)
  High ε → CONFORMIST (broad trust, fast updating)
  Low ε  → SELECTIVE  (selective trust, slow integration)

  If confirmed: Φ_gap ∝ ε^(-b) where b ≈ 0.7–1.2

Falsifiable EEG prediction:
  Φ_gap maps to: latency between N2/P2 (early integration onset) and P3b (ignition)
  The N2→P3b window should scale as a power law with subjects' Bayesian update speed.
  Test: correlate (P3b_latency - N2_latency) vs reaction time slope across subjects
  in a probabilistic cue–target task (Poeppel/Dehaene paradigm).

  If slope of log(P3b-N2 gap) vs log(RT slope) matches our b exponent → confirmed.
  If relationship is linear not power law → our model is wrong.
  If no relationship → Φ gap is not a real pre-ignition signal.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Base profile: SELECTIVE parameters, trust_build_rate varied
BASE = {
    "trust_threshold":    0.60,
    "trust_decay_rate":   0.18,
    "self_weight":        0.85,
    "update_rate":        0.12,
    "cynicism_threshold": 0.20,
    "noise_std":          0.02,
    "connection_prob":    0.20,
    "contrarian":         False,
}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _entropy(values: list[float], n_bins: int = 20) -> float:
    if not values:
        return 0.0
    bins = [0] * n_bins
    for v in values:
        bins[min(n_bins - 1, int(v * n_bins))] += 1
    N = len(values)
    H = 0.0
    for c in bins:
        if c > 0:
            p = c / N
            H -= p * math.log2(p)
    return H


def _phi(beliefs: list[float]) -> float:
    half = len(beliefs) // 2
    if half == 0:
        return 0.0
    return _entropy(beliefs[:half]) + _entropy(beliefs[half:]) - _entropy(beliefs)


def _run_one(profile: dict, n_agents: int, n_steps: int, seed: int) -> dict:
    p = profile
    rng = random.Random(seed)
    N = n_agents

    beliefs = [rng.random() for _ in range(N)]
    edges: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            if rng.random() < p["connection_prob"]:
                edges[i].append(j)
                edges[j].append(i)

    trust = [0.0] * (N * N)
    gap_series: list[float] = []
    phi_series: list[float] = []

    for step in range(n_steps):
        prev = beliefs[:]
        new_b = beliefs[:]
        for i in range(N):
            t_inf = 0.0; t_wt = 0.0
            for j in edges[i]:
                t = trust[i * N + j]
                if t >= p["trust_threshold"]:
                    t_inf += t * beliefs[j]
                    t_wt  += t
            if t_wt > 0.0:
                external = t_inf / t_wt
                new_b[i] = (
                    p["self_weight"] * beliefs[i]
                    + (1.0 - p["self_weight"]) * p["update_rate"] * external
                    + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i]
                )
            if p["noise_std"] > 0.0:
                new_b[i] += rng.uniform(-p["noise_std"], p["noise_std"])
            new_b[i] = max(0.0, min(1.0, new_b[i]))

        for i in range(N):
            for j in edges[i]:
                delta = abs(beliefs[j] - prev[j])
                t = trust[i * N + j]
                if delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_b
        mean_b = sum(beliefs) / N
        gap = sum(abs(b - mean_b) for b in beliefs) / N
        gap_series.append(gap)
        phi_series.append(_phi(beliefs))

    collapse = next((i for i, g in enumerate(gap_series) if g < 0.10), -1)
    if collapse < 0:
        return {"collapse_step": -1, "phi_gap": None}

    phi_peak = phi_series.index(max(phi_series))
    return {
        "collapse_step": collapse,
        "phi_peak_step": phi_peak,
        "phi_gap": collapse - phi_peak,
        "phi_max": max(phi_series),
        "phi_at_collapse": phi_series[collapse],
    }


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def sweep(n_seeds: int = 8, n_agents: int = 80, n_steps: int = 400) -> list[dict]:
    rates = [
        0.01, 0.015, 0.02, 0.03, 0.04, 0.05,
        0.06, 0.08, 0.10, 0.15, 0.20, 0.30,
        0.40, 0.50, 0.70, 1.0,
    ]
    rows = []
    for rate in rates:
        profile = {**BASE, "trust_build_rate": rate}
        gaps, collapses = [], []
        for seed in range(n_seeds):
            r = _run_one(profile, n_agents, n_steps, seed)
            if r["collapse_step"] >= 0 and r["phi_gap"] is not None:
                gaps.append(r["phi_gap"])
                collapses.append(r["collapse_step"])

        if gaps:
            mean_gap     = sum(gaps) / len(gaps)
            mean_col     = sum(collapses) / len(collapses)
            std_gap      = math.sqrt(sum((g - mean_gap)**2 for g in gaps) / len(gaps))
            rows.append({
                "trust_build_rate": rate,
                "mean_phi_gap":     round(mean_gap, 2),
                "std_phi_gap":      round(std_gap, 2),
                "mean_collapse":    round(mean_col, 1),
                "n_valid":          len(gaps),
            })
        else:
            rows.append({
                "trust_build_rate": rate,
                "mean_phi_gap":     None,
                "std_phi_gap":      None,
                "mean_collapse":    None,
                "n_valid":          0,
                "note":             "no collapse in any seed",
            })

    return rows


# ---------------------------------------------------------------------------
# Power law fit (log-log linear regression)
# ---------------------------------------------------------------------------

def fit_power_law(rows: list[dict]) -> tuple[float, float, float]:
    """
    Φ_gap = a * rate^(-b)
    log(Φ_gap) = log(a) - b * log(rate)
    Returns (a, b, r_squared).
    """
    valid = [(r["trust_build_rate"], r["mean_phi_gap"])
             for r in rows if r["mean_phi_gap"] and r["mean_phi_gap"] > 0]
    if len(valid) < 3:
        return 0.0, 0.0, 0.0

    xs = [math.log(rate) for rate, _ in valid]
    ys = [math.log(gap)  for _, gap  in valid]
    n = len(xs)
    xm = sum(xs) / n
    ym = sum(ys) / n
    ss_xy = sum((x - xm) * (y - ym) for x, y in zip(xs, ys))
    ss_xx = sum((x - xm) ** 2 for x in xs)
    slope = ss_xy / ss_xx if ss_xx > 0 else 0.0
    intercept = ym - slope * xm
    a = math.exp(intercept)
    b = -slope   # positive exponent in a * rate^(-b)

    # R²
    y_pred = [intercept + slope * x for x in xs]
    ss_res = sum((y - yp)**2 for y, yp in zip(ys, y_pred))
    ss_tot = sum((y - ym)**2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return round(a, 3), round(b, 3), round(r2, 3)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

W = 72

def print_sweep(rows: list[dict], a: float, b: float, r2: float) -> None:
    print("\n" + "=" * W)
    print("  PATH A: Φ TIMING VS TRUST_BUILD_RATE SWEEP")
    print("  Hypothesis: Φ_gap = a × rate^(-b)  [power law in log-log space]")
    print("=" * W)

    print(f"\n  {'rate':>8}  {'Φ_gap':>8}  {'±std':>6}  {'collapse':>9}  {'valid':>6}")
    print(f"  {'─' * 45}")
    for r in rows:
        if r["mean_phi_gap"] is None:
            print(f"  {r['trust_build_rate']:>8.3f}  {'—':>8}  {'—':>6}  {'—':>9}  {r['n_valid']:>6}")
        else:
            print(f"  {r['trust_build_rate']:>8.3f}  {r['mean_phi_gap']:>8.1f}  "
                  f"{r['std_phi_gap']:>6.1f}  {r['mean_collapse']:>9.1f}  {r['n_valid']:>6}")

    print(f"\n  Power law fit:  Φ_gap = {a:.3f} × rate^(-{b:.3f})    R² = {r2:.3f}")

    if r2 > 0.85:
        print(f"  → STRONG fit (R²={r2:.3f}): power law holds across the sweep range")
    elif r2 > 0.65:
        print(f"  → MODERATE fit (R²={r2:.3f}): power law is approximate")
    else:
        print(f"  → WEAK fit (R²={r2:.3f}): relationship may not be a power law")

    if b > 0:
        print(f"\n  Exponent b={b:.3f}: Φ gap scales as rate^(-{b:.3f})")
        if 0.8 <= b <= 1.2:
            print(f"  → Near-linear inverse: halving trust_build_rate doubles the Φ gap")
        elif b > 1.2:
            print(f"  → Super-linear: slow integrators accumulate disproportionately long gaps")
        else:
            print(f"  → Sub-linear: some compression but weaker than linear")

    print(f"\n  NEURAL PREDICTION (falsifiable):")
    print(f"  ─────────────────────────────────────────────────────────────────")
    print(f"  In humans, trust_build_rate maps to synaptic learning rate ε.")
    print(f"  Behavioral proxy: RT slope in probabilistic updating task.")
    print(f"")
    print(f"  Prediction: (P3b_latency - N2_latency) ∝ ε^(-{b:.2f})")
    print(f"  Where ε is estimated from trial-by-trial belief updating speed.")
    print(f"")
    print(f"  Test: Poeppel/Dehaene probabilistic cue-target EEG paradigm")
    print(f"    1. Present sequences of probabilistic cues (like our belief updates)")
    print(f"    2. Measure N2 onset (early integration) and P3b onset (ignition)")
    print(f"    3. Compute RT slope as proxy for ε per subject")
    print(f"    4. Test: log(P3b - N2) ~ b × log(ε)  [b = {b:.3f} from our model]")
    print(f"")
    print(f"  Null hypothesis: no relationship between RT slope and N2→P3b window")
    print(f"  Alternative: power law with exponent {b:.3f} ± 0.2")
    print(f"")

    # Specific numeric predictions for SELECTIVE
    selective_rate = 0.04
    predicted_gap = a * (selective_rate ** (-b))
    conformist_rate = 1.0
    conformist_gap = a * (conformist_rate ** (-b))
    print(f"  Specific predictions:")
    print(f"    SELECTIVE (ε=0.04):    Φ gap ≈ {predicted_gap:.0f} integration steps")
    print(f"    CONFORMIST (ε=1.0):    Φ gap ≈ {conformist_gap:.1f} integration steps")
    print(f"    Ratio SELECTIVE/CONFORMIST: {predicted_gap/max(conformist_gap,0.1):.1f}x")
    print(f"")
    print(f"  In EEG milliseconds (assuming ~50ms per integration step at 20Hz gamma):")
    print(f"    SELECTIVE predicted N2→P3b gap: ≈ {predicted_gap * 50:.0f}ms")
    print(f"    CONFORMIST predicted N2→P3b gap: ≈ {conformist_gap * 50:.0f}ms")
    print(f"    Published P3b latency in autistic spectrum: 350–500ms (vs 280–350ms NT)")
    print(f"    → {'CONSISTENT' if predicted_gap * 50 > 300 else 'INCONSISTENT'} with published ASD P3b latency literature")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Sweeping trust_build_rate (0.01 → 1.0, 16 values × 8 seeds each)...")
    rows = sweep(n_seeds=8, n_agents=80, n_steps=400)

    valid = [r for r in rows if r["mean_phi_gap"] and r["mean_phi_gap"] > 0]
    print(f"  {len(valid)}/{len(rows)} rate values produced collapses")

    a, b, r2 = fit_power_law(rows)
    print_sweep(rows, a, b, r2)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "gwt_phi_timing.json"
    with open(out, "w") as f:
        json.dump({"sweep": rows, "power_law": {"a": a, "b": b, "r2": r2}}, f, indent=2)
    print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

