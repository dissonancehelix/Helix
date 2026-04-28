"""
model/domains/games/probes/gwt_adversarial_formalism.py

Helix — Path 4: Adversarial Ecology Formalism

The ecology experiments (godot_ecology.py) produced the strongest findings
of the whole cognition arc. This probe formalizes them mathematically and
tests the derivations against the simulation.

--- CONTRARIAN IMMUNITY ---

Observation: CONTRARIAN achieves network accuracy comparable to SELECTIVE
specifically under consistent adversarial noise.

Mechanism: CONTRARIAN updates toward (1 - trusted_mean).
  If liars consistently anchor at L (false belief), CONTRARIAN moves to 1-L.
  CONTRARIAN error = |1 - L - truth|
  CONFORMIST error  = |L - truth|

Immunity condition: CONTRARIAN error < CONFORMIST error
  |1 - L - truth| < |L - truth|
  Case: L > truth (liars oversell, L = truth + ε)
    LHS = |1 - (truth + ε) - truth| = |1 - 2·truth - ε|
    RHS = ε
    For truth ≈ 0.5: LHS ≈ |−ε| = ε → tie
    For truth > 0.5, L = 1 - truth + δ (liars pushing wrong direction):
      CONTRARIAN gets 1 - L = truth - δ → nearly correct
    For truth < 0.5, liars pushing L > 0.5:
      CONTRARIAN gets 1 - L < 0.5 → closer to truth than L

  Simplified: CONTRARIAN has immunity whenever liars are on the opposite side
  of 0.5 from truth, i.e., sign(L - 0.5) ≠ sign(truth - 0.5).

  Perfect immunity case: L = 1 - truth (liars anchor exactly opposite to truth).
  Then CONTRARIAN gets 1 - L = truth exactly.

Prediction (testable): CONTRARIAN advantage over CONFORMIST should peak when
  liar_anchor ≈ 1 - truth, and decay symmetrically as liar_anchor approaches truth.

--- SELECTIVE NICHE ---

Observation: SELECTIVE wins 100/100 seeds against consistent adversarial noise
because self_weight caps external influence at update_rate × (1 - self_weight)
per step = 0.12 × 0.15 = 0.018/step.

Formalized: max external influence per step = update_rate × (1 - self_weight)
  For SELECTIVE: 0.12 × 0.15 = 0.018
  For CONFORMIST: 0.70 × 0.95 = 0.665

Signal crossover: CONFORMIST overtakes SELECTIVE at signal_weight ≈ 0.01.
Prediction: crossover occurs when signal_weight > update_rate × (1 - self_weight)
  For SELECTIVE: crossover at signal_weight ≈ 0.018

--- HETEROGENEOUS NETWORK DOMINANCE ---

Observation: mixed SELECTIVE + CONTRARIAN networks survive adversarial environments
better than homogeneous CONFORMIST networks.

Prediction: the optimal CONTRARIAN fraction in a CONFORMIST network is the
liar fraction (c* ≈ f_liar), because each CONTRARIAN exactly cancels one liar's
influence in expectation.

This probe tests all three predictions.
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

PROFILES: dict[str, dict] = {
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


# ---------------------------------------------------------------------------
# Simulation core
# ---------------------------------------------------------------------------

def _run_mixed(
    population: list[str],
    truth: float,
    liar_anchor: float,
    n_steps: int,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    N = len(population)
    is_liar = [population[i] == "LIAR" for i in range(N)]

    beliefs = [rng.random() for _ in range(N)]
    for i in range(N):
        if is_liar[i]:
            beliefs[i] = liar_anchor

    edges: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            p_i = PROFILES.get(population[i], PROFILES["CONFORMIST"])["connection_prob"]
            p_j = PROFILES.get(population[j], PROFILES["CONFORMIST"])["connection_prob"]
            if rng.random() < 0.5 * (p_i + p_j):
                edges[i].append(j)
                edges[j].append(i)

    trust = [0.0] * (N * N)

    for step in range(n_steps):
        prev = beliefs[:]
        new_b = beliefs[:]

        for i in range(N):
            if is_liar[i]:
                new_b[i] = liar_anchor
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
            for j in edges[i]:
                delta = abs(beliefs[j] - prev[j])
                t = trust[i * N + j]
                p = PROFILES.get(population[i], PROFILES["CONFORMIST"])
                if delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_b

    non_liar_beliefs = [b for i, b in enumerate(beliefs) if not is_liar[i]]
    final_mean = sum(non_liar_beliefs) / len(non_liar_beliefs) if non_liar_beliefs else 0.5
    error = abs(final_mean - truth)
    return {"final_mean": round(final_mean, 4), "error": round(error, 4)}


def _mean_error(
    profile_type: str,
    n_agents: int,
    liar_frac: float,
    truth: float,
    liar_anchor: float,
    n_seeds: int,
    n_steps: int,
) -> float:
    n_liars = int(n_agents * liar_frac)
    errors = []
    for seed in range(n_seeds):
        pop = [profile_type] * (n_agents - n_liars) + ["LIAR"] * n_liars
        r = _run_mixed(pop, truth, liar_anchor, n_steps, seed)
        errors.append(r["error"])
    return sum(errors) / len(errors)


# ---------------------------------------------------------------------------
# Experiment 1: CONTRARIAN immunity vs liar anchor
# ---------------------------------------------------------------------------

def exp1_contrarian_immunity(n_agents: int = 80, n_seeds: int = 8, n_steps: int = 200) -> dict:
    """
    Vary liar_anchor from 0.1 to 0.9 with truth=0.75, liar_frac=0.25.
    Prediction: CONTRARIAN advantage peaks at liar_anchor ≈ 1 - truth = 0.25.
    """
    truth = 0.75
    liar_frac = 0.25
    anchors = [round(0.1 + i * 0.1, 1) for i in range(9)]   # 0.1 .. 0.9
    predicted_peak = round(1.0 - truth, 2)  # 0.25

    rows = []
    for anchor in anchors:
        conf_err = _mean_error("CONFORMIST", n_agents, liar_frac, truth, anchor, n_seeds, n_steps)
        cont_err = _mean_error("CONTRARIAN", n_agents, liar_frac, truth, anchor, n_seeds, n_steps)
        advantage = conf_err - cont_err   # positive = CONTRARIAN is better
        rows.append({
            "liar_anchor":           anchor,
            "conformist_error":      round(conf_err, 4),
            "contrarian_error":      round(cont_err, 4),
            "contrarian_advantage":  round(advantage, 4),
        })
        print(f"  anchor={anchor:.1f}  CONF={conf_err:.3f}  CONT={cont_err:.3f}  adv={advantage:+.3f}")

    advantages = [r["contrarian_advantage"] for r in rows]
    peak_anchor = anchors[advantages.index(max(advantages))]
    peak_error = abs(peak_anchor - predicted_peak)

    verdict = (
        f"confirmed — peak advantage at anchor={peak_anchor} (predicted {predicted_peak}, error={peak_error:.2f})"
        if peak_error <= 0.15
        else f"not confirmed — peak at anchor={peak_anchor} vs predicted {predicted_peak}"
    )

    return {
        "truth": truth, "liar_frac": liar_frac,
        "predicted_peak_anchor": predicted_peak,
        "observed_peak_anchor": peak_anchor,
        "rows": rows,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Experiment 2: SELECTIVE max-influence cap and signal crossover
# ---------------------------------------------------------------------------

def exp2_selective_niche(n_agents: int = 80, n_seeds: int = 10, n_steps: int = 200) -> dict:
    """
    Sweep signal_weight (reliable external signal) from 0 to 0.05.
    Prediction: CONFORMIST overtakes SELECTIVE at signal_weight ≈ 0.018
    (= update_rate × (1 - self_weight) = 0.12 × 0.15 for SELECTIVE).

    Measured as: final error vs truth=0.75 with no liars, just a clean signal.
    """
    truth = 0.75
    predicted_crossover = PROFILES["SELECTIVE"]["update_rate"] * (1.0 - PROFILES["SELECTIVE"]["self_weight"])

    signal_weights = [0.0, 0.005, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050]

    rows = []
    for sw in signal_weights:
        sel_errs, conf_errs = [], []
        for seed in range(n_seeds):
            for profile_name, errs in [("SELECTIVE", sel_errs), ("CONFORMIST", conf_errs)]:
                p = PROFILES[profile_name]
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

                for step in range(n_steps):
                    prev = beliefs[:]
                    new_b = beliefs[:]
                    for i in range(N):
                        t_inf = 0.0; t_wt = 0.0
                        for j in edges[i]:
                            t = trust[i * N + j]
                            if t >= p["trust_threshold"]:
                                t_inf += t * beliefs[j]; t_wt += t
                        if t_wt > 0.0:
                            external = t_inf / t_wt
                            new_b[i] = (p["self_weight"] * beliefs[i]
                                       + (1.0 - p["self_weight"]) * p["update_rate"] * external
                                       + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i])
                        if sw > 0.0:
                            new_b[i] += sw * (truth - new_b[i])
                        if p["noise_std"] > 0.0:
                            new_b[i] += rng.uniform(-p["noise_std"], p["noise_std"])
                        new_b[i] = max(0.0, min(1.0, new_b[i]))
                    for i in range(N):
                        for j in edges[i]:
                            delta = abs(beliefs[j] - prev[j]); t = trust[i * N + j]
                            trust[i * N + j] = (min(1.0, t + p["trust_build_rate"])
                                               if delta < p["cynicism_threshold"]
                                               else max(0.0, t - p["trust_decay_rate"]))
                    beliefs = new_b

                errs.append(abs(sum(beliefs) / N - truth))

        sel_mean  = sum(sel_errs)  / len(sel_errs)
        conf_mean = sum(conf_errs) / len(conf_errs)
        rows.append({
            "signal_weight": sw,
            "selective_error":   round(sel_mean, 4),
            "conformist_error":  round(conf_mean, 4),
            "selective_wins":    sel_mean < conf_mean,
        })
        winner = "SELECTIVE" if sel_mean < conf_mean else "CONFORMIST"
        print(f"  sw={sw:.3f}  SEL={sel_mean:.3f}  CONF={conf_mean:.3f}  winner={winner}")

    # Find empirical crossover (first sw where CONFORMIST wins)
    crossover_observed = next(
        (r["signal_weight"] for r in rows if not r["selective_wins"]),
        None
    )
    crossover_error = abs(crossover_observed - predicted_crossover) if crossover_observed is not None else None

    verdict = "unsupported"
    if crossover_observed is not None and crossover_error is not None:
        if crossover_error <= 0.010:
            verdict = f"confirmed — crossover at sw={crossover_observed} (predicted {predicted_crossover:.3f})"
        else:
            verdict = f"not confirmed — crossover at sw={crossover_observed} vs predicted {predicted_crossover:.3f}"

    return {
        "predicted_crossover": round(predicted_crossover, 4),
        "observed_crossover":  crossover_observed,
        "rows": rows,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Experiment 3: Optimal CONTRARIAN fraction
# ---------------------------------------------------------------------------

def exp3_optimal_contrarian_fraction(n_agents: int = 80, n_seeds: int = 8, n_steps: int = 200) -> dict:
    """
    Fix truth=0.75, liars at 20% (anchor=0.25 — opposite side).
    Vary CONTRARIAN fraction from 0% to 50% in a mostly-CONFORMIST network.
    Prediction: optimal CONTRARIAN fraction ≈ liar fraction ≈ 0.20.
    """
    truth = 0.75
    liar_frac = 0.20
    liar_anchor = 1.0 - truth   # 0.25 — worst case for CONFORMIST, best for CONTRARIAN
    n_liars = int(n_agents * liar_frac)
    predicted_optimal = liar_frac

    cont_fracs = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
    rows = []

    for cf in cont_fracs:
        n_cont = int(n_agents * cf)
        n_conf = n_agents - n_liars - n_cont
        if n_conf < 0:
            continue

        errors = []
        for seed in range(n_seeds):
            pop = (["CONFORMIST"] * n_conf
                   + ["CONTRARIAN"] * n_cont
                   + ["LIAR"] * n_liars)
            r = _run_mixed(pop, truth, liar_anchor, n_steps, seed)
            errors.append(r["error"])

        mean_err = sum(errors) / len(errors)
        rows.append({
            "contrarian_frac": cf,
            "mean_error":      round(mean_err, 4),
            "n_contrarian":    n_cont,
            "n_conformist":    n_conf,
            "n_liars":         n_liars,
        })
        print(f"  cf={cf:.2f}  n_cont={n_cont}  n_conf={n_conf}  n_liars={n_liars}  error={mean_err:.3f}")

    if not rows:
        return {"rows": [], "verdict": "no valid conditions"}

    best = min(rows, key=lambda r: r["mean_error"])
    observed_optimal = best["contrarian_frac"]
    opt_error = abs(observed_optimal - predicted_optimal)

    verdict = (
        f"confirmed — optimal CONTRARIAN fraction={observed_optimal} (predicted {predicted_optimal}, error={opt_error:.2f})"
        if opt_error <= 0.10
        else f"not confirmed — optimal at {observed_optimal} vs predicted {predicted_optimal}"
    )

    return {
        "truth": truth, "liar_frac": liar_frac, "liar_anchor": liar_anchor,
        "predicted_optimal_contrarian_frac": predicted_optimal,
        "observed_optimal_contrarian_frac": observed_optimal,
        "rows": rows,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Path 4: Adversarial Ecology Formalism ===\n")

    print("--- Exp 1: CONTRARIAN immunity vs liar anchor ---")
    e1 = exp1_contrarian_immunity()
    print(f"  Verdict: {e1['verdict']}\n")

    print("--- Exp 2: SELECTIVE niche / signal crossover ---")
    e2 = exp2_selective_niche()
    print(f"  Verdict: {e2['verdict']}\n")

    print("--- Exp 3: Optimal CONTRARIAN fraction ---")
    e3 = exp3_optimal_contrarian_fraction()
    print(f"  Verdict: {e3['verdict']}\n")

    result = {
        "exp1_contrarian_immunity": e1,
        "exp2_selective_niche":     e2,
        "exp3_optimal_contrarian":  e3,
        "theoretical_summary": {
            "contrarian_immunity_condition":
                "CONTRARIAN beats CONFORMIST when sign(liar_anchor - 0.5) ≠ sign(truth - 0.5); "
                "perfect immunity when liar_anchor = 1 - truth",
            "selective_max_influence_per_step":
                "update_rate × (1 - self_weight) = 0.012 × 0.15 = 0.018/step",
            "crossover_condition":
                "CONFORMIST wins when signal_weight > update_rate × (1 - self_weight)",
            "optimal_contrarian_fraction":
                "c* ≈ liar_fraction — each CONTRARIAN cancels one liar in expectation",
        },
    }

    dest = ARTIFACTS / "gwt_adversarial_formalism.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved → {dest}")


if __name__ == "__main__":
    main()

