"""
model/domains/games/probes/gwt_consciousness_probe.py

Helix — GWT / IIT Consciousness Structure Probe

Three experiments testing whether the DCP compression event has the structural
signatures predicted by Global Workspace Theory and Integrated Information Theory.

The hypothesis being tested:
  The DCP "collapse step" is structurally equivalent to GWT ignition —
  the moment when locally-processed information achieves global broadcast.
  If true, we should observe:

  1. IGNITION SHAPE (GWT)
     The transition from high to low possibility_breadth should be SUDDEN
     (non-linear, sigmoid with steep k), not gradual.
     GWT predicts all-or-nothing ignition; predictive processing predicts gradual.
     Profiles with longer arcs (SELECTIVE) should show SHALLOWER k — more gradual
     workspace integration vs CONFORMIST's snap ignition.

  2. Φ INTEGRATION PEAK (IIT)
     Integrated information (Φ) = mutual information between network halves.
     Φ is maximized when the system is neither fully random nor fully uniform —
     at the intermediate integration state.
     IIT predicts Φ peaks AT or just before the collapse step.
     If Φ peaks after collapse → information integrates post-broadcast (wrong).
     If Φ peaks before → integration precedes ignition (GWT-consistent).

  3. CROSS-DOMAIN SHAPE MATCHING (DCP invariant)
     Extract normalized collapse curves from:
       - Simulation (all 6 profiles)
       - Language domain (sentence_trajectory: finnish, spanish, mandarin)
     Fit logistic sigmoid to each: gap(t) = 1 / (1 + exp(-k*(t - t0)))
     If k clusters across domains → universal compression rate → DCP is structural.
     If functional form matches → the invariant is real, not projected.

Connections to theory:
  GWT  — Baars (1988), Dehaene (2011 Global Neuronal Workspace)
  IIT  — Tononi (2004, 2014) Phi as integrated information
  DCP  — Helix invariant: possibility_breadth → constraint → tension → collapse
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
# Profiles (identical to godot_ecology.py)
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict[str, Any]] = {
    "CONFORMIST": {
        "trust_threshold": 0.0,  "trust_build_rate": 1.0,  "trust_decay_rate": 0.0,
        "self_weight": 0.05,     "update_rate": 0.70,      "cynicism_threshold": 1.0,
        "noise_std": 0.01,       "connection_prob": 0.50,  "contrarian": False,
    },
    "IMPULSIVE": {
        "trust_threshold": 0.0,  "trust_build_rate": 1.0,  "trust_decay_rate": 0.0,
        "self_weight": 0.15,     "update_rate": 0.80,      "cynicism_threshold": 0.60,
        "noise_std": 0.05,       "connection_prob": 0.45,  "contrarian": False,
    },
    "DIPLOMAT": {
        "trust_threshold": 0.30, "trust_build_rate": 0.10, "trust_decay_rate": 0.08,
        "self_weight": 0.50,     "update_rate": 0.30,      "cynicism_threshold": 0.25,
        "noise_std": 0.01,       "connection_prob": 0.35,  "contrarian": False,
    },
    "SELECTIVE": {
        "trust_threshold": 0.60, "trust_build_rate": 0.04, "trust_decay_rate": 0.18,
        "self_weight": 0.85,     "update_rate": 0.12,      "cynicism_threshold": 0.20,
        "noise_std": 0.02,       "connection_prob": 0.20,  "contrarian": False,
    },
    "PARANOID": {
        "trust_threshold": 0.85, "trust_build_rate": 0.02, "trust_decay_rate": 0.50,
        "self_weight": 0.95,     "update_rate": 0.05,      "cynicism_threshold": 0.05,
        "noise_std": 0.03,       "connection_prob": 0.10,  "contrarian": False,
    },
    "CONTRARIAN": {
        "trust_threshold": 0.20, "trust_build_rate": 0.20, "trust_decay_rate": 0.05,
        "self_weight": 0.60,     "update_rate": 0.35,      "cynicism_threshold": 0.40,
        "noise_std": 0.02,       "connection_prob": 0.35,  "contrarian": True,
    },
}

# ---------------------------------------------------------------------------
# Simulation with full step data
# ---------------------------------------------------------------------------

def _simulate(
    profile_name: str,
    n_agents: int = 80,
    n_steps: int = 300,
    seed: int = 42,
    liar_fraction: float = 0.0,
    truth: float = 0.75,
) -> dict:
    p = PROFILES[profile_name]
    rng = random.Random(seed)
    N = n_agents
    n_liars = int(N * liar_fraction)
    is_liar = [i < n_liars for i in range(N)]

    beliefs = [rng.random() for _ in range(N)]
    for i in range(N):
        if is_liar[i]:
            beliefs[i] = 1.0 - truth

    edges: list[list[int]] = [[] for _ in range(N)]
    for i in range(N):
        for j in range(i + 1, N):
            if rng.random() < p["connection_prob"]:
                edges[i].append(j)
                edges[j].append(i)

    trust = [0.0] * (N * N)

    gap_series:    list[float] = []
    belief_snaps:  list[list[float]] = []   # full belief state each step

    for step in range(n_steps):
        prev = beliefs[:]
        new_b = beliefs[:]

        for i in range(N):
            if is_liar[i]:
                new_b[i] = 1.0 - truth
                continue
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
            for j in edges[i]:
                delta = abs(beliefs[j] - prev[j])
                t = trust[i * N + j]
                if delta < p["cynicism_threshold"]:
                    trust[i * N + j] = min(1.0, t + p["trust_build_rate"])
                else:
                    trust[i * N + j] = max(0.0, t - p["trust_decay_rate"])

        beliefs = new_b
        honest = [beliefs[i] for i in range(N) if not is_liar[i]]
        mean_b = sum(honest) / max(1, len(honest))
        gap = sum(abs(b - mean_b) for b in honest) / max(1, len(honest))
        gap_series.append(gap)
        belief_snaps.append(honest[:])

    collapse_step = next((i for i, g in enumerate(gap_series) if g < 0.10), -1)
    return {
        "profile": profile_name,
        "gap_series": gap_series,
        "belief_snaps": belief_snaps,
        "collapse_step": collapse_step,
        "n_agents": N - n_liars,
    }


# ---------------------------------------------------------------------------
# Math utilities
# ---------------------------------------------------------------------------

def _entropy(values: list[float], n_bins: int = 20) -> float:
    """Shannon entropy of a scalar distribution, binned."""
    if not values:
        return 0.0
    bins = [0] * n_bins
    for v in values:
        k = min(n_bins - 1, int(v * n_bins))
        bins[k] += 1
    N = len(values)
    H = 0.0
    for c in bins:
        if c > 0:
            p = c / N
            H -= p * math.log2(p)
    return H


def _phi_proxy(beliefs: list[float]) -> float:
    """
    Mutual information between two halves of the agent population.
    I(A;B) = H(A) + H(B) - H(AB)
    Peaks when halves are maximally correlated — the integration signature.
    """
    half = len(beliefs) // 2
    if half == 0:
        return 0.0
    A = beliefs[:half]
    B = beliefs[half:]
    return _entropy(A) + _entropy(B) - _entropy(beliefs)


def _fit_logistic(
    t_vals: list[float],
    y_vals: list[float],
) -> tuple[float, float, float]:
    """
    Fit y = 1 / (1 + exp(k * (t - t0))) via grid search.
    Returns (k, t0, r_squared).
    k > 0: y decreases (gap collapses).
    """
    if not t_vals or not y_vals:
        return 0.0, 0.0, 0.0

    best_r2  = -float("inf")
    best_k   = 0.1
    best_t0  = sum(t_vals) / len(t_vals)
    y_mean   = sum(y_vals) / len(y_vals)
    ss_tot   = sum((y - y_mean) ** 2 for y in y_vals)
    if ss_tot < 1e-10:
        return 0.0, t_vals[len(t_vals) // 2], 1.0

    for k in [0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80, 1.0, 1.5, 2.0, 3.0, 5.0]:
        for t0_frac in [i / 20.0 for i in range(21)]:
            t0 = t_vals[0] + t0_frac * (t_vals[-1] - t_vals[0])
            ss_res = sum(
                (y - 1.0 / (1.0 + math.exp(k * (t - t0)))) ** 2
                for t, y in zip(t_vals, y_vals)
            )
            r2 = 1.0 - ss_res / ss_tot
            if r2 > best_r2:
                best_r2 = r2
                best_k  = k
                best_t0 = t0

    return best_k, best_t0, max(0.0, best_r2)


# ---------------------------------------------------------------------------
# Experiment 1: Ignition shape analysis
# ---------------------------------------------------------------------------

def run_ignition_analysis(sims: dict[str, dict]) -> list[dict]:
    """
    For each simulation, analyze the gap series around the collapse event.
    Measures:
      sharpness   = max |d_gap/dt| in collapse window / mean |d_gap/dt| overall
      width       = steps from gap=0.40 to gap=0.10 (transition window)
      fit_k       = logistic steepness parameter
      fit_r2      = logistic fit quality
    """
    results = []
    for pname, sim in sims.items():
        gap  = sim["gap_series"]
        cs   = sim["collapse_step"]
        T    = len(gap)

        if cs < 0:
            results.append({
                "profile": pname, "collapse_step": -1,
                "sharpness": None, "width": None,
                "fit_k": None, "fit_r2": None, "note": "no collapse",
            })
            continue

        # Rate of change
        dgap = [abs(gap[t] - gap[t - 1]) for t in range(1, T)]
        mean_dgap = sum(dgap) / max(1, len(dgap))

        # Sharpness: peak change in [cs-10, cs+10] vs overall mean
        win_start = max(0, cs - 10)
        win_end   = min(T - 2, cs + 10)
        win_max   = max(dgap[win_start:win_end + 1]) if win_start <= win_end else 0.0
        sharpness = win_max / mean_dgap if mean_dgap > 0 else 0.0

        # Transition width: steps from gap > 0.40 to gap < 0.10
        t_high = next((t for t in range(cs, -1, -1) if gap[t] > 0.40), 0)
        width = cs - t_high

        # Logistic fit on the collapse window (wider: 40 steps before to 20 after)
        fit_start = max(0, cs - 40)
        fit_end   = min(T, cs + 20)
        t_window  = list(range(fit_start, fit_end))
        y_window  = [gap[t] for t in t_window]
        # Normalize t to [0,1] for fitting
        t_norm = [(t - fit_start) / max(1, fit_end - fit_start - 1) for t in t_window]
        t0_norm = (cs - fit_start) / max(1, fit_end - fit_start - 1)
        k, t0, r2 = _fit_logistic(t_norm, y_window)

        results.append({
            "profile":      pname,
            "collapse_step": cs,
            "sharpness":    round(sharpness, 2),
            "width":        width,
            "fit_k":        round(k, 3),
            "fit_r2":       round(r2, 3),
            "mean_dgap":    round(mean_dgap, 5),
            "note":         "",
        })

    results.sort(key=lambda r: r["collapse_step"] if r["collapse_step"] >= 0 else 9999)
    return results


# ---------------------------------------------------------------------------
# Experiment 2: Φ integration measure
# ---------------------------------------------------------------------------

def run_phi_analysis(sims: dict[str, dict]) -> list[dict]:
    """
    For each simulation, compute H(beliefs) and Φ_proxy = I(A;B) at every step.
    Test whether Φ peaks at, before, or after the collapse step.
    """
    results = []
    for pname, sim in sims.items():
        snaps = sim["belief_snaps"]
        cs    = sim["collapse_step"]
        T     = len(snaps)

        h_series   = [_entropy(snaps[t]) for t in range(T)]
        phi_series = [_phi_proxy(snaps[t]) for t in range(T)]

        phi_max      = max(phi_series)
        phi_peak_t   = phi_series.index(phi_max)
        phi_at_cs    = phi_series[cs] if cs >= 0 else None
        h_at_cs      = h_series[cs]   if cs >= 0 else None
        timing       = phi_peak_t - cs if cs >= 0 else None

        # Normalized Φ at collapse vs peak
        phi_frac_at_collapse = (phi_at_cs / phi_max) if (phi_max > 0 and phi_at_cs is not None) else None

        results.append({
            "profile":              pname,
            "collapse_step":        cs,
            "phi_peak_step":        phi_peak_t,
            "phi_peak_value":       round(phi_max, 4),
            "phi_at_collapse":      round(phi_at_cs, 4) if phi_at_cs is not None else None,
            "phi_frac_at_collapse": round(phi_frac_at_collapse, 3) if phi_frac_at_collapse else None,
            "timing_vs_collapse":   timing,   # negative = Φ peaks BEFORE collapse (GWT-consistent)
            "h_initial":            round(h_series[0], 3),
            "h_at_collapse":        round(h_at_cs, 3) if h_at_cs is not None else None,
            "h_final":              round(h_series[-1], 3),
            "phi_series":           [round(v, 4) for v in phi_series],   # for plotting
        })

    results.sort(key=lambda r: r["collapse_step"] if r["collapse_step"] >= 0 else 9999)
    return results


# ---------------------------------------------------------------------------
# Experiment 3: Cross-domain shape matching
# ---------------------------------------------------------------------------

def _load_language_series() -> list[dict]:
    """Load temporal DCP series from sentence_trajectory probe output."""
    path = ARTIFACTS / "sentence_trajectory_results.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    series = []
    for key, val in data.items():
        traj = val.get("trajectory", [])
        if len(traj) < 4:
            continue
        # fraction = cumulative token coverage = possibility_breadth (increases toward 1)
        # gap equivalent = 1 - fraction (starts high, collapses toward 0)
        gap_equiv = [max(0.0, 1.0 - t.get("fraction", 0.0)) for t in traj]
        series.append({
            "domain":   "language",
            "source":   f"sentence/{val.get('language', key)}",
            "gap_norm": gap_equiv,
            "n_steps":  len(gap_equiv),
        })
    return series


def _normalize_gap_series(gap: list[float]) -> tuple[list[float], list[float]]:
    """
    Normalize a gap series to t_norm ∈ [0,1], gap ∈ [0,1].
    Centers on the collapse point (first crossing of 0.10), rescales.
    """
    T = len(gap)
    collapse = next((i for i, g in enumerate(gap) if g < 0.10), T - 1)
    # Use window 30 steps before collapse to 10 after (or full series if short)
    win_start = max(0, collapse - 30)
    win_end   = min(T, collapse + 10)
    window    = gap[win_start:win_end]
    if len(window) < 4:
        window = gap  # fallback
    # Normalize t
    t_norm = [i / max(1, len(window) - 1) for i in range(len(window))]
    # Normalize gap to [0,1]
    g_max  = max(window) if max(window) > 0 else 1.0
    g_norm = [g / g_max for g in window]
    return t_norm, g_norm


def run_cross_domain_shape(sims: dict[str, dict]) -> list[dict]:
    """
    Fit logistic curves to normalized collapse windows from all domains.
    Compare steepness k and midpoint t0 across simulation profiles and language data.
    """
    shape_results = []

    # Simulation sources
    for pname, sim in sims.items():
        if sim["collapse_step"] < 0:
            continue
        t_norm, g_norm = _normalize_gap_series(sim["gap_series"])
        k, t0, r2 = _fit_logistic(t_norm, g_norm)
        shape_results.append({
            "domain":  "simulation",
            "source":  f"sim/{pname}",
            "fit_k":   round(k, 3),
            "fit_t0":  round(t0, 3),
            "fit_r2":  round(r2, 3),
            "n_steps": len(t_norm),
            "collapse_step": sim["collapse_step"],
        })

    # Language sources
    for lang in _load_language_series():
        t_norm, g_norm = _normalize_gap_series(lang["gap_norm"])
        k, t0, r2 = _fit_logistic(t_norm, g_norm)
        shape_results.append({
            "domain":  lang["domain"],
            "source":  lang["source"],
            "fit_k":   round(k, 3),
            "fit_t0":  round(t0, 3),
            "fit_r2":  round(r2, 3),
            "n_steps": lang["n_steps"],
            "collapse_step": None,
        })

    shape_results.sort(key=lambda r: r["fit_k"], reverse=True)
    return shape_results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

W = 72

def print_ignition(results: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  GWT PROBE 1: IGNITION SHAPE")
    print("  GWT predicts: sudden (high sharpness, narrow width, high fit_k)")
    print("  Gradual compression predicts: low k, wide width")
    print("=" * W)
    print(f"\n  {'profile':>12}  {'collapse':>8}  {'sharpness':>10}  {'width':>6}  {'fit_k':>7}  {'fit_R²':>7}  {'shape'}")
    print(f"  {'─' * 66}")
    for r in results:
        if r["collapse_step"] < 0:
            print(f"  {r['profile']:>12}  {'never':>8}  {'—':>10}  {'—':>6}  {'—':>7}  {'—':>7}  {r.get('note','no collapse')}")
            continue
        k    = r["fit_k"]
        shape = "SNAP" if k >= 1.0 else ("steep" if k >= 0.50 else ("gradual" if k >= 0.20 else "very gradual"))
        print(f"  {r['profile']:>12}  {r['collapse_step']:>8}  {r['sharpness']:>10.1f}x  "
              f"{r['width']:>6}  {r['fit_k']:>7.3f}  {r['fit_r2']:>7.3f}  {shape}")

    ks = [r["fit_k"] for r in results if r["collapse_step"] >= 0 and r["fit_k"]]
    if len(ks) >= 2:
        k_mean = sum(ks) / len(ks)
        k_std  = math.sqrt(sum((k - k_mean)**2 for k in ks) / len(ks))
        print(f"\n  k range: {min(ks):.3f} – {max(ks):.3f}  mean={k_mean:.3f}  std={k_std:.3f}")
        if k_std / k_mean > 0.3:
            print(f"  → HIGH variance in ignition shape across profiles (k_std/k_mean={k_std/k_mean:.2f})")
            print(f"    Ignition sharpness is profile-dependent, not a universal constant")
        else:
            print(f"  → LOW variance — ignition shape may be universal across profiles")


def print_phi(results: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  GWT PROBE 2: Φ INTEGRATION MEASURE  (mutual information between halves)")
    print("  IIT predicts: Φ peaks AT or just BEFORE collapse (ignition = max integration)")
    print("=" * W)
    print(f"\n  {'profile':>12}  {'collapse':>8}  {'Φ_peak@':>8}  {'timing':>8}  {'Φ@collapse':>11}  {'Φ_frac':>7}  verdict")
    print(f"  {'─' * 72}")

    gwt_confirmed = 0
    total = 0

    for r in results:
        cs = r["collapse_step"]
        if cs < 0:
            print(f"  {r['profile']:>12}  {'never':>8}  {r['phi_peak_step']:>8}  {'—':>8}  {'—':>11}  {'—':>7}  no collapse")
            continue
        timing = r["timing_vs_collapse"]
        frac   = r["phi_frac_at_collapse"] or 0.0
        total += 1

        if timing is not None and timing <= 0:
            verdict = "GWT ✓" if frac > 0.70 else "partial"
            gwt_confirmed += 1
        else:
            verdict = "post-ignition"

        timing_str = f"{timing:+d}" if timing is not None else "—"
        phi_cs_str = f"{r['phi_at_collapse']:.4f}" if r['phi_at_collapse'] is not None else "—"

        print(f"  {r['profile']:>12}  {cs:>8}  {r['phi_peak_step']:>8}  {timing_str:>8}  "
              f"{phi_cs_str:>11}  {frac:>7.3f}  {verdict}")

    print(f"\n  GWT prediction (Φ peaks before/at collapse): {gwt_confirmed}/{total} profiles")
    if gwt_confirmed == total:
        print(f"  → ALL profiles show Φ peaking before/at ignition — CONSISTENT with GWT/IIT")
    elif gwt_confirmed > total // 2:
        print(f"  → MAJORITY consistent with GWT/IIT (Φ precedes ignition)")
    else:
        print(f"  → MIXED — Φ structure does not cleanly precede collapse")

    # Show Φ series for two contrasting profiles
    for r in results:
        if r["profile"] in ("CONFORMIST", "SELECTIVE") and r["collapse_step"] >= 0:
            cs  = r["collapse_step"]
            phi = r["phi_series"]
            print(f"\n  Φ trajectory ({r['profile']}, collapse@{cs}):")
            step = max(1, len(phi) // 20)
            for t in range(0, min(len(phi), cs + 20), step):
                bar_len = int(phi[t] * 40 / max(phi)) if max(phi) > 0 else 0
                marker  = " ← collapse" if t == cs else ("        ← Φ peak" if t == r["phi_peak_step"] else "")
                print(f"    t={t:>4}: {'█' * bar_len}{'░' * (40 - bar_len)}  {phi[t]:.4f}{marker}")


def print_cross_domain(results: list[dict]) -> None:
    print("\n" + "=" * W)
    print("  GWT PROBE 3: CROSS-DOMAIN SHAPE MATCHING")
    print("  If k clusters across domains → universal compression rate → DCP is structural")
    print("=" * W)
    print(f"\n  {'source':>28}  {'domain':>12}  {'fit_k':>7}  {'fit_t0':>7}  {'R²':>6}  shape_class")
    print(f"  {'─' * 72}")
    for r in results:
        k     = r["fit_k"]
        shape = "SNAP" if k >= 1.0 else ("steep" if k >= 0.50 else ("gradual" if k >= 0.20 else "very gradual"))
        print(f"  {r['source']:>28}  {r['domain']:>12}  {r['fit_k']:>7.3f}  "
              f"{r['fit_t0']:>7.3f}  {r['fit_r2']:>6.3f}  {shape}")

    sim_ks  = [r["fit_k"] for r in results if r["domain"] == "simulation"]
    lang_ks = [r["fit_k"] for r in results if r["domain"] == "language"]
    all_ks  = [r["fit_k"] for r in results]

    if sim_ks and lang_ks:
        sim_mean  = sum(sim_ks)  / len(sim_ks)
        lang_mean = sum(lang_ks) / len(lang_ks)
        all_mean  = sum(all_ks)  / len(all_ks)
        all_std   = math.sqrt(sum((k - all_mean)**2 for k in all_ks) / len(all_ks))
        cv        = all_std / all_mean if all_mean > 0 else 0

        print(f"\n  Simulation mean k:  {sim_mean:.3f}")
        print(f"  Language mean k:    {lang_mean:.3f}")
        print(f"  Cross-domain CV:    {cv:.3f}  (coefficient of variation — lower = more universal)")

        if cv < 0.25:
            print(f"\n  LOW cross-domain variance (CV={cv:.3f})")
            print(f"  → Collapse shape is CONSISTENT across simulation and language domains")
            print(f"  → Supports DCP as a structural invariant with universal compression rate")
        elif cv < 0.50:
            print(f"\n  MODERATE cross-domain variance (CV={cv:.3f})")
            print(f"  → Some consistency in collapse shape, but not universal")
            print(f"  → DCP may be domain-specific, not fully invariant")
        else:
            print(f"\n  HIGH cross-domain variance (CV={cv:.3f})")
            print(f"  → Collapse shapes differ substantially across domains")
            print(f"  → Functional form is NOT consistent — DCP shape is not universal")

        if abs(sim_mean - lang_mean) / max(sim_mean, lang_mean) < 0.20:
            print(f"  → Simulation and language domain k values within 20% of each other")
            print(f"    This is the strongest available evidence for cross-domain DCP structure")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Simulating all 6 profiles (300 steps, 80 agents, no liars)...")
    sims = {
        pname: _simulate(pname, n_agents=80, n_steps=300, seed=42)
        for pname in PROFILES
    }
    for pname, s in sims.items():
        cs = s["collapse_step"]
        print(f"  {pname:>12}: collapse @ step {cs if cs >= 0 else 'never'}")

    print("\nRunning Probe 1: ignition shape analysis...")
    ignition = run_ignition_analysis(sims)

    print("Running Probe 2: Φ integration measure...")
    phi_results = run_phi_analysis(sims)

    print("Running Probe 3: cross-domain shape matching...")
    shape_results = run_cross_domain_shape(sims)

    print_ignition(ignition)
    print_phi(phi_results)
    print_cross_domain(shape_results)

    # Save
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / "gwt_consciousness_probe.json"
    with open(out, "w") as f:
        json.dump({
            "ignition":     ignition,
            "phi":          [{k: v for k, v in r.items() if k != "phi_series"}
                             for r in phi_results],
            "cross_domain": shape_results,
        }, f, indent=2)
    print(f"\n  saved → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

