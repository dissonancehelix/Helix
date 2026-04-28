"""
domains/games/model/probes/gwt_topology_floor.py

Helix — Path 1: Topology Floor

The ~53-step structural floor on Phi_gap (pre-ignition integration window) was
observed at N=80, connection_prob=0.20 regardless of trust_build_rate. The
hypothesis is that this floor is determined by the network graph topology —
specifically the characteristic path length L (average shortest path between
any two nodes) — and not by any cognitive parameter.

Prediction: floor ∝ L(N, connection_prob)

If true: the minimum pre-ignition window before any broadcast network can
achieve ignition is a graph-theoretic lower bound, not a learning-rate effect.
This would be worth formalizing independently of the cognitive simulation.

Test design:
  - Vary N: 20, 40, 80, 160, 320
  - Vary connection_prob: 0.05, 0.10, 0.20, 0.40, 0.80
  - Hold all cognitive params at SELECTIVE (trust_build_rate=1.0 to minimize
    learning-rate effect and reveal the topological floor cleanly)
  - For each (N, p): run 8 seeds, record mean Phi_gap at floor
  - Also compute approximate L (characteristic path length via BFS mean)
  - Fit: floor = a * L + b; if R² > 0.85, floor ∝ L is supported

Falsification: if floor vs L shows no monotonic relationship (R² < 0.3),
the floor is not topologically determined and the Path A result was noise.
"""

from __future__ import annotations

import json
import math
import random
from collections import deque
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Fixed cognitive profile — trust_build_rate maxed to isolate topology
FLOOR_PROFILE = {
    "trust_threshold":    0.60,
    "trust_build_rate":   1.0,     # maximally fast — removes learning-rate floor
    "trust_decay_rate":   0.18,
    "self_weight":        0.85,
    "update_rate":        0.12,
    "cynicism_threshold": 0.20,
    "noise_std":          0.02,
    "contrarian":         False,
}


# ---------------------------------------------------------------------------
# Graph utilities
# ---------------------------------------------------------------------------

def _build_graph(n: int, prob: float, rng: random.Random) -> list[list[int]]:
    edges: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < prob:
                edges[i].append(j)
                edges[j].append(i)
    return edges


def _characteristic_path_length(edges: list[list[int]]) -> float:
    """
    Mean shortest-path length over all reachable (i,j) pairs via BFS.
    Unreachable pairs (disconnected graph) are excluded from the mean.
    Returns 0.0 if the graph has no edges at all.
    """
    N = len(edges)
    total, count = 0, 0
    for src in range(N):
        dist = [-1] * N
        dist[src] = 0
        q: deque[int] = deque([src])
        while q:
            u = q.popleft()
            for v in edges[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    q.append(v)
        for d in dist:
            if d > 0:
                total += d
                count += 1
    return total / count if count > 0 else 0.0


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


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _run_one(edges: list[list[int]], profile: dict, n_steps: int, seed: int) -> dict:
    p = profile
    rng = random.Random(seed + 10000)   # separate rng for beliefs
    N = len(edges)

    beliefs = [rng.random() for _ in range(N)]
    trust = [0.0] * (N * N)
    gap_series: list[float] = []
    phi_series: list[float] = []

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
        phi_series.append(_phi(beliefs))

    collapse = next((i for i, g in enumerate(gap_series) if g < 0.10), -1)
    if collapse < 0 or collapse == 0:
        return {"collapse_step": -1, "phi_gap": None}

    phi_peak = phi_series.index(max(phi_series[:collapse + 1]))
    return {
        "collapse_step": collapse,
        "phi_peak_step": phi_peak,
        "phi_gap": collapse - phi_peak,
    }


# ---------------------------------------------------------------------------
# Linear regression utilities (no scipy)
# ---------------------------------------------------------------------------

def _linreg(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"slope": None, "intercept": None, "r2": None}
    mx = sum(xs) / n
    my = sum(ys) / n
    ss_xy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    ss_xx = sum((x - mx) ** 2 for x in xs)
    ss_yy = sum((y - my) ** 2 for y in ys)
    if ss_xx < 1e-12 or ss_yy < 1e-12:
        return {"slope": None, "intercept": None, "r2": None}
    slope = ss_xy / ss_xx
    intercept = my - slope * mx
    r2 = (ss_xy ** 2) / (ss_xx * ss_yy)
    return {"slope": round(slope, 4), "intercept": round(intercept, 4), "r2": round(r2, 4)}


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def sweep(n_seeds: int = 8, n_steps: int = 600) -> list[dict]:
    sizes = [20, 40, 80, 160, 320]
    probs = [0.05, 0.10, 0.20, 0.40, 0.80]

    rows = []
    total = len(sizes) * len(probs)
    done = 0

    for N in sizes:
        for prob in probs:
            done += 1
            print(f"  [{done}/{total}] N={N} p={prob:.2f}", end="", flush=True)

            phi_gaps, path_lengths = [], []

            for seed in range(n_seeds):
                rng = random.Random(seed)
                edges = _build_graph(N, prob, rng)

                # Skip pathologically disconnected graphs
                n_edges = sum(len(e) for e in edges) // 2
                if n_edges < N // 2:
                    continue

                L = _characteristic_path_length(edges)
                r = _run_one(edges, FLOOR_PROFILE, n_steps, seed)

                if r["phi_gap"] is not None:
                    phi_gaps.append(r["phi_gap"])
                    path_lengths.append(L)

            if phi_gaps:
                mean_gap = sum(phi_gaps) / len(phi_gaps)
                std_gap  = math.sqrt(sum((g - mean_gap)**2 for g in phi_gaps) / len(phi_gaps))
                mean_L   = sum(path_lengths) / len(path_lengths)
                rows.append({
                    "N": N,
                    "connection_prob": prob,
                    "mean_phi_gap": round(mean_gap, 2),
                    "std_phi_gap":  round(std_gap, 2),
                    "mean_path_length": round(mean_L, 3),
                    "n_valid": len(phi_gaps),
                })
                print(f"  floor={mean_gap:.1f}  L={mean_L:.2f}  n={len(phi_gaps)}")
            else:
                rows.append({
                    "N": N, "connection_prob": prob,
                    "mean_phi_gap": None, "std_phi_gap": None,
                    "mean_path_length": None, "n_valid": 0,
                    "note": "no collapse reached",
                })
                print("  no collapse")

    return rows


def analyze(rows: list[dict]) -> dict:
    valid = [r for r in rows if r["mean_phi_gap"] is not None]
    xs = [r["mean_path_length"] for r in valid]
    ys = [r["mean_phi_gap"] for r in valid]
    fit_all = _linreg(xs, ys)

    # Re-fit on well-connected regime only (N≥80): removes near-percolation noise
    well_connected = [r for r in valid if r["N"] >= 80]
    xs_wc = [r["mean_path_length"] for r in well_connected]
    ys_wc = [r["mean_phi_gap"] for r in well_connected]
    fit_wc = _linreg(xs_wc, ys_wc)

    r2 = fit_wc["r2"] if fit_wc["r2"] is not None else fit_all["r2"]
    verdict = "unsupported"
    if r2 is not None:
        if r2 >= 0.85:
            verdict = "supported (floor ∝ path_length in well-connected regime, R²≥0.85)"
        elif r2 >= 0.50:
            verdict = "partial (monotonic but noisy, R²≥0.50)"
        else:
            verdict = "rejected (R²<0.50, floor not topologically determined)"

    # Estimate irreducible floor constant: intercept of well-connected fit
    irreducible_floor = fit_wc["intercept"]

    return {
        "linear_fit_all": fit_all,
        "linear_fit_well_connected_N_ge_80": fit_wc,
        "irreducible_floor_estimate": irreducible_floor,
        "verdict": verdict,
        "n_conditions_all": len(valid),
        "n_conditions_well_connected": len(well_connected),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Path 1: Topology Floor ===")
    print(f"Sweeping {5} N values × {5} connection_prob values × 8 seeds\n")

    rows = sweep()
    result = analyze(rows)

    print(f"\n--- Topology floor fit (all N) ---")
    f_all = result["linear_fit_all"]
    print(f"  floor = {f_all['slope']} × L + {f_all['intercept']}  R²={f_all['r2']}  (n={result['n_conditions_all']})")
    print(f"\n--- Topology floor fit (N≥80, well-connected only) ---")
    f_wc = result["linear_fit_well_connected_N_ge_80"]
    print(f"  floor = {f_wc['slope']} × L + {f_wc['intercept']}  R²={f_wc['r2']}  (n={result['n_conditions_well_connected']})")
    print(f"  Irreducible floor estimate: ~{result['irreducible_floor_estimate']} steps")
    print(f"  Verdict: {result['verdict']}")

    out = {"rows": rows, "analysis": result}
    dest = ARTIFACTS / "gwt_topology_floor.json"
    with open(dest, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()

