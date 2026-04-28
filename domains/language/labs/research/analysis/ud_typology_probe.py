"""
UD Typology Probe — language-agnostic structural invariant test.

This is the rigorous follow-up to typology_cluster_probe.py, which failed
because the heuristic structural vectorizer is Spanish-biased. This probe
uses Universal Dependencies morphological annotations directly (FEATS column +
dependency relations), which are language-neutral ground truth.

Features (all derived from UD CoNLL-U annotations, not surface text):
  case_density        — % tokens with Case= morphology OR case-particle deprel
                        Captures both fusional case (Finnish, Russian) and
                        particle-marked case (Japanese, Korean) in one metric.
  agreement_density   — % VERB/AUX tokens bearing Person= or Number= features
  order_rigidity      — consistency of nsubj position relative to verb head
                        (1.0=perfectly rigid like English; 0.5=free like Russian)
  morph_richness      — mean FEATS key-value count per token
  compression_density — timing-weighted sum of the three signals above

Hypotheses
----------
  [1] Cluster separation: mean intra-cluster UD distance < mean inter-cluster
      (same test as typology_cluster_probe, now with real features)

  [2] Feature ordering:
      morph_richness: agglutinative > fusional > analytic
      case_density:   agglutinative ≈ fusional > analytic
      agreement_density: fusional > agglutinative > analytic
      order_rigidity: analytic > agglutinative > fusional

  [3] k_eff ordering:
      analytic > agglutinative > fusional
      (more morphological compression → lower parse ambiguity → lower k_eff)

  [4] Morphosyntax tradeoff (using real UD features now):
      r(morph_richness, order_rigidity) < 0
      r(case_density, agreement_density) — distinguish fusional from agglutinative

Run
---
    python domains/language/model/probes/ud_typology_probe.py
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

CACHE_DIR = REPO_ROOT / "domains" / "language" / "data" / "ud_cache"
ARTIFACT_DIR = REPO_ROOT / "domains" / "language" / "artifacts"

from domains.language.research.ud_weight_extractor import extract_rule_weights

# ── UD registry ──────────────────────────────────────────────────────────────

_UD_REGISTRY: dict[str, tuple[str, str, str]] = {
    "finnish":    ("UD_Finnish-TDT",    "fi_tdt",   "dev"),
    "turkish":    ("UD_Turkish-BOUN",   "tr_boun",  "dev"),
    "korean":     ("UD_Korean-GSD",     "ko_gsd",   "dev"),
    "japanese":   ("UD_Japanese-GSD",   "ja_gsd",   "dev"),
    "spanish":    ("UD_Spanish-GSD",    "es_gsd",   "dev"),
    "russian":    ("UD_Russian-GSD",    "ru_gsd",   "dev"),
    "german":     ("UD_German-GSD",     "de_gsd",   "dev"),
    "arabic":     ("UD_Arabic-PADT",    "ar_padt",  "dev"),
    "mandarin":   ("UD_Chinese-GSD",    "zh_gsd",   "dev"),
    "english":    ("UD_English-EWT",    "en_ewt",   "dev"),
}

_UD_TEMPLATE = (
    "https://raw.githubusercontent.com/UniversalDependencies"
    "/{repo}/{branch}/{lang}-ud-{split}.conllu"
)

CLUSTERS: dict[str, str] = {
    "finnish":  "agglutinative",
    "turkish":  "agglutinative",
    "korean":   "agglutinative",
    "japanese": "agglutinative",
    "spanish":  "fusional",
    "russian":  "fusional",
    "german":   "fusional",
    "arabic":   "fusional",
    "mandarin": "analytic",
    "english":  "analytic",
}

# Feature axes extracted from UD (all in [0, ∞] but bounded for our languages)
UD_AXES = [
    "case_density",
    "agreement_density",
    "order_rigidity",
    "morph_richness",
    "compression_density",
]

MAX_SENTENCES = 500


# ── UD fetching ──────────────────────────────────────────────────────────────

def _fetch_ud_raw(language: str, timeout: int = 25) -> str | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{language}.conllu"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")

    repo, lang, split = _UD_REGISTRY[language]
    for branch in ("main", "master"):
        url = _UD_TEMPLATE.format(repo=repo, branch=branch, lang=lang, split=split)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Helix-Research/1.0 (ud_typology_probe.py)"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            cache_file.write_text(raw, encoding="utf-8")
            time.sleep(0.5)
            return raw
        except urllib.error.HTTPError:
            continue
        except Exception as exc:
            print(f"  [{language}] fetch error: {exc}")
            return None
    return None


def fetch_ud_features(language: str) -> dict | None:
    print(f"  [{language}] ", end="", flush=True)
    raw = _fetch_ud_raw(language)
    if not raw:
        print("FAILED")
        return None

    weights = extract_rule_weights(raw, max_sentences=MAX_SENTENCES)
    diag = weights["diagnostics"]

    if diag["sentences_analyzed"] == 0:
        print("no sentences parsed")
        return None

    source = "cache" if (CACHE_DIR / f"{language}.conllu").exists() else "network"
    print(
        f"n={diag['sentences_analyzed']}  "
        f"case={diag['case_density']:.3f}  "
        f"agree={diag['agreement_density']:.3f}  "
        f"order={diag['order_rigidity']:.3f}  "
        f"morph={diag['morphological_richness']:.2f}  "
        f"k_eff={weights['ud_k_eff']}  "
        f"({source})"
    )

    return {
        "language": language,
        "morphological_class": CLUSTERS.get(language, "unknown"),
        "case_density": diag["case_density"],
        "agreement_density": diag["agreement_density"],
        "order_rigidity": diag["order_rigidity"],
        "morph_richness": diag["morphological_richness"],
        "compression_density": diag["compression_density"],
        "order_signal": diag["order_signal"],
        "ud_k_eff": weights["ud_k_eff"],
        "dominant_signal": weights["dominant_rule_1_type"],
    }


# ── Distance and clustering ──────────────────────────────────────────────────

def ud_vector(features: dict) -> list[float]:
    """Normalize UD features to [0,1] for distance computation."""
    # morph_richness can go to ~5.0 for Finnish; normalize to [0, 5]
    return [
        float(features["case_density"]),                     # already [0,1]
        float(features["agreement_density"]),                # already [0,1]
        float(features["order_rigidity"]),                   # already [0,1]
        min(float(features["morph_richness"]) / 5.0, 1.0),  # normalize by max ~5
        min(float(features["compression_density"]) / 3.0, 1.0),  # normalize by ~3
    ]


def euclidean_distance(a: list[float], b: list[float]) -> float:
    return round(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)), 5)


def pairwise_distances(
    features_by_lang: dict[str, dict],
) -> dict[tuple[str, str], float]:
    langs = sorted(features_by_lang)
    vectors = {l: ud_vector(features_by_lang[l]) for l in langs}
    distances: dict[tuple[str, str], float] = {}
    for i, a in enumerate(langs):
        for b in langs[i + 1:]:
            distances[(a, b)] = euclidean_distance(vectors[a], vectors[b])
    return distances


def cluster_stats(
    distances: dict[tuple[str, str], float],
    features_by_lang: dict[str, dict],
) -> dict:
    intra: list[float] = []
    inter: list[float] = []
    for (a, b), d in distances.items():
        ca = features_by_lang[a]["morphological_class"]
        cb = features_by_lang[b]["morphological_class"]
        (intra if ca == cb else inter).append(d)

    mean_intra = sum(intra) / len(intra) if intra else 0.0
    mean_inter = sum(inter) / len(inter) if inter else 0.0
    ratio = mean_inter / mean_intra if mean_intra > 0 else float("inf")
    return {
        "mean_intra_cluster_distance": round(mean_intra, 5),
        "mean_inter_cluster_distance": round(mean_inter, 5),
        "cluster_separation_ratio": round(ratio, 4),
        "invariant_holds": ratio > 1.0,
        "intra_pairs": len(intra),
        "inter_pairs": len(inter),
    }


def nearest_cluster(
    language: str,
    features_by_lang: dict[str, dict],
) -> str:
    cluster_vecs: dict[str, list[list[float]]] = {}
    for lang, feat in features_by_lang.items():
        if lang == language:
            continue
        cl = feat["morphological_class"]
        cluster_vecs.setdefault(cl, []).append(ud_vector(feat))

    cluster_means: dict[str, list[float]] = {}
    for cl, vecs in cluster_vecs.items():
        n_axes = len(vecs[0])
        cluster_means[cl] = [
            sum(v[i] for v in vecs) / len(vecs)
            for i in range(n_axes)
        ]

    my_vec = ud_vector(features_by_lang[language])
    return min(cluster_means, key=lambda cl: euclidean_distance(my_vec, cluster_means[cl]))


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


def cluster_mean_feature(
    features_by_lang: dict[str, dict],
    feature_key: str,
) -> dict[str, float]:
    by_cluster: dict[str, list[float]] = {}
    for feat in features_by_lang.values():
        cl = feat["morphological_class"]
        by_cluster.setdefault(cl, []).append(float(feat[feature_key]))
    return {
        cl: round(sum(vals) / len(vals), 4)
        for cl, vals in by_cluster.items()
    }


def test_ordering(
    cluster_means: dict[str, float],
    expected_order: list[str],
    label: str,
) -> dict:
    available = [c for c in expected_order if c in cluster_means]
    comparisons = []
    holds = True
    for i in range(len(available) - 1):
        hi, lo = available[i], available[i + 1]
        h_val, l_val = cluster_means[hi], cluster_means[lo]
        comp_holds = h_val > l_val
        if not comp_holds:
            holds = False
        comparisons.append({
            "comparison": f"{hi} > {lo}",
            "values": f"{h_val:.4f} vs {l_val:.4f}",
            "holds": comp_holds,
        })
    return {
        "feature": label,
        "expected_order": " > ".join(available),
        "invariant_holds": holds,
        "comparisons": comparisons,
    }


# ── Printing ─────────────────────────────────────────────────────────────────

def bar(value: float, max_val: float, width: int = 28) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    return "█" * filled + "░" * (width - filled)


def print_results(
    features_by_lang: dict[str, dict],
    distances: dict[tuple[str, str], float],
    sep_stats: dict,
    classifications: dict[str, tuple[str, str, bool]],
    ordering_tests: list[dict],
    tradeoff_correlations: list[dict],
) -> None:
    print("\n" + "═" * 76)
    print("  UD TYPOLOGY PROBE — LANGUAGE-AGNOSTIC STRUCTURAL INVARIANT TEST")
    print("═" * 76)

    # ── Per-language feature table
    print("\n── UD Feature Profiles ─────────────────────────────────────────────────")
    print(
        f"  {'Language':<14} {'Class':<16} "
        f"{'case':>6} {'agree':>6} {'order':>6} {'morph':>6} {'comp':>6} "
        f"{'k_eff':>6} {'dominant':<12}"
    )
    print("  " + "─" * 74)
    cluster_order = ["agglutinative", "fusional", "analytic"]
    for cl in cluster_order:
        for lang in sorted(features_by_lang, key=lambda l: features_by_lang[l]["morphological_class"] + l):
            if features_by_lang[lang]["morphological_class"] != cl:
                continue
            f = features_by_lang[lang]
            print(
                f"  {lang:<14} {cl:<16} "
                f"{f['case_density']:>6.3f} "
                f"{f['agreement_density']:>6.3f} "
                f"{f['order_rigidity']:>6.3f} "
                f"{f['morph_richness']:>6.2f} "
                f"{f['compression_density']:>6.3f} "
                f"{f['ud_k_eff']:>6.2f} "
                f"{f['dominant_signal']:<12}"
            )

    # ── k_eff bar chart
    print("\n── k_eff Parse Ambiguity by Language (lower = more compressed) ─────────")
    max_k = max(f["ud_k_eff"] for f in features_by_lang.values())
    for lang in sorted(features_by_lang, key=lambda l: features_by_lang[l]["ud_k_eff"]):
        f = features_by_lang[lang]
        cl = f["morphological_class"]
        k = f["ud_k_eff"]
        b = bar(k, max_k)
        print(f"  {lang:<14} {cl[0].upper()}  k={k:.3f}  {b}")

    # ── Cluster separation test
    print("\n── Cluster Separation (Hypothesis 1) ───────────────────────────────────")
    print(f"  Mean intra-cluster distance: {sep_stats['mean_intra_cluster_distance']:.5f}")
    print(f"  Mean inter-cluster distance: {sep_stats['mean_inter_cluster_distance']:.5f}")
    print(f"  Separation ratio (inter/intra): {sep_stats['cluster_separation_ratio']:.4f}")
    result = "✓ HOLDS" if sep_stats["invariant_holds"] else "✗ FAILS"
    print(f"  Invariant (ratio > 1.0): {result}")

    # ── Nearest-cluster classification
    print("\n── Nearest-Cluster Classification ──────────────────────────────────────")
    print(f"  {'Language':<14} {'True':<18} {'Predicted':<18} {'Correct'}")
    print("  " + "─" * 56)
    correct = sum(1 for _, (_, _, ok) in classifications.items() if ok)
    for lang in sorted(classifications):
        true, pred, ok = classifications[lang]
        print(f"  {lang:<14} {true:<18} {pred:<18} {'✓' if ok else '✗'}")
    print(f"\n  Accuracy: {correct}/{len(classifications)} = {correct/len(classifications)*100:.0f}%")

    # ── Feature ordering tests
    print("\n── Feature Ordering Tests (Hypothesis 2) ───────────────────────────────")
    for ot in ordering_tests:
        overall = "✓" if ot["invariant_holds"] else "✗"
        print(f"\n  {overall}  {ot['feature']}  (expected: {ot['expected_order']})")
        for comp in ot["comparisons"]:
            mark = "  ✓" if comp["holds"] else "  ✗"
            print(f"    {mark}  {comp['comparison']}: {comp['values']}")

    # ── Morphosyntax tradeoff correlations
    print("\n── Morphosyntax Tradeoff Correlations (Hypothesis 4) ──────────────────")
    print(f"  {'Pair':<44} {'Pearson r':>10}  {'Expected':>10}  {'Holds'}")
    print("  " + "─" * 72)
    for tc in tradeoff_correlations:
        mark = "✓" if tc["holds"] else "✗"
        print(
            f"  {tc['x']} ↔ {tc['y']:<{36-len(tc['x'])}}"
            f" {tc['pearson_r']:>10.4f}  {tc['expected']:>10}  {mark}"
        )

    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("UD Typology Probe (language-agnostic, annotation-derived features)")
    print("━" * 76)
    print("\nFeature source: UD FEATS column + dependency relations (NOT surface text)")
    print("Fixes the Spanish-bias found in the heuristic structural vectorizer.\n")

    print("[1] Extracting UD features from treebank annotations...")
    features_by_lang: dict[str, dict] = {}
    for language in sorted(_UD_REGISTRY):
        feat = fetch_ud_features(language)
        if feat:
            features_by_lang[language] = feat

    if len(features_by_lang) < 4:
        print("Insufficient languages. Aborting.")
        return

    print(f"\n[2] Computing pairwise distances ({len(features_by_lang)} languages)...")
    distances = pairwise_distances(features_by_lang)

    print("[3] Cluster separation test (Hypothesis 1)...")
    sep_stats = cluster_stats(distances, features_by_lang)

    print("[4] Nearest-cluster classification...")
    classifications: dict[str, tuple[str, str, bool]] = {}
    for lang in features_by_lang:
        true_cl = features_by_lang[lang]["morphological_class"]
        pred_cl = nearest_cluster(lang, features_by_lang)
        classifications[lang] = (true_cl, pred_cl, true_cl == pred_cl)

    print("[5] Feature ordering tests (Hypothesis 2)...")
    ordering_tests = [
        test_ordering(
            cluster_mean_feature(features_by_lang, "morph_richness"),
            ["agglutinative", "fusional", "analytic"],
            "morph_richness",
        ),
        test_ordering(
            cluster_mean_feature(features_by_lang, "agreement_density"),
            ["fusional", "agglutinative", "analytic"],
            "agreement_density (fusional > agglutinative > analytic)",
        ),
        test_ordering(
            cluster_mean_feature(features_by_lang, "order_rigidity"),
            ["analytic", "agglutinative", "fusional"],
            "order_rigidity (analytic > agglutinative > fusional)",
        ),
    ]

    print("[6] Morphosyntax tradeoff correlations (Hypothesis 4)...")
    langs = sorted(features_by_lang)
    tradeoff_tests = [
        ("morph_richness", "order_rigidity", "negative"),
        ("case_density", "agreement_density", "positive"),
        ("morph_richness", "agreement_density", "positive"),
        ("compression_density", "ud_k_eff", "negative"),
    ]
    tradeoff_correlations = []
    for x_key, y_key, expected in tradeoff_tests:
        xs = [float(features_by_lang[l][x_key]) for l in langs]
        ys = [float(features_by_lang[l][y_key]) for l in langs]
        r = pearson_r(xs, ys)
        holds = (r < -0.2) if expected == "negative" else (r > 0.2)
        tradeoff_correlations.append({
            "x": x_key,
            "y": y_key,
            "expected": expected,
            "pearson_r": r,
            "holds": holds,
        })

    print_results(
        features_by_lang,
        distances,
        sep_stats,
        classifications,
        ordering_tests,
        tradeoff_correlations,
    )

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "probe": "ud_typology",
        "feature_source": "UD FEATS column + deprel annotations (language-agnostic)",
        "language_count": len(features_by_lang),
        "languages": sorted(features_by_lang.keys()),
        "clusters": {lang: CLUSTERS[lang] for lang in features_by_lang if lang in CLUSTERS},
        "features": features_by_lang,
        "pairwise_distances": {f"{a}|{b}": d for (a, b), d in distances.items()},
        "cluster_separation": sep_stats,
        "classifications": {
            lang: {"true": t, "predicted": p, "correct": ok}
            for lang, (t, p, ok) in classifications.items()
        },
        "ordering_tests": ordering_tests,
        "tradeoff_correlations": tradeoff_correlations,
    }
    out_path = ARTIFACT_DIR / "ud_typology_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()

