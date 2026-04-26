"""
domains/games/probes/godot_ecology.py

Helix — Mixed Cognitive Ecology
All 6 profiles competing simultaneously in the same network.

Profiles:
  CONFORMIST    maximum social sensitivity, zero resistance
  IMPULSIVE     fast volatile, high noise, fires on everything
  DIPLOMAT      balanced, moderate on every axis
  SELECTIVE     high self-weight, slow trust, cynicism, sparse network
  PARANOID      near-total isolation, extreme cynicism
  CONTRARIAN    inverts consensus signal (moves toward 1 - trusted_mean)

Experiments:
  1. mixed_monoculture
     Equal fractions of all 6 types in one network.
     Per-type accuracy within the shared environment.
     With and without liars.

  2. contrarian_sweep
     Fix remaining agents as CONFORMIST.
     Vary CONTRARIAN fraction 0%→60%.
     Find optimal CONTRARIAN density for network accuracy under consistent liars.

  3. profile_antagonism
     All pairwise 50/50 splits. Which pair produces best / worst collective outcome?

  4. evolutionary_pressure
     Start 100% CONFORMIST. Replace worst-performing agents with SELECTIVE each round.
     Does SELECTIVE spread or die out? Tracks population composition over time.
"""

from __future__ import annotations

import json
import math
import random
import sys
from itertools import combinations
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
    "CONTRARIAN": {
        "trust_threshold":    0.20,
        "trust_build_rate":   0.20,
        "trust_decay_rate":   0.05,
        "self_weight":        0.60,
        "update_rate":        0.35,
        "cynicism_threshold": 0.40,
        "noise_std":          0.02,
        "connection_prob":    0.35,
        "contrarian":         True,
    },
}

ALL_PROFILES = list(PROFILES.keys())

# ---------------------------------------------------------------------------
# Heterogeneous network simulation
# ---------------------------------------------------------------------------

def _run_mixed(
    population: list[str],         # profile name per agent (including liars marked as "LIAR")
    n_steps: int = 200,
    seed: int = 42,
    truth: float = 0.75,
    signal_weight: float = 0.0,
    truth_fn: Callable[[int], float] | None = None,
) -> dict:
    """
    Core heterogeneous simulation.
    population[i] = profile name for agent i (or "LIAR").
    Each agent uses their own profile for trust and belief updates.
    Graph edges drawn with probability = average of the two agents' connection_probs.
    Trust is asymmetric: agent i uses their own parameters to trust agent j.
    """
    rng = random.Random(seed)
    N = len(population)
    is_liar = [population[i] == "LIAR" for i in range(N)]

    beliefs = [rng.random() for _ in range(N)]
    for i in range(N):
        if is_liar[i]:
            beliefs[i] = 1.0 - truth

    # Build graph: connection prob = average of both agents' probs
    edges: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            p_i = PROFILES.get(population[i], PROFILES["CONFORMIST"])["connection_prob"]
            p_j = PROFILES.get(population[j], PROFILES["CONFORMIST"])["connection_prob"]
            if rng.random() < 0.5 * (p_i + p_j):
                edges[i].append(j)
                edges[j].append(i)

    trust = [0.0] * (N * N)
    errors_by_type: dict[str, list[list[float]]] = {t: [] for t in ALL_PROFILES}
    errors_network: list[float] = []

    for step in range(n_steps):
        current_truth = truth_fn(step) if truth_fn else truth
        prev = beliefs[:]
        new_b = beliefs[:]

        for i in range(N):
            if is_liar[i]:
                new_b[i] = 1.0 - truth
                continue

            p = PROFILES[population[i]]
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
                    external = 1.0 - external
                new_b[i] = (
                    p["self_weight"] * beliefs[i]
                    + (1.0 - p["self_weight"]) * p["update_rate"] * external
                    + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i]
                )

            if signal_weight > 0.0:
                new_b[i] += signal_weight * (current_truth - new_b[i])
            if p["noise_std"] > 0.0:
                new_b[i] += rng.uniform(-p["noise_std"], p["noise_std"])
            new_b[i] = max(0.0, min(1.0, new_b[i]))

        # Trust update
        for i in range(N):
            if is_liar[i]:
                continue
            p = PROFILES[population[i]]
            for j in edges[i]:
                delta = abs(beliefs[j] - prev[j])
                t = trust[i * N + j]
                if delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_b

        for ptype in ALL_PROFILES:
            errs = [abs(beliefs[i] - current_truth)
                    for i in range(N) if population[i] == ptype]
            errors_by_type[ptype].append(sum(errs) / max(1, len(errs)) if errs else float("nan"))

        honest = [beliefs[i] for i in range(N) if not is_liar[i]]
        errors_network.append(sum(abs(b - current_truth) for b in honest) / max(1, len(honest)))

    # Summarize
    type_final: dict[str, float] = {}
    type_mean: dict[str, float] = {}
    for ptype in ALL_PROFILES:
        series = [v for v in errors_by_type[ptype] if not math.isnan(v)]
        if series:
            type_final[ptype] = round(series[-1], 4)
            type_mean[ptype]  = round(sum(series) / len(series), 4)
        else:
            type_final[ptype] = float("nan")
            type_mean[ptype]  = float("nan")

    return {
        "network_final_error": round(errors_network[-1], 4),
        "network_mean_error":  round(sum(errors_network) / len(errors_network), 4),
        "type_final_error":    type_final,
        "type_mean_error":     type_mean,
    }


def _build_population(
    fractions: dict[str, float],
    n_agents: int,
    liar_fraction: float = 0.0,
    seed: int = 42,
) -> list[str]:
    """Build agent population list from type fractions."""
    rng = random.Random(seed)
    n_liars = int(n_agents * liar_fraction)
    n_honest = n_agents - n_liars

    agents: list[str] = []
    types  = list(fractions.keys())
    weights= [fractions[t] for t in types]
    total  = sum(weights)
    weights= [w / total for w in weights]

    for _ in range(n_honest):
        agents.append(rng.choices(types, weights=weights)[0])

    agents += ["LIAR"] * n_liars
    rng.shuffle(agents)
    return agents


# ---------------------------------------------------------------------------
# Experiment 1: Mixed monoculture
# ---------------------------------------------------------------------------

def run_mixed_monoculture(
    n_agents: int = 120,   # ~20 per type
    n_steps: int = 200,
    seed: int = 42,
    liar_fraction: float = 0.20,
) -> dict:
    equal = {p: 1.0 for p in ALL_PROFILES}
    pop_clean = _build_population(equal, n_agents, liar_fraction=0.0, seed=seed)
    pop_liars = _build_population(equal, n_agents, liar_fraction=liar_fraction, seed=seed)

    return {
        "clean":   _run_mixed(pop_clean, n_steps=n_steps, seed=seed),
        "liars":   _run_mixed(pop_liars, n_steps=n_steps, seed=seed),
    }


# ---------------------------------------------------------------------------
# Experiment 2: Contrarian density sweep
# ---------------------------------------------------------------------------

def run_contrarian_sweep(
    n_agents: int = 100,
    n_steps:  int = 200,
    seed:     int = 42,
    liar_fraction: float = 0.20,
) -> list[dict]:
    fractions_contrarian = [i * 0.05 for i in range(13)]  # 0% to 60%
    rows = []
    for fc in fractions_contrarian:
        fc = round(fc, 2)
        fracs = {"CONTRARIAN": fc, "CONFORMIST": max(0.0, 1.0 - fc)}
        pop = _build_population(fracs, n_agents, liar_fraction=liar_fraction, seed=seed)
        r = _run_mixed(pop, n_steps=n_steps, seed=seed)
        n_contrarian = sum(1 for a in pop if a == "CONTRARIAN")
        n_conformist = sum(1 for a in pop if a == "CONFORMIST")
        rows.append({
            "contrarian_fraction": fc,
            "n_contrarian": n_contrarian,
            "n_conformist": n_conformist,
            "network_final_error": r["network_final_error"],
            "contrarian_error": r["type_final_error"].get("CONTRARIAN", float("nan")),
            "conformist_error": r["type_final_error"].get("CONFORMIST", float("nan")),
        })
    return rows


# ---------------------------------------------------------------------------
# Experiment 3: Profile antagonism — all pairwise 50/50 splits
# ---------------------------------------------------------------------------

def run_profile_antagonism(
    n_agents: int = 60,
    n_steps:  int = 200,
    seed:     int = 42,
    liar_fraction: float = 0.20,
) -> list[dict]:
    rows = []
    for p1, p2 in combinations(ALL_PROFILES, 2):
        fracs = {p1: 0.50, p2: 0.50}
        pop = _build_population(fracs, n_agents, liar_fraction=liar_fraction, seed=seed)
        r = _run_mixed(pop, n_steps=n_steps, seed=seed)
        e1 = r["type_final_error"].get(p1, float("nan"))
        e2 = r["type_final_error"].get(p2, float("nan"))
        winner = p1 if e1 < e2 else p2
        rows.append({
            "p1": p1, "p2": p2,
            "p1_error": e1, "p2_error": e2,
            "network_error": r["network_final_error"],
            "winner": winner,
            "delta": round(abs(e1 - e2), 4),
        })
    rows.sort(key=lambda r: r["network_error"])
    return rows


# ---------------------------------------------------------------------------
# Experiment 4: Evolutionary pressure
# ---------------------------------------------------------------------------

def run_evolutionary_pressure(
    n_agents:      int   = 60,
    n_steps_eval:  int   = 100,   # steps per evaluation round
    n_rounds:      int   = 20,    # number of replacement rounds
    replace_n:     int   = 3,     # agents replaced per round
    seed:          int   = 42,
    liar_fraction: float = 0.20,
    invader:       str   = "SELECTIVE",
    host:          str   = "CONFORMIST",
) -> list[dict]:
    """
    Start with 100% host. Each round:
      1. Run simulation for n_steps_eval steps.
      2. Find the replace_n worst-performing non-liar agents (highest error).
      3. Replace them with the invader type.
    Track population composition and network accuracy over rounds.
    """
    rng = random.Random(seed)
    truth = 0.75
    n_liars = int(n_agents * liar_fraction)

    # Initial population: all host + liars
    population = [host] * (n_agents - n_liars) + ["LIAR"] * n_liars
    rng.shuffle(population)

    history = []

    for rnd in range(n_rounds):
        # Count composition
        counts = {t: population.count(t) for t in ALL_PROFILES + ["LIAR"]}

        # Run simulation and track per-agent final error
        N = len(population)
        is_liar = [population[i] == "LIAR" for i in range(N)]
        beliefs = [rng.random() for _ in range(N)]
        for i in range(N):
            if is_liar[i]:
                beliefs[i] = 1.0 - truth
        trust = [0.0] * (N * N)

        # Build graph
        edges: list[list[int]] = [[] for _ in range(N)]
        for i in range(N):
            for j in range(i + 1, N):
                p_i = PROFILES.get(population[i], PROFILES["CONFORMIST"])["connection_prob"]
                p_j = PROFILES.get(population[j], PROFILES["CONFORMIST"])["connection_prob"]
                if rng.random() < 0.5 * (p_i + p_j):
                    edges[i].append(j)
                    edges[j].append(i)

        for _ in range(n_steps_eval):
            prev = beliefs[:]
            new_b = beliefs[:]
            for i in range(N):
                if is_liar[i]:
                    new_b[i] = 1.0 - truth
                    continue
                p = PROFILES[population[i]]
                t_inf = 0.0; t_wt = 0.0
                for j in edges[i]:
                    t = trust[i * N + j]
                    if t >= p["trust_threshold"]:
                        t_inf += t * beliefs[j]
                        t_wt  += t
                if t_wt > 0.0:
                    external = t_inf / t_wt
                    if p["contrarian"]:
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
                if is_liar[i]:
                    continue
                p = PROFILES[population[i]]
                for j in edges[i]:
                    delta = abs(beliefs[j] - prev[j])
                    t = trust[i * N + j]
                    if delta < p["cynicism_threshold"]:
                        trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                    else:
                        trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])
            beliefs = new_b

        # Score each agent
        agent_errors = [(abs(beliefs[i] - truth), i)
                        for i in range(N) if not is_liar[i]]
        agent_errors.sort(reverse=True)  # worst first

        net_error = sum(abs(beliefs[i] - truth) for i in range(N) if not is_liar[i])
        net_error /= max(1, n_agents - n_liars)

        history.append({
            "round": rnd,
            "n_invader":     counts.get(invader, 0),
            "n_host":        counts.get(host, 0),
            "n_liars":       counts["LIAR"],
            "network_error": round(net_error, 4),
            "invader_frac":  round(counts.get(invader, 0) / max(1, n_agents - n_liars), 3),
        })

        # Replace worst replace_n agents with invader
        replaced = 0
        for _, idx in agent_errors:
            if replaced >= replace_n:
                break
            if population[idx] != invader:
                population[idx] = invader
                replaced += 1

    return history


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

W = 70

def print_mixed_monoculture(result: dict) -> None:
    print("\n" + "=" * W)
    print("  MIXED MONOCULTURE  (all 6 types, equal fractions, same network)")
    print("=" * W)

    for env in ("clean", "liars"):
        label = "no liars" if env == "clean" else "20% consistent liars"
        r = result[env]
        print(f"\n  env = {label.upper()}")
        print(f"  network_final_error: {r['network_final_error']:.4f}")
        print(f"\n  {'profile':>12}  {'final_error':>12}  {'mean_error':>12}  rank")
        print(f"  {'─' * 48}")
        sorted_types = sorted(ALL_PROFILES, key=lambda t: r["type_final_error"].get(t, 99))
        for rank, ptype in enumerate(sorted_types, 1):
            fe = r["type_final_error"].get(ptype, float("nan"))
            me = r["type_mean_error"].get(ptype, float("nan"))
            star = " ★" if rank == 1 else (" ·" if rank == len(sorted_types) else "")
            print(f"  {ptype:>12}  {fe:>12.4f}  {me:>12.4f}  #{rank}{star}")


def print_contrarian_sweep(rows: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  CONTRARIAN DENSITY SWEEP  (CONTRARIAN + CONFORMIST, 20% consistent liars)")
    print("=" * W)
    print(f"\n  {'frac':>6}  {'n_ctr':>6}  {'net_err':>9}  {'ctr_err':>9}  {'cnf_err':>9}")
    print(f"  {'─' * 45}")
    best = min(rows, key=lambda r: r["network_final_error"])
    for r in rows:
        marker = " ← optimal" if r is best else ""
        ctr = f"{r['contrarian_error']:.4f}" if not math.isnan(r["contrarian_error"]) else "   —  "
        cnf = f"{r['conformist_error']:.4f}" if not math.isnan(r["conformist_error"]) else "   —  "
        print(f"  {r['contrarian_fraction']:>6.2f}  {r['n_contrarian']:>6}  "
              f"{r['network_final_error']:>9.4f}  {ctr:>9}  {cnf:>9}{marker}")


def print_antagonism(rows: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  PROFILE ANTAGONISM  (50/50 splits, 20% consistent liars)")
    print("  sorted by network accuracy (best pairings first)")
    print("=" * W)
    print(f"\n  {'pair':>24}  {'net_err':>9}  {'p1_err':>8}  {'p2_err':>8}  {'winner':>12}  {'Δ':>6}")
    print(f"  {'─' * 72}")
    for r in rows:
        pair = f"{r['p1']} / {r['p2']}"
        print(f"  {pair:>24}  {r['network_error']:>9.4f}  "
              f"{r['p1_error']:>8.4f}  {r['p2_error']:>8.4f}  "
              f"{r['winner']:>12}  {r['delta']:>6.4f}")


def print_evolutionary(history: list[dict], invader: str, host: str) -> None:
    print("\n" + "=" * W)
    print(f"  EVOLUTIONARY PRESSURE  ({invader} invades {host})")
    print(f"  3 worst agents replaced per round, 20% consistent liars")
    print("=" * W)
    print(f"\n  {'round':>6}  {'n_invader':>10}  {'inv_frac':>9}  {'net_err':>9}")
    print(f"  {'─' * 40}")
    for r in history:
        print(f"  {r['round']:>6}  {r['n_invader']:>10}  "
              f"{r['invader_frac']:>9.3f}  {r['network_error']:>9.4f}")

    start_err = history[0]["network_error"]
    end_err   = history[-1]["network_error"]
    delta     = end_err - start_err
    direction = "improved" if delta < -0.005 else ("degraded" if delta > 0.005 else "unchanged")
    final_frac = history[-1]["invader_frac"]
    print(f"\n  Network accuracy {direction} by {abs(delta):.4f} as {invader} reached {final_frac:.0%}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Experiment 1: Mixed monoculture (all 6 types in one network)...")
    mono = run_mixed_monoculture(n_agents=120, n_steps=200)
    print_mixed_monoculture(mono)

    print("\nExperiment 2: Contrarian density sweep...")
    sweep = run_contrarian_sweep(n_agents=100, n_steps=200)
    print_contrarian_sweep(sweep)

    print("\nExperiment 3: Profile antagonism (all 15 pairwise splits)...")
    antag = run_profile_antagonism(n_agents=60, n_steps=200)
    print_antagonism(antag)

    print("\nExperiment 4a: SELECTIVE invades CONFORMIST...")
    evo_selective = run_evolutionary_pressure(
        n_agents=60, n_rounds=20, replace_n=3,
        invader="SELECTIVE", host="CONFORMIST",
    )
    print_evolutionary(evo_selective, "SELECTIVE", "CONFORMIST")

    print("\nExperiment 4b: CONTRARIAN invades CONFORMIST...")
    evo_contrarian = run_evolutionary_pressure(
        n_agents=60, n_rounds=20, replace_n=3,
        invader="CONTRARIAN", host="CONFORMIST",
    )
    print_evolutionary(evo_contrarian, "CONTRARIAN", "CONFORMIST")

    print("\nExperiment 4c: CONFORMIST invades SELECTIVE...")
    evo_reverse = run_evolutionary_pressure(
        n_agents=60, n_rounds=20, replace_n=3,
        invader="CONFORMIST", host="SELECTIVE",
    )
    print_evolutionary(evo_reverse, "CONFORMIST", "SELECTIVE")

    # Save
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "godot_ecology.json"
    with open(out, "w") as f:
        json.dump({
            "mixed_monoculture": mono,
            "contrarian_sweep":  sweep,
            "antagonism":        antag,
            "evolutionary": {
                "selective_invades_conformist":  evo_selective,
                "contrarian_invades_conformist": evo_contrarian,
                "conformist_invades_selective":  evo_reverse,
            },
        }, f, indent=2)
    print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
