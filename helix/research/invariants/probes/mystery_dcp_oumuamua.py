"""
core/probes/math/probes/mystery_dcp_oumuamua.py

Helix — 'Oumuamua: Two Competing Hypotheses

On October 19, 2017, Pan-STARRS detected the first confirmed interstellar object
passing through the solar system. It had unexpected properties:
  - Cigar-shaped or pancake-shaped (aspect ratio ~6:1 to 10:1)
  - Non-gravitational acceleration WITHOUT detectable outgassing
  - No coma, no tail, no detectable water or volatiles
  - Tumbling rotation (not spin-stabilized)
  - Color: red, consistent with interstellar medium processing

Two primary hypotheses compete:
  H1: Natural object (nitrogen ice, hydrogen iceberg, fractal dust aggregate,
      cometary fragment — various proposals)
  H2: Artifact hypothesis (Loeb & Bialy 2018: light sail propelled by radiation
      pressure; thin sheet ~0.3–0.9mm, area ~0.1km²)

This probe tracks the trajectory of both hypotheses as evidence accumulates.
We model two parallel DCP trajectories: P(H1_viable) and P(H2_viable).
If one collapses to near 0, the other "wins" by elimination.

Sources: Meech et al. 2017 Nature, Micheli et al. 2018 Nature, Bialy & Loeb 2018,
Flekkøy et al. 2019, Seligman & Laughlin 2020, Jackson & Desch 2021.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Evidence timeline — each event updates both P(natural_viable) and P(artifact_viable)
# Values represent normalized confidence [0,1] — not probabilities that sum to 1
# (both can decrease simultaneously if evidence is ambiguous)
EVIDENCE = [
    {"date": "2017-10-19",
     "event": "Discovery — interstellar origin confirmed from hyperbolic trajectory",
     "p_natural": 0.90, "p_artifact": 0.10,
     "note": "Strong prior for natural; interstellar objects expected to exist"},

    {"date": "2017-10-25",
     "event": "Shape constraint: aspect ratio ~6:1 to 10:1 from lightcurve",
     "p_natural": 0.75, "p_artifact": 0.25,
     "note": "Extreme elongation unusual but not impossible for natural object; "
             "consistent with light sail geometry"},

    {"date": "2017-11-01",
     "event": "Color: red, featureless spectrum — consistent with irradiated organics",
     "p_natural": 0.80, "p_artifact": 0.20,
     "note": "Red color supports natural irradiated surface; no spectral lines"},

    {"date": "2017-11-14",
     "event": "No detectable outgassing, no coma, no CO/CO2 emission",
     "p_natural": 0.60, "p_artifact": 0.35,
     "note": "Most comets outgas; lack of outgassing strains cometary hypothesis"},

    {"date": "2018-06-20",
     "event": "Micheli et al. (Nature): confirmed non-gravitational acceleration — "
              "0.001 cm/s² at 1AU, inconsistent with solar gravity + drag alone",
     "p_natural": 0.45, "p_artifact": 0.55,
     "note": "Major finding — acceleration without outgassing is the crux. "
             "Natural explanations require novel mechanisms"},

    {"date": "2018-11-01",
     "event": "Bialy & Loeb: light sail hypothesis — thin sheet propelled by radiation pressure. "
              "Fits acceleration with ~0.3-0.9mm thick object, ~0.1km² area",
     "p_natural": 0.40, "p_artifact": 0.60,
     "note": "Formal artifact hypothesis published in peer-reviewed journal; "
             "parameters self-consistent"},

    {"date": "2019-03-01",
     "event": "Flekkøy et al.: fractal dust aggregate model — porous low-density "
              "object could produce acceleration from solar radiation without outgassing",
     "p_natural": 0.55, "p_artifact": 0.45,
     "note": "Natural hypothesis recovers; fractal structure could explain both shape and acceleration"},

    {"date": "2019-07-01",
     "event": "Jackson & Desch critique Bialy-Loeb: tumbling rotation inconsistent with "
              "intact light sail (would be torn apart); structural objection",
     "p_natural": 0.60, "p_artifact": 0.35,
     "note": "Artifact hypothesis weakened by dynamic instability argument"},

    {"date": "2020-05-01",
     "event": "Seligman & Laughlin: hydrogen iceberg hypothesis — H2 ice evaporates "
              "invisibly, explains acceleration without visible outgassing",
     "p_natural": 0.70, "p_artifact": 0.30,
     "note": "H2 ice could explain everything — but requires formation in cold molecular cloud, "
              "and H2 ice is very fragile"},

    {"date": "2021-03-01",
     "event": "Jackson & Desch detailed critique of H2 model: H2 ice would have "
              "sublimated entirely before reaching inner solar system",
     "p_natural": 0.55, "p_artifact": 0.30,
     "note": "H2 hypothesis challenged; natural explanations running out of options"},

    {"date": "2021-08-01",
     "event": "Nitrogen ice shard hypothesis (Desch & Jackson): fragment of exo-Pluto "
              "surface, N2 ice, transparent evaporation explains acceleration",
     "p_natural": 0.65, "p_artifact": 0.25,
     "note": "N2 ice hypothesis: consistent with acceleration if ~30m thick, "
              "but requires exotic formation scenario"},

    {"date": "2023-03-01",
     "event": "JWST operational but 'Oumuamua already gone — no follow-up spectroscopy possible",
     "p_natural": 0.60, "p_artifact": 0.25,
     "note": "No new evidence; object unobservable. Both hypotheses stall"},

    {"date": "2024-01-01",
     "event": "Current state: N2 ice and fractal aggregate are leading natural hypotheses; "
              "artifact hypothesis unfalsified but not supported by new evidence",
     "p_natural": 0.60, "p_artifact": 0.20,
     "note": "Convergence toward natural but with high residual uncertainty"},
]


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.05: return 0.0, 0.5, 0.0
    norm = [(v-mn)/(mx-mn) for v in series]
    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [0.5,1,2,3,5,7,10,15,20,30,50]:
        for t0 in [i/20 for i in range(21)]:
            ss = sum((y-1/(1+math.exp(k*(t-t0))))**2 for t,y in zip(ts,norm))
            if ss < best_ss: best_ss, best_k, best_t0 = ss, k, t0
    mean_y = sum(norm)/n
    ss_tot = sum((y-mean_y)**2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss/ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== 'Oumuamua — Two-Hypothesis DCP Race ===\n")

    p_nats    = [e["p_natural"]  for e in EVIDENCE]
    p_arts    = [e["p_artifact"] for e in EVIDENCE]

    k_nat, t0_nat, r2_nat = _fit_logistic(p_nats)
    k_art, t0_art, r2_art = _fit_logistic(p_arts)

    # Direction changes (oscillation)
    def direction_changes(series):
        return sum(
            1 for i in range(len(series)-2)
            if (series[i+2]-series[i+1]) * (series[i+1]-series[i]) < 0
        )

    dc_nat = direction_changes(p_nats)
    dc_art = direction_changes(p_arts)

    final_nat = p_nats[-1]
    final_art = p_arts[-1]

    print(f"  Evidence events: {len(EVIDENCE)}")
    print(f"  P(natural) trajectory: {[round(p,2) for p in p_nats]}")
    print(f"  P(artifact) trajectory:{[round(p,2) for p in p_arts]}")
    print(f"  Final P(natural):  {final_nat:.2f}  (k={k_nat}, R²={r2_nat:.3f}, dir_changes={dc_nat})")
    print(f"  Final P(artifact): {final_art:.2f}  (k={k_art}, R²={r2_art:.3f}, dir_changes={dc_art})")

    # Verdict
    gap = final_nat - final_art
    if final_nat > 0.85:
        verdict = "resolved — natural origin confirmed"
    elif final_art > 0.85:
        verdict = "resolved — artifact hypothesis confirmed"
    elif gap > 0.25:
        verdict = (f"LEANING NATURAL — P(natural)={final_nat:.2f} leads P(artifact)={final_art:.2f} "
                   f"by {gap:.2f}. Non-gravitational acceleration without outgassing remains "
                   f"the central unexplained feature. N2 ice and fractal aggregate models "
                   f"are viable but require exotic conditions.")
    elif gap < -0.25:
        verdict = (f"LEANING ARTIFACT — P(artifact)={final_art:.2f} leads P(natural)={final_nat:.2f}. "
                   f"Structural objections to light sail (tumbling) weaken this.")
    else:
        verdict = (f"GENUINELY UNDECIDED — gap={gap:.2f}. The acceleration is real; "
                   f"the mechanism is unknown; the object is gone.")

    print(f"\n  Verdict: {verdict}")
    print(f"\n  Key structural finding:")
    print(f"    The non-gravitational acceleration (Micheli 2018) is the single most")
    print(f"    discriminating data point — it cannot be explained by standard physics.")
    print(f"    Every natural hypothesis proposed since then requires an exotic or ad hoc")
    print(f"    mechanism. The artifact hypothesis is structurally simpler but dynamically")
    print(f"    unstable (tumbling). The object is now beyond detection — evidence closed.")

    result = {
        "mystery": "'Oumuamua (2017 interstellar object)",
        "evidence": EVIDENCE,
        "natural": {"k": k_nat, "t0": t0_nat, "r2": r2_nat,
                    "final_p": final_nat, "direction_changes": dc_nat},
        "artifact": {"k": k_art, "t0": t0_art, "r2": r2_art,
                     "final_p": final_art, "direction_changes": dc_art},
        "verdict": verdict,
    }
    dest = ARTIFACTS / "mystery_oumuamua.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
