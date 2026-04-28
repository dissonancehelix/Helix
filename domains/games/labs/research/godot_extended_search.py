"""
domains/games/model/probes/godot_extended_search.py

Helix — Extended Search: Three follow-up experiments.

A. self_weight_isolation
   Run three profiles (baseline sw=0, sw_only sw=0.85, full DISSONANCE) against
   consistent liars across liar fractions. Isolates whether self_weight is doing
   all the work and cynicism adds anything.

B. calibrated_attack
   Two adversary strategies that know the architecture:
     slow_drift:           liar drifts truth→0 at 0.003/step (below cynicism_threshold=0.20)
                           builds full trust, then pulls down continuously
     patient_then_attack:  liar holds neutral (0.50) for 100 steps, then snaps to 0.0
                           trust is built during patience phase; snap triggers cynicism
   Which attack is more damaging? Does cynicism matter?

C. post_collapse_tracking
   Long run (500 steps). Truth drifts 0.25→0.75 over 500 steps.
   Each step, agents receive a weak truth injection: Δbelief += signal_weight*(truth-belief)
   This simulates agents receiving ambient environmental signals.
   Key question: which profile maintains lower tracking error over the full run?
   Does DISSONANCE's noise_std allow re-opening after collapse while baseline stays frozen?
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
sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# ---------------------------------------------------------------------------
# Profile definitions
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

# Derived profiles for experiment A
def _make_sw_only() -> dict:
    """Baseline parameters but with DISSONANCE's self_weight. Isolates sw effect."""
    p = dict(PROFILES["baseline"])
    p["self_weight"] = 0.85
    return p

def _make_cynicism_only() -> dict:
    """Baseline parameters but with DISSONANCE's cynicism + trust mechanics. No sw."""
    p = dict(PROFILES["baseline"])
    p["trust_threshold"]    = 0.60
    p["trust_build_rate"]   = 0.04
    p["trust_decay_rate"]   = 0.18
    p["cynicism_threshold"] = 0.20
    return p


def _build_graph(N: int, connection_prob: float, rng: random.Random) -> list[list[int]]:
    edges: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            if rng.random() < connection_prob:
                edges[i].append(j)
                edges[j].append(i)
    return edges


# ---------------------------------------------------------------------------
# Experiment A — self_weight isolation
# ---------------------------------------------------------------------------

def _run_with_profile(
    profile: dict[str, Any],
    profile_name: str,
    n_agents: int,
    n_steps: int,
    seed: int,
    truth: float,
    liar_fraction: float,
    liar_type: str,          # "consistent" | "slow_drift" | "patient_then_attack" | "noisy"
    liar_target: float = 0.0,
) -> dict:
    """
    Core simulation. Profile is passed directly (not looked up by name).
    Supports all liar_type variants needed by A and B.
    """
    p = profile
    rng = random.Random(seed)
    N = n_agents
    n_liars = int(N * liar_fraction)
    is_liar = [i < n_liars for i in range(N)]

    beliefs = [rng.random() for _ in range(N)]
    # Liars start at truth for slow_drift and patient_then_attack (neutral approach)
    for i in range(N):
        if is_liar[i]:
            if liar_type in ("slow_drift",):
                beliefs[i] = truth          # start near truth, drift to 0
            elif liar_type == "patient_then_attack":
                beliefs[i] = 0.50           # neutral during patience phase
            else:
                beliefs[i] = 1.0 - truth    # classic: maximally wrong from start

    trust = [0.0] * (N * N)
    edges = _build_graph(N, p["connection_prob"], rng)

    steps_data = []
    mean_error_series: list[float] = []
    collapse_step = -1

    # Pre-compute slow_drift step size
    slow_drift_rate = truth / n_steps if n_steps > 0 else 0.0

    for step in range(n_steps):
        prev_beliefs = beliefs[:]
        new_beliefs = beliefs[:]

        # Determine liar belief for this step
        for i in range(N):
            if not is_liar[i]:
                continue
            if liar_type == "consistent":
                new_beliefs[i] = 1.0 - truth
            elif liar_type == "noisy":
                new_beliefs[i] = rng.random()
            elif liar_type == "slow_drift":
                # Drift from truth down to liar_target (default 0.0), below cynicism threshold
                progress = step / max(1, n_steps - 1)
                new_beliefs[i] = truth - (truth - liar_target) * progress
            elif liar_type == "patient_then_attack":
                if step < n_steps // 2:
                    new_beliefs[i] = 0.50   # patience phase: neutral
                else:
                    new_beliefs[i] = liar_target  # attack phase: jump to target

        # Honest agent updates
        for i in range(N):
            if is_liar[i]:
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
        consensus_gap = sum(abs(beliefs[i] - mean_honest) for i in range(N)) / N
        mean_error_series.append(mean_error)

        if collapse_step == -1 and consensus_gap < 0.10:
            collapse_step = step

        steps_data.append({
            "step": step,
            "mean_belief": round(mean_honest, 3),
            "mean_error": round(mean_error, 3),
            "consensus_gap": round(consensus_gap, 3),
        })

    final_error = mean_error_series[-1] if mean_error_series else 1.0
    mean_liar_trust = []
    for i in range(N):
        if not is_liar[i]:
            for j in edges[i]:
                if is_liar[j]:
                    mean_liar_trust.append(trust[i * N + j])

    return {
        "profile": profile_name,
        "liar_type": liar_type,
        "liar_fraction": liar_fraction,
        "final_error": round(final_error, 4),
        "collapse_step": collapse_step,
        "mean_liar_trust": round(sum(mean_liar_trust) / max(1, len(mean_liar_trust)), 4),
        "steps": steps_data,
    }


def run_self_weight_isolation(
    n_agents: int = 50,
    n_steps: int = 200,
    seed: int = 42,
    truth: float = 0.75,
) -> dict:
    """
    Four profiles across five liar fractions, consistent liars only.
    Isolates the contribution of self_weight vs cynicism mechanics.
    """
    named_profiles = {
        "baseline":       PROFILES["baseline"],
        "sw_only":        _make_sw_only(),
        "cynicism_only":  _make_cynicism_only(),
        "selective":     PROFILES["selective"],
    }
    fractions = [0.0, 0.10, 0.20, 0.30, 0.40]
    results: dict[str, list[dict]] = {k: [] for k in named_profiles}

    for name, prof in named_profiles.items():
        for lf in fractions:
            r = _run_with_profile(
                prof, name, n_agents, n_steps, seed, truth,
                liar_fraction=lf, liar_type="consistent",
            )
            results[name].append(r)

    return {"experiment": "self_weight_isolation", "profiles": results, "fractions": fractions}


# ---------------------------------------------------------------------------
# Experiment B — calibrated attacks
# ---------------------------------------------------------------------------

def run_calibrated_attack(
    n_agents: int = 50,
    n_steps: int = 200,
    seed: int = 42,
    truth: float = 0.75,
    liar_fraction: float = 0.20,
) -> dict:
    """
    Two attack types vs two profiles.
    slow_drift:           drifts truth→0 at rate below cynicism threshold; trust builds fully
    patient_then_attack:  neutral for n_steps//2, then snaps to 0; tests cynicism on sudden shift
    """
    results = {}
    for attack in ("slow_drift", "patient_then_attack"):
        for pname, prof in PROFILES.items():
            r = _run_with_profile(
                prof, pname, n_agents, n_steps, seed, truth,
                liar_fraction=liar_fraction,
                liar_type=attack,
                liar_target=0.0,
            )
            results[f"{attack}_{pname}"] = r
    return {"experiment": "calibrated_attack", "results": results}


# ---------------------------------------------------------------------------
# Experiment C — post-collapse tracking with truth injection
# ---------------------------------------------------------------------------

def _run_tracking(
    profile: dict[str, Any],
    profile_name: str,
    n_agents: int,
    n_steps: int,
    seed: int,
    truth_fn,          # callable(step) -> float
    signal_weight: float = 0.02,
) -> dict:
    """
    Consensus network with a weak truth-injection signal.
    Each step: belief += signal_weight * (truth - belief)
    This models agents receiving ambient environmental feedback.
    Truth can change over time via truth_fn.
    """
    p = profile
    rng = random.Random(seed)
    N = n_agents

    beliefs = [rng.random() for _ in range(N)]
    trust = [0.0] * (N * N)
    edges = _build_graph(N, p["connection_prob"], rng)

    steps_data = []
    tracking_errors: list[float] = []
    collapse_events: list[int] = []
    reopen_events: list[int] = []
    was_collapsed = False
    collapse_step = -1

    for step in range(n_steps):
        current_truth = truth_fn(step)
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

            # Weak truth injection
            new_beliefs[i] += signal_weight * (current_truth - new_beliefs[i])

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
        tracking_errors.append(mean_error)

        is_collapsed_now = consensus_gap < 0.10
        if is_collapsed_now and not was_collapsed:
            collapse_step = step
            collapse_events.append(step)
        if not is_collapsed_now and was_collapsed:
            reopen_events.append(step)
        was_collapsed = is_collapsed_now

        steps_data.append({
            "step":          step,
            "truth":         round(current_truth, 3),
            "mean_belief":   round(mean_belief, 3),
            "mean_error":    round(mean_error, 3),
            "consensus_gap": round(consensus_gap, 3),
            "collapsed":     is_collapsed_now,
        })

    mean_tracking_error = sum(tracking_errors) / max(1, len(tracking_errors))
    # Tracking error only after first collapse (fair comparison of post-lock behavior)
    post_collapse_errors = tracking_errors[collapse_step:] if collapse_step >= 0 else tracking_errors
    post_collapse_mean = sum(post_collapse_errors) / max(1, len(post_collapse_errors))

    return {
        "profile": profile_name,
        "collapse_step": collapse_step,
        "n_collapse_events": len(collapse_events),
        "n_reopen_events": len(reopen_events),
        "reopen_events": reopen_events[:10],   # first 10
        "mean_tracking_error": round(mean_tracking_error, 4),
        "post_collapse_tracking_error": round(post_collapse_mean, 4),
        "final_error": round(tracking_errors[-1], 4),
        "steps": steps_data,
    }


def run_post_collapse_tracking(
    n_agents: int = 50,
    n_steps: int = 500,
    seed: int = 42,
    signal_weight: float = 0.02,
) -> dict:
    """
    Long run (500 steps). Two truth modes:
      linear_drift:  truth drifts 0.25 → 0.75 over full run
      oscillating:   truth = 0.50 + 0.25*sin(2π*step/150), period=150 steps
    """
    results = {}

    def linear_drift(step: int) -> float:
        return 0.25 + 0.50 * (step / (n_steps - 1))

    def oscillating(step: int) -> float:
        return 0.50 + 0.25 * math.sin(2 * math.pi * step / 150)

    for mode, truth_fn in (("linear_drift", linear_drift), ("oscillating", oscillating)):
        for pname, prof in PROFILES.items():
            r = _run_tracking(
                prof, pname, n_agents, n_steps, seed,
                truth_fn=truth_fn,
                signal_weight=signal_weight,
            )
            results[f"{mode}_{pname}"] = r

    return {
        "experiment": "post_collapse_tracking",
        "n_steps": n_steps,
        "signal_weight": signal_weight,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

W = 62

def print_self_weight_isolation(result: dict) -> None:
    print("\n" + "=" * W)
    print("  EXPERIMENT A: SELF-WEIGHT ISOLATION")
    print("  (consistent liars; which part of the profile matters?)")
    print("=" * W)
    fractions = result["fractions"]
    profiles = result["profiles"]

    print(f"\n  {'liar_frac':>9}", end="")
    for name in profiles:
        print(f"  {name:>14}", end="")
    print()
    print(f"  {'─' * (9 + 16 * len(profiles))}")

    for fi, lf in enumerate(fractions):
        print(f"  {lf:>9.2f}", end="")
        errors = {}
        for name, runs in profiles.items():
            err = runs[fi]["final_error"]
            errors[name] = err
            print(f"  {err:>14.4f}", end="")
        min_err = min(errors.values())
        winner = [k for k, v in errors.items() if v == min_err][0]
        print(f"  ← {winner}")

    print(f"\n  profiles explained:")
    print(f"    baseline      sw=0.00, trust_threshold=0.0,  no cynicism")
    print(f"    sw_only       sw=0.85, trust_threshold=0.0,  no cynicism")
    print(f"    cynicism_only sw=0.00, trust_threshold=0.60, with cynicism")
    print(f"    dissonance    sw=0.85, trust_threshold=0.60, with cynicism")


def print_calibrated_attack(result: dict) -> None:
    print("\n" + "=" * W)
    print("  EXPERIMENT B: CALIBRATED ATTACK")
    print("  (adversaries that know the architecture)")
    print("=" * W)
    rs = result["results"]

    for attack in ("slow_drift", "patient_then_attack"):
        d = rs[f"{attack}_dissonance"]
        b = rs[f"{attack}_baseline"]

        if attack == "slow_drift":
            desc = "slow_drift:  starts at truth, drifts to 0 at 0.003/step (below cynicism)"
        else:
            desc = "patient:     neutral 0.5 for 100 steps, then snaps to 0.0"

        print(f"\n  {desc}")
        print(f"  {'':30s}  {'dissonance':>12}  {'baseline':>10}")
        print(f"  {'─' * 55}")
        print(f"  {'final_error':30s}  {d['final_error']:>12.4f}  {b['final_error']:>10.4f}", end="")
        if d["final_error"] < b["final_error"] - 0.005:
            print("  ← DISSONANCE survives better")
        elif b["final_error"] < d["final_error"] - 0.005:
            print("  ← baseline survives better")
        else:
            print("  (tie)")
        print(f"  {'collapse_step':30s}  {str(d['collapse_step']):>12}  {str(b['collapse_step']):>10}")
        print(f"  {'mean_liar_trust':30s}  {d['mean_liar_trust']:>12.4f}  {b['mean_liar_trust']:>10.4f}")

    sd_d = rs["slow_drift_dissonance"]
    sd_b = rs["slow_drift_baseline"]
    pa_d = rs["patient_then_attack_dissonance"]
    pa_b = rs["patient_then_attack_baseline"]

    print(f"\n  KEY: slow_drift vs patient_then_attack damage to DISSONANCE:")
    print(f"    slow_drift error:           {sd_d['final_error']:.4f}")
    print(f"    patient_then_attack error:  {pa_d['final_error']:.4f}")
    more_damage = "slow_drift" if sd_d["final_error"] > pa_d["final_error"] else "patient_then_attack"
    print(f"    → more damaging attack: {more_damage}")


def print_post_collapse_tracking(result: dict) -> None:
    print("\n" + "=" * W)
    print("  EXPERIMENT C: POST-COLLAPSE TRACKING  (500 steps)")
    print("  (weak truth signal; does DISSONANCE re-track?)")
    print("=" * W)
    rs = result["results"]

    for mode in ("linear_drift", "oscillating"):
        d = rs[f"{mode}_dissonance"]
        b = rs[f"{mode}_baseline"]

        if mode == "linear_drift":
            desc = "linear_drift  truth: 0.25 → 0.75 over 500 steps"
        else:
            desc = "oscillating   truth: 0.50 + 0.25*sin(2π*t/150)"

        print(f"\n  {desc}")
        print(f"  {'':35s}  {'dissonance':>10}  {'baseline':>10}")
        print(f"  {'─' * 58}")
        metrics = [
            ("mean_tracking_error",         "mean_tracking_error"),
            ("post_collapse_tracking_error", "post_collapse_tracking_error"),
            ("collapse_step",                "collapse_step"),
            ("n_reopen_events",              "n_reopen_events"),
            ("final_error",                  "final_error"),
        ]
        for label, key in metrics:
            dv = d[key]
            bv = b[key]
            print(f"  {label:35s}  {str(dv):>10}  {str(bv):>10}", end="")
            if isinstance(dv, float) and isinstance(bv, float):
                if dv < bv - 0.005:
                    print("  ← DISSONANCE")
                elif bv < dv - 0.005:
                    print("  ← baseline")
                else:
                    print()
            else:
                print()

        if d["n_reopen_events"] > 0:
            print(f"\n  DISSONANCE reopened {d['n_reopen_events']}x at steps: {d['reopen_events']}")
            print(f"  → noise_std is allowing post-collapse belief drift + re-collapse cycles")
        if b["n_reopen_events"] == 0 and d["n_reopen_events"] > 0:
            print(f"  baseline: 0 reopens. Frozen after first collapse.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Running experiment A: self-weight isolation...")
    sw_result = run_self_weight_isolation()

    print("Running experiment B: calibrated attack...")
    ca_result = run_calibrated_attack()

    print("Running experiment C: post-collapse tracking (500 steps × 4 runs)...")
    pc_result = run_post_collapse_tracking()

    print_self_weight_isolation(sw_result)
    print_calibrated_attack(ca_result)
    print_post_collapse_tracking(pc_result)

    # Save
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "godot_extended_search.json"
    save = {
        "self_weight_isolation": sw_result,
        "calibrated_attack":     ca_result,
        "post_collapse_tracking": pc_result,
    }
    # Strip per-step arrays
    for mode_results in (save["post_collapse_tracking"]["results"].values(),):
        for r in mode_results:
            r.pop("steps", None)
    for prof_runs in save["self_weight_isolation"]["profiles"].values():
        for r in prof_runs:
            r.pop("steps", None)
    for r in save["calibrated_attack"]["results"].values():
        r.pop("steps", None)
    with open(out, "w") as f:
        json.dump(save, f, indent=2)
    print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

