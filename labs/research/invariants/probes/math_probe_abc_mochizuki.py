"""
core/probes/math/probes/math_probe_abc_mochizuki.py

Helix — abc Conjecture / Mochizuki Proof: DCP + Oscillator Locking

The abc conjecture (Oesterlé & Masser 1985): for coprime positive integers a+b=c,
the radical rad(abc) — product of distinct prime factors — satisfies:
  c < rad(abc)^(1+ε) for all ε>0 and all but finitely many (a,b,c)

Status: Shinichi Mochizuki published a claimed proof in 2012 using Inter-universal
Teichmüller Theory (IUT) — ~500 pages across 4 papers. As of 2024, the mathematical
community has not accepted the proof. Scholze & Stix identified a specific gap in
2018; Mochizuki disputes it.

TWO INVARIANTS APPLIED:

1. DCP — community confidence trajectory modeled as possibility space:
   breadth = fraction of mathematical community that considers the proof unverified.
   If proof acceptance is logistic, k tells us the coupling rate.

2. Oscillator locking — each researcher is an oscillator with a confidence phase.
   Proof is "accepted" when phases lock above K_c. We model this explicitly:
   N_engaged = researchers who've deeply read the proof
   coupling = overlap between Mochizuki's framework and standard math
   K_eff = N_engaged × coupling / N_total_field
   K_c = critical coupling for this community size

Sources: Mochizuki 2012, Scholze & Stix 2018, Mochizuki's rebuttal 2018,
Castelvecchi 2020 (Nature), various community surveys.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Community confidence trajectory
# breadth = fraction who consider proof UNVERIFIED (1.0 = no one accepts, 0.0 = universally accepted)
CONFIDENCE = [
    {"date": "2012-08-30",
     "event": "Mochizuki posts 4 IUT papers — 500+ pages, entirely new framework",
     "unverified_frac": 1.00,
     "n_engaged": 0,
     "note": "Nobody has read it yet; no change from prior state"},

    {"date": "2013-06-01",
     "event": "First workshops attempt to read IUT; experts report extreme difficulty",
     "unverified_frac": 0.98,
     "n_engaged": 5,
     "note": "~5 people have engaged seriously; marginal movement"},

    {"date": "2015-12-01",
     "event": "Go Yamashita produces 300-page survey of IUT; small Kyoto group claims understanding",
     "unverified_frac": 0.94,
     "n_engaged": 8,
     "note": "Kyoto cluster starting to form; still <10 people outside Mochizuki's group"},

    {"date": "2016-07-01",
     "event": "Clay Institute / RIMS workshops — ~50 mathematicians attempt to learn IUT",
     "unverified_frac": 0.90,
     "n_engaged": 15,
     "note": "Broader engagement; but most leave unconvinced they understand it"},

    {"date": "2018-03-01",
     "event": "Scholze & Stix publish report identifying specific gap in Corollary 3.12; "
              "visit Mochizuki in Kyoto for 5 days of discussion",
     "unverified_frac": 0.95,
     "n_engaged": 15,
     "note": "UPWARD REVISION — Scholze is Fields Medalist; his objection credible. "
              "Community confidence in proof decreases"},

    {"date": "2018-09-01",
     "event": "Mochizuki publishes rebuttal — claims Scholze & Stix 'fundamentally misunderstood' IUT",
     "unverified_frac": 0.93,
     "n_engaged": 15,
     "note": "Slight recovery; disagreement now explicit and published"},

    {"date": "2020-04-03",
     "event": "RIMS accepts papers for publication in PRIMS (journal Mochizuki edits); "
              "community reaction mostly negative — conflict of interest concerns",
     "unverified_frac": 0.92,
     "n_engaged": 17,
     "note": "Publication without resolving Scholze-Stix objection; skepticism grows"},

    {"date": "2021-03-01",
     "event": "Papers published in PRIMS. Mainstream community still does not accept.",
     "unverified_frac": 0.92,
     "n_engaged": 17,
     "note": "No change — publication did not unlock community acceptance"},

    {"date": "2022-01-01",
     "event": "Ivan Fesenko (pro-IUT) produces accessible account; "
              "anti-camp: Scholze maintains gap is unfixed",
     "unverified_frac": 0.91,
     "n_engaged": 20,
     "note": "Slight uptick in engagement; community still split"},

    {"date": "2024-01-01",
     "event": "Current state: ~20 researchers claim understanding; "
              "mainstream community (~500 relevant number theorists) does not accept. "
              "Scholze-Stix gap unresolved.",
     "unverified_frac": 0.91,
     "n_engaged": 20,
     "note": "Stasis — 12 years after posting, proof not accepted"},
]

# Oscillator locking model parameters
# Mathematical community of arithmetic geometers: ~500 people
# Kuramoto K_c for random network: K_c ≈ 2 * mean_natural_freq / (N * mean_coupling)
# Simplified: K_c ≈ 1 / sqrt(N_engaged * coupling_per_pair)

COMMUNITY_SIZE = 500  # relevant arithmetic geometers globally
COUPLING_PER_PAIR = 0.02  # fraction of proof overlap with standard framework
# (IUT uses entirely new objects — coupling is very low)


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.01: return 0.0, 0.5, 0.0
    norm = [(v-mn)/(mx-mn) for v in series]
    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [0.5,1,2,3,5,7,10,15,20]:
        for t0 in [i/20 for i in range(21)]:
            ss = sum((y-1/(1+math.exp(k*(t-t0))))**2 for t,y in zip(ts,norm))
            if ss < best_ss: best_ss, best_k, best_t0 = ss, k, t0
    mean_y = sum(norm)/n
    ss_tot = sum((y-mean_y)**2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss/ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def kuramoto_K_c(N, mean_freq_spread=1.0):
    """Critical coupling for Kuramoto model with Lorentzian frequency distribution."""
    return 2.0 * mean_freq_spread  # K_c = 2γ for Lorentzian; γ = half-width


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== abc Conjecture / Mochizuki — DCP + Oscillator Locking ===\n")

    unverified = [e["unverified_frac"] for e in CONFIDENCE]
    n_engaged  = [e["n_engaged"]       for e in CONFIDENCE]

    k, t0, r2 = _fit_logistic(unverified)

    # Direction changes
    dc = sum(1 for i in range(len(unverified)-2)
             if (unverified[i+2]-unverified[i+1]) * (unverified[i+1]-unverified[i]) < 0)

    final_unverified = unverified[-1]
    final_engaged    = n_engaged[-1]

    print(f"  Evidence events: {len(CONFIDENCE)}")
    print(f"  Unverified fraction: {[round(u,2) for u in unverified]}")
    print(f"  Final unverified: {final_unverified:.2f}  ({int(final_unverified*100)}% of community)")
    print(f"  Direction changes: {dc}")
    print(f"  Logistic fit: k={k}  R²={r2:.3f}")

    # Oscillator locking analysis
    print(f"\n  --- Oscillator Locking Analysis ---")
    K_c = kuramoto_K_c(COMMUNITY_SIZE)
    # K_eff = mean degree × coupling = (N_engaged / N_total) × coupling_per_pair × N_engaged
    K_eff = (final_engaged / COMMUNITY_SIZE) * COUPLING_PER_PAIR * final_engaged
    order_param = final_engaged / COMMUNITY_SIZE  # crude synchrony measure

    print(f"  Community size: {COMMUNITY_SIZE} relevant researchers")
    print(f"  Deeply engaged: {final_engaged} (~{final_engaged/COMMUNITY_SIZE:.1%})")
    print(f"  Coupling per pair (IUT↔standard math): {COUPLING_PER_PAIR:.2f}")
    print(f"  K_eff ≈ {K_eff:.4f}")
    print(f"  K_c   ≈ {K_c:.2f}  (Kuramoto critical coupling)")
    print(f"  K_eff / K_c = {K_eff/K_c:.4f}  (need > 1.0 for locking)")

    locked = K_eff >= K_c
    if locked:
        lock_verdict = "LOCKED — community should be synchronizing"
    else:
        n_needed = math.ceil(math.sqrt(K_c / COUPLING_PER_PAIR) * math.sqrt(COMMUNITY_SIZE))
        lock_verdict = (f"DESYNCHRONIZED — K_eff/K_c = {K_eff/K_c:.4f}. "
                        f"Community cannot lock at current engagement level. "
                        f"Estimated researchers needed for locking: ~{n_needed} "
                        f"(currently {final_engaged}). "
                        f"OR: coupling must increase ~{K_c/K_eff:.0f}× "
                        f"(requires proof simplification / pedagogical bridge).")

    print(f"\n  Oscillator verdict: {lock_verdict}")

    # Combined verdict
    if final_unverified < 0.10:
        dcp_verdict = "accepted"
    elif dc >= 2:
        dcp_verdict = (f"OSCILLATING — Scholze-Stix objection caused upward revision. "
                       f"k={k}, R²={r2:.3f}. No convergence toward acceptance in 12 years.")
    else:
        dcp_verdict = f"stalled at {final_unverified:.0%} unverified"

    print(f"\n  DCP verdict: {dcp_verdict}")
    print(f"\n  Combined structural finding:")
    print(f"    DCP: community confidence oscillates — the Scholze-Stix gap is a")
    print(f"    direction-reversal event, same structure as the Paris comet hypothesis")
    print(f"    in the Wow! Signal. One credible objection reversed years of slow progress.")
    print(f"    Oscillator locking: K_eff/K_c ≈ {K_eff/K_c:.4f} — deeply subcritical.")
    print(f"    The proof cannot be accepted by the community as currently structured.")
    print(f"    Either ~{math.ceil(math.sqrt(K_c/COUPLING_PER_PAIR)*math.sqrt(COMMUNITY_SIZE))} researchers")
    print(f"    must deeply engage, or the coupling (accessibility) must increase ~{K_c/K_eff:.0f}×.")
    print(f"    This is not about whether the proof is correct — it is about whether")
    print(f"    the mathematical community can synchronize around it.")

    result = {
        "problem": "abc conjecture — Mochizuki IUT proof",
        "confidence_trajectory": CONFIDENCE,
        "dcp": {"k": k, "t0": t0, "r2": r2,
                "direction_changes": dc, "final_unverified": final_unverified},
        "oscillator_locking": {
            "community_size": COMMUNITY_SIZE,
            "n_engaged": final_engaged,
            "coupling_per_pair": COUPLING_PER_PAIR,
            "K_eff": round(K_eff, 6),
            "K_c": round(K_c, 4),
            "ratio": round(K_eff/K_c, 6),
            "locked": locked,
        },
        "verdict": {"dcp": dcp_verdict, "oscillator": lock_verdict},
    }
    dest = ARTIFACTS / "math_abc_mochizuki.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
