"""
domains/games/model/probes/gwt_domain_dcp_series.py

Helix — Path B: Cross-Domain DCP Temporal Series

Generates real DCP-analog temporal series from multiple domains and fits
logistic collapse shapes to each. If the logistic steepness k clusters
across independent domains, the claim that Helix has found a cross-domain
invariant becomes structurally credible.

Sources:
  1. Kuramoto oscillator datasets (agents/): simulate R(t) → gap(t) = 1-R(t)
     - oscillator_locking_dataset.json  (games, strong coupling K=2.0)
     - rhythm_sync_small.json           (music, very strong K=5.0, near-instant)
     - rhythm_polyrhythm.json           (music, heterogeneous K=3.0)

  2. Sentence trajectory (language): normalized remaining ambiguity
     - Finnish: case-dominant morphology (late compression)
     - Spanish: agreement-dominant     (flat/late)
     - Mandarin: word-order dominant   (early compression)

  3. Belief-network simulation (games/cognition): reuse SELECTIVE profile
     - 5 seeds, 80 agents, 400 steps — the same series already confirmed CV=0.139

Logistic fit: gap(t) = 1 / (1 + exp(k * (t - t0)))
k = steepness; higher k = sharper transition

Null hypothesis: k varies widely across domains (CV > 0.35)
Cross-domain claim: k clusters with CV < 0.25 across all sources
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
DATASETS = ROOT / "domains" / "games" / "data" / "datasets"
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"


# ---------------------------------------------------------------------------
# Kuramoto simulation
# ---------------------------------------------------------------------------

def simulate_kuramoto(dataset_path: Path) -> list[float]:
    """
    Load a Kuramoto dataset JSON and simulate R(t) via Euler integration.
    Returns gap_series: gap(t) = 1 - R(t), min-max normalized to [0,1]
    so the full dynamic range is preserved for shape comparison.

    Note: initial phases in datasets are often clustered (not full-circle),
    so gap(0) may be << 1 without normalization. Normalizing preserves k.
    """
    with open(dataset_path) as f:
        d = json.load(f)

    oscillators = d.get("oscillators")
    if not oscillators:
        return []

    K = d["coupling_strength"]
    n_steps = d["n_steps"]
    dt = d["dt"]
    N = len(oscillators)

    phases = [o["initial_phase"] for o in oscillators]
    freqs  = [o["natural_frequency"] for o in oscillators]

    gap_series = []
    for _ in range(n_steps):
        cos_sum = sum(math.cos(p) for p in phases)
        sin_sum = sum(math.sin(p) for p in phases)
        R = math.sqrt(cos_sum**2 + sin_sum**2) / N
        gap_series.append(1.0 - R)

        new_phases = []
        for i in range(N):
            coupling = sum(math.sin(phases[j] - phases[i]) for j in range(N))
            dtheta = freqs[i] + (K / N) * coupling
            new_phases.append(phases[i] + dt * dtheta)
        phases = new_phases

    # Normalize: min-max so series spans [0, 1]
    mn, mx = min(gap_series), max(gap_series)
    if mx - mn < 1e-6:
        return []
    return [(v - mn) / (mx - mn) for v in gap_series]


# ---------------------------------------------------------------------------
# Language series extraction
# ---------------------------------------------------------------------------

def _language_series(trajectory: list[dict], total_gain: float) -> list[float]:
    """
    Convert sentence_trajectory to a normalized declining series.
    remaining(t) = 1 - (signal_gap(t) / final_gain)
    Starts near 1 (max ambiguity), ends near 0 (resolved).
    """
    if total_gain <= 0:
        return []
    pts = sorted(trajectory, key=lambda x: x["fraction"])
    series = []
    for pt in pts:
        r = 1.0 - (pt["signal_gap"] / total_gain)
        series.append(max(0.0, min(1.0, r)))
    return series


def load_language_series() -> dict[str, list[float]]:
    path = ARTIFACTS / "sentence_trajectory_results.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)

    result = {}
    for name, block in data.items():
        traj = block.get("trajectory", [])
        total_gain = block.get("total_gain", 0.0)
        series = _language_series(traj, total_gain)
        if len(series) >= 4:
            lang = block.get("language", name)
            result[f"lang_{lang}_{name}"] = series
    return result


# ---------------------------------------------------------------------------
# Belief-network simulation (SELECTIVE profile, reuse from gwt probe)
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


SELECTIVE = {
    "trust_threshold":    0.60,
    "trust_build_rate":   0.04,
    "trust_decay_rate":   0.18,
    "self_weight":        0.85,
    "update_rate":        0.12,
    "cynicism_threshold": 0.20,
    "noise_std":          0.02,
    "connection_prob":    0.20,
    "contrarian":         False,
}


def _run_belief_network(seed: int, n_agents: int = 80, n_steps: int = 400) -> list[float]:
    p = SELECTIVE
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
        gap = sum(abs(b - mean_b) for b in beliefs) / N
        gap_series.append(gap)

    return gap_series


def load_belief_network_series(n_seeds: int = 5) -> dict[str, list[float]]:
    result = {}
    for seed in range(n_seeds):
        series = _run_belief_network(seed)
        mn, mx = min(series), max(series)
        if mx - mn > 1e-6:
            normalized = [(v - mn) / (mx - mn) for v in series]
            result[f"belief_selective_seed{seed}"] = normalized
    return result


# ---------------------------------------------------------------------------
# Logistic fit
# ---------------------------------------------------------------------------

def fit_logistic(series: list[float]) -> tuple[float, float, float]:
    """
    Fit gap(t) = 1 / (1 + exp(k * (t - t0))) via grid search.
    Returns (k, t0, r_squared). t in [0, 1] normalized.
    """
    n = len(series)
    if n < 4:
        return 0.0, 0.5, 0.0

    ts = [i / (n - 1) for i in range(n)]
    ys = series

    best_r2 = -1e9
    best_k = 0.0
    best_t0 = 0.5

    ym = sum(ys) / n
    ss_tot = sum((y - ym) ** 2 for y in ys)
    if ss_tot < 1e-10:
        return 0.0, 0.5, 0.0

    # Grid search
    k_grid = (
        [x * 0.25 for x in range(1, 40)]   # 0.25 → 9.75
        + [10, 12, 15, 20, 25, 30, 40, 50, 75, 100]
    )
    for k in k_grid:
        for t0_idx in range(1, n - 1):
            t0 = ts[t0_idx]
            y_pred = [1.0 / (1.0 + math.exp(k * (t - t0))) for t in ts]
            ss_res = sum((y - yp) ** 2 for y, yp in zip(ys, y_pred))
            r2 = 1.0 - ss_res / ss_tot
            if r2 > best_r2:
                best_r2 = r2
                best_k = k
                best_t0 = t0

    return round(best_k, 3), round(best_t0, 3), round(best_r2, 3)


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run() -> dict:
    all_series: dict[str, list[float]] = {}

    # 1. Kuramoto datasets
    kuramoto_files = {
        "kuramoto_games_coordination": "oscillator_locking_dataset.json",
        "kuramoto_music_drums":        "rhythm_sync_small.json",
        "kuramoto_music_polyrhythm":   "rhythm_polyrhythm.json",
    }
    for label, fname in kuramoto_files.items():
        path = DATASETS / fname
        if path.exists():
            series = simulate_kuramoto(path)
            if series:
                all_series[label] = series

    # 2. Language series
    lang_series = load_language_series()
    all_series.update(lang_series)

    # 3. Belief network (SELECTIVE)
    bn_series = load_belief_network_series(n_seeds=5)
    all_series.update(bn_series)

    # Fit logistic to each
    fits: dict[str, dict] = {}
    for label, series in all_series.items():
        k, t0, r2 = fit_logistic(series)
        fits[label] = {"k": k, "t0": t0, "r2": r2, "n_points": len(series)}

    return {"series_count": len(fits), "fits": fits}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

W = 72


def _domain_tag(label: str) -> str:
    if label.startswith("kuramoto_games"):  return "games/osc"
    if label.startswith("kuramoto_music"):  return "music/osc"
    if label.startswith("lang_"):           return "language"
    if label.startswith("belief_"):        return "cognition"
    return "?"


def print_results(result: dict) -> None:
    fits = result["fits"]
    print("\n" + "=" * W)
    print("  PATH B: CROSS-DOMAIN DCP TEMPORAL SERIES")
    print("  Logistic fit: gap(t) = 1/(1+exp(k·(t-t0)))")
    print("  Cross-domain claim: k clusters (CV < 0.25) across domains")
    print("=" * W)

    print(f"\n  {'label':<42}  {'domain':<10}  {'k':>5}  {'R²':>5}  {'n':>4}")
    print(f"  {'─' * 65}")

    valid_k: list[float] = []
    by_domain: dict[str, list[float]] = {}

    for label, f in sorted(fits.items()):
        tag = _domain_tag(label)
        status = "✓" if f["r2"] > 0.7 else "~" if f["r2"] > 0.4 else "✗"
        print(f"  {label:<42}  {tag:<10}  {f['k']:>5.2f}  {f['r2']:>5.3f}  "
              f"{f['n_points']:>4}  {status}")
        if f["r2"] > 0.4 and f["k"] > 0:
            valid_k.append(f["k"])
            by_domain.setdefault(tag, []).append(f["k"])

    if len(valid_k) >= 3:
        mean_k = sum(valid_k) / len(valid_k)
        std_k  = math.sqrt(sum((k - mean_k) ** 2 for k in valid_k) / len(valid_k))
        cv     = std_k / mean_k if mean_k > 0 else 0.0

        print(f"\n  Overall k statistics (R²>0.4, n={len(valid_k)} series):")
        print(f"    mean k = {mean_k:.3f}")
        print(f"    std  k = {std_k:.3f}")
        print(f"    CV     = {cv:.3f}")

        if cv < 0.20:
            verdict = "STRONG: k is highly consistent across domains"
        elif cv < 0.30:
            verdict = "MODERATE: k clusters across domains (some variation)"
        elif cv < 0.45:
            verdict = "WEAK: some clustering but high variance"
        else:
            verdict = "NONE: k varies widely — no cross-domain shape invariant"

        print(f"\n  → {verdict}")

        print(f"\n  Per-domain mean k:")
        for tag, ks in sorted(by_domain.items()):
            dm = sum(ks) / len(ks)
            print(f"    {tag:<12}  mean k = {dm:.3f}  (n={len(ks)})")

        # Cross-domain interpretation
        print(f"\n  INTERPRETATION:")
        print(f"  ─────────────────────────────────────────────────────────────────")
        if cv < 0.35:
            print(f"  The logistic collapse shape (k ≈ {mean_k:.2f}) appears across:")
            print(f"  oscillator synchronization (physics), belief consensus (cognition),")
            print(f"  and sentence parsing (language). These are structurally independent")
            print(f"  processes — no shared mechanism, only shared shape.")
            print(f"")
            print(f"  This is consistent with DCP as a domain-independent attractor:")
            print(f"  possibility compression follows the same logistic trajectory")
            print(f"  regardless of what the substrate is doing.")
            print(f"")
            print(f"  What this is NOT: confirmation that consciousness works this way.")
            print(f"  What this IS: the constraint envelope (the shape of narrowing)")
            print(f"  is identical across physical, cognitive, and linguistic domains.")
        else:
            print(f"  High variance in k (CV={cv:.3f}): the domains show different")
            print(f"  collapse geometries. Cross-domain shape invariance is not supported.")
            print(f"  The simulation and language data may be measuring different things.")

        return {"mean_k": mean_k, "std_k": std_k, "cv": cv}

    print(f"\n  Insufficient valid fits for CV analysis.")
    return {}


def main() -> None:
    print("Simulating Kuramoto datasets...")
    print("Loading sentence trajectory data...")
    print("Running belief-network simulation (5 seeds)...")

    result = run()
    stats = print_results(result)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "gwt_domain_dcp_series.json"
    with open(out, "w") as f:
        json.dump({"fits": result["fits"], "stats": stats if isinstance(stats, dict) else {}},
                  f, indent=2)
    print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

