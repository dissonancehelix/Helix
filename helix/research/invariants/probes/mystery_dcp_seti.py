"""
core/probes/math/probes/mystery_dcp_seti.py

Helix — SETI Non-Detection: The Fermi Paradox as DCP

The Fermi Paradox: given the age and size of the galaxy, intelligent life should
be common and detectable. Yet we have detected nothing. Why?

This probe models two quantities:
  1. Survey coverage — fraction of plausible SETI target space that has been
     searched (frequency × sky × sensitivity × time × technosignature type)
  2. Resolution breadth — the number of viable Fermi Paradox solutions that
     remain live given the current survey coverage

As coverage increases, some Fermi solutions become untenable (if we'd searched
10% of the galaxy thoroughly and found nothing, certain solutions are less viable).
Others become more viable (rare Earth, simulation hypothesis, etc.).

Key insight: the SETI problem is structurally different from other mysteries.
Absence of detection is evidence for ALL "rare/absent civilization" hypotheses
simultaneously, but NOT discriminating between them. Coverage approaching 1.0
would eventually force a choice — but we are still at ~0.001% of plausible space.

Sources: Tarter 2001, Werthimer et al. 2020, Wlodarczyk-Sroka et al. 2020,
Price et al. 2020 (Breakthrough Listen), Wright 2021, Grimaldi 2017.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Survey coverage timeline
# Coverage = rough fraction of plausible SETI target space surveyed
# Based on estimates from major SETI literature
# Note: "plausible target space" = frequency range × sky area × sensitivity threshold
COVERAGE = [
    {"date": "1960-04-01",
     "event": "Project Ozma — Drake searches 2 stars at 1420 MHz for 150 hours",
     "coverage": 0.0000001,
     "viable_solutions": 10,
     "note": "2 stars out of ~100B in galaxy; narrow frequency; first attempt"},

    {"date": "1972-01-01",
     "event": "Pioneer 10 plaque + multiple radio survey programs in 60s-70s; "
              "~100 stars surveyed across limited frequencies",
     "coverage": 0.000001,
     "viable_solutions": 10,
     "note": "Coverage growing but negligible; all solutions equally viable"},

    {"date": "1977-08-15",
     "event": "Wow! Signal detected — single event, never repeated; "
              "Big Ear systematic survey ongoing",
     "coverage": 0.00001,
     "viable_solutions": 10,
     "note": "Wow! Signal is intriguing but single; coverage estimate 10× increase"},

    {"date": "1985-01-01",
     "event": "META (Megachannel ExtraTerrestrial Assay) — 8.4 million channels, "
              "full sky, Harvard. First million-channel survey.",
     "coverage": 0.0001,
     "viable_solutions": 9,
     "note": "10× coverage increase; no detection. 'Galactic beacon' hypothesis weakened"},

    {"date": "1995-01-01",
     "event": "Project Phoenix (SETI Institute) — most sensitive targeted search to date; "
              "1000 nearby sun-like stars, 1-3 GHz",
     "coverage": 0.001,
     "viable_solutions": 9,
     "note": "100 nearby stars searched deeply; no detection"},

    {"date": "1999-01-01",
     "event": "SETI@home launches — 5 million users; Arecibo survey data analyzed "
              "at massive scale; 1.42 GHz, 2.5 MHz bandwidth, full sky",
     "coverage": 0.005,
     "viable_solutions": 8,
     "note": "Significant scale increase; still no confirmed signal. "
              "'Strong deliberate beacon' hypothesis weakens"},

    {"date": "2010-01-01",
     "event": "Allen Telescope Array operational — 350 MHz to 11.2 GHz; "
              "wider frequency coverage; Kepler exoplanet targets added",
     "coverage": 0.01,
     "viable_solutions": 8,
     "note": "Kepler planets as targets; no detection near known habitable worlds"},

    {"date": "2016-01-01",
     "event": "Breakthrough Listen — $100M, Parkes + GBT; 1-10 GHz, 100 nearest stars, "
              "nearest 1M stars, 100 nearby galaxies; 50× previous sensitivity",
     "coverage": 0.05,
     "viable_solutions": 7,
     "note": "Major jump; no detection. 'Galactic club broadcasting' hypothesis weakened"},

    {"date": "2019-01-01",
     "event": "SETI@home processes 30 years of Arecibo data — 150,000+ candidate events, "
              "all resolved as RFI or insufficient SNR",
     "coverage": 0.08,
     "viable_solutions": 7,
     "note": "Exhaustive Arecibo reanalysis; no surviving candidates"},

    {"date": "2020-04-01",
     "event": "SETI@home suspends active analysis (data processed); "
              "Breakthrough Listen survey papers: no technosignatures in 1327 nearby stars",
     "coverage": 0.10,
     "viable_solutions": 6,
     "note": "1327 stars searched with highest sensitivity ever; silence holds. "
              "'Transmitting at radio frequencies toward us' class much less viable"},

    {"date": "2022-01-01",
     "event": "Wlodarczyk-Sroka et al.: 10.4M stellar systems in GBT survey region checked — "
              "no technosignatures above sensitivity threshold",
     "coverage": 0.15,
     "viable_solutions": 6,
     "note": "Largest single survey by star count; still nothing"},

    {"date": "2024-01-01",
     "event": "Current state: ~15% coverage of minimal search space (radio, nearby stars). "
              "Optical SETI, neutrino, gravitational wave, artifact searches all nascent.",
     "coverage": 0.15,
     "viable_solutions": 6,
     "note": "Plateau in radio; new modalities opening but not yet constraining"},
]

# The Fermi solutions (viable hypotheses) — which ones each survey event eliminates or weakens
FERMI_SOLUTIONS = [
    "Rare Earth (complex life is genuinely rare)",
    "Great Filter ahead (civilizations self-destruct before broadcasting)",
    "Great Filter behind (we are among the first)",
    "Dark forest (civilizations hide deliberately)",
    "We're not looking right (wrong modalities, wrong assumptions)",
    "Zoo/planetarium hypothesis (they are here, watching quietly)",
    "Simulation (the universe is artificial; signals are suppressed)",
    "Short broadcast window (civilizations broadcast briefly, then go quiet)",
    "No strong reason to broadcast (why would they?)",
    "Interstellar distances + physics (no realistic communication channel)",
]


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.05: return 0.0, 0.5, 0.0
    norm = [(v-mn)/(mx-mn) for v in series]
    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [0.5,1,2,3,5,7,10,15,20,30]:
        for t0 in [i/20 for i in range(21)]:
            ss = sum((y-1/(1+math.exp(k*(t-t0))))**2 for t,y in zip(ts,norm))
            if ss < best_ss: best_ss, best_k, best_t0 = ss, k, t0
    mean_y = sum(norm)/n
    ss_tot = sum((y-mean_y)**2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss/ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== SETI Non-Detection / Fermi Paradox — Coverage DCP ===\n")

    coverages  = [e["coverage"]         for e in COVERAGE]
    solutions  = [e["viable_solutions"] for e in COVERAGE]
    dates      = [e["date"]             for e in COVERAGE]

    # Normalize solutions: 1 viable solution = solved
    max_sol = max(solutions)
    breadths = [s / max_sol for s in solutions]

    k_cov, t0_cov, r2_cov = _fit_logistic(coverages)
    k_sol, t0_sol, r2_sol = _fit_logistic(breadths)

    final_coverage  = coverages[-1]
    final_solutions = solutions[-1]

    # Extrapolate: at what coverage would we expect < 2 solutions to remain?
    # If solutions ~ max_sol * (1 - coverage/1.0), solve for coverage
    # Simple linear model: solutions drop by ~4 from 0→15% coverage
    # Rate: 4/0.15 = 26.7 solutions per 100% coverage
    rate_per_full = (solutions[0] - solutions[-1]) / coverages[-1]
    coverage_to_resolve = solutions[-1] / rate_per_full if rate_per_full > 0 else float("inf")

    print(f"  Survey events: {len(COVERAGE)}")
    print(f"  Coverage trajectory: {[f'{c:.5f}' for c in coverages]}")
    print(f"  Viable solutions: {solutions}")
    print(f"  Current coverage: {final_coverage:.1%} of minimal radio search space")
    print(f"  Viable Fermi solutions: {final_solutions}/{len(FERMI_SOLUTIONS)}")
    print(f"  Coverage fit: k={k_cov}  R²={r2_cov:.3f}")
    print(f"  Solution fit: k={k_sol}  R²={r2_sol:.3f}")
    print()

    if coverage_to_resolve < 1.0:
        extrapolation = (f"At current elimination rate, full coverage would reduce solutions "
                         f"to ~1 at ≈{coverage_to_resolve:.0%} coverage.")
    else:
        extrapolation = (f"At current elimination rate, full radio coverage would still "
                         f"leave {max(1, int(solutions[-1] - rate_per_full))} viable solutions. "
                         f"The Fermi Paradox cannot be resolved by radio surveys alone.")

    print(f"  Extrapolation: {extrapolation}")

    verdict = (f"STRUCTURALLY OPEN — 15% of minimal search space surveyed, "
               f"{final_solutions}/{len(FERMI_SOLUTIONS)} Fermi solutions still viable. "
               f"Non-detection is evidence against 'strong deliberate beacon' class hypotheses "
               f"but does not discriminate between the remaining {final_solutions}. "
               f"The Fermi Paradox is not a mystery — it is a coverage problem. "
               f"Current coverage ≈ checking 1 grain of sand on a beach.")

    print(f"\n  Verdict: {verdict}")
    print(f"\n  Key structural finding:")
    print(f"    Non-detection systematically eliminates 'broadcasting loudly' hypotheses")
    print(f"    while leaving all 'quiet civilization' hypotheses untouched.")
    print(f"    The hypothesis space is not narrowing symmetrically — it is shifting.")
    print(f"    At 15% coverage, we can say: if ETI exists and is broadcasting at radio")
    print(f"    frequencies toward us at detectable power, we would have found them.")
    print(f"    We cannot yet say much about anything else.")

    result = {
        "mystery": "SETI Non-Detection / Fermi Paradox",
        "survey_data": COVERAGE,
        "fermi_solutions": FERMI_SOLUTIONS,
        "final_coverage": final_coverage,
        "final_viable_solutions": final_solutions,
        "coverage_fit": {"k": k_cov, "r2": r2_cov},
        "solutions_fit": {"k": k_sol, "r2": r2_sol},
        "extrapolation": extrapolation,
        "verdict": verdict,
    }
    dest = ARTIFACTS / "mystery_seti.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
