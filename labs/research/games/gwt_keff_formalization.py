"""
model/domains/games/probes/gwt_keff_formalization.py

Helix — Path 2: K_eff Formalization

Path B found that logistic collapse steepness k sorts by coupling strength:
  - Language (Finnish):        k ≈ 7.5
  - Cognition (belief net):    k ≈ 15–20
  - Physics (Kuramoto K=2.0):  k ≈ 50
  - Physics (Kuramoto K=5.0):  k ≈ 75

The Q-factor intuition: tighter coupling → sharper resonance → higher k.

The hypothesis: k = f(K_eff) where K_eff is the effective coupling constant
of the system, defined as:

  K_eff = trust_build_rate × connection_prob × N

This is analogous to K/N in the Kuramoto model (coupling per oscillator pair).

If k and K_eff follow a clean functional form (power law, linear, or log),
this bridges the domains without claiming identity — they share the same
collapse equation parameterized by their natural coupling ratio.

Test design:
  1. Sweep K_eff by varying all three components:
       trust_build_rate:  0.02, 0.05, 0.10, 0.20, 0.50, 1.0
       connection_prob:   0.10, 0.20, 0.40
       N:                 40,   80,   160
  2. For each (rate, prob, N): run 5 seeds, fit logistic to gap series,
     extract k; average across seeds
  3. Compute K_eff = rate × prob × N for each condition
  4. Fit k vs K_eff: try power law (k = a × K_eff^b), linear, and log
  5. Pick best fit by R²

Additional comparison against Kuramoto values from Path B:
  Kuramoto K=2.0, N=8  → K_eff=2.0  → k≈50
  Kuramoto K=5.0, N=8  → K_eff=5.0  → k≈75
If the belief-net fit extends to these values cleanly, cross-domain bridge
is supported.

Falsification: if R² < 0.6 for all fit forms, K_eff does not predict k and
the k-coupling relationship is domain-specific noise.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Fixed non-varying cognitive params
BASE_PROFILE = {
    "trust_threshold":    0.60,
    "trust_decay_rate":   0.18,
    "self_weight":        0.85,
    "update_rate":        0.12,
    "cynicism_threshold": 0.20,
    "noise_std":          0.02,
    "contrarian":         False,
}


# ---------------------------------------------------------------------------
# Logistic fit
# ---------------------------------------------------------------------------

def _fit_logistic(series: list[float]) -> tuple[float, float]:
    """
    Fit gap(t) = 1 / (1 + exp(k * (t - t0))) to a normalized series.
    Uses grid search over k ∈ [0.5, 200] and t0 ∈ [0, 1].
    Returns (k, R²).
    """
    n = len(series)
    if n < 4:
        return 0.0, 0.0

    ts = [i / (n - 1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 1e-6:
        return 0.0, 0.0
    norm = [(v - mn) / (mx - mn) for v in series]

    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    k_vals = [0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200]
    t0_vals = [i / 20 for i in range(21)]

    for k in k_vals:
        for t0 in t0_vals:
            ss = 0.0
            for t, y in zip(ts, norm):
                pred = 1.0 / (1.0 + math.exp(k * (t - t0)))
                ss += (y - pred) ** 2
            if ss < best_ss:
                best_ss, best_k, best_t0 = ss, k, t0

    mean_y = sum(norm) / n
    ss_tot = sum((y - mean_y) ** 2 for y in norm)
    r2 = 1.0 - best_ss / ss_tot if ss_tot > 1e-9 else 0.0
    return best_k, max(0.0, r2)


# ---------------------------------------------------------------------------
# Simulation (same core as phi_timing_probe)
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


def _run_one(profile: dict, n_agents: int, n_steps: int, seed: int) -> list[float]:
    """Returns the gap series (mean absolute deviation from consensus)."""
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

    for _ in range(n_steps):
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
        gap_series.append(sum(abs(b - mean_b) for b in beliefs) / N)

    return gap_series


# ---------------------------------------------------------------------------
# Regression utilities
# ---------------------------------------------------------------------------

def _linreg(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    if n < 3:
        return {"slope": None, "intercept": None, "r2": None}
    mx, my = sum(xs) / n, sum(ys) / n
    ss_xy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    ss_xx = sum((x - mx) ** 2 for x in xs)
    ss_yy = sum((y - my) ** 2 for y in ys)
    if ss_xx < 1e-12 or ss_yy < 1e-12:
        return {"slope": None, "intercept": None, "r2": None}
    slope = ss_xy / ss_xx
    intercept = my - slope * mx
    r2 = (ss_xy ** 2) / (ss_xx * ss_yy)
    return {"slope": round(slope, 4), "intercept": round(intercept, 4), "r2": round(r2, 4)}


def _power_law_fit(xs: list[float], ys: list[float]) -> dict:
    """Fit y = a * x^b via linear regression on log-log."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pairs) < 3:
        return {"a": None, "b": None, "r2": None}
    lx = [math.log(x) for x, _ in pairs]
    ly = [math.log(y) for _, y in pairs]
    fit = _linreg(lx, ly)
    if fit["slope"] is None:
        return {"a": None, "b": None, "r2": None}
    return {
        "a": round(math.exp(fit["intercept"]), 4),
        "b": round(fit["slope"], 4),
        "r2": fit["r2"],
    }


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def sweep(n_seeds: int = 5, n_steps: int = 400) -> list[dict]:
    rates = [0.02, 0.05, 0.10, 0.20, 0.50, 1.0]
    probs = [0.10, 0.20, 0.40]
    ns    = [40, 80, 160]

    rows = []
    total = len(rates) * len(probs) * len(ns)
    done = 0

    for N in ns:
        for prob in probs:
            for rate in rates:
                done += 1
                K_eff = rate * prob * N
                profile = {**BASE_PROFILE, "trust_build_rate": rate, "connection_prob": prob}

                k_vals, r2_vals = [], []
                for seed in range(n_seeds):
                    gap = _run_one(profile, N, n_steps, seed)
                    k, r2 = _fit_logistic(gap)
                    if r2 > 0.5:
                        k_vals.append(k)
                        r2_vals.append(r2)

                if k_vals:
                    mean_k  = sum(k_vals) / len(k_vals)
                    mean_r2 = sum(r2_vals) / len(r2_vals)
                    rows.append({
                        "N": N, "connection_prob": prob, "trust_build_rate": rate,
                        "K_eff": round(K_eff, 4),
                        "mean_k": round(mean_k, 2),
                        "mean_fit_r2": round(mean_r2, 3),
                        "n_valid": len(k_vals),
                    })
                    print(f"  N={N} p={prob:.2f} rate={rate:.2f}  K_eff={K_eff:.3f}  k={mean_k:.1f}  R²={mean_r2:.2f}")
                else:
                    rows.append({
                        "N": N, "connection_prob": prob, "trust_build_rate": rate,
                        "K_eff": round(K_eff, 4),
                        "mean_k": None, "mean_fit_r2": None, "n_valid": 0,
                    })

    return rows


def analyze(rows: list[dict]) -> dict:
    valid = [r for r in rows if r["mean_k"] is not None]
    keffs = [r["K_eff"] for r in valid]
    ks    = [r["mean_k"] for r in valid]

    linear = _linreg(keffs, ks)
    power  = _power_law_fit(keffs, ks)
    log_fit = _linreg([math.log(x) for x in keffs if x > 0],
                      [k for x, k in zip(keffs, ks) if x > 0])

    # Kuramoto reference points from Path B
    kuramoto_refs = [
        {"domain": "Kuramoto K=2.0 (games)", "K_eff": 2.0, "k_observed": 50},
        {"domain": "Kuramoto K=5.0 (music)",  "K_eff": 5.0, "k_observed": 75},
        {"domain": "Language Finnish",         "K_eff": None, "k_observed": 7.5},
        {"domain": "Cognition (belief net)",   "K_eff": None, "k_observed": 17.5},
    ]

    # Predict k for Kuramoto K_eff values using power law fit
    if power["a"] is not None and power["b"] is not None:
        for ref in kuramoto_refs:
            if ref["K_eff"] is not None:
                ref["k_predicted"] = round(power["a"] * ref["K_eff"] ** power["b"], 1)

    best_r2 = max(
        v for v in [linear["r2"], power["r2"], log_fit["r2"]] if v is not None
    ) if any(v is not None for v in [linear["r2"], power["r2"], log_fit["r2"]]) else None

    if best_r2 is None:
        verdict = "insufficient data"
    elif best_r2 >= 0.85:
        verdict = "supported — K_eff predicts k (R²≥0.85)"
    elif best_r2 >= 0.60:
        verdict = "partial — K_eff correlates with k but noisily (R²≥0.60)"
    else:
        verdict = "rejected — K_eff does not predict k (R²<0.60)"

    return {
        "linear_fit":    linear,
        "power_law_fit": power,
        "log_fit":       log_fit,
        "best_r2":       best_r2,
        "verdict":       verdict,
        "kuramoto_comparison": kuramoto_refs,
        "n_conditions":  len(valid),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Path 2: K_eff Formalization ===")
    print("Sweeping trust_build_rate × connection_prob × N\n")

    rows = sweep()
    result = analyze(rows)

    print(f"\n--- K_eff → k fit ---")
    print(f"  Linear:    k = {result['linear_fit']['slope']} × K_eff + {result['linear_fit']['intercept']}  R²={result['linear_fit']['r2']}")
    print(f"  Power law: k = {result['power_law_fit']['a']} × K_eff^{result['power_law_fit']['b']}  R²={result['power_law_fit']['r2']}")
    print(f"  Log:       k = {result['log_fit']['slope']} × ln(K_eff) + {result['log_fit']['intercept']}  R²={result['log_fit']['r2']}")
    print(f"  Best R² = {result['best_r2']}")
    print(f"  Verdict: {result['verdict']}")
    print("\n  Kuramoto comparison:")
    for ref in result["kuramoto_comparison"]:
        pred = ref.get("k_predicted", "N/A")
        print(f"    {ref['domain']}: observed k={ref['k_observed']}  predicted={pred}")

    out = {"rows": rows, "analysis": result}
    dest = ARTIFACTS / "gwt_keff_formalization.json"
    with open(dest, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()

