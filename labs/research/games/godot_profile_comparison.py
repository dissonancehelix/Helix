"""
model/domains/games/probes/godot_profile_comparison.py

Helix — Cognitive Profile Comparison
Six cognitive monocultures + one embedding test + signal crossover sweep.

Profiles (all modeled from real cognitive patterns, not arbitrary):
  CONFORMIST    zero resistance to social influence; maximum connectivity
  IMPULSIVE     fast volatile updates; high noise; fires on everything
  DIPLOMAT      balanced; builds trust carefully; moderate anchoring
  DISSONANCE    high self-weight; slow trust; cynicism filter; sparse network
  PARANOID      near-total isolation; extreme cynicism; almost never trusts
  CONTRARIAN    inverts consensus signal; believes opposite of trusted neighbors

Environments:
  clean              no adversaries; pure consensus dynamics
  consistent_liars   20% liars anchored at 1-truth (stable, patient)
  noisy_liars        20% liars re-randomized each step (volatile)
  moving_truth       truth drifts 0.25→0.75 with weak injection signal
  adversarial_heavy  40% consistent liars (stress test)

Embedding test:
  DISSONANCE minority (20%) embedded in CONFORMIST majority (80%)
  vs consistent liars at 20%. Does minority selective-trust help or isolate?

Signal crossover:
  Sweep signal_weight 0.0→0.10 for DISSONANCE vs CONFORMIST.
  Find crossover point where CONFORMIST catches up to DISSONANCE accuracy.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict[str, Any]] = {

    # Goes along with everything. Maximally social. No resistance.
    "CONFORMIST": {
        "trust_threshold":    0.0,
        "trust_build_rate":   1.0,
        "trust_decay_rate":   0.0,
        "self_weight":        0.05,
        "update_rate":        0.70,
        "cynicism_threshold": 1.0,
        "noise_std":          0.01,
        "connection_prob":    0.50,
        "contrarian":         False,
    },

    # Fast, volatile, low anchoring, high noise. Jumps at everything.
    "IMPULSIVE": {
        "trust_threshold":    0.0,
        "trust_build_rate":   1.0,
        "trust_decay_rate":   0.0,
        "self_weight":        0.15,
        "update_rate":        0.80,
        "cynicism_threshold": 0.60,
        "noise_std":          0.05,
        "connection_prob":    0.45,
        "contrarian":         False,
    },

    # Community builder. Moderate on every axis. Careful but not isolated.
    "DIPLOMAT": {
        "trust_threshold":    0.30,
        "trust_build_rate":   0.10,
        "trust_decay_rate":   0.08,
        "self_weight":        0.50,
        "update_rate":        0.30,
        "cynicism_threshold": 0.25,
        "noise_std":          0.01,
        "connection_prob":    0.35,
        "contrarian":         False,
    },

    # Reference: the prior experiments.
    "SELECTIVE": {
        "trust_threshold":    0.60,
        "trust_build_rate":   0.04,
        "trust_decay_rate":   0.18,
        "self_weight":        0.85,
        "update_rate":        0.12,
        "cynicism_threshold": 0.20,
        "noise_std":          0.02,
        "connection_prob":    0.20,
        "contrarian":         False,
    },

    # Near-total isolation. Trust threshold almost unreachable.
    # Extreme cynicism: any shift > 0.05 fires.
    "PARANOID": {
        "trust_threshold":    0.85,
        "trust_build_rate":   0.02,
        "trust_decay_rate":   0.50,
        "self_weight":        0.95,
        "update_rate":        0.05,
        "cynicism_threshold": 0.05,
        "noise_std":          0.03,
        "connection_prob":    0.10,
        "contrarian":         False,
    },

    # Inverts consensus signal: moves toward (1 - trusted_mean).
    # If everyone believes X, contrarian moves toward 1-X.
    # Accidentally truth-seeking when liars dominate (liar at 0.25 → contrarian drifts toward 0.75).
    "CONTRARIAN": {
        "trust_threshold":    0.20,
        "trust_build_rate":   0.20,
        "trust_decay_rate":   0.05,
        "self_weight":        0.60,
        "update_rate":        0.35,
        "cynicism_threshold": 0.40,
        "noise_std":          0.02,
        "connection_prob":    0.35,
        "contrarian":         True,   # flips external signal: uses (1 - external) as target
    },
}

# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def _build_graph(N: int, prob: float, rng: random.Random) -> list[list[int]]:
    e: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            if rng.random() < prob:
                e[i].append(j)
                e[j].append(i)
    return e


def _run(
    profile_name: str,
    n_agents: int = 50,
    n_steps: int = 200,
    seed: int = 42,
    truth_fn: Callable[[int], float] | None = None,  # None → static truth=0.75
    liar_fraction: float = 0.0,
    liar_type: str = "consistent",   # consistent | noisy
    signal_weight: float = 0.0,      # truth injection per step
) -> dict:
    p = PROFILES[profile_name]
    rng = random.Random(seed)
    N = n_agents
    static_truth = 0.75

    n_liars = int(N * liar_fraction)
    is_liar = [i < n_liars for i in range(N)]

    beliefs = [rng.random() for _ in range(N)]
    for i in range(N):
        if is_liar[i]:
            beliefs[i] = 1.0 - static_truth  # maximally wrong anchor

    trust = [0.0] * (N * N)
    edges = _build_graph(N, p["connection_prob"], rng)

    steps_data: list[dict] = []
    errors: list[float] = []
    collapse_step = -1
    n_reopens = 0
    was_collapsed = False

    for step in range(n_steps):
        truth = truth_fn(step) if truth_fn else static_truth
        prev = beliefs[:]
        new_b = beliefs[:]

        # Liar update
        for i in range(N):
            if not is_liar[i]:
                continue
            new_b[i] = rng.random() if liar_type == "noisy" else (1.0 - static_truth)

        # Honest agent update
        for i in range(N):
            if is_liar[i]:
                continue
            t_inf = 0.0
            t_wt  = 0.0
            for j in edges[i]:
                t = trust[i * N + j]
                if t >= p["trust_threshold"]:
                    t_inf += t * beliefs[j]
                    t_wt  += t

            if t_wt > 0.0:
                external = t_inf / t_wt
                if p["contrarian"]:
                    external = 1.0 - external   # invert consensus
                new_b[i] = (
                    p["self_weight"] * beliefs[i]
                    + (1.0 - p["self_weight"]) * p["update_rate"] * external
                    + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i]
                )

            if signal_weight > 0.0:
                new_b[i] += signal_weight * (truth - new_b[i])
            if p["noise_std"] > 0.0:
                new_b[i] += rng.uniform(-p["noise_std"], p["noise_std"])
            new_b[i] = max(0.0, min(1.0, new_b[i]))

        # Trust update
        for i in range(N):
            for j in edges[i]:
                delta = abs(beliefs[j] - prev[j])
                t = trust[i * N + j]
                if delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_b
        honest  = [beliefs[i] for i in range(N) if not is_liar[i]]
        mean_b  = sum(honest) / max(1, len(honest))
        mean_e  = sum(abs(b - truth) for b in honest) / max(1, len(honest))
        gap     = sum(abs(beliefs[i] - mean_b) for i in range(N)) / N
        errors.append(mean_e)

        collapsed_now = gap < 0.10
        if collapsed_now and not was_collapsed:
            if collapse_step < 0:
                collapse_step = step
        if not collapsed_now and was_collapsed:
            n_reopens += 1
        was_collapsed = collapsed_now

        steps_data.append({
            "step": step,
            "mean_belief": round(mean_b, 3),
            "mean_error":  round(mean_e, 3),
            "gap":         round(gap, 3),
            "truth":       round(truth, 3),
        })

    final_e  = errors[-1] if errors else 1.0
    mean_e_all = sum(errors) / max(1, len(errors))
    post_e = errors[collapse_step:] if collapse_step >= 0 else errors
    post_mean = sum(post_e) / max(1, len(post_e))

    return {
        "profile":             profile_name,
        "final_error":         round(final_e, 4),
        "mean_error":          round(mean_e_all, 4),
        "post_collapse_error": round(post_mean, 4),
        "collapse_step":       collapse_step,
        "n_reopens":           n_reopens,
        "steps":               steps_data,
    }


# ---------------------------------------------------------------------------
# Multi-profile runner
# ---------------------------------------------------------------------------

def _run_all(profiles: list[str], **kwargs) -> dict[str, dict]:
    return {name: _run(name, **kwargs) for name in profiles}


ALL_PROFILES = list(PROFILES.keys())

# ---------------------------------------------------------------------------
# Embedding simulation (mixed-type network)
# ---------------------------------------------------------------------------

def _run_embedding(
    minority_profile: str,
    majority_profile: str,
    minority_fraction: float = 0.20,
    n_agents: int = 50,
    n_steps: int = 200,
    seed: int = 42,
    liar_fraction: float = 0.20,
    truth: float = 0.75,
) -> dict:
    """
    Mixed network: minority_fraction of agents use minority_profile,
    the rest use majority_profile. Liars added on top.
    Tests whether a cognitive minority benefits from or is isolated by their architecture.
    """
    rng = random.Random(seed)
    N = n_agents
    n_minority = int(N * minority_fraction)
    n_liars    = int(N * liar_fraction)

    # Assignment: first n_liars=liars, next n_minority=minority, rest=majority
    roles = ["liar"] * n_liars + ["minority"] * n_minority + ["majority"] * (N - n_liars - n_minority)
    assert len(roles) == N

    pm = PROFILES[minority_profile]
    pM = PROFILES[majority_profile]

    def _prof(i: int) -> dict:
        if roles[i] == "minority":
            return pm
        return pM   # majority and liars use majority profile for trust (liars are dumb)

    beliefs = [rng.random() for _ in range(N)]
    for i in range(N):
        if roles[i] == "liar":
            beliefs[i] = 1.0 - truth

    # Use average connection_prob
    avg_conn = 0.5 * (pm["connection_prob"] + pM["connection_prob"])
    edges = _build_graph(N, avg_conn, rng)
    trust = [0.0] * (N * N)

    errors_minority: list[float] = []
    errors_majority: list[float] = []
    errors_all:      list[float] = []

    for step in range(n_steps):
        prev = beliefs[:]
        new_b = beliefs[:]

        for i in range(N):
            if roles[i] == "liar":
                new_b[i] = 1.0 - truth
                continue
            p = _prof(i)
            t_inf = 0.0; t_wt = 0.0
            for j in edges[i]:
                t = trust[i * N + j]
                if t >= p["trust_threshold"]:
                    t_inf += t * beliefs[j]
                    t_wt  += t
            if t_wt > 0.0:
                external = t_inf / t_wt
                if p.get("contrarian"):
                    external = 1.0 - external
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
                p = _prof(i)
                if delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_b
        e_min = [abs(beliefs[i] - truth) for i in range(N) if roles[i] == "minority"]
        e_maj = [abs(beliefs[i] - truth) for i in range(N) if roles[i] == "majority"]
        e_all = [abs(beliefs[i] - truth) for i in range(N) if roles[i] != "liar"]

        errors_minority.append(sum(e_min) / max(1, len(e_min)))
        errors_majority.append(sum(e_maj) / max(1, len(e_maj)))
        errors_all.append(sum(e_all) / max(1, len(e_all)))

    return {
        "minority_profile":       minority_profile,
        "majority_profile":       majority_profile,
        "minority_final_error":   round(errors_minority[-1], 4),
        "majority_final_error":   round(errors_majority[-1], 4),
        "network_final_error":    round(errors_all[-1],      4),
        "minority_mean_error":    round(sum(errors_minority) / len(errors_minority), 4),
        "majority_mean_error":    round(sum(errors_majority) / len(errors_majority), 4),
    }


# ---------------------------------------------------------------------------
# Signal crossover sweep
# ---------------------------------------------------------------------------

def _signal_crossover(
    profiles_to_compare: list[str],
    n_agents: int = 50,
    n_steps: int = 300,
    seed: int = 42,
) -> list[dict]:
    """
    Sweep signal_weight from 0.0 to 0.10 in 20 steps.
    Find where DISSONANCE error crosses below/above CONFORMIST error.
    (Strong signal = cooperative env; weak signal = adversarial env.)
    """
    weights = [round(i * 0.005, 3) for i in range(21)]  # 0.000 to 0.100
    rows = []
    for sw in weights:
        results = {}
        for pname in profiles_to_compare:
            r = _run(pname, n_agents=n_agents, n_steps=n_steps, seed=seed,
                     signal_weight=sw, liar_fraction=0.0)
            results[pname] = r["final_error"]
        rows.append({"signal_weight": sw, **results})
    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

W = 70

def _rank_str(val: float, vals: list[float]) -> str:
    sorted_v = sorted(vals)
    rank = sorted_v.index(val) + 1
    stars = "★" if rank == 1 else ("·" if rank == len(vals) else " ")
    return f"{val:.4f} {stars}"


def print_environment_table(env_results: dict[str, dict[str, dict]]) -> None:
    envs = list(env_results.keys())
    profiles = ALL_PROFILES

    print("\n" + "=" * W)
    print("  COGNITIVE ECOLOGY — FINAL ERROR BY ENVIRONMENT")
    print("  ★ = best in environment  · = worst")
    print("=" * W)
    print(f"\n  {'profile':>12}", end="")
    for env in envs:
        print(f"  {env:>18}", end="")
    print(f"  {'avg_rank':>9}")
    print(f"  {'─' * (13 + 20 * len(envs) + 10)}")

    profile_ranks: dict[str, list[int]] = {p: [] for p in profiles}
    for env, results in env_results.items():
        vals = [results[p]["final_error"] for p in profiles]
        sorted_v = sorted(vals)
        for p in profiles:
            rank = sorted_v.index(results[p]["final_error"]) + 1
            profile_ranks[p].append(rank)

    for pname in profiles:
        print(f"  {pname:>12}", end="")
        for env, results in env_results.items():
            vals = [results[p]["final_error"] for p in profiles]
            v = results[pname]["final_error"]
            print(f"  {_rank_str(v, vals):>18}", end="")
        avg_rank = sum(profile_ranks[pname]) / len(profile_ranks[pname])
        print(f"  {avg_rank:>9.2f}")


def print_contrarian_note(env_results: dict) -> None:
    print(f"\n  CONTRARIAN mechanics note:")
    print(f"  → Updates toward (1 - trusted_mean) instead of trusted_mean")
    print(f"  → With liars at 0.25 (truth=0.75): contrarian drifts toward 0.75 (truth)")
    print(f"  → With honest network at 0.75: contrarian drifts toward 0.25 (away from truth)")
    if "consistent_liars" in env_results and "clean" in env_results:
        c_clean = env_results["clean"]["CONTRARIAN"]["final_error"]
        c_liar  = env_results["consistent_liars"]["CONTRARIAN"]["final_error"]
        print(f"  → clean error: {c_clean:.4f}  |  consistent_liar error: {c_liar:.4f}")
        if c_liar < c_clean:
            print(f"  CONFIRMED: CONTRARIAN performs BETTER under consistent-liar attack")


def print_embedding(results: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  EMBEDDING TEST — MINORITY IN MAJORITY NETWORK")
    print("  (20% minority embedded in 80% CONFORMIST, 20% consistent liars)")
    print("=" * W)
    for r in results:
        min_p = r["minority_profile"]
        print(f"\n  {min_p} minority vs CONFORMIST majority:")
        print(f"    minority final_error:  {r['minority_final_error']:.4f}")
        print(f"    majority final_error:  {r['majority_final_error']:.4f}")
        print(f"    network final_error:   {r['network_final_error']:.4f}")
        if r["minority_final_error"] < r["majority_final_error"] - 0.01:
            print(f"    → minority OUTPERFORMS majority in their own subgroup")
        elif r["minority_final_error"] > r["majority_final_error"] + 0.01:
            print(f"    → minority UNDERPERFORMS majority (isolation cost)")
        else:
            print(f"    → minority and majority converge similarly")


def print_crossover(rows: list[dict], profiles: list[str]) -> None:
    print("\n" + "=" * W)
    print("  SIGNAL CROSSOVER — where does truth-injection change the ranking?")
    print("  (signal_weight=0 = pure adversarial; 0.10 = strong truth signal)")
    print("=" * W)
    print(f"\n  {'sw':>6}", end="")
    for p in profiles:
        print(f"  {p:>12}", end="")
    print()
    print(f"  {'─' * (7 + 14 * len(profiles))}")

    crossover_logged: set[tuple] = set()
    prev_row = None
    for row in rows:
        sw = row["signal_weight"]
        print(f"  {sw:>6.3f}", end="")
        for p in profiles:
            v = row[p]
            print(f"  {v:>12.4f}", end="")
        print()

        if prev_row:
            for i, p1 in enumerate(profiles):
                for p2 in profiles[i+1:]:
                    pair = tuple(sorted([p1, p2]))
                    if pair not in crossover_logged:
                        # Check sign flip in (p1_err - p2_err)
                        prev_diff = prev_row[p1] - prev_row[p2]
                        curr_diff = row[p1]    - row[p2]
                        if prev_diff * curr_diff < 0:
                            winner = p2 if curr_diff > 0 else p1
                            loser  = p1 if curr_diff > 0 else p2
                            print(f"  ↑ CROSSOVER at sw≈{sw:.3f}: {winner} overtakes {loser}")
                            crossover_logged.add(pair)
        prev_row = row


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Building environments...")

    environments: dict[str, dict] = {}

    print("  clean (no liars)...")
    environments["clean"] = _run_all(ALL_PROFILES, liar_fraction=0.0, n_steps=200)

    print("  consistent_liars 20%...")
    environments["consistent_liars"] = _run_all(
        ALL_PROFILES, liar_fraction=0.20, liar_type="consistent", n_steps=200)

    print("  noisy_liars 20%...")
    environments["noisy_liars"] = _run_all(
        ALL_PROFILES, liar_fraction=0.20, liar_type="noisy", n_steps=200)

    print("  moving_truth (signal=0.02)...")
    def drift(s): return 0.25 + 0.50 * (s / 199)
    environments["moving_truth"] = _run_all(
        ALL_PROFILES, truth_fn=drift, signal_weight=0.02, n_steps=200)

    print("  adversarial_heavy (40% consistent liars)...")
    environments["heavy_adversarial"] = _run_all(
        ALL_PROFILES, liar_fraction=0.40, liar_type="consistent", n_steps=200)

    print_environment_table(environments)
    print_contrarian_note(environments)

    print("\nRunning embedding tests...")
    embed_results = []
    for minority in ("SELECTIVE", "PARANOID", "CONTRARIAN", "DIPLOMAT"):
        r = _run_embedding(
            minority_profile=minority,
            majority_profile="CONFORMIST",
            minority_fraction=0.20,
            liar_fraction=0.20,
        )
        embed_results.append(r)
    print_embedding(embed_results)

    print("\nRunning signal crossover sweep (DISSONANCE vs CONFORMIST vs DIPLOMAT)...")
    compare_profiles = ["SELECTIVE", "CONFORMIST", "DIPLOMAT", "PARANOID"]
    crossover_rows = _signal_crossover(compare_profiles, n_steps=300)
    print_crossover(crossover_rows, compare_profiles)

    # Save
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "godot_profile_comparison.json"
    save: dict[str, Any] = {}
    for env_name, env_data in environments.items():
        save[env_name] = {
            p: {k: v for k, v in r.items() if k != "steps"}
            for p, r in env_data.items()
        }
    save["embedding"] = embed_results
    save["crossover"] = crossover_rows
    with open(out, "w") as f:
        json.dump(save, f, indent=2)
    print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

