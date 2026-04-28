"""
domains/games/model/probes/godot_cognition.py

Helix — Godot Cognition Experiments
Three simulations parameterized against the DISSONANCE cognitive profile.

Experiments:
  1. kuramoto_spatial   — Spatial Kuramoto oscillator with trust-gated coupling
  2. geometric_dcp      — Agent navigating geometrically narrowing possibility space
  3. consensus_network  — Belief-update network with selective trust / cynicism

Each simulation is defined in GDScript (canonical) and Python (fallback).
The Python fallback implements the identical algorithm so results match.

Godot integration:
  - Set HELIX_GODOT_BIN to the godot4 binary path
  - If not set or binary not found, Python fallback runs automatically

Profile mapping (DISSONANCE → simulation parameters):
  Perceiving / delayed compression    → high trust_window, commit_threshold low
  Low extraversion                    → coupling_radius=1, connection_prob=0.20
  High internal variability (omega)   → omega_std=0.40 vs baseline 0.20
  Schizoid self-weight                → self_weight=0.70–0.85
  High filtering / trust threshold    → trust_threshold=0.60, trust_build_rate=0.04
  Betrayal sensitivity                → trust_decay_rate=0.15–0.18
  Cynicism as constraint detection    → cynicism_threshold=0.20 (sudden shifts trigger decay)

Usage:
  python domains/games/model/probes/godot_cognition.py
  python domains/games/model/probes/godot_cognition.py --experiments kuramoto consensus
  python domains/games/model/probes/godot_cognition.py --compare          # run both profiles
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "domains" / "language" / "artifacts"
_GODOT_DEFAULT = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Microsoft/WinGet/Packages"
    / "GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "Godot_v4.6.1-stable_win64_console.exe"
)
GODOT_BIN = os.environ.get(
    "HELIX_GODOT_BIN",
    str(_GODOT_DEFAULT) if _GODOT_DEFAULT.exists() else "godot",
)
GD_SCRIPTS = ROOT / "domains" / "games" / "godot_engine" / "simulations"

# ---------------------------------------------------------------------------
# Profile definitions (must match GDScript exactly)
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict[str, Any]] = {
    "selective": {
        # Kuramoto
        "trust_window":        15,
        "trust_build_rate":    0.06,
        "trust_decay_rate":    0.15,
        "coupling_radius":     1,
        "omega_std":           0.40,
        "self_weight":         0.70,
        "coherence_threshold": 0.08,
        "coupling_K":          2.0,
        # Geometric DCP
        "explore_bias":        0.80,
        "commit_threshold":    0.15,
        "prune_patience":      3,
        "backtrack_on_block":  True,
        "wall_advance_rate":   0.015,
        # Consensus
        "trust_threshold":     0.60,
        "update_rate":         0.12,
        "cynicism_threshold":  0.20,
        "noise_std":           0.02,
        "connection_prob":     0.20,
    },
    "baseline": {
        # Kuramoto
        "trust_window":        1,
        "trust_build_rate":    1.0,
        "trust_decay_rate":    0.0,
        "coupling_radius":     2,
        "omega_std":           0.20,
        "self_weight":         0.0,
        "coherence_threshold": 1.0,
        "coupling_K":          1.5,
        # Geometric DCP
        "explore_bias":        0.30,
        "commit_threshold":    0.35,
        "prune_patience":      1,
        "backtrack_on_block":  False,
        "wall_advance_rate":   0.015,
        # Consensus
        "trust_threshold":     0.0,
        "update_rate":         0.50,
        "cynicism_threshold":  1.0,
        "noise_std":           0.0,
        "connection_prob":     0.40,
    },
}

# ---------------------------------------------------------------------------
# Godot launcher (tries binary, falls back to Python)
# ---------------------------------------------------------------------------

def _try_godot(script_name: str, params: dict[str, Any]) -> dict | None:
    script = GD_SCRIPTS / script_name
    if not script.exists():
        return None
    try:
        args = [GODOT_BIN, "--headless", "--script", str(script), "--"]
        for k, v in params.items():
            args.append(f"{k}={v}")
        result = subprocess.run(args, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            # Godot prepends a version header line before the JSON output
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    return json.loads(line)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None

# ---------------------------------------------------------------------------
# Python fallback — Experiment 1: Spatial Kuramoto
# ---------------------------------------------------------------------------

def _run_kuramoto(profile: str, n_agents: int = 64, n_steps: int = 300,
                  seed: int = 42) -> dict:
    p  = PROFILES[profile]
    G  = int(math.sqrt(n_agents))
    dt = 0.05
    rng = random.Random(seed)

    phases = [rng.uniform(0, 2 * math.pi) for _ in range(n_agents)]
    omegas = [rng.uniform(-p["omega_std"], p["omega_std"]) for _ in range(n_agents)]
    trust  = [[0.0] * n_agents for _ in range(n_agents)]

    steps_data = []
    R_series   = []

    for step in range(n_steps):
        new_phases = phases[:]

        for i in range(n_agents):
            ix, iy = i % G, i // G
            influence = 0.0
            r = p["coupling_radius"]
            for dxi in range(-r, r + 1):
                for dyi in range(-r, r + 1):
                    if dxi == 0 and dyi == 0:
                        continue
                    jx, jy = ix + dxi, iy + dyi
                    if not (0 <= jx < G and 0 <= jy < G):
                        continue
                    j = jy * G + jx
                    influence += trust[i][j] * math.sin(phases[j] - phases[i])

            dphi = omegas[i] + (1.0 - p["self_weight"]) * p["coupling_K"] * influence
            new_phases[i] = phases[i] + dphi * dt

        # Update trust
        for i in range(n_agents):
            ix, iy = i % G, i // G
            r = p["coupling_radius"]
            for dxi in range(-r, r + 1):
                for dyi in range(-r, r + 1):
                    if dxi == 0 and dyi == 0:
                        continue
                    jx, jy = ix + dxi, iy + dyi
                    if not (0 <= jx < G and 0 <= jy < G):
                        continue
                    j = jy * G + jx
                    freq_diff = abs(omegas[j] - omegas[i])
                    if freq_diff < p["coherence_threshold"]:
                        trust[i][j] = min(1.0, trust[i][j] + p["trust_build_rate"])
                    else:
                        trust[i][j] = max(0.0, trust[i][j] - p["trust_decay_rate"])

        phases = new_phases

        cx = sum(math.cos(ph) for ph in phases)
        cy = sum(math.sin(ph) for ph in phases)
        R  = math.sqrt(cx * cx + cy * cy) / n_agents

        trusted_vals = []
        for i in range(n_agents):
            ix, iy = i % G, i // G
            r = p["coupling_radius"]
            for dxi in range(-r, r + 1):
                for dyi in range(-r, r + 1):
                    if dxi == 0 and dyi == 0:
                        continue
                    jx, jy = ix + dxi, iy + dyi
                    if 0 <= jx < G and 0 <= jy < G:
                        trusted_vals.append(trust[i][jy * G + jx])
        mean_trust = sum(trusted_vals) / max(1, len(trusted_vals))

        R_series.append(R)
        window = R_series[-10:]
        tension = abs(R - sum(window) / len(window)) if len(window) > 1 else 0.0

        steps_data.append({
            "step":                step,
            "order_parameter":     round(R, 4),
            "mean_trust":          round(mean_trust, 4),
            "possibility_breadth": round(1.0 - R, 4),
            "constraint_proxy":    round(mean_trust, 4),
            "tension_proxy":       round(tension, 4),
        })

    lock_step = next((i for i, d in enumerate(steps_data)
                      if d["order_parameter"] >= 0.80), -1)

    return {
        "experiment": "kuramoto_spatial",
        "profile":    profile,
        "n_agents":   n_agents,
        "n_steps":    n_steps,
        "seed":       seed,
        "lock_step":  lock_step,
        "final_R":    round(R_series[-1], 4) if R_series else 0.0,
        "steps":      steps_data,
        "backend":    "python",
    }

# ---------------------------------------------------------------------------
# Python fallback — Experiment 2: Geometric DCP
# ---------------------------------------------------------------------------

def _flood_fill(grid: list[list[int]], start: tuple, G: int) -> int:
    visited = set()
    queue   = [start]
    count   = 0
    while queue:
        x, y = queue.pop()
        if (x, y) in visited:
            continue
        if not (0 <= x < G and 0 <= y < G):
            continue
        if grid[y][x] == 1:
            continue
        visited.add((x, y))
        count += 1
        queue.extend([(x+1,y),(x-1,y),(x,y+1),(x,y-1)])
    return count

def _run_geometric_dcp(profile: str, grid_size: int = 32, n_steps: int = 200,
                       seed: int = 42) -> dict:
    p   = PROFILES[profile]
    G   = grid_size
    rng = random.Random(seed)

    grid = [[0] * G for _ in range(G)]
    start = (1, 1)
    goal  = (G - 2, G - 2)
    agent = list(start)
    wall_margin = 0

    EXPAND, PRUNE, COMMIT, DONE = 0, 1, 2, 3
    state       = EXPAND
    prune_count = 0
    steps_data  = []

    for step in range(n_steps):
        # Advance walls
        new_margin = int(step * p["wall_advance_rate"])
        if new_margin != wall_margin:
            wall_margin = new_margin
            for x in range(G):
                for y in range(G):
                    is_border = (x < wall_margin or x >= G - wall_margin
                                 or y < wall_margin or y >= G - wall_margin)
                    if is_border and (x, y) != start and (x, y) != goal:
                        grid[y][x] = 1

        # Clamp agent
        if grid[agent[1]][agent[0]] == 1:
            for r in range(1, G):
                found = False
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        nx, ny = agent[0] + dx, agent[1] + dy
                        if 0 <= nx < G and 0 <= ny < G and grid[ny][nx] == 0:
                            agent = [nx, ny]
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

        reachable = _flood_fill(grid, tuple(agent), G)
        total_open = sum(grid[y][x] == 0 for y in range(G) for x in range(G))
        breadth    = reachable / max(1, (G - 2) ** 2)
        constraint = 1.0 - breadth

        if state == EXPAND:
            if breadth < p["commit_threshold"]:
                state = COMMIT
            elif rng.random() < p["explore_bias"]:
                dirs = [(1,0),(-1,0),(0,1),(0,-1)]
                rng.shuffle(dirs)
                moved = False
                for dx, dy in dirs:
                    nx, ny = agent[0] + dx, agent[1] + dy
                    if 0 <= nx < G and 0 <= ny < G and grid[ny][nx] == 0:
                        agent = [nx, ny]
                        moved = True
                        break
                if not moved:
                    state = PRUNE
                    prune_count = 0
            else:
                state = PRUNE
                prune_count = 0

        elif state == PRUNE:
            prune_count += 1
            if prune_count >= p["prune_patience"]:
                state = EXPAND

        elif state == COMMIT:
            best = tuple(agent)
            best_dist = math.dist(agent, goal)
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = agent[0] + dx, agent[1] + dy
                if 0 <= nx < G and 0 <= ny < G and grid[ny][nx] == 0:
                    d = math.dist((nx, ny), goal)
                    if d < best_dist:
                        best_dist = d
                        best = (nx, ny)
            if tuple(agent) == best and p["backtrack_on_block"]:
                state = EXPAND
            else:
                agent = list(best)
            if tuple(agent) == goal:
                state = DONE

        collapse_flag = (breadth < p["commit_threshold"] and state == COMMIT)
        goal_reached  = (tuple(agent) == goal)

        steps_data.append({
            "step":                step,
            "possibility_breadth": round(breadth, 4),
            "constraint_proxy":    round(constraint, 4),
            "tension_proxy":       round(constraint * step / n_steps, 4),
            "agent_state":         ["EXPAND","PRUNE","COMMIT","DONE"][state],
            "wall_margin":         wall_margin,
            "reachable_cells":     reachable,
            "collapse_flag":       collapse_flag,
            "goal_reached":        goal_reached,
        })

        if state == DONE:
            break

    collapse_step = next((i for i, d in enumerate(steps_data) if d["collapse_flag"]), -1)

    return {
        "experiment":    "geometric_dcp",
        "profile":       profile,
        "grid_size":     G,
        "n_steps":       n_steps,
        "seed":          seed,
        "collapse_step": collapse_step,
        "goal_reached":  steps_data[-1]["goal_reached"] if steps_data else False,
        "final_breadth": steps_data[-1]["possibility_breadth"] if steps_data else 0.0,
        "steps":         steps_data,
        "backend":       "python",
    }

# ---------------------------------------------------------------------------
# Python fallback — Experiment 3: Consensus Network
# ---------------------------------------------------------------------------

def _run_consensus(profile: str, n_agents: int = 50, n_steps: int = 200,
                   seed: int = 42, truth: float = 0.75) -> dict:
    p   = PROFILES[profile]
    rng = random.Random(seed)

    beliefs      = [rng.random() for _ in range(n_agents)]
    prev_beliefs = beliefs[:]
    trust        = [[0.0] * n_agents for _ in range(n_agents)]

    # Erdős–Rényi graph
    edges: list[list[int]] = [[] for _ in range(n_agents)]
    for i in range(n_agents):
        for j in range(i + 1, n_agents):
            if rng.random() < p["connection_prob"]:
                edges[i].append(j)
                edges[j].append(i)

    steps_data        = []
    mean_error_series = []

    for step in range(n_steps):
        prev_beliefs = beliefs[:]
        new_beliefs  = beliefs[:]

        for i in range(n_agents):
            trusted_inf = 0.0
            trusted_w   = 0.0
            for j in edges[i]:
                t = trust[i][j]
                if t >= p["trust_threshold"]:
                    trusted_inf += t * beliefs[j]
                    trusted_w   += t

            if trusted_w > 0.0:
                external = trusted_inf / trusted_w
                new_beliefs[i] = (
                    p["self_weight"] * beliefs[i]
                    + (1.0 - p["self_weight"]) * p["update_rate"] * external
                    + (1.0 - p["update_rate"]) * (1.0 - p["self_weight"]) * beliefs[i]
                )

            if p["noise_std"] > 0.0:
                new_beliefs[i] += rng.gauss(0, p["noise_std"])
            new_beliefs[i] = max(0.0, min(1.0, new_beliefs[i]))

        # Update trust
        for i in range(n_agents):
            for j in edges[i]:
                delta = abs(beliefs[j] - prev_beliefs[j])
                if delta < p["cynicism_threshold"]:
                    trust[i][j] = min(1.0, trust[i][j] + p["trust_build_rate"])
                else:
                    trust[i][j] = max(0.0, trust[i][j] - p["trust_decay_rate"])

        beliefs = new_beliefs

        mean_belief   = sum(beliefs) / n_agents
        mean_error    = sum(abs(b - truth) for b in beliefs) / n_agents
        consensus_gap = sum(abs(b - mean_belief) for b in beliefs) / n_agents
        n_trusted     = sum(1 for i in range(n_agents) for j in edges[i]
                            if trust[i][j] >= p["trust_threshold"]) // 2

        mean_error_series.append(mean_error)
        window = mean_error_series[-20:]
        tension = sum(window) / len(window) if window else 0.0

        steps_data.append({
            "step":                step,
            "mean_belief":         round(mean_belief, 4),
            "mean_error":          round(mean_error, 4),
            "consensus_gap":       round(consensus_gap, 4),
            "n_trusted_edges":     n_trusted,
            "possibility_breadth": round(consensus_gap, 4),
            "constraint_proxy":    round(1.0 - consensus_gap, 4),
            "tension_proxy":       round(tension, 4),
        })

    final_error  = mean_error_series[-1] if mean_error_series else 1.0
    converged    = final_error < 0.05
    collapse_step = next((i for i, d in enumerate(steps_data)
                          if d["consensus_gap"] < 0.10), -1)

    return {
        "experiment":    "consensus_network",
        "profile":       profile,
        "n_agents":      n_agents,
        "n_steps":       n_steps,
        "seed":          seed,
        "truth":         truth,
        "converged":     converged,
        "collapse_step": collapse_step,
        "final_error":   round(final_error, 4),
        "steps":         steps_data,
        "backend":       "python",
    }

# ---------------------------------------------------------------------------
# DCP analysis (maps simulation output → TrajectoryLog fields)
# ---------------------------------------------------------------------------

def _dcp_summary(result: dict) -> dict:
    steps = result["steps"]
    if not steps:
        return {}

    breadths   = [s["possibility_breadth"] for s in steps]
    constraints= [s["constraint_proxy"]    for s in steps]
    tensions   = [s["tension_proxy"]       for s in steps]

    collapse_step = result.get("collapse_step", -1)

    # Post-collapse narrowing
    post_narrowing = None
    if collapse_step >= 0 and collapse_step < len(breadths) - 1:
        pre  = breadths[collapse_step]
        post = breadths[-1]
        post_narrowing = round(pre - post, 4) if pre > 0 else None

    # DCP composite score (reuse branching-fixture formula)
    max_constraint = max(constraints) if constraints else 0.0
    mean_tension   = sum(tensions) / len(tensions) if tensions else 0.0
    min_breadth    = min(breadths) if breadths else 1.0
    composite = round(
        0.35 * max_constraint
        + 0.35 * mean_tension
        + 0.30 * (1.0 - min_breadth),
        4,
    )
    qualification = "FULL" if (composite >= 0.40 and collapse_step >= 0) else "PARTIAL"

    return {
        "composite":       composite,
        "qualification":   qualification,
        "collapse_step":   collapse_step,
        "post_narrowing":  post_narrowing,
        "max_constraint":  round(max_constraint, 4),
        "mean_tension":    round(mean_tension, 4),
        "min_breadth":     round(min_breadth, 4),
        "n_steps_run":     len(steps),
    }

# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def _bar(val: float, width: int = 20) -> str:
    filled = int(val * width)
    return "█" * filled + "░" * (width - filled)

def _print_experiment(result: dict, dcp: dict) -> None:
    exp  = result["experiment"]
    prof = result["profile"]
    backend = result.get("backend", "godot")

    print(f"\n{'─'*60}")
    print(f"  {exp.upper().replace('_', ' ')}  [{prof}]  backend={backend}")
    print(f"{'─'*60}")

    # Experiment-specific summary line
    if exp == "kuramoto_spatial":
        lock = result.get("lock_step", -1)
        R    = result.get("final_R", 0.0)
        lock_str = f"step {lock}" if lock >= 0 else "never"
        print(f"  final order_parameter (R):  {R:.3f}  {_bar(R)}")
        print(f"  locking event (R≥0.80):     {lock_str}")

    elif exp == "geometric_dcp":
        goal  = result.get("goal_reached", False)
        fb    = result.get("final_breadth", 0.0)
        print(f"  goal reached:               {'YES' if goal else 'NO'}")
        print(f"  final breadth:              {fb:.3f}  {_bar(fb)}")

    elif exp == "consensus_network":
        err   = result.get("final_error", 1.0)
        conv  = result.get("converged", False)
        truth = result.get("truth", 0.75)
        print(f"  truth: {truth:.2f}  |  final mean error: {err:.3f}  {_bar(1-err)}")
        print(f"  converged (error<0.05):     {'YES' if conv else 'NO'}")

    print()
    print(f"  DCP composite:              {dcp.get('composite', 0):.3f}  "
          f"  [{dcp.get('qualification','?')}]")
    print(f"  collapse step:              {dcp.get('collapse_step', -1)}")
    print(f"  post-collapse narrowing:    {dcp.get('post_narrowing', 'n/a')}")
    print(f"  max_constraint:             {dcp.get('max_constraint', 0):.3f}")
    print(f"  mean_tension:               {dcp.get('mean_tension', 0):.3f}")
    print(f"  min_breadth:                {dcp.get('min_breadth', 1):.3f}")

def _print_comparison(r_dis: dict, dcp_dis: dict, r_base: dict, dcp_base: dict) -> None:
    exp = r_dis["experiment"]
    print(f"\n{'═'*60}")
    print(f"  COMPARISON: {exp.upper().replace('_', ' ')}")
    print(f"  {'metric':<28}  {'dissonance':>12}  {'baseline':>12}")
    print(f"  {'─'*28}  {'─'*12}  {'─'*12}")

    def row(label, d_val, b_val):
        print(f"  {label:<28}  {str(d_val):>12}  {str(b_val):>12}")

    row("DCP composite",   dcp_dis.get("composite"),    dcp_base.get("composite"))
    row("collapse_step",   dcp_dis.get("collapse_step"), dcp_base.get("collapse_step"))
    row("qualification",   dcp_dis.get("qualification"), dcp_base.get("qualification"))
    row("post_narrowing",  dcp_dis.get("post_narrowing"), dcp_base.get("post_narrowing"))
    row("max_constraint",  dcp_dis.get("max_constraint"), dcp_base.get("max_constraint"))
    row("mean_tension",    dcp_dis.get("mean_tension"),   dcp_base.get("mean_tension"))
    row("min_breadth",     dcp_dis.get("min_breadth"),    dcp_base.get("min_breadth"))

    if exp == "kuramoto_spatial":
        row("final_R",     r_dis.get("final_R"), r_base.get("final_R"))
        row("lock_step",   r_dis.get("lock_step"), r_base.get("lock_step"))
    elif exp == "consensus_network":
        row("final_error", r_dis.get("final_error"), r_base.get("final_error"))
        row("converged",   r_dis.get("converged"),   r_base.get("converged"))

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

EXPERIMENT_MAP = {
    "kuramoto":  ("kuramoto_spatial.gd",  _run_kuramoto,
                  lambda p, **kw: _run_kuramoto(p, **kw)),
    "geometric": ("geometric_dcp.gd",     _run_geometric_dcp,
                  lambda p, **kw: _run_geometric_dcp(p, **kw)),
    "consensus": ("consensus_network.gd", _run_consensus,
                  lambda p, **kw: _run_consensus(p, **kw)),
}

def run_experiment(name: str, profile: str, compare: bool = False,
                   **kwargs) -> tuple[dict, dict]:
    script, py_fn, _ = EXPERIMENT_MAP[name]

    # Try Godot first
    params = {"profile": profile, **{k: str(v) for k, v in kwargs.items()}}
    result = _try_godot(script, params)
    if result is None:
        result = py_fn(profile, **kwargs)

    dcp = _dcp_summary(result)
    return result, dcp

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Godot cognition experiments")
    ap.add_argument("--experiments", nargs="*",
                    default=["kuramoto", "geometric", "consensus"],
                    choices=["kuramoto", "geometric", "consensus"])
    ap.add_argument("--compare",  action="store_true",
                    help="Run both dissonance and baseline profiles side by side")
    ap.add_argument("--profile",  default="selective",
                    choices=["selective", "baseline"])
    ap.add_argument("--seed",     type=int, default=42)
    ap.add_argument("--no-save",  action="store_true")
    args = ap.parse_args()

    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for exp_name in args.experiments:
        kw: dict[str, Any] = {"seed": args.seed}

        if args.compare:
            r_dis,  dcp_dis  = run_experiment(exp_name, "selective", **kw)
            r_base, dcp_base = run_experiment(exp_name, "baseline",   **kw)
            _print_experiment(r_dis,  dcp_dis)
            _print_experiment(r_base, dcp_base)
            _print_comparison(r_dis, dcp_dis, r_base, dcp_base)
            all_results[exp_name] = {
                "selective": {"result": r_dis,  "dcp": dcp_dis},
                "baseline":   {"result": r_base, "dcp": dcp_base},
            }
        else:
            result, dcp = run_experiment(exp_name, args.profile, **kw)
            _print_experiment(result, dcp)
            all_results[exp_name] = {"result": result, "dcp": dcp}

    if not args.no_save:
        out = ARTIFACTS / "godot_cognition_results.json"
        out.write_text(json.dumps(all_results, indent=2))
        print(f"\n  saved → {out.relative_to(ROOT)}")

if __name__ == "__main__":
    main()

