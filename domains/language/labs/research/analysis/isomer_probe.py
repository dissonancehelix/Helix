"""
Isomer Probe — DCP structural isomers in language.

The isomer concept
------------------
An isomer has the same atomic composition but different structural arrangement.
Two isomers are the same "substance" read from a different orientation.

DCP components: [possibility_space, constraint, tension, collapse, post_narrowing]

These five components can be arranged in different orderings depending on:
  - WHERE the observer stands (inside the system vs outside)
  - WHICH direction time flows (encoding vs decoding)
  - WHAT is treated as primary (the collapse event vs what surrounds it)

This produces structurally distinct but chemically equivalent formulations:

  DCP-L  (Listener / decoder isomer):
    constraint → possibility_space narrows → tension → collapse → post_narrowing
    "As I receive tokens, my uncertainty decreases."
    Observable: k_eff drops as morphological constraints fire.
    Already tested: sentence_trajectory.py

  DCP-S  (Speaker / encoder isomer):
    post_narrowing → constraint → tension → collapse → possibility_space
    "I have a compressed intention. I must expand it into surface structure."
    The speaker's k_eff is already 1 (fully determined). The grammatical
    constraint EXPANDS intent into a surface form with deliberate redundancy.
    Observable: agreement re-encodes information already present (subject number
    marked on both noun AND verb). This redundancy is NOT waste — it's the
    surface signature of the encoding isomer. High agreement = high expansion.

  DCP-R  (Retrospective / analyst isomer):
    post_narrowing → collapse → tension → constraint → possibility_space
    "I see the stable output and reconstruct what constraints produced it."
    Observable: given a morphological paradigm, infer the grammatical rules.
    This is what a linguist does. Also what a learner does.
    The "difficulty" of language acquisition maps to this isomer's complexity.

  DCP-C  (Concurrent / resonance isomer):
    All five components fire simultaneously at every level of the grammar.
    Phonological DCP + morphological DCP + syntactic DCP run in parallel.
    They can interfere constructively (agreement + case = over-determined)
    or destructively (word order ambiguity + no morphology = under-determined).
    Observable: the COHERENCE between levels — do case and agreement point to
    the same parse, or do they conflict?

The key test
------------
DCP-S (expansion isomer) predicts:
  Agreement density = surface redundancy.
  Agreement re-encodes role information that word order or case already encode.
  High agreement → high surface expansion → same information encoded ≥2 times.

  But: agreement compresses LATER than case (fires at verb, not per noun token).
  So agreement-dominant isomers have higher k_eff at the sentence midpoint —
  they achieve the same endpoint but via a less efficient trajectory.

  This predicts: for the same morphological_richness,
    case-dominant languages → lower k_eff  (efficient isomer)
    agreement-dominant languages → higher k_eff  (redundant isomer)
    order-dominant languages → highest k_eff  (deferred isomer)

  The "isomeric strain energy" = k_eff excess above the case-dominant baseline
  at the same compression level. Agreement isomers carry isomeric strain.

DCP-C (coherence isomer) predicts:
  Languages where case and agreement are BOTH high are "over-determined" —
  the same information is encoded twice with different timing. This is the
  language equivalent of resonance stabilization: mutual reinforcement.
  These languages should have the LOWEST k_eff for their compression density.

Run
---
    python domains/language/model/probes/isomer_probe.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_DIR = REPO_ROOT / "domains" / "language" / "artifacts"


def load_ud_features() -> dict[str, dict]:
    path = ARTIFACT_DIR / "ud_typology_results.json"
    if not path.exists():
        raise FileNotFoundError("Run ud_typology_probe.py first.")
    return json.loads(path.read_text(encoding="utf-8"))["features"]


# ── Isomer classification ─────────────────────────────────────────────────────

def classify_isomer(features: dict) -> dict:
    """
    Assign each language to a DCP isomeric form based on which compression
    mechanism dominates and how the mechanisms relate to each other.
    """
    case = float(features["case_density"])
    agree = float(features["agreement_density"])
    order = float(features["order_rigidity"])
    order_signal = float(features.get("order_signal", max((order - 0.5) / 0.45, 0)))
    morph = float(features["morph_richness"])
    k_eff = float(features["ud_k_eff"])
    comp = float(features["compression_density"])

    # --- Isomeric form ---
    # Which mechanism is primary determines the structural arrangement of DCP
    dominant = features.get("dominant_signal", "unknown")
    if dominant == "case":
        isomer = "DCP-L"      # listener/case isomer — early compression
        isomer_label = "case-dominant  (DCP-L)"
    elif dominant == "agreement":
        isomer = "DCP-S"      # speaker/expansion isomer — verb-position compression
        isomer_label = "agreement-dom  (DCP-S)"
    else:
        isomer = "DCP-C"      # deferred/order isomer — clause-boundary compression
        isomer_label = "order-dominant (DCP-C)"

    # --- Coherence: case + agreement overlap (resonance stabilization) ---
    # If both case and agreement are high, the same role information is encoded
    # twice with different timing. This is constructive interference.
    coherence = round(case * agree, 4)   # 0 = no overlap, 1 = perfect double-encoding

    # --- Expansion redundancy (DCP-S signal) ---
    # Agreement density as surface expansion metric:
    # How much of the surface form re-encodes already-determined information?
    # Case encodes role once (per noun). Agreement re-encodes it at the verb.
    # expansion_redundancy > 0 means the system is "over-encoding" — a speaker's
    # signature, not a listener's optimization.
    expansion_redundancy = round(agree * (1.0 - case * 0.5), 4)  # agree adjusted for case presence

    # --- Isomeric strain: k_eff excess above case-baseline ---
    # Case-dominant languages at comp ~ 2.0 achieve k_eff ≈ 1.5.
    # The linear fit from SCE-1: k_eff = -0.6416 * comp + 2.9420
    # Strain = observed k_eff - expected k_eff from compression density alone.
    expected_k_eff = round(-0.6416 * comp + 2.9420, 4)
    isomeric_strain = round(k_eff - expected_k_eff, 4)

    # --- Timing profile ---
    # When does compression fire relative to sentence length?
    # Case: early (per noun token) → low timing_index
    # Agreement: mid (at verb) → medium timing_index
    # Order: late (at clause boundary) → high timing_index
    timing_index = {
        "case": 0.15,       # fires early — case marker arrives with each noun
        "agreement": 0.55,  # fires mid — verb is typically sentence midpoint
        "word_order": 0.85, # fires late — clause boundary resolves structure
    }.get(dominant, 0.5)

    return {
        "language": features["language"],
        "morphological_class": features["morphological_class"],
        "isomer": isomer,
        "isomer_label": isomer_label,
        "dominant_mechanism": dominant,
        "case_density": case,
        "agreement_density": agree,
        "order_rigidity": order,
        "morph_richness": morph,
        "compression_density": comp,
        "ud_k_eff": k_eff,
        "coherence": coherence,
        "expansion_redundancy": expansion_redundancy,
        "expected_k_eff": expected_k_eff,
        "isomeric_strain": isomeric_strain,
        "timing_index": timing_index,
    }


# ── Statistics ────────────────────────────────────────────────────────────────

def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return round(num / den, 4) if den else 0.0


def group_mean(items: list[dict], key: str, group_key: str) -> dict[str, float]:
    groups: dict[str, list[float]] = {}
    for item in items:
        groups.setdefault(item[group_key], []).append(float(item[key]))
    return {g: round(sum(v) / len(v), 4) for g, v in groups.items()}


# ── Timing profile visualization ──────────────────────────────────────────────

def render_timing_diagram(isomers: list[dict], width: int = 50) -> None:
    """
    Show where in the sentence each language's compression fires.
    The horizontal axis is sentence position (0=start, 1=end).
    The marker shows the timing_index — when the dominant mechanism engages.
    """
    print("\n── Compression Timing (DCP isomer position in sentence) ────────────────")
    print(f"  {'start':<6}{'':>{width//2-3}}{'mid'}{'':>{width//2-4}}{'end'}")
    print(f"  |{'-'*width}|")

    for iso in sorted(isomers, key=lambda x: x["timing_index"]):
        pos = int(iso["timing_index"] * width)
        pos = max(0, min(pos, width - 1))
        line = " " * pos + "●" + " " * (width - pos - 1)
        marker = iso["language"][:8]
        print(f"  |{line}|  {marker:<10} {iso['isomer']}  k={iso['ud_k_eff']:.3f}")

    print(f"  |{'-'*width}|")
    print(f"  case fires early → agreement fires mid → order fires late")


# ── Isomeric strain visualization ────────────────────────────────────────────

def render_strain_chart(isomers: list[dict]) -> None:
    print("\n── Isomeric Strain (k_eff excess above SCE-predicted baseline) ─────────")
    print("  Positive strain = language is 'higher energy' than its compression level")
    print("  predicts. Agreement isomers carry more strain than case isomers.\n")

    max_abs = max(abs(iso["isomeric_strain"]) for iso in isomers) or 0.01
    center = 20

    for iso in sorted(isomers, key=lambda x: x["isomeric_strain"]):
        strain = iso["isomeric_strain"]
        bar_len = int(abs(strain) / max_abs * center)
        if strain >= 0:
            bar = " " * center + "│" + "▶" * bar_len
        else:
            bar = " " * (center - bar_len) + "◀" * bar_len + "│"
        print(
            f"  {iso['language']:<14} {bar}  "
            f"{strain:+.4f}  [{iso['isomer']}]"
        )

    print(f"\n  {'─'*center}┤ baseline (0 strain) = SCE prediction")


# ── Hypothesis tests ──────────────────────────────────────────────────────────

def run_isomer_tests(isomers: list[dict]) -> list[dict]:
    results = []

    # Group by isomeric form
    by_isomer: dict[str, list[dict]] = {}
    for iso in isomers:
        by_isomer.setdefault(iso["isomer"], []).append(iso)

    # Test 1: Case isomers (DCP-L) have lower k_eff than agreement isomers (DCP-S)
    # for comparable compression levels
    dcp_l = [iso for iso in isomers if iso["isomer"] == "DCP-L"]
    dcp_s = [iso for iso in isomers if iso["isomer"] == "DCP-S"]
    dcp_c = [iso for iso in isomers if iso["isomer"] == "DCP-C"]

    mean_k_l = sum(iso["ud_k_eff"] for iso in dcp_l) / len(dcp_l) if dcp_l else 0
    mean_k_s = sum(iso["ud_k_eff"] for iso in dcp_s) / len(dcp_s) if dcp_s else 0
    mean_k_c = sum(iso["ud_k_eff"] for iso in dcp_c) / len(dcp_c) if dcp_c else 0

    test1_holds = mean_k_l < mean_k_s < mean_k_c
    results.append({
        "id": "ISO-1",
        "label": "DCP-L (case) < DCP-S (agreement) < DCP-C (order) for mean k_eff",
        "holds": test1_holds,
        "detail": [
            f"DCP-L mean k_eff = {mean_k_l:.4f}  ({', '.join(i['language'] for i in dcp_l)})",
            f"DCP-S mean k_eff = {mean_k_s:.4f}  ({', '.join(i['language'] for i in dcp_s)})",
            f"DCP-C mean k_eff = {mean_k_c:.4f}  ({', '.join(i['language'] for i in dcp_c)})",
            "Prediction: each isomeric form is less efficient at parse compression",
            "than the one that fires earlier in the sentence.",
        ],
    })

    # Test 2: Isomeric strain correlates with timing_index
    # Later-firing mechanisms carry more strain at the same compression density
    strains = [iso["isomeric_strain"] for iso in isomers]
    timings = [iso["timing_index"] for iso in isomers]
    r_strain_timing = pearson_r(timings, strains)
    test2_holds = r_strain_timing > 0.3
    results.append({
        "id": "ISO-2",
        "label": "r(timing_index, isomeric_strain) > 0  (later firing → more strain)",
        "holds": test2_holds,
        "detail": [
            f"Pearson r(timing, strain) = {r_strain_timing:.4f}",
            "Prediction: agreement (fires mid-sentence) carries more isomeric strain",
            "than case (fires per-token). Order (fires at clause boundary) carries most.",
            "Strain = observed k_eff − SCE-predicted k_eff from compression density.",
        ],
    })

    # Test 3: Coherence (case × agreement overlap) predicts lower strain
    # "Resonance stabilization": double-encoding reduces k_eff below expectation
    coherences = [iso["coherence"] for iso in isomers]
    r_coh_strain = pearson_r(coherences, strains)
    test3_holds = r_coh_strain < -0.2
    results.append({
        "id": "ISO-3",
        "label": "r(coherence, strain) < 0  (double-encoding stabilizes — resonance isomers)",
        "holds": test3_holds,
        "detail": [
            f"Pearson r(case×agree coherence, strain) = {r_coh_strain:.4f}",
            "Coherence = case_density × agreement_density",
            "High coherence = both mechanisms fire, encoding role information twice.",
            "Prediction: double-encoded languages are 'resonance-stabilized' —",
            "lower k_eff than either mechanism alone would predict.",
            f"Highest coherence: {max(isomers, key=lambda x: x['coherence'])['language']} "
            f"({max(isomers, key=lambda x: x['coherence'])['coherence']:.4f})",
            f"Lowest coherence: {min(isomers, key=lambda x: x['coherence'])['language']} "
            f"({min(isomers, key=lambda x: x['coherence'])['coherence']:.4f})",
        ],
    })

    # Test 4: DCP-L and DCP-C are structural isomers of each other
    # They achieve the same function via opposite strategies:
    #   DCP-L: high surface morphology, low positional constraint → low k_eff
    #   DCP-C: zero surface morphology, high positional constraint → high k_eff
    # The "structural distance" between them should be maximal (they are
    # the most different arrangement of the same components).
    if dcp_l and dcp_c:
        l_case = sum(i["case_density"] for i in dcp_l) / len(dcp_l)
        l_order = sum(i["order_rigidity"] for i in dcp_l) / len(dcp_l)
        c_case = sum(i["case_density"] for i in dcp_c) / len(dcp_c)
        c_order = sum(i["order_rigidity"] for i in dcp_c) / len(dcp_c)
        case_contrast = round(abs(l_case - c_case), 4)
        order_contrast = round(abs(l_order - c_order), 4)
        test4_holds = case_contrast > 0.3 and order_contrast > 0.1
        results.append({
            "id": "ISO-4",
            "label": "DCP-L ↔ DCP-C are structural opposites (maximum isomeric distance)",
            "holds": test4_holds,
            "detail": [
                f"DCP-L mean case_density  = {l_case:.4f}  DCP-C mean = {c_case:.4f}  Δ={case_contrast:.4f}",
                f"DCP-L mean order_rigidity = {l_order:.4f}  DCP-C mean = {c_order:.4f}  Δ={order_contrast:.4f}",
                "DCP-L: maximum case, minimum order rigidity (case does all the work)",
                "DCP-C: minimum case, maximum order rigidity (position does all the work)",
                "These are structural isomers in the most literal sense: same result",
                "(parse disambiguation), opposite mechanism arrangement.",
            ],
        })
    else:
        results.append({"id": "ISO-4", "label": "DCP-L ↔ DCP-C structural distance", "holds": False, "detail": ["Insufficient data"]})

    return results


# ── Print full results ────────────────────────────────────────────────────────

def print_results(isomers: list[dict], test_results: list[dict]) -> None:
    print("\n" + "═" * 76)
    print("  ISOMER PROBE — DCP STRUCTURAL ISOMERS")
    print("═" * 76)

    print("""
  Four structural isomers of DCP — same components, different arrangement:

  DCP-L  Listener/decoder:  constraint → space narrows → collapse
         Early-firing. Each token reduces parse ambiguity. (case morphology)

  DCP-S  Speaker/encoder:   intention → constraint → surface expansion
         Mid-firing. Verb agreement re-encodes already-determined information.
         The redundancy is the encoding signature.

  DCP-R  Retrospective:     stable output → infer constraints → reconstruct space
         (Not directly tested — this is linguistic analysis and L2 acquisition)

  DCP-C  Concurrent/deferred: full sentence available → position resolves role
         Late-firing. Word order is the only cue; fires at clause boundary.
""")

    print("── Language Isomer Assignments ──────────────────────────────────────────")
    print(
        f"  {'Language':<14} {'Isomer':<10} {'case':>6} {'agree':>6} "
        f"{'order':>6} {'coh':>6} {'strain':>7} {'k_eff':>6}"
    )
    print("  " + "─" * 70)
    for iso in sorted(isomers, key=lambda x: x["ud_k_eff"]):
        print(
            f"  {iso['language']:<14} {iso['isomer']:<10} "
            f"{iso['case_density']:>6.3f} {iso['agreement_density']:>6.3f} "
            f"{iso['order_rigidity']:>6.3f} {iso['coherence']:>6.4f} "
            f"{iso['isomeric_strain']:>+7.4f} {iso['ud_k_eff']:>6.3f}"
        )

    render_timing_diagram(isomers)
    render_strain_chart(isomers)

    print("\n── Isomer Test Results ───────────────────────────────────────────────────")
    for test in test_results:
        mark = "✓" if test["holds"] else "✗"
        print(f"\n  {mark}  [{test['id']}] {test['label']}")
        for line in test["detail"]:
            print(f"       {line}")

    # Summary of what the isomers mean
    n_pass = sum(1 for t in test_results if t["holds"])
    print(f"\n  {n_pass}/{len(test_results)} isomer tests pass.")
    print()
    print("  Structural interpretation:")
    print("  ─────────────────────────────────────────────────────────────────")
    print("  DCP-L and DCP-C are the 'extreme isomers' — maximum structural")
    print("  contrast, same function (parse disambiguation), opposite mechanism.")
    print("  DCP-S (agreement) is the intermediate isomer — partially redundant,")
    print("  carrying isomeric strain relative to the compression-efficient DCP-L.")
    print()
    print("  The isomeric strain is NOT a defect. Agreement's redundancy provides")
    print("  fault tolerance — if one signal is missing (noisy channel, fast speech),")
    print("  the other survives. DCP-L (case only) is more efficient but fragile.")
    print("  DCP-S (agreement) is less efficient but robust under noise.")
    print()
    print("  This reframes DCP: the 'collapse' is not a single event but a")
    print("  trajectory whose shape (timing, redundancy, fault tolerance) varies")
    print("  by isomeric form. The invariant is the DESTINATION (k_eff band),")
    print("  not the path.")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Isomer Probe — DCP structural isomers")
    print("━" * 76)
    print("\nSame DCP components, different structural arrangement.")
    print("Isomers: DCP-L (case/early), DCP-S (agreement/mid), DCP-C (order/late)\n")

    print("[1] Loading UD features...")
    features_by_lang = load_ud_features()

    print("[2] Classifying DCP isomers...")
    isomers = [classify_isomer(feat) for feat in features_by_lang.values()]
    for iso in sorted(isomers, key=lambda x: x["ud_k_eff"]):
        print(
            f"  {iso['language']:<14} → {iso['isomer']}  "
            f"strain={iso['isomeric_strain']:+.4f}  coherence={iso['coherence']:.4f}"
        )

    print("\n[3] Running isomer hypothesis tests...")
    test_results = run_isomer_tests(isomers)

    print_results(isomers, test_results)

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "probe": "isomer",
        "framework": "DCP structural isomers",
        "isomers": {iso["language"]: iso for iso in isomers},
        "test_results": test_results,
        "summary": {
            "tests_passed": sum(1 for t in test_results if t["holds"]),
            "tests_run": len(test_results),
            "dcp_l_languages": [i["language"] for i in isomers if i["isomer"] == "DCP-L"],
            "dcp_s_languages": [i["language"] for i in isomers if i["isomer"] == "DCP-S"],
            "dcp_c_languages": [i["language"] for i in isomers if i["isomer"] == "DCP-C"],
        },
    }
    out_path = ARTIFACT_DIR / "isomer_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()

