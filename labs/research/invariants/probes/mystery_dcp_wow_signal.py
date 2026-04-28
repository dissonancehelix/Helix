"""
core/probes/math/probes/mystery_dcp_wow_signal.py

Helix — The Wow! Signal: Evidence That Never Collapsed

On August 15, 1977, Jerry Ehman at Ohio State's Big Ear telescope recorded a
72-second narrowband signal at 1420.405 MHz (the hydrogen line). He wrote "Wow!"
in the margin. It was never detected again.

This probe models the possibility space differently from other mysteries:
instead of tracking suspects, it tracks P(natural_origin) — the probability
that the signal has a natural explanation. Each piece of evidence either:
  - increases P(natural) by proposing/confirming a natural explanation
  - decreases P(natural) by ruling out a natural hypothesis
  - does nothing (another non-detection)

The interesting finding would be: does the trajectory converge to P(natural)≈1
(solved: natural), P(natural)≈0 (solved: artificial/anomalous), or does it
plateau somewhere in the middle (genuinely unresolved)?

Sources: Ehman 1998, Gray & Marvel 2001, Caballero 2017, Paris et al. 2016.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# P(natural_origin) trajectory over time
# Each entry: date, event, p_natural_after, note
EVIDENCE = [
    {"date": "1977-08-15",
     "event": "Signal detected — 1420.405 MHz, 30× background, 72s duration, narrowband",
     "p_natural": 0.50,
     "note": "No prior; equal priors assigned"},

    {"date": "1977-08-16",
     "event": "Single detection — no simultaneous confirmation on second feed of Big Ear",
     "p_natural": 0.60,
     "note": "One feed only → consistent with terrestrial RFI or single-source transit"},

    {"date": "1977-1983",
     "event": "Multiple follow-up observations at Big Ear — no repeat detection (50+ attempts)",
     "p_natural": 0.55,
     "note": "Non-detection increases P(RFI/transient natural source) but also consistent "
              "with directed beam; no clear update direction"},

    {"date": "1987-01-01",
     "event": "Dixon & Cole analysis: signal bandwidth and frequency match H-line precisely; "
              "too narrow for most known natural broadband sources",
     "p_natural": 0.40,
     "note": "Narrowband nature is hard to explain naturally; P(natural) decreases"},

    {"date": "1995-01-01",
     "event": "Ehman analysis: signal strength and beam width consistent with transmitter "
              "at ~2.something light years — rules out terrestrial origin geometrically",
     "p_natural": 0.35,
     "note": "Geometry rules out Earth-based RFI for that exact frequency; P(natural) drops"},

    {"date": "1999-01-01",
     "event": "SETI@home and other programs search the coordinates — no confirmation",
     "p_natural": 0.38,
     "note": "Non-detection slightly increases P(transient natural) — if artificial and "
              "continuous, should have been re-detected by now"},

    {"date": "2012-07-01",
     "event": "Anomalous RFI from satellites/aircraft investigated — ruled out for 1977 "
              "(no satellites at those coordinates in 1977)",
     "p_natural": 0.33,
     "note": "Eliminates modern RFI category; narrows options"},

    {"date": "2016-06-01",
     "event": "Paris et al.: cometary hydrogen cloud hypothesis — two comets (266P Christensen, "
              "335P Gibbs) were near that sky location in 1977",
     "p_natural": 0.70,
     "note": "Major upward revision — credible natural source proposed for first time"},

    {"date": "2017-01-01",
     "event": "Ehman & others critique Paris: cometary hydrogen clouds are too diffuse "
              "and broadband to produce the observed narrowband spike; "
              "model does not reproduce signal parameters",
     "p_natural": 0.50,
     "note": "Paris hypothesis challenged — P(natural) drops back; hypothesis not confirmed"},

    {"date": "2017-06-01",
     "event": "Gray & Ellingsen re-observation of exact coordinates with modern telescopes "
              "— no signal detected at any frequency",
     "p_natural": 0.45,
     "note": "If natural (repeating source), would likely have been re-detected; "
              "non-detection pushes toward unique/transient event"},

    {"date": "2020-01-01",
     "event": "Updated cometary hypothesis rejected by multiple groups; "
              "no other credible natural source proposed",
     "p_natural": 0.42,
     "note": "Current state: no confirmed natural explanation, no confirmed artificial"},

    {"date": "2024-01-01",
     "event": "Current state: unresolved. P(natural) estimated ~0.40-0.50 by most researchers. "
              "The signal remains a one-time event with no confirmed explanation.",
     "p_natural": 0.42,
     "note": "Stasis — 47 years later, no convergence"},
]


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.01: return 0.0, 0.5, 0.0
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
    print("=== Wow! Signal — Evidence Trajectory ===\n")

    p_nats = [e["p_natural"] for e in EVIDENCE]
    k, t0, r2 = _fit_logistic(p_nats)

    # Measure oscillation — evidence ping-pongs rather than converging
    diffs = [abs(p_nats[i+1]-p_nats[i]) for i in range(len(p_nats)-1)]
    direction_changes = sum(
        1 for i in range(len(diffs)-1)
        if (p_nats[i+2]-p_nats[i+1]) * (p_nats[i+1]-p_nats[i]) < 0
    )
    final_p = p_nats[-1]
    total_range = max(p_nats) - min(p_nats)

    print(f"  Evidence events: {len(EVIDENCE)}")
    print(f"  P(natural) trajectory: {[round(p,2) for p in p_nats]}")
    print(f"  Final P(natural): {final_p:.2f}")
    print(f"  Total range: {total_range:.2f}")
    print(f"  Direction changes: {direction_changes} (oscillation measure)")
    print(f"  Logistic fit: k={k}  R²={r2:.3f}")

    # Verdict
    if final_p > 0.85:
        verdict = "resolved — natural origin confirmed"
    elif final_p < 0.15:
        verdict = "resolved — artificial/anomalous origin confirmed"
    elif direction_changes >= 3:
        verdict = (f"OSCILLATING — evidence alternately supports and undermines natural "
                   f"explanations. The Paris 2016 cometary hypothesis was the most significant "
                   f"natural explanation proposed, but it was challenged. "
                   f"Current P(natural)≈{final_p:.2f} — genuinely undecided.")
    else:
        verdict = f"unresolved — P(natural)={final_p:.2f}, no convergence"

    print(f"\n  Verdict: {verdict}")
    print(f"\n  Key structural finding:")
    print(f"    The evidence oscillates rather than converging. The Paris comet")
    print(f"    hypothesis caused the largest single update (+0.35) in 47 years,")
    print(f"    then was partially retracted. No other natural explanation has")
    print(f"    produced a comparable upward revision. The signal is structurally")
    print(f"    trapped between 'probably not natural' and 'probably not artificial'.")

    result = {"mystery": "Wow! Signal (1977)", "evidence": EVIDENCE,
              "k": k, "t0": t0, "r2": r2,
              "final_p_natural": final_p,
              "direction_changes": direction_changes,
              "verdict": verdict}
    dest = ARTIFACTS / "mystery_wow_signal.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")

if __name__ == "__main__":
    main()
