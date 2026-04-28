"""
model/domains/games/probes/godot_deep_search.py

Helix — Deep Search Experiments
Four experiment classes targeting structural anomalies and unexpected behavior.

  adversarial   — consensus network with liar agents (consistent vs noisy)
  moving_truth  — truth drifts or flips mid-run; tests tracking vs early lock-in
  liar_sweep    — sweep liar_fraction 0→0.45; find crossover where DISSONANCE wins/loses
  seed_dist     — 100-seed distribution; variance, win rates, tail behavior

Core hypothesis being tested:
  The cynicism mechanism in DISSONANCE is a VOLATILITY filter, not an accuracy filter.
  Consistent liars (stable, wrong) may DEFEAT it by building trust through consistency.
  Noisy liars (volatile, wrong) should be CAUGHT by it.
  Moving truth should favor DISSONANCE's longer compression arc.
"""

from __future__ import annotations

import argparse
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
sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# ---------------------------------------------------------------------------
# Profile definitions (must stay in sync with godot_cognition.py)
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict[str, Any]] = {
    "selective": {
        "trust_threshold":    0.60,
        "trust_build_rate":   0.04,
        "trust_decay_rate":   0.18,
        "self_weight":        0.85,
        "update_rate":        0.12,
        "cynicism_threshold": 0.20,
        "noise_std":          0.02,
        "connection_prob":    0.20,
    },
    "baseline": {
        "trust_threshold":    0.0,
        "trust_build_rate":   1.0,
        "trust_decay_rate":   0.0,
        "self_weight":        0.0,
        "update_rate":        0.50,
        "cynicism_threshold": 1.0,
        "noise_std":          0.0,
        "connection_prob":    0.40,
    },
}

# ---------------------------------------------------------------------------
# Core simulation engines
# ---------------------------------------------------------------------------

def _build_graph(N: int, connection_prob: float, rng: random.Random) -> list[list[int]]:
    edges: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            if rng.random() < connection_prob:
                edges[i].append(j)
                edges[j].append(i)
    return edges


def _run_adversarial_consensus(
    profile_name: str,
    n_agents: int = 50,
    n_steps: int = 200,
    seed: int = 42,
    truth: float = 0.75,
    liar_fraction: float = 0.20,
    liar_type: str = "consistent",  # "consistent" | "noisy"
) -> dict:
    """
    Consensus network with a fraction of adversarial agents.

    consistent liars: anchored at 1-truth, belief never shifts → build trust via stability
    noisy liars:      belief re-randomized each step → cynicism fires, trust collapses
    """
    p = PROFILES[profile_name]
    rng = random.Random(seed)
    N = n_agents
    liar_belief = 1.0 - truth  # maximally misleading

    n_liars = int(N * liar_fraction)
    is_liar = [i < n_liars for i in range(N)]

    beliefs = [rng.random() for _ in range(N)]
    for i in range(N):
        if is_liar[i]:
            beliefs[i] = liar_belief

    trust = [0.0] * (N * N)
    edges = _build_graph(N, p["connection_prob"], rng)

    steps_data = []
    mean_error_series: list[float] = []

    for step in range(n_steps):
        prev_beliefs = beliefs[:]
        new_beliefs = beliefs[:]

        # Liar belief update
        for i in range(N):
            if is_liar[i]:
                if liar_type == "noisy":
                    new_beliefs[i] = rng.random()
                else:
                    new_beliefs[i] = liar_belief
                continue

            trusted_influence = 0.0
            trusted_weight = 0.0
            for j in edges[i]:
                t = trust[i * N + j]
                if t >= p["trust_threshold"]:
                    trusted_influence += t * beliefs[j]
                    trusted_weight += t

            if trusted_weight > 0.0:
                external = trusted_influence / trusted_weight
                new_beliefs[i] = (
                    p["self_weight"] * beliefs[i]
                    + (1.0 - p["self_weight"]) * p["update_rate"] * external
                    + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i]
                )

            if p["noise_std"] > 0.0:
                new_beliefs[i] += rng.uniform(-p["noise_std"], p["noise_std"])
            new_beliefs[i] = max(0.0, min(1.0, new_beliefs[i]))

        # Trust update
        for i in range(N):
            for j in edges[i]:
                belief_delta = abs(beliefs[j] - prev_beliefs[j])
                t = trust[i * N + j]
                if belief_delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_beliefs

        honest = [beliefs[i] for i in range(N) if not is_liar[i]]
        mean_honest = sum(honest) / max(1, len(honest))
        mean_error = sum(abs(b - truth) for b in honest) / max(1, len(honest))
        mean_error_series.append(mean_error)

        consensus_gap = sum(abs(beliefs[i] - mean_honest) for i in range(N)) / N

        steps_data.append({
            "step": step,
            "mean_belief": round(mean_honest, 3),
            "mean_error": round(mean_error, 3),
            "consensus_gap": round(consensus_gap, 3),
            "possibility_breadth": round(consensus_gap, 3),
        })

    final_error = mean_error_series[-1] if mean_error_series else 1.0
    collapse_step = next(
        (i for i, s in enumerate(steps_data) if s["consensus_gap"] < 0.10),
        -1,
    )

    # Mean trust that liars accumulated toward honest agents
    liar_trust_held = []
    for i in range(N):
        if not is_liar[i]:
            for j in edges[i]:
                if is_liar[j]:
                    liar_trust_held.append(trust[i * N + j])
    mean_liar_trust = sum(liar_trust_held) / max(1, len(liar_trust_held))

    return {
        "experiment": "consensus_adversarial",
        "profile": profile_name,
        "liar_type": liar_type,
        "liar_fraction": liar_fraction,
        "n_agents": N,
        "n_steps": n_steps,
        "seed": seed,
        "truth": truth,
        "final_error": round(final_error, 4),
        "collapse_step": collapse_step,
        "converged": final_error < 0.05,
        "mean_liar_trust": round(mean_liar_trust, 4),
        "steps": steps_data,
    }


def _run_moving_truth(
    profile_name: str,
    n_agents: int = 50,
    n_steps: int = 200,
    seed: int = 42,
    truth_start: float = 0.25,
    truth_end: float = 0.75,
    truth_mode: str = "drift",  # "drift" | "flip"
    flip_step: int = 100,
) -> dict:
    """
    Consensus network where truth is not static.

    drift: truth moves linearly from truth_start to truth_end over n_steps
    flip:  truth is truth_start for [0,flip_step), then jumps to truth_end
    """
    p = PROFILES[profile_name]
    rng = random.Random(seed)
    N = n_agents

    beliefs = [rng.random() for _ in range(N)]
    trust = [0.0] * (N * N)
    edges = _build_graph(N, p["connection_prob"], rng)

    steps_data = []
    mean_error_series: list[float] = []
    belief_at_collapse = None
    collapse_step = -1

    for step in range(n_steps):
        if truth_mode == "drift":
            current_truth = truth_start + (truth_end - truth_start) * (step / n_steps)
        else:
            current_truth = truth_start if step < flip_step else truth_end

        prev_beliefs = beliefs[:]
        new_beliefs = beliefs[:]

        for i in range(N):
            trusted_influence = 0.0
            trusted_weight = 0.0
            for j in edges[i]:
                t = trust[i * N + j]
                if t >= p["trust_threshold"]:
                    trusted_influence += t * beliefs[j]
                    trusted_weight += t

            if trusted_weight > 0.0:
                external = trusted_influence / trusted_weight
                new_beliefs[i] = (
                    p["self_weight"] * beliefs[i]
                    + (1.0 - p["self_weight"]) * p["update_rate"] * external
                    + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i]
                )

            if p["noise_std"] > 0.0:
                new_beliefs[i] += rng.uniform(-p["noise_std"], p["noise_std"])
            new_beliefs[i] = max(0.0, min(1.0, new_beliefs[i]))

        for i in range(N):
            for j in edges[i]:
                belief_delta = abs(beliefs[j] - prev_beliefs[j])
                t = trust[i * N + j]
                if belief_delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_beliefs

        mean_belief = sum(beliefs) / N
        mean_error = sum(abs(b - current_truth) for b in beliefs) / N
        consensus_gap = sum(abs(b - mean_belief) for b in beliefs) / N
        mean_error_series.append(mean_error)

        if collapse_step == -1 and consensus_gap < 0.10:
            collapse_step = step
            belief_at_collapse = round(mean_belief, 4)

        steps_data.append({
            "step": step,
            "current_truth": round(current_truth, 4),
            "mean_belief": round(mean_belief, 3),
            "mean_error": round(mean_error, 3),
            "consensus_gap": round(consensus_gap, 3),
        })

    final_truth = truth_start + (truth_end - truth_start) if truth_mode == "drift" else truth_end
    final_error = mean_error_series[-1] if mean_error_series else 1.0

    return {
        "experiment": "moving_truth",
        "profile": profile_name,
        "truth_mode": truth_mode,
        "truth_start": truth_start,
        "truth_end": truth_end,
        "n_agents": N,
        "n_steps": n_steps,
        "seed": seed,
        "collapse_step": collapse_step,
        "belief_at_collapse": belief_at_collapse,
        "final_error": round(final_error, 4),
        "final_truth": round(final_truth, 4),
        "steps": steps_data,
    }

# ---------------------------------------------------------------------------
# Experiment suites
# ---------------------------------------------------------------------------

def run_adversarial_suite(n_agents=50, n_steps=200, seed=42, truth=0.75) -> dict:
    """Run both profiles against consistent and noisy liars at 20% fraction."""
    results = {}
    for liar_type in ("consistent", "noisy"):
        for profile in ("selective", "baseline"):
            r = _run_adversarial_consensus(
                profile, n_agents=n_agents, n_steps=n_steps,
                seed=seed, truth=truth,
                liar_fraction=0.20, liar_type=liar_type,
            )
            results[f"{liar_type}_{profile}"] = r
    return results


def run_liar_sweep(n_agents=50, n_steps=200, seed=42, truth=0.75) -> list[dict]:
    """
    Sweep liar_fraction from 0 to 0.45 for both profiles and both liar types.
    Find the crossover point — if any — where DISSONANCE outperforms baseline.
    """
    fractions = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    rows = []
    for lf in fractions:
        for liar_type in ("consistent", "noisy"):
            d = _run_adversarial_consensus(
                "selective", n_agents=n_agents, n_steps=n_steps,
                seed=seed, truth=truth, liar_fraction=lf, liar_type=liar_type,
            )
            b = _run_adversarial_consensus(
                "baseline", n_agents=n_agents, n_steps=n_steps,
                seed=seed, truth=truth, liar_fraction=lf, liar_type=liar_type,
            )
            rows.append({
                "liar_fraction":      lf,
                "liar_type":          liar_type,
                "selective_error":   d["final_error"],
                "baseline_error":     b["final_error"],
                "selective_wins":    d["final_error"] < b["final_error"],
                "delta":              round(b["final_error"] - d["final_error"], 4),
                "s_liar_trust":       d["mean_liar_trust"],
                "d_collapse":         d["collapse_step"],
                "b_collapse":         b["collapse_step"],
            })
    return rows


def run_moving_truth_suite(n_agents=50, n_steps=200, seed=42) -> dict:
    """Run drift and flip variants for both profiles."""
    results = {}
    for profile in ("selective", "baseline"):
        results[f"drift_{profile}"] = _run_moving_truth(
            profile, n_agents=n_agents, n_steps=n_steps, seed=seed,
            truth_mode="drift", truth_start=0.25, truth_end=0.75,
        )
        results[f"flip_{profile}"] = _run_moving_truth(
            profile, n_agents=n_agents, n_steps=n_steps, seed=seed,
            truth_mode="flip", truth_start=0.25, truth_end=0.75, flip_step=100,
        )
    return results


def run_seed_distribution(
    n_seeds: int = 100,
    liar_fraction: float = 0.20,
    liar_type: str = "noisy",  # noisy = where DISSONANCE is expected to win
    n_agents: int = 50,
    n_steps: int = 200,
    truth: float = 0.75,
) -> dict:
    """
    Run n_seeds seeds for each profile under adversarial conditions.
    Compute win rate, mean error, std, and tail (worst-case) behavior.
    """
    d_errors, b_errors = [], []
    wins = 0

    for s in range(n_seeds):
        d = _run_adversarial_consensus(
            "selective", n_agents=n_agents, n_steps=n_steps,
            seed=s, truth=truth, liar_fraction=liar_fraction, liar_type=liar_type,
        )
        b = _run_adversarial_consensus(
            "baseline", n_agents=n_agents, n_steps=n_steps,
            seed=s, truth=truth, liar_fraction=liar_fraction, liar_type=liar_type,
        )
        d_errors.append(d["final_error"])
        b_errors.append(b["final_error"])
        if d["final_error"] < b["final_error"]:
            wins += 1

    def _stats(vals: list[float]) -> dict:
        n = len(vals)
        mu = sum(vals) / n
        variance = sum((v - mu) ** 2 for v in vals) / n
        std = math.sqrt(variance)
        sorted_v = sorted(vals)
        p95 = sorted_v[int(0.95 * n)]
        p05 = sorted_v[int(0.05 * n)]
        return {
            "mean":   round(mu, 4),
            "std":    round(std, 4),
            "min":    round(min(vals), 4),
            "max":    round(max(vals), 4),
            "p05":    round(p05, 4),
            "p95":    round(p95, 4),
        }

    return {
        "experiment":      "seed_distribution",
        "liar_type":       liar_type,
        "liar_fraction":   liar_fraction,
        "n_seeds":         n_seeds,
        "win_rate":        round(wins / n_seeds, 3),
        "wins":            wins,
        "selective":      _stats(d_errors),
        "baseline":        _stats(b_errors),
        "per_seed":        [
            {"seed": s, "d": d_errors[s], "b": b_errors[s], "d_wins": d_errors[s] < b_errors[s]}
            for s in range(n_seeds)
        ],
    }

# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

W = 60

def _bar(v: float, width: int = 20) -> str:
    filled = round(v * width)
    return "█" * filled + "░" * (width - filled)


def _win_marker(d_err: float, b_err: float) -> str:
    if d_err < b_err - 0.005:
        return "  ← DISSONANCE WINS"
    if b_err < d_err - 0.005:
        return "  ← baseline wins"
    return "  (tie)"


def print_adversarial(results: dict) -> None:
    print("\n" + "=" * W)
    print("  ADVERSARIAL CONSENSUS  (20% liars, truth=0.75)")
    print("=" * W)

    for liar_type in ("consistent", "noisy"):
        d = results[f"{liar_type}_dissonance"]
        b = results[f"{liar_type}_baseline"]
        print(f"\n  liar_type = {liar_type.upper()}")
        print(f"  {'':30s}  {'dissonance':>12}  {'baseline':>10}")
        print(f"  {'─' * 55}")
        print(f"  {'final_error':30s}  {d['final_error']:>12.4f}  {b['final_error']:>10.4f}{_win_marker(d['final_error'], b['final_error'])}")
        print(f"  {'collapse_step':30s}  {str(d['collapse_step']):>12}  {str(b['collapse_step']):>10}")
        print(f"  {'mean_liar_trust (honest→liar)':30s}  {d['mean_liar_trust']:>12.4f}  {b['mean_liar_trust']:>10.4f}")
        print(f"  {'converged':30s}  {str(d['converged']):>12}  {str(b['converged']):>10}")

        if liar_type == "consistent":
            print(f"\n  NOTE: consistent liars build trust via stability.")
            if d["mean_liar_trust"] > 0.30:
                print(f"  DISSONANCE honest agents trusted liars at {d['mean_liar_trust']:.3f} avg")
                print(f"  → cynicism did not protect (liars were stable, not volatile)")
        else:
            print(f"\n  NOTE: noisy liars trigger cynicism (belief shifts > {PROFILES['dissonance']['cynicism_threshold']})")
            if d["final_error"] < b["final_error"]:
                print(f"  → DISSONANCE filtered volatile adversaries: {d['final_error']:.4f} vs {b['final_error']:.4f}")


def print_liar_sweep(rows: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  LIAR FRACTION SWEEP  (0 → 0.45)")
    print("=" * W)

    for liar_type in ("consistent", "noisy"):
        subset = [r for r in rows if r["liar_type"] == liar_type]
        print(f"\n  liar_type = {liar_type.upper()}")
        print(f"  {'frac':>5}  {'D_err':>7}  {'B_err':>7}  {'Δ(B-D)':>8}  {'winner':>12}  {'D_liar_trust':>13}")
        print(f"  {'─' * 58}")
        crossover_found = False
        for r in subset:
            winner = "SELECTIVE" if r["selective_wins"] else "baseline  "
            if r["selective_wins"] and not crossover_found:
                crossover_found = True
                print(f"  {'─ crossover ─':^58}")
            print(
                f"  {r['liar_fraction']:>5.2f}  "
                f"{r['selective_error']:>7.4f}  "
                f"{r['baseline_error']:>7.4f}  "
                f"{r['delta']:>+8.4f}  "
                f"{winner:>12}  "
                f"{r['s_liar_trust']:>13.4f}"
            )
        if not crossover_found:
            print(f"  → no crossover found for {liar_type} liars across this range")


def print_moving_truth(results: dict) -> None:
    print("\n" + "=" * W)
    print("  MOVING TRUTH  (drift: 0.25→0.75 | flip at step 100)")
    print("=" * W)

    for mode in ("drift", "flip"):
        d = results[f"{mode}_dissonance"]
        b = results[f"{mode}_baseline"]
        print(f"\n  mode = {mode.upper()}")
        print(f"  {'':30s}  {'dissonance':>12}  {'baseline':>10}")
        print(f"  {'─' * 55}")
        print(f"  {'collapse_step':30s}  {str(d['collapse_step']):>12}  {str(b['collapse_step']):>10}")
        print(f"  {'belief_at_collapse':30s}  {str(d['belief_at_collapse']):>12}  {str(b['belief_at_collapse']):>10}")
        print(f"  {'final_truth':30s}  {d['final_truth']:>12.4f}  {b['final_truth']:>10.4f}")
        print(f"  {'final_error':30s}  {d['final_error']:>12.4f}  {b['final_error']:>10.4f}{_win_marker(d['final_error'], b['final_error'])}")

        if mode == "drift" and d["collapse_step"] > b["collapse_step"]:
            d_truth_at_collapse = 0.25 + 0.50 * (d["collapse_step"] / d["n_steps"])
            b_truth_at_collapse = 0.25 + 0.50 * (b["collapse_step"] / b["n_steps"])
            print(f"\n  Truth at collapse:")
            print(f"    dissonance (step {d['collapse_step']}): {d_truth_at_collapse:.3f}")
            print(f"    baseline   (step {b['collapse_step']}):  {b_truth_at_collapse:.3f}")
            print(f"  DISSONANCE locked onto a later (closer) snapshot of truth")

        if mode == "flip":
            print(f"\n  Truth flipped from 0.25→0.75 at step 100.")
            print(f"  Both profiles collapsed before the flip.")
            print(f"  Post-flip recovery depends on noise_std and self_weight.")


def print_seed_dist(result: dict) -> None:
    print("\n" + "=" * W)
    print(f"  SEED DISTRIBUTION  ({result['n_seeds']} seeds, "
          f"{result['liar_type']} liars @ {result['liar_fraction']:.0%})")
    print("=" * W)
    d = result["selective"]
    b = result["baseline"]
    print(f"\n  {'':15s}  {'dissonance':>12}  {'baseline':>10}")
    print(f"  {'─' * 40}")
    for k in ("mean", "std", "min", "max", "p05", "p95"):
        print(f"  {k:15s}  {d[k]:>12.4f}  {b[k]:>10.4f}")
    print(f"\n  DISSONANCE win rate:  {result['win_rate']:.1%}  ({result['wins']}/{result['n_seeds']} seeds)")

    # Show histogram of delta (b_error - d_error)
    deltas = [r["b"] - r["d"] for r in result["per_seed"]]
    bins = [-0.30, -0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20, 0.30, 1.0]
    counts = [0] * (len(bins) - 1)
    for delta in deltas:
        for k in range(len(bins) - 1):
            if bins[k] <= delta < bins[k + 1]:
                counts[k] += 1
                break
    print(f"\n  Distribution of Δ error (B - D), positive = DISSONANCE wins:")
    for k in range(len(counts)):
        label = f"[{bins[k]:+.2f},{bins[k+1]:+.2f})"
        bar = "█" * counts[k]
        print(f"  {label:>16}  {bar:<30} {counts[k]}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Helix deep search experiments")
    parser.add_argument(
        "--experiments", nargs="+",
        choices=["adversarial", "sweep", "moving_truth", "seed_dist", "all"],
        default=["all"],
    )
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--agents", type=int, default=50)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--save", action="store_true", default=True)
    args = parser.parse_args()

    run_all = "all" in args.experiments
    all_results: dict[str, Any] = {}

    if run_all or "adversarial" in args.experiments:
        print("\nRunning adversarial suite...")
        adv = run_adversarial_suite(n_agents=args.agents, n_steps=args.steps)
        all_results["adversarial"] = adv
        print_adversarial(adv)

    if run_all or "sweep" in args.experiments:
        print("\nRunning liar fraction sweep (this takes ~30s)...")
        sweep = run_liar_sweep(n_agents=args.agents, n_steps=args.steps)
        all_results["liar_sweep"] = sweep
        print_liar_sweep(sweep)

    if run_all or "moving_truth" in args.experiments:
        print("\nRunning moving truth suite...")
        mt = run_moving_truth_suite(n_agents=args.agents, n_steps=args.steps)
        all_results["moving_truth"] = mt
        print_moving_truth(mt)

    if run_all or "seed_dist" in args.experiments:
        print(f"\nRunning seed distribution ({args.seeds} seeds × 2 profiles × 2 liar types)...")
        sd_noisy = run_seed_distribution(
            n_seeds=args.seeds, liar_type="noisy",
            n_agents=args.agents, n_steps=args.steps,
        )
        sd_consistent = run_seed_distribution(
            n_seeds=args.seeds, liar_type="consistent",
            n_agents=args.agents, n_steps=args.steps,
        )
        all_results["seed_dist_noisy"] = sd_noisy
        all_results["seed_dist_consistent"] = sd_consistent
        print_seed_dist(sd_noisy)
        print_seed_dist(sd_consistent)

    if args.save:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        out = ARTIFACTS / "godot_deep_search.json"
        # Strip per-step data from sweep/seed_dist for smaller file
        save_results = {k: v for k, v in all_results.items()}
        for key in ("adversarial",):
            if key in save_results:
                for r in save_results[key].values():
                    r.pop("steps", None)
        if "moving_truth" in save_results:
            for r in save_results["moving_truth"].values():
                r.pop("steps", None)
        with open(out, "w") as f:
            json.dump(save_results, f, indent=2)
        print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

