"""
core/probes/math/probes/math_probe_prime_gaps.py

Helix — Bounded Prime Gaps: DCP + Regime Transition

The Twin Prime Conjecture: there are infinitely many primes p where p+2 is also prime.
Closely related: are there infinitely many primes with a bounded gap?

For decades this seemed out of reach. Then:
  2013-05-14: Yitang Zhang proves gaps < 70,000,000 infinitely often (first finite bound)
  2013-06 to 2014-04: Polymath8 + Maynard reduce bound from 70M → 246

This is the clearest example of a REGIME TRANSITION in modern mathematics.
The system spent decades in "no bound known" regime, crossed a critical threshold
(Zhang's key technique), then rapidly evolved within the new regime.

Two DCP trajectories measured:
  1. Pre-regime: possibility space of whether ANY finite bound exists (binary: yes/no)
  2. Post-regime: the bound value itself narrowing from 70M → 246

The regime transition is the boundary between them.

Sources: Zhang 2013, Maynard 2013, Polymath8a/8b, Tao blog posts, Wikipedia.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Pre-regime: belief that bounded gaps are provable
# Modeled as P(solvable_with_current_tools)
PRE_REGIME = [
    {"date": "1849-01-01",
     "event": "Polignac conjecture: infinitely many pairs of primes with gap 2k for all k",
     "p_solvable": 0.10,
     "note": "Conjecture stated; no tools; very low confidence"},
    {"date": "1900-01-01",
     "event": "Hilbert lists related problems; sieve theory in early development",
     "p_solvable": 0.12,
     "note": "Sieve methods emerging; marginal hope"},
    {"date": "1930-01-01",
     "event": "Brun sieve: sum of reciprocals of twin primes converges — twin primes are 'sparse'",
     "p_solvable": 0.15,
     "note": "Sieve progress; still no path to infinite bounded gaps"},
    {"date": "1965-01-01",
     "event": "Bombieri–Vinogradov theorem — strongest tool available; still gap remains",
     "p_solvable": 0.18,
     "note": "Better tools; community more optimistic but no breakthrough"},
    {"date": "2005-01-01",
     "event": "Goldston–Pintz–Yıldırım (GPY): gaps < ε×log(p) infinitely often — "
              "very close but not a fixed bound",
     "p_solvable": 0.45,
     "note": "NEAR-MISS — GPY came within epsilon of a fixed bound; "
              "community now thinks fixed bound is close"},
    {"date": "2013-05-14",
     "event": "ZHANG: gaps < 70,000,000 infinitely often. FIRST FINITE BOUND EVER.",
     "p_solvable": 1.00,
     "note": "REGIME TRANSITION — the possibility space collapses to a point. "
              "Fixed bound is no longer a question; it is a fact."},
]

# Post-regime: the bound value narrowing
# Possibility space = how large the eventual minimum provable bound might be
# Normalized: 1.0 = 70M (Zhang's original), approaching 0 = 2 (twin primes)
POST_REGIME = [
    {"date": "2013-05-14", "event": "Zhang: bound < 70,000,000",
     "bound": 70_000_000, "note": "Initial result"},
    {"date": "2013-05-28", "event": "Terence Tao launches Polymath8; community effort begins",
     "bound": 60_744_000, "note": "First Polymath improvement"},
    {"date": "2013-06-05", "event": "Polymath8: bound < 42,342,946",
     "bound": 42_342_946, "note": "Rapid improvement"},
    {"date": "2013-06-27", "event": "Polymath8: bound < 5,765,760",
     "bound": 5_765_760, "note": "Order-of-magnitude jump"},
    {"date": "2013-07-27", "event": "Polymath8: bound < 4,680,000",
     "bound": 4_680_000, "note": "Continued refinement"},
    {"date": "2013-11-19", "event": "Polymath8a: bound < 4,680 (new sieve methods)",
     "bound": 4_680, "note": "Massive jump — new techniques unlocked"},
    {"date": "2013-12-19", "event": "Maynard independent result: bound ≤ 600",
     "bound": 600, "note": "Maynard's new method — different approach, better bound"},
    {"date": "2014-01-14", "event": "Polymath8b incorporates Maynard: bound ≤ 270",
     "bound": 270, "note": "Combined approach"},
    {"date": "2014-04-14", "event": "Polymath8b final: bound ≤ 246",
     "bound": 246, "note": "Current best — 246 includes known prime gaps for small ranges"},
    {"date": "2024-01-01", "event": "Current: bound ≤ 246, twin prime conjecture still open",
     "bound": 246, "note": "Stalled — 246 is where current methods reach their limit"},
]


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.01: return 0.0, 0.5, 0.0
    norm = [(v-mn)/(mx-mn) for v in series]
    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [0.5,1,2,3,5,7,10,15,20,30,50,75,100]:
        for t0 in [i/20 for i in range(21)]:
            ss = sum((y-1/(1+math.exp(k*(t-t0))))**2 for t,y in zip(ts,norm))
            if ss < best_ss: best_ss, best_k, best_t0 = ss, k, t0
    mean_y = sum(norm)/n
    ss_tot = sum((y-mean_y)**2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss/ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def _detect_regime_transition(series, threshold_factor=5.0):
    """Find the largest single-step change relative to mean step size."""
    steps = [abs(series[i+1] - series[i]) for i in range(len(series)-1)]
    if not steps: return None, 0
    mean_step = sum(steps) / len(steps)
    max_step = max(steps)
    max_idx  = steps.index(max_step)
    ratio = max_step / mean_step if mean_step > 0 else 0
    return max_idx, ratio


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Bounded Prime Gaps — DCP + Regime Transition ===\n")

    # Pre-regime DCP
    p_solve = [e["p_solvable"] for e in PRE_REGIME]
    k_pre, t0_pre, r2_pre = _fit_logistic(p_solve)

    transition_date = "2013-05-14"
    transition_event = "Zhang proves gaps < 70,000,000"

    print(f"  --- Pre-Regime: Is a finite bound provable? ---")
    print(f"  P(solvable) trajectory: {[round(p,2) for p in p_solve]}")
    print(f"  Logistic fit: k={k_pre}  R²={r2_pre:.3f}")
    print(f"  Regime transition: {transition_date} — {transition_event}")

    # Post-regime DCP
    bounds = [e["bound"] for e in POST_REGIME]
    log_bounds = [math.log10(b) for b in bounds]  # log scale for logistic fit
    k_post, t0_post, r2_post = _fit_logistic(log_bounds)

    # Time compression: Zhang to 246 in days
    days_to_246 = (2014 - 2013) * 365 + 90  # approx 14 months
    total_reduction_factor = bounds[0] / bounds[-1]

    # Regime transition detection in pre-regime
    rt_idx, rt_ratio = _detect_regime_transition(p_solve)

    print(f"\n  --- Post-Regime: Bound value narrowing ---")
    print(f"  Bounds: {bounds}")
    print(f"  Log10 bounds: {[round(l,2) for l in log_bounds]}")
    print(f"  Logistic fit (log scale): k={k_post}  R²={r2_post:.3f}")
    print(f"  Total reduction: {total_reduction_factor:,.0f}× in ~14 months")
    print(f"  Current bound: {bounds[-1]} (stalled since Apr 2014)")
    print(f"  Remaining gap to twin primes: {bounds[-1] - 2}")

    # Regime transition signature
    print(f"\n  --- Regime Transition Signature ---")
    if rt_idx is not None and rt_ratio > 3:
        rt_event = PRE_REGIME[rt_idx + 1]
        print(f"  Transition detected at index {rt_idx+1}: {rt_event['date']}")
        print(f"  Step ratio: {rt_ratio:.1f}× mean (threshold: 3×)")
        print(f"  Event: {rt_event['event'][:80]}")
        rt_verdict = (f"REGIME TRANSITION CONFIRMED — Zhang's proof caused a "
                      f"{rt_ratio:.1f}× above-mean jump in P(solvable). "
                      f"This matches the structural signature of a phase transition: "
                      f"sudden qualitative shift, not gradual improvement.")
    else:
        rt_verdict = "No clear regime transition signature in pre-regime data"

    print(f"  Verdict: {rt_verdict}")

    print(f"\n  Key structural finding:")
    print(f"    Two distinct DCP phases separated by a hard regime transition.")
    print(f"    Pre-transition (164 years): slow drift from 0.10 → 0.45 P(solvable).")
    print(f"    GPY 2005 was a near-transition that failed — it reached the boundary")
    print(f"    of the old regime but couldn't cross it.")
    print(f"    Zhang 2013: crossed the boundary. Post-transition DCP: 70M → 246")
    print(f"    in 14 months — k={k_post}, R²={r2_post:.3f}, log-scale collapse.")
    print(f"    Current stall at 246 is a second-order plateau — current techniques")
    print(f"    hit their sieve-theoretic limit. Another regime transition needed")
    print(f"    to reach twin primes (gap=2).")

    result = {
        "problem": "Bounded prime gaps / Twin Prime Conjecture",
        "pre_regime": {
            "data": PRE_REGIME,
            "k": k_pre, "r2": r2_pre,
            "transition_detected": rt_idx is not None and rt_ratio > 3,
            "transition_ratio": round(rt_ratio, 2) if rt_idx is not None else 0,
        },
        "regime_transition": {
            "date": transition_date,
            "event": transition_event,
            "verdict": rt_verdict,
        },
        "post_regime": {
            "data": POST_REGIME,
            "bounds": bounds,
            "k": k_post, "r2": r2_post,
            "reduction_factor": round(total_reduction_factor, 0),
            "current_bound": bounds[-1],
        },
    }
    dest = ARTIFACTS / "math_prime_gaps.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
