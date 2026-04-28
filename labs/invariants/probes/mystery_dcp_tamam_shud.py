"""
core/probes/math/probes/mystery_dcp_tamam_shud.py

Helix — Tamam Shud / Somerton Man: The Solved Arc

On December 1, 1948, a well-dressed man was found dead on Somerton Beach, Adelaide,
Australia. No ID. Autopsy inconclusive. Hidden in his pocket: a torn scrap reading
"Tamam Shud" (Persian: "it is ended") from a rare Omar Khayyam edition. A phone
number inside the book led to a woman ("Jestyn") who denied knowing him. A coded
message in the book was never solved. The man was never identified.

In 2022, investigator Derek Abbott's team used investigative genetic genealogy
(IGG) to identify the man as Carl "Charles" Webb, 43, electrical engineer from
Melbourne. His wife Gwenneth Dorothy Thomson was "Jestyn".

This mystery has a COMPLETE ARC — unresolved for 74 years, then solved.
This makes it uniquely valuable for Helix: we can measure the actual collapse
shape, not just estimate it. The DCP trajectory should show a long plateau
followed by a sudden collapse — the "solved cold case" pattern.

Sources: Adelaide Coroner's Court records, Abbott et al. 2022 PLOS One,
SA Police historical files, news reports.
"""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
ARTIFACTS = ROOT / "domains" / "language" / "artifacts"

# Possibility breadth = fraction of adult male population still viable as identity
# Pre-identification: broad then plateaued
# Post-2022: collapsed to 1 person
EVIDENCE = [
    {"date": "1948-12-01",
     "event": "Body found — Somerton Beach. Male, ~40-45, athletic build, no ID",
     "breadth": 1.000,
     "note": "All adult men viable"},

    {"date": "1948-12-10",
     "event": "Fingerprints not matched in Australian/UK/US databases; "
              "no missing person report matches",
     "breadth": 0.400,
     "note": "Probably foreign or living off-grid; major reduction"},

    {"date": "1949-01-14",
     "event": "Tamam Shud scrap found in secret pocket; linked to Fitzgerald translation "
              "of Rubaiyat of Omar Khayyam (very rare edition)",
     "breadth": 0.200,
     "note": "Educated, literate, possibly military intelligence interest in Khayyam"},

    {"date": "1949-07-22",
     "event": "Phone number inside Rubaiyat leads to 'Jestyn' (Jo Thomson) — "
              "she denies knowing him but is visibly distressed",
     "breadth": 0.100,
     "note": "Likely connected to Adelaide area; some personal connection"},

    {"date": "1949-09-01",
     "event": "Coded message in Rubaiyat (MRGOABABD...) — cryptanalysts at GCHQ, "
              "NSA, and academics unable to crack it",
     "breadth": 0.080,
     "note": "Code could be personal/improvised — not standard cipher; "
              "suggests non-standard intelligence training or personal code"},

    {"date": "1950-01-01",
     "event": "Inquest inconclusive: identity unknown, cause of death unknown "
              "(poison suspected but not confirmed); case administratively closed",
     "breadth": 0.080,
     "note": "No further official investigation — breadth stalls"},

    {"date": "1978-01-01",
     "event": "Stuart Littlemore investigation: 'Jestyn' believed to have been a nurse "
              "and possible Soviet contact during Cold War; Cold War spy theory emerges",
     "breadth": 0.070,
     "note": "Possible intelligence angle; marginally narrows to Cold War era operatives"},

    {"date": "2009-01-01",
     "event": "Derek Abbott (Adelaide Univ.) begins systematic investigation; "
              "discovers Jestyn's real identity — Jo Thomson née McGuire",
     "breadth": 0.060,
     "note": "Jestyn identified; case now has a named connection but man still unknown"},

    {"date": "2011-01-01",
     "event": "Abbott team: facial reconstruction suggests possible Eastern European ancestry; "
              "Abbott proposes link to Jo Thomson's son Robin (unusual ears, possible paternity link)",
     "breadth": 0.050,
     "note": "Genetic hypothesis forming; not yet testable without exhumation"},

    {"date": "2019-05-01",
     "event": "South Australian government approves exhumation of Somerton Man's remains",
     "breadth": 0.040,
     "note": "DNA extraction now possible; major procedural step"},

    {"date": "2021-01-01",
     "event": "DNA extracted from hair roots preserved on plaster cast; "
              "Y-chromosome and mitochondrial profiles obtained",
     "breadth": 0.020,
     "note": "DNA in hand; investigative genetic genealogy now possible"},

    {"date": "2022-07-26",
     "event": "Abbott et al. (PLOS One): IGG identifies man as Carl/Charles Webb, "
              "43, electrical engineer from Fitzroy, Victoria. Wife: Gwenneth Dorothy Thomson "
              "= 'Jestyn'. Webb was a known person, not a spy.",
     "breadth": 0.001,
     "note": "SOLVED — 74 years after discovery. Breadth collapses to near zero."},

    {"date": "2022-08-01",
     "event": "SA Police confirm identification is 'viable'; inquest to be re-opened. "
              "Cause of death still formally unknown (digitalis poisoning suspected).",
     "breadth": 0.001,
     "note": "Identity resolved; cause of death remains open but is secondary mystery"},
]


def _fit_logistic(series):
    n = len(series)
    if n < 4: return 0.0, 0.5, 0.0
    ts = [i/(n-1) for i in range(n)]
    mn, mx = min(series), max(series)
    if mx - mn < 0.05: return 0.0, 0.5, 0.0
    norm = [(v-mn)/(mx-mn) for v in series]
    best_k, best_t0, best_ss = 1.0, 0.5, float("inf")
    for k in [0.5,1,2,3,5,7,10,15,20,30,50,75,100,150,200]:
        for t0 in [i/20 for i in range(21)]:
            ss = sum((y-1/(1+math.exp(k*(t-t0))))**2 for t,y in zip(ts,norm))
            if ss < best_ss: best_ss, best_k, best_t0 = ss, k, t0
    mean_y = sum(norm)/n
    ss_tot = sum((y-mean_y)**2 for y in norm)
    r2 = max(0.0, 1.0 - best_ss/ss_tot) if ss_tot > 1e-9 else 0.0
    return best_k, best_t0, r2


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("=== Tamam Shud / Somerton Man — Cold Case Solved Arc ===\n")

    breadths = [e["breadth"] for e in EVIDENCE]
    dates    = [e["date"]    for e in EVIDENCE]

    k, t0, r2 = _fit_logistic(breadths)

    # Find the plateau (years of stasis) and the collapse point
    plateau_start_idx = None
    plateau_end_idx   = None
    for i in range(len(breadths)-1):
        if abs(breadths[i+1] - breadths[i]) < 0.01 and plateau_start_idx is None:
            plateau_start_idx = i
        if abs(breadths[i+1] - breadths[i]) > 0.01 and plateau_start_idx is not None:
            if plateau_end_idx is None:
                plateau_end_idx = i

    # The final collapse: last major drop
    drops = [(i, breadths[i] - breadths[i+1]) for i in range(len(breadths)-1)]
    max_drop_idx, max_drop = max(drops, key=lambda x: x[1])
    collapse_date = dates[max_drop_idx+1]

    final_breadth = breadths[-1]
    total_elimination = 1.0 - final_breadth

    print(f"  Evidence events: {len(EVIDENCE)}")
    print(f"  Breadth trajectory: {[round(b,3) for b in breadths]}")
    print(f"  Total elimination: {total_elimination:.1%}")
    print(f"  Logistic fit: k={k}  t0={t0}  R²={r2:.3f}")
    print(f"  Largest single drop: -{max_drop:.3f} at {collapse_date}")

    # Structural analysis: plateau length
    plateau_count = sum(1 for i in range(len(breadths)-1)
                        if abs(breadths[i+1]-breadths[i]) < 0.015)
    print(f"  Stasis events (change <0.015): {plateau_count}/{len(breadths)-1}")
    print()

    # Verdict
    if final_breadth < 0.005:
        verdict = (f"SOLVED — 74-year cold case resolved by investigative genetic genealogy. "
                   f"Identity: Carl Webb, electrical engineer. 'Jestyn' = his wife. "
                   f"The solution required technology (IGG) that did not exist for 70 years. "
                   f"k={k} — collapse was rapid once DNA was extracted.")
    else:
        verdict = f"unresolved — breadth={final_breadth:.3f}"

    print(f"  Verdict: {verdict}")
    print(f"\n  Key structural finding:")
    print(f"    74-year plateau followed by rapid collapse. The case was not")
    print(f"    unsolvable — it was technology-gated. IGG (investigative genetic genealogy)")
    print(f"    was the key. Once exhumation was approved (2019) and DNA extracted (2021),")
    print(f"    identification followed within 12 months.")
    print(f"    This is the 'latent collapse' pattern: possibility space frozen at a non-zero")
    print(f"    floor by tool unavailability, not evidence exhaustion.")

    result = {
        "mystery": "Tamam Shud / Somerton Man",
        "status": "SOLVED 2022",
        "solution": "Carl Webb, electrical engineer, Fitzroy Victoria; "
                    "wife Gwenneth Dorothy Thomson = Jestyn",
        "evidence": EVIDENCE,
        "k": k, "t0": t0, "r2": r2,
        "final_breadth": final_breadth,
        "total_elimination_pct": round(total_elimination * 100, 1),
        "largest_drop_date": collapse_date,
        "verdict": verdict,
    }
    dest = ARTIFACTS / "mystery_tamam_shud.json"
    with open(dest, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {dest}")


if __name__ == "__main__":
    main()
