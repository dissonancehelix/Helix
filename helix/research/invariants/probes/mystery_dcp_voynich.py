"""
core/probes/math/probes/mystery_dcp_voynich.py

Helix — The Voynich Manuscript: Interpretive Possibility Space

The Voynich Manuscript is a ~240-page illustrated codex, carbon-dated to 1404–1438,
written in an unknown script with no confirmed decode. It has:
  - ~170,000 characters in an unknown writing system
  - Illustrations of plants, astronomical diagrams, baths, biological figures
  - Statistical regularities (Zipf's law, word frequency distributions consistent
    with natural language)
  - No confirmed linguistic identification despite 100+ years of attempts

Possibility space modeled here: number of viable interpretive hypotheses.
Each time a hypothesis is formally proposed AND achieves peer consensus it contracts
the space; each time a hypothesis is refuted OR a new competing hypothesis is
introduced it may contract OR expand.

Unlike D.B. Cooper (one solution, gradually narrowing), Voynich has ACCUMULATED
hypotheses over time. The DCP trajectory may be FLAT or EXPANDING — which would
mean it is structurally anti-convergent.

Sources: Wilfrid Voynich 1912, Newbold 1921, Tiltman 1951, Currier 1976,
Stolfi 2003, Rugg 2004, Bax 2014, Montemurro & Zanette 2013, Cheshire 2019,
Davis 2020, Timm & Schinner 2021.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Hypothesis count trajectory
# breadth = normalized count of ACTIVE viable hypotheses (not refuted, not merged)
# We track the raw count and normalize at the end
HYPOTHESES = [
    {"date": "1912-01-01",
     "event": "Voynich acquires manuscript; announces discovery to world",
     "active_hypotheses": 1,
     "note": "Only one hypothesis: genuine ancient text, language unknown"},

    {"date": "1921-01-01",
     "event": "Newbold: Roger Bacon authorship + microscopic cipher theory",
     "active_hypotheses": 2,
     "note": "Bacon hypothesis added; original 'unknown language' still open"},

    {"date": "1931-01-01",
     "event": "Manly refutes Newbold — microscopic marks are ink cracking, not cipher",
     "active_hypotheses": 1,
     "note": "Newbold hypothesis eliminated; back to 1"},

    {"date": "1944-01-01",
     "event": "Friedman: possibly a constructed language (conlang) not natural language",
     "active_hypotheses": 2,
     "note": "Conlang hypothesis added"},

    {"date": "1951-01-01",
     "event": "Tiltman: detailed linguistic analysis — consistent with natural language statistics; "
              "adds 'extinct natural language' as separate hypothesis",
     "active_hypotheses": 3,
     "note": "Natural language + conlang + hoax all viable"},

    {"date": "1976-01-01",
     "event": "Currier: identifies two distinct 'languages' (A and B) within manuscript",
     "active_hypotheses": 4,
     "note": "Multi-author theory added; two scribes writing different content"},

    {"date": "1978-01-01",
     "event": "Levitov: proto-Romance Cathar liturgy hypothesis",
     "active_hypotheses": 5,
     "note": "Specific language claim; later refuted by historians"},

    {"date": "1987-01-01",
     "event": "Levitov hypothesis refuted by Cathar historians and linguists",
     "active_hypotheses": 4,
     "note": "One hypothesis eliminated"},

    {"date": "2003-01-01",
     "event": "Stolfi: statistical analysis consistent with East Asian agglutinative language",
     "active_hypotheses": 5,
     "note": "East Asian hypothesis added — interesting but not confirmed"},

    {"date": "2004-01-01",
     "event": "Rugg: hoax hypothesis formalized — Gordon table method could generate "
              "Voynich-like text; statistical patterns explainable without meaning",
     "active_hypotheses": 6,
     "note": "Hoax hypothesis formalized with mechanism"},

    {"date": "2013-01-01",
     "event": "Montemurro & Zanette: information-theoretic analysis shows non-random "
              "structure beyond statistical mimicry — argues against hoax",
     "active_hypotheses": 5,
     "note": "Rugg hoax hypothesis weakened but not eliminated; -1 strength"},

    {"date": "2014-01-01",
     "event": "Bax: partial decode attempt — claims to identify ~10 plant names using "
              "comparative linguistics (contested by community)",
     "active_hypotheses": 6,
     "note": "New 'partial natural language' hypothesis; community skeptical"},

    {"date": "2019-01-01",
     "event": "Cheshire: claims full decode as 'proto-Romance language' — published, "
              "then widely criticized and considered pseudoscientific by linguists",
     "active_hypotheses": 6,
     "note": "New hypothesis added then immediately contested; net 0 change"},

    {"date": "2021-01-01",
     "event": "Timm & Schinner: detailed statistical analysis supports sophisticated "
              "hoax via table-based generation — hoax hypothesis revived",
     "active_hypotheses": 6,
     "note": "Hoax hypothesis strengthened again; natural language hypothesis weakened"},

    {"date": "2024-01-01",
     "event": "Current state: ~6 active hypotheses, none with scientific consensus. "
              "Carbon dating (1404-1438) is the only hard fact.",
     "active_hypotheses": 6,
     "note": "Case structurally stalled at high hypothesis count"},
]

MAX_H = max(e["active_hypotheses"] for e in HYPOTHESES)


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.05: return 0.0, 0.5, 0.0
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


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Voynich Manuscript — Anti-Convergent DCP ===\n")

    counts   = [e["active_hypotheses"] for e in HYPOTHESES]
    # Invert: DCP normally measures possibility space closing down.
    # For Voynich, MORE hypotheses = MORE open space. Normalize so that
    # 1 hypothesis = breadth 1.0 and MAX_H hypotheses = breadth MAX_H/1 = expanded.
    # We track normalized counts (1 = minimum = solved).
    breadths = [c / MAX_H for c in counts]

    k, t0, r2 = _fit_logistic(breadths)

    final_count  = counts[-1]
    initial_count = counts[0]
    net_change   = final_count - initial_count

    # Is this expanding, flat, or converging?
    first_half_mean  = sum(breadths[:len(breadths)//2]) / (len(breadths)//2)
    second_half_mean = sum(breadths[len(breadths)//2:]) / len(breadths[len(breadths)//2:])
    trend = second_half_mean - first_half_mean

    print(f"  Evidence events: {len(HYPOTHESES)}")
    print(f"  Hypothesis count trajectory: {counts}")
    print(f"  Initial hypotheses: {initial_count}  Final: {final_count}  Net change: +{net_change}")
    print(f"  Normalized breadths: {[round(b,2) for b in breadths]}")
    print(f"  Logistic fit: k={k}  R²={r2:.3f}")
    print(f"  Trend (2nd half vs 1st half): {trend:+.3f} ({'expanding' if trend>0.05 else 'flat' if abs(trend)<0.05 else 'converging'})")
    print()

    if final_count <= 1:
        verdict = "SOLVED — converged to single hypothesis"
    elif trend > 0.05:
        verdict = (f"ANTI-CONVERGENT — hypothesis space EXPANDED from {initial_count} to "
                   f"{final_count} over 112 years. Each new analysis adds a hypothesis without "
                   f"eliminating others. The manuscript is structurally resistant to resolution: "
                   f"it has enough complexity to support multiple internally-consistent "
                   f"interpretations simultaneously.")
    elif abs(trend) <= 0.05:
        verdict = (f"FLAT — hypothesis count oscillates between {min(counts)} and {max(counts)} "
                   f"with no net convergence. The Voynich is a stable attractor for hypotheses.")
    else:
        verdict = f"slow convergence — {final_count} hypotheses remain"

    print(f"  Verdict: {verdict}")
    print(f"\n  Key structural finding:")
    print(f"    Unlike other mysteries, Voynich does not narrow — it accumulates.")
    print(f"    The manuscript's statistical regularity (Zipf's law, bigram structure)")
    print(f"    is simultaneously evidence FOR natural language and evidence that a")
    print(f"    sophisticated hoax COULD produce it. This ambiguity is irreducible")
    print(f"    without an external reference — a Rosetta Stone that doesn't exist.")
    print(f"    DCP predicts: the case will only resolve when a physical artifact")
    print(f"    is found that cross-references the manuscript, OR when AI can")
    print(f"    statistically rule out all known language families definitively.")

    result = {
        "mystery": "Voynich Manuscript (~1404-1438)",
        "evidence": HYPOTHESES,
        "hypothesis_counts": counts,
        "breadths": [round(b, 3) for b in breadths],
        "k": k, "t0": t0, "r2": r2,
        "initial_hypotheses": initial_count,
        "final_hypotheses": final_count,
        "net_change": net_change,
        "trend": round(trend, 3),
        "verdict": verdict,
    }
    dest = ARTIFACTS / "mystery_voynich.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
