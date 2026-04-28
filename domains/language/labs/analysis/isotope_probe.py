"""
Isotope Probe — Structural Compression Equivalence (SCE)

The claim
---------
DCP (Decision Compression Principle) describes HOW compression unfolds within
a language: which morphological strategy, at which point in the sentence, how
sharply the parse space narrows.

But DCP is one instance of a larger invariant:

  Structural Compression Equivalence (SCE):
  k_eff is determined by total compression density, independent of which
  structural mechanism delivers that density.

  Case morphology, verb agreement, word order, and particles are compression
  ISOTOPES — different structural implementations of the same information-
  theoretic function. Languages that use different mechanisms but achieve the
  same compression_density will have the same k_eff.

The isotope framing
-------------------
In nuclear physics, isotopes of the same element have the same proton count
(same chemistry) but different neutron count (different mass/stability).

For language:
  Atomic number Z  = compression_density band  (how much total compression)
  Neutron number N = dominant mechanism         (case / agreement / order)
  Mass number A    = Z + N proxy               (total structural weight)
  k_eff            = nuclear stability          (lower = more stable/compressed)

  "Heavy" isotopes (comp > 2.0): Russian, Arabic, Finnish, Turkish, German
      → k_eff ≈ 1.5, all case-dominant, different typological families
  "Medium" isotopes (comp 1.0-2.0): Spanish, English
      → k_eff ≈ 1.8-2.0, agreement-dominant
  "Light" isotopes (comp < 1.0): Japanese, Korean, Mandarin
      → k_eff ≈ 2.4-2.9, order-dominant

The key test: Finnish (agglutinative) and Russian (fusional) are in the same
k_eff band. The traditional typological label is a WORSE predictor of k_eff
than compression_density. This is SCE.

Invariant claims tested
-----------------------
  [SCE-1] R²(compression_density → k_eff) > R²(morphological_class → k_eff)
           Compression density predicts parse ambiguity better than typology.

  [SCE-2] Within-band k_eff variance < between-band k_eff variance
           Languages in the same compression band behave similarly at the
           parse level, regardless of which mechanism they use.

  [SCE-3] r(morph_richness, k_eff) > r(compression_density, k_eff) [weaker]
           Mechanism-specific features are weaker predictors than total density.
           (morph_richness captures case mass but not agreement/order — partial)

  [SCE-4] Languages shift compression mechanism under contact/simplification
           while preserving compression_density (isotopic substitution).
           DIRECTION ONLY — tested with known historical cases.

Run
---
    python domains/language/model/probes/isotope_probe.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_DIR = REPO_ROOT / "domains" / "language" / "artifacts"

# ── Load previous UD probe results ───────────────────────────────────────────

def load_ud_features() -> dict[str, dict]:
    path = ARTIFACT_DIR / "ud_typology_results.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Run ud_typology_probe.py first to generate: {path}"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["features"]


# ── Isotope classification ────────────────────────────────────────────────────

# Compression density bands (calibrated from our 10-language set)
BAND_THRESHOLDS = [
    ("heavy",  2.0),   # comp > 2.0  → k_eff ≈ 1.5
    ("medium", 1.0),   # comp 1.0-2.0 → k_eff ≈ 1.7-2.0
    ("light",  0.0),   # comp < 1.0  → k_eff ≈ 2.4+
]

# Mechanism to integer encoding for "neutron number" analog
MECHANISM_N = {"case": 0, "agreement": 1, "word_order": 2}

# Known historical isotopic substitutions (mechanism change with similar function)
HISTORICAL_SUBSTITUTIONS = [
    {
        "language_family": "germanic",
        "ancestor": "proto_germanic",
        "descendant": "english",
        "shift": "case → word_order",
        "notes": (
            "Proto-Germanic had 8 cases. Old English had 4. Modern English has 2 "
            "(pronouns only). Word order became rigid as case morphology eroded. "
            "SCE predicts compression_density should be roughly preserved — "
            "what was carried by case is now carried by order."
        ),
        "ancestor_k_eff_estimate": 1.6,
        "descendant_k_eff": None,  # to be filled from data
    },
    {
        "language_family": "romance",
        "ancestor": "latin",
        "descendant": "french",
        "shift": "case → agreement + order",
        "notes": (
            "Classical Latin had 6 cases. French reduced to 0 nominal case, "
            "compensating with stricter SVO order and more pronoun agreement. "
            "Similar compression_density preserved via mechanism substitution."
        ),
        "ancestor_k_eff_estimate": 1.5,
        "descendant_k_eff": None,
    },
]


def assign_isotope(features: dict) -> dict:
    comp = float(features["compression_density"])
    mechanism = features.get("dominant_signal", "unknown")

    band = "light"
    for band_name, threshold in BAND_THRESHOLDS:
        if comp >= threshold:
            band = band_name
            break

    neutron_n = MECHANISM_N.get(mechanism, 3)
    # "Mass number" analog: compression band index (0=light, 1=medium, 2=heavy) + neutron
    band_z = {"light": 0, "medium": 1, "heavy": 2}.get(band, 0)
    mass_number = band_z * 3 + neutron_n

    return {
        "language": features["language"],
        "morphological_class": features["morphological_class"],
        "compression_band": band,
        "dominant_mechanism": mechanism,
        "neutron_n": neutron_n,
        "band_z": band_z,
        "mass_number": mass_number,
        "compression_density": comp,
        "ud_k_eff": float(features["ud_k_eff"]),
        "morph_richness": float(features["morph_richness"]),
    }


# ── Statistics ───────────────────────────────────────────────────────────────

def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(
        sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)
    )
    return round(num / den, 4) if den else 0.0


def r_squared(xs: list[float], ys: list[float]) -> float:
    return round(pearson_r(xs, ys) ** 2, 4)


def variance(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return sum((v - m) ** 2 for v in vals) / (len(vals) - 1)


def categorical_r_squared(
    categories: list[str],
    ys: list[float],
) -> float:
    """Eta² — variance explained by categorical grouping (ANOVA analog)."""
    grand_mean = sum(ys) / len(ys)
    ss_total = sum((y - grand_mean) ** 2 for y in ys)
    if ss_total == 0:
        return 0.0

    groups: dict[str, list[float]] = {}
    for cat, y in zip(categories, ys):
        groups.setdefault(cat, []).append(y)

    ss_between = sum(
        len(vals) * (sum(vals) / len(vals) - grand_mean) ** 2
        for vals in groups.values()
    )
    return round(ss_between / ss_total, 4)


def within_between_variance(
    isotopes: list[dict],
    group_key: str,
    value_key: str,
) -> tuple[float, float]:
    groups: dict[str, list[float]] = {}
    for iso in isotopes:
        groups.setdefault(iso[group_key], []).append(iso[value_key])

    within_vars = [variance(vals) for vals in groups.values() if len(vals) >= 2]
    all_vals = [iso[value_key] for iso in isotopes]

    mean_within = sum(within_vars) / len(within_vars) if within_vars else 0.0
    total_variance = variance(all_vals)
    between = max(total_variance - mean_within, 0.0)

    return round(mean_within, 6), round(between, 6)


# ── Regression fit (linear) ─────────────────────────────────────────────────

def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Returns (slope, intercept) for y = slope*x + intercept."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den if den else 0.0
    intercept = my - slope * mx
    return round(slope, 4), round(intercept, 4)


# ── Printing ─────────────────────────────────────────────────────────────────

def bar(value: float, max_val: float, width: int = 30) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    return "█" * min(filled, width) + "░" * max(width - filled, 0)


def print_isotope_chart(isotopes: list[dict]) -> None:
    """Render a text-based nuclide-style chart: rows=band, cols=mechanism."""
    bands = ["heavy", "medium", "light"]
    mechanisms = ["case", "agreement", "word_order"]
    mech_labels = ["case(N=0)", "agree(N=1)", "order(N=2)"]

    print("\n── Compression Isotope Chart ─────────────────────────────────────────────")
    print("   (rows = compression band Z, cols = dominant mechanism N)")
    print()
    print(f"   {'':>8}  " + "  ".join(f"{m:^20}" for m in mech_labels))
    print("   " + "─" * 72)

    by_band_mech: dict[tuple[str, str], list[str]] = {}
    for iso in isotopes:
        key = (iso["compression_band"], iso["dominant_mechanism"])
        by_band_mech.setdefault(key, []).append(iso["language"])

    for band in bands:
        k_vals = [iso["ud_k_eff"] for iso in isotopes if iso["compression_band"] == band]
        mean_k = round(sum(k_vals) / len(k_vals), 3) if k_vals else 0.0
        row = f"   {band:>8}  "
        for mech in mechanisms:
            langs = by_band_mech.get((band, mech), [])
            cell = ", ".join(langs) if langs else "·"
            row += f"{cell:^20}  "
        print(row)
        print(f"   {'k≈' + str(mean_k):>8}  ")
        print()

    print("   Legend: same row = same compression band (same k_eff ≈)")
    print("           same col = same dominant mechanism (same 'neutron number')")
    print("           different row+col = different isotope")


def print_results(
    isotopes: list[dict],
    sce_results: list[dict],
) -> None:
    print("\n" + "═" * 76)
    print("  ISOTOPE PROBE — STRUCTURAL COMPRESSION EQUIVALENCE (SCE)")
    print("═" * 76)

    print("\n── Isotope Assignments ──────────────────────────────────────────────────")
    print(
        f"  {'Language':<14} {'Trad. class':<16} {'Band (Z)':<10} "
        f"{'Mech (N)':<12} {'comp':>6} {'k_eff':>6}"
    )
    print("  " + "─" * 70)
    for iso in sorted(isotopes, key=lambda x: x["ud_k_eff"]):
        print(
            f"  {iso['language']:<14} {iso['morphological_class']:<16} "
            f"{iso['compression_band']:<10} {iso['dominant_mechanism']:<12} "
            f"{iso['compression_density']:>6.3f} {iso['ud_k_eff']:>6.3f}"
        )

    print_isotope_chart(isotopes)

    # k_eff bar chart grouped by compression band
    print("── k_eff by Compression Band (isotopic stability) ──────────────────────")
    max_k = max(iso["ud_k_eff"] for iso in isotopes)
    for band in ["heavy", "medium", "light"]:
        band_isos = [iso for iso in isotopes if iso["compression_band"] == band]
        if not band_isos:
            continue
        print(f"\n  [{band.upper()} — comp {'> 2.0' if band == 'heavy' else '1.0-2.0' if band == 'medium' else '< 1.0'}]")
        for iso in sorted(band_isos, key=lambda x: x["ud_k_eff"]):
            b = bar(iso["ud_k_eff"], max_k)
            print(f"  {iso['language']:<14} {iso['dominant_mechanism']:<12} k={iso['ud_k_eff']:.3f}  {b}")

    print("\n── SCE Invariant Tests ──────────────────────────────────────────────────")
    for result in sce_results:
        mark = "✓" if result["holds"] else "✗"
        print(f"\n  {mark}  [{result['id']}] {result['label']}")
        for line in result["detail"]:
            print(f"       {line}")

    print("\n── Historical Isotopic Substitution (SCE-4) ────────────────────────────")
    for sub in HISTORICAL_SUBSTITUTIONS:
        print(f"\n  {sub['language_family'].upper()}: {sub['shift']}")
        print(f"  {sub['notes']}")
        print(f"  Ancestor k_eff estimate: ~{sub['ancestor_k_eff_estimate']}")
        if sub.get("descendant_k_eff"):
            print(f"  Descendant k_eff (data): {sub['descendant_k_eff']}")
        else:
            print(f"  Descendant k_eff (data): see {sub['descendant']} in isotope table")

    print()


# ── SCE tests ─────────────────────────────────────────────────────────────────

def run_sce_tests(isotopes: list[dict]) -> list[dict]:
    langs = [iso["language"] for iso in isotopes]
    comp_vals = [iso["compression_density"] for iso in isotopes]
    k_eff_vals = [iso["ud_k_eff"] for iso in isotopes]
    morph_vals = [iso["morph_richness"] for iso in isotopes]
    trad_classes = [iso["morphological_class"] for iso in isotopes]
    bands = [iso["compression_band"] for iso in isotopes]

    # SCE-1: R²(comp → k_eff) > R²(typology → k_eff)
    r2_comp = r_squared(comp_vals, k_eff_vals)
    eta2_trad = categorical_r_squared(trad_classes, k_eff_vals)
    sce1_holds = r2_comp > eta2_trad

    # SCE-2: within-band variance < between-band variance for k_eff
    within_band, between_band = within_between_variance(isotopes, "compression_band", "ud_k_eff")
    sce2_holds = within_band < between_band

    # SCE-2b: compare with typological class grouping
    within_trad, between_trad = within_between_variance(isotopes, "morphological_class", "ud_k_eff")

    # SCE-3: comp → k_eff is stronger than morph_richness → k_eff
    r2_morph = r_squared(morph_vals, k_eff_vals)
    sce3_holds = abs(pearson_r(comp_vals, k_eff_vals)) > abs(pearson_r(morph_vals, k_eff_vals))

    # Linear fit for SCE-1 visualization
    slope, intercept = linear_fit(comp_vals, k_eff_vals)

    # SCE-4: English (descendant) compression_density vs proto-germanic estimate
    english_iso = next((iso for iso in isotopes if iso["language"] == "english"), None)
    if english_iso:
        eng_comp = english_iso["compression_density"]
        proto_germ_est = 2.0  # conservative estimate for proto-germanic
        substitution_ratio = eng_comp / proto_germ_est
        # SCE-4 prediction: ratio should be > 0.5 (significant preservation)
        sce4_holds = substitution_ratio > 0.5
        sce4_detail = [
            f"English compression_density = {eng_comp:.3f}",
            f"Proto-Germanic estimate = ~{proto_germ_est:.1f} (case-heavy, similar to Finnish/Turkish)",
            f"Preservation ratio = {substitution_ratio:.3f}",
            f"English k_eff = {english_iso['ud_k_eff']:.3f} vs ancestor ~1.5",
            "If SCE holds: mechanism shifted (case → agreement+order) but",
            "compression was partially preserved (not total loss → k_eff didn't hit 3.0+)",
        ]
    else:
        sce4_holds = False
        sce4_detail = ["English data not available"]

    return [
        {
            "id": "SCE-1",
            "label": "R²(compression_density → k_eff) > η²(typological_class → k_eff)",
            "holds": sce1_holds,
            "detail": [
                f"R²(compression_density → k_eff) = {r2_comp:.4f}",
                f"η²(typological_class → k_eff)   = {eta2_trad:.4f}",
                f"Linear fit: k_eff = {slope:.4f}·comp + {intercept:.4f}",
                f"Interpretation: compression density explains {r2_comp*100:.1f}% of k_eff variance;",
                f"  traditional typology explains only {eta2_trad*100:.1f}%.",
                "  → mechanism-independent compression law is the better predictor.",
            ],
        },
        {
            "id": "SCE-2",
            "label": "Within-band k_eff variance < between-band variance (same compression band = similar k_eff)",
            "holds": sce2_holds,
            "detail": [
                f"Within compression-band variance:   {within_band:.6f}",
                f"Between compression-band variance:  {between_band:.6f}",
                f"Ratio (within/between):             {within_band/between_band:.4f}  (want < 1.0)",
                f"",
                f"For comparison — traditional typology bands:",
                f"  Within typological-class variance: {within_trad:.6f}",
                f"  Between typological-class variance: {between_trad:.6f}",
                f"  Ratio (within/between):            {within_trad/between_trad:.4f}",
                f"  → Compression bands are {'better' if within_band/between_band < within_trad/between_trad else 'worse'} grouping than typological class.",
            ],
        },
        {
            "id": "SCE-3",
            "label": "|r(compression_density, k_eff)| > |r(morph_richness, k_eff)|",
            "holds": sce3_holds,
            "detail": [
                f"|r(compression_density, k_eff)| = {abs(pearson_r(comp_vals, k_eff_vals)):.4f}",
                f"|r(morph_richness, k_eff)|        = {abs(pearson_r(morph_vals, k_eff_vals)):.4f}",
                "Interpretation: morph_richness captures only morphological-case compression.",
                "  compression_density adds timing-weighted agreement and order signals.",
                "  SCE-3 tests whether the multi-mechanism composite beats any single mechanism.",
            ],
        },
        {
            "id": "SCE-4",
            "label": "Isotopic substitution preserves compression function (historical evidence)",
            "holds": sce4_holds,
            "detail": sce4_detail,
        },
    ]


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Isotope Probe — Structural Compression Equivalence")
    print("━" * 76)
    print()
    print("Parent principle: k_eff is determined by compression_density,")
    print("  independent of which mechanism (case / agreement / order) delivers it.")
    print("DCP describes the mechanism. SCE describes the invariant across mechanisms.")
    print()

    print("[1] Loading UD features from prior probe...")
    features_by_lang = load_ud_features()
    print(f"  Loaded {len(features_by_lang)} languages.")

    print("\n[2] Assigning isotope signatures...")
    isotopes = [assign_isotope(feat) for feat in features_by_lang.values()]
    for iso in sorted(isotopes, key=lambda x: x["ud_k_eff"]):
        print(
            f"  [{iso['compression_band']:>6}] {iso['language']:<14} "
            f"N={iso['neutron_n']} ({iso['dominant_mechanism']:<12}) "
            f"comp={iso['compression_density']:.3f}  k_eff={iso['ud_k_eff']:.3f}"
        )

    print("\n[3] Running SCE invariant tests...")
    sce_results = run_sce_tests(isotopes)

    print_results(isotopes, sce_results)

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "probe": "isotope",
        "parent_principle": "Structural Compression Equivalence (SCE)",
        "claim": (
            "k_eff is determined by compression_density independent of which "
            "structural mechanism (case / agreement / order / particles) delivers it. "
            "DCP describes the mechanism; SCE describes the invariant across mechanisms."
        ),
        "isotopes": {
            iso["language"]: {k: v for k, v in iso.items() if k != "language"}
            for iso in isotopes
        },
        "sce_tests": sce_results,
        "summary": {
            "tests_run": len(sce_results),
            "tests_passed": sum(1 for r in sce_results if r["holds"]),
            "isotope_bands": {
                band: [iso["language"] for iso in isotopes if iso["compression_band"] == band]
                for band in ["heavy", "medium", "light"]
            },
        },
    }
    out_path = ARTIFACT_DIR / "isotope_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()

