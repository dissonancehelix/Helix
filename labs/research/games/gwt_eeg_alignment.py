"""
model/domains/games/probes/gwt_eeg_alignment.py

Helix — Path 3: Real EEG Alignment

Path B found: cognition k ≈ 15–20 corresponds to a ~20% transition window,
consistent with the 200ms N2→P3b window in a ~1s EEG trial.

This probe has two modes:

MODE A — SYNTHETIC (runs without external data):
  Compute what the simulation predicts for EEG timing under the assumption
  that k maps to cognitive timescale via the belief-network model.
  - Run SELECTIVE (k≈18) and CONFORMIST (k≈200) at 400 steps
  - Map step-duration to 2.5ms (400 steps = 1000ms, a typical P300 trial)
  - Predict: N2→P3b window (step where gap crosses 0.5 → 0.1 threshold)
  - Compare against published EEG landmarks:
      N2: ~200ms, P3b: ~350–450ms  (neurotypical)
      P3b delayed to ~500ms in high-self_weight individuals (ASD literature)

MODE B — EMPIRICAL (requires EEG CSV file):
  Given a CSV with columns [time_ms, voltage, subject_id, condition],
  fit the logistic model to each subject's voltage rise in the N2→P3b window,
  extract empirical k, and compare to simulation prediction.

  OpenNeuro datasets compatible with this probe:
    ds002034 — Dehaene paradigm, ~500ms trial, auditory P300
    ds003517 — visual P300, N=30 subjects
    ds001810 — mismatch negativity + P3b, single-subject dense array

  Usage:
    python -m domains.games.probes.gwt_eeg_alignment --eeg path/to/data.csv

MODE A runs automatically without arguments.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

PROFILES: dict[str, dict] = {
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
}

# EEG timing parameters — 400 simulation steps mapped to a 1000ms trial
STEPS_PER_TRIAL = 400
TRIAL_DURATION_MS = 1000.0
MS_PER_STEP = TRIAL_DURATION_MS / STEPS_PER_TRIAL  # 2.5ms

# Published GWT/EEG landmarks (neurotypical)
EEG_LANDMARKS = {
    "N2_onset_ms":           200,
    "P3b_peak_ms":           380,
    "N2_to_P3b_window_ms":   180,
    "P3b_delayed_ASD_ms":    500,  # consistent with high self_weight
    "source": "Dehaene 2006, Bekinschtein 2009, Fuentemilla 2008",
}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _run_gap_series(profile_name: str, n_agents: int = 80, seed: int = 0) -> list[float]:
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
    gap_series: list[float] = []

    for _ in range(STEPS_PER_TRIAL):
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
# Logistic fit
# ---------------------------------------------------------------------------

def _fit_logistic(series: list[float]) -> tuple[float, float, float]:
    """Returns (k, t0_normalized, R²)."""
    n = len(series)
    if n < 4:
        return 0.0, 0.5, 0.0
    ts = [i / (n - 1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 1e-6:
        return 0.0, 0.5, 0.0
    norm = [(v - mn) / (mx - mn) for v in series]

    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200]:
        for t0 in [i / 20 for i in range(21)]:
            ss = sum((y - 1.0 / (1.0 + math.exp(k * (t - t0)))) ** 2
                     for t, y in zip(ts, norm))
            if ss < best_ss:
                best_ss, best_k, best_t0 = ss, k, t0

    mean_y = sum(norm) / n
    ss_tot = sum((y - mean_y) ** 2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss / ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


# ---------------------------------------------------------------------------
# Mode A: synthetic timing prediction
# ---------------------------------------------------------------------------

def mode_a_synthetic(n_seeds: int = 5) -> dict:
    """
    Run both profiles across multiple seeds, extract:
      - t0 (midpoint of collapse) → maps to P3b peak latency
      - transition window (steps from gap=0.5 to gap=0.1) → maps to N2→P3b width
      - k → logistic steepness (collapse sharpness)
    Compare against published EEG landmarks.
    """
    results = {}

    for profile_name in ["SELECTIVE", "CONFORMIST"]:
        k_vals, t0_ms_vals, window_ms_vals = [], [], []

        for seed in range(n_seeds):
            gap = _run_gap_series(profile_name, seed=seed)
            k, t0_norm, r2 = _fit_logistic(gap)

            if r2 < 0.5:
                continue

            # t0 in milliseconds
            t0_ms = t0_norm * TRIAL_DURATION_MS

            # Transition window: first step below 0.5 → first step below 0.1
            mn, mx = min(gap), max(gap)
            if mx - mn < 1e-6:
                continue
            norm = [(v - mn) / (mx - mn) for v in gap]
            step_half = next((i for i, g in enumerate(norm) if g < 0.5), -1)
            step_done = next((i for i, g in enumerate(norm) if g < 0.1), -1)

            if step_half > 0 and step_done > step_half:
                window_ms = (step_done - step_half) * MS_PER_STEP
                window_ms_vals.append(window_ms)

            k_vals.append(k)
            t0_ms_vals.append(t0_ms)

        if k_vals:
            results[profile_name] = {
                "mean_k":         round(sum(k_vals) / len(k_vals), 1),
                "mean_t0_ms":     round(sum(t0_ms_vals) / len(t0_ms_vals), 1),
                "mean_window_ms": round(sum(window_ms_vals) / len(window_ms_vals), 1) if window_ms_vals else None,
                "n_valid":        len(k_vals),
            }

    # Alignment assessment
    sel = results.get("SELECTIVE", {})
    eeg_p3b = EEG_LANDMARKS["P3b_peak_ms"]
    eeg_win  = EEG_LANDMARKS["N2_to_P3b_window_ms"]

    alignment = {}
    if sel.get("mean_t0_ms") is not None:
        t0_err = abs(sel["mean_t0_ms"] - eeg_p3b)
        alignment["P3b_latency_error_ms"] = round(t0_err, 1)
        alignment["P3b_within_50ms"] = t0_err < 50
    if sel.get("mean_window_ms") is not None:
        win_err = abs(sel["mean_window_ms"] - eeg_win)
        alignment["N2_P3b_window_error_ms"] = round(win_err, 1)
        alignment["window_within_50ms"] = win_err < 50

    if alignment.get("P3b_within_50ms") and alignment.get("window_within_50ms"):
        alignment["verdict"] = "strong alignment — SELECTIVE timing matches N2→P3b window"
    elif alignment.get("P3b_within_50ms") or alignment.get("window_within_50ms"):
        alignment["verdict"] = "partial alignment — one of two landmarks matches"
    else:
        alignment["verdict"] = "no alignment — simulation timing does not match EEG"

    return {
        "profiles": results,
        "eeg_landmarks": EEG_LANDMARKS,
        "ms_per_step": MS_PER_STEP,
        "alignment": alignment,
    }


# ---------------------------------------------------------------------------
# Mode B: empirical EEG CSV
# ---------------------------------------------------------------------------

def mode_b_empirical(csv_path: Path) -> dict:
    """
    Given a CSV file with columns: time_ms, voltage, subject_id
    Extract the N2→P3b window (200–500ms), fit logistic to voltage rise,
    compute empirical k per subject, compare to simulation prediction k≈15–25.
    """
    try:
        import csv as _csv
    except ImportError:
        return {"error": "csv module not available"}

    rows_by_subject: dict[str, list[tuple[float, float]]] = {}
    with open(csv_path) as f:
        reader = _csv.DictReader(f)
        for row in reader:
            sid = row.get("subject_id", "all")
            t = float(row["time_ms"])
            v = float(row["voltage"])
            if 150 <= t <= 550:   # N2→P3b window
                rows_by_subject.setdefault(sid, []).append((t, v))

    subject_ks = []
    for sid, pairs in rows_by_subject.items():
        pairs.sort()
        voltages = [v for _, v in pairs]
        k, _, r2 = _fit_logistic(voltages)
        if r2 > 0.5:
            subject_ks.append({"subject": sid, "k": round(k, 2), "r2": round(r2, 3)})

    if not subject_ks:
        return {"error": "no subjects with R²>0.5 in the N2→P3b window"}

    ks = [s["k"] for s in subject_ks]
    mean_k = sum(ks) / len(ks)
    std_k  = math.sqrt(sum((k - mean_k)**2 for k in ks) / len(ks))

    sim_range = (15, 25)
    fraction_in_range = sum(1 for k in ks if sim_range[0] <= k <= sim_range[1]) / len(ks)

    verdict = (
        "confirmed — empirical k clusters in simulation range k=15–25"
        if fraction_in_range >= 0.5
        else f"not confirmed — only {fraction_in_range:.0%} of subjects in k=15–25 range"
    )

    return {
        "subjects": subject_ks,
        "mean_k":   round(mean_k, 2),
        "std_k":    round(std_k, 2),
        "n_subjects": len(subject_ks),
        "simulation_predicted_range": sim_range,
        "fraction_in_sim_range": round(fraction_in_range, 3),
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    eeg_path = None
    if "--eeg" in sys.argv:
        idx = sys.argv.index("--eeg")
        if idx + 1 < len(sys.argv):
            eeg_path = Path(sys.argv[idx + 1])

    if eeg_path and eeg_path.exists():
        print(f"=== Path 3: EEG Alignment (MODE B — empirical: {eeg_path.name}) ===\n")
        result = {"mode": "empirical", "data": mode_b_empirical(eeg_path)}
    else:
        print("=== Path 3: EEG Alignment (MODE A — synthetic prediction) ===\n")
        result = {"mode": "synthetic", "data": mode_a_synthetic()}

    data = result["data"]
    if result["mode"] == "synthetic":
        for pname, pdata in data["profiles"].items():
            print(f"  {pname}: k={pdata['mean_k']}  t0={pdata['mean_t0_ms']}ms  window={pdata['mean_window_ms']}ms")
        print(f"\n  EEG landmarks: P3b={data['eeg_landmarks']['P3b_peak_ms']}ms  N2→P3b={data['eeg_landmarks']['N2_to_P3b_window_ms']}ms")
        al = data["alignment"]
        print(f"  P3b latency error: {al.get('P3b_latency_error_ms', 'N/A')}ms  window error: {al.get('N2_P3b_window_error_ms', 'N/A')}ms")
        print(f"  Verdict: {al.get('verdict')}")
    else:
        print(f"  Mean empirical k = {data.get('mean_k')} ± {data.get('std_k')}  (n={data.get('n_subjects')})")
        print(f"  Simulation predicted range: k={data.get('simulation_predicted_range')}")
        print(f"  Verdict: {data.get('verdict')}")

    dest = ARTIFACTS / "gwt_eeg_alignment.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")
    if result["mode"] == "synthetic" and not eeg_path:
        print("\nNote: for empirical validation run with --eeg path/to/data.csv")
        print("Compatible datasets: OpenNeuro ds002034, ds003517, ds001810")


if __name__ == "__main__":
    main()

