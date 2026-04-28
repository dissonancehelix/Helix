"""
Morphosyntax Tradeoff Probe — non-DCP structural law test.

Hypothesis
----------
Morphological complexity and syntactic scaffolding are in NEGATIVE tradeoff
across languages. Languages that encode grammatical relations through word-
internal morphology (case markers, agreement affixes) rely less on function
words and rigid word order — and vice versa.

This is a structural law claim about the Helix 8-axis feature space:
  inflectional_load ↑  →  function_word_scaffolding ↓
  inflectional_load ↑  →  clause_subordination ↓ (fewer overt connectives)

Analogy: Menzerath-Altmann law (constituent length trades off with constituent
count). Here: morphological encoding budget trades off with syntactic encoding
budget. One strategy dominates; the other is suppressed.

Invariant claims
----------------
  [A] Pearson r(inflectional_load, function_word_scaffolding) < 0
  [B] Pearson r(inflectional_load, clause_subordination) < 0  [softer — subordination is
      affected by information structure, not just morphology]
  [C] r(function_word_scaffolding, subject_explicitness) > 0
      (analytic languages use both function words AND explicit subjects)

Data source
-----------
Structural vector centroids computed from UD treebank sentences (same UD
infrastructure as typology_cluster_probe.py — results cached on disk).

Run
---
    python model/domains/language/probes/morphosyntax_tradeoff_probe.py
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

from model.domains.language.feature_extraction.structural_vector import StructuralVectorExtractor

# ── UD registry (same as other probes) ──────────────────────────────────────

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

SENTENCES_PER_LANG = 40
MIN_TOKENS = 8


# ── UD fetching (same pattern as typology_cluster_probe.py) ──────────────────

def _fetch_ud_raw(language: str, timeout: int = 20) -> str | None:
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
                headers={"User-Agent": "Helix-Research/1.0 (morphosyntax_tradeoff_probe.py)"},
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


def _parse_sentences(raw: str, language: str, n: int, min_tokens: int) -> list[dict]:
    sentences = []
    for line in raw.splitlines():
        if line.startswith("# text = "):
            text = line[len("# text = "):].strip()
            if len(text.split()) >= min_tokens:
                sentences.append({"text": text, "language": language})
            if len(sentences) >= n:
                break
    return sentences


def fetch_centroid(language: str) -> dict[str, float] | None:
    print(f"  [{language}] ", end="", flush=True)
    raw = _fetch_ud_raw(language)
    if not raw:
        print("FAILED")
        return None

    sentences = _parse_sentences(raw, language, SENTENCES_PER_LANG, MIN_TOKENS)
    if not sentences:
        print("no sentences")
        return None

    try:
        extractor = StructuralVectorExtractor(language=language)
        summary = extractor.summarize(sentences)
        centroid = summary["centroid"]
        source = "cache" if (CACHE_DIR / f"{language}.conllu").exists() else "network"
        print(f"OK ({len(sentences)} sentences, {source})")
        return centroid
    except Exception as exc:
        print(f"error: {exc}")
        return None


# ── Statistics ───────────────────────────────────────────────────────────────

def pearson_r(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation coefficient between two equal-length sequences."""
    n = len(xs)
    if n < 3:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 4)


def rank_correlation(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation (non-parametric, robust to outliers)."""
    n = len(xs)
    if n < 3:
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        sorted_vals = sorted(enumerate(vals), key=lambda x: x[1])
        result = [0.0] * n
        for rank, (i, _) in enumerate(sorted_vals, 1):
            result[i] = float(rank)
        return result

    rx = ranks(xs)
    ry = ranks(ys)
    d_sq = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return round(1.0 - (6 * d_sq) / (n * (n * n - 1)), 4)


# ── Tradeoff analysis ────────────────────────────────────────────────────────

# Each hypothesis: (axis_x, axis_y, expected_sign, label)
HYPOTHESES: list[tuple[str, str, str, str]] = [
    (
        "inflectional_load",
        "function_word_scaffolding",
        "negative",
        "[A] Morphological encoding displaces function-word scaffolding",
    ),
    (
        "inflectional_load",
        "clause_subordination",
        "negative",
        "[B] Morphological richness reduces overt subordination markers",
    ),
    (
        "function_word_scaffolding",
        "subject_explicitness",
        "positive",
        "[C] Analytic languages use both function words AND overt subjects",
    ),
    (
        "inflectional_load",
        "lexical_variation",
        "positive",
        "[D] Morphological inflection expands the surface form vocabulary",
    ),
]


def test_hypothesis(
    x_axis: str,
    y_axis: str,
    expected_sign: str,
    centroids: dict[str, dict[str, float]],
) -> dict:
    langs = sorted(centroids)
    xs = [float(centroids[l].get(x_axis, 0.0)) for l in langs]
    ys = [float(centroids[l].get(y_axis, 0.0)) for l in langs]

    r_pearson = pearson_r(xs, ys)
    r_spearman = rank_correlation(xs, ys)

    if expected_sign == "negative":
        holds = r_pearson < -0.1 and r_spearman < 0.0
    else:
        holds = r_pearson > 0.1 and r_spearman > 0.0

    return {
        "x_axis": x_axis,
        "y_axis": y_axis,
        "expected_sign": expected_sign,
        "pearson_r": r_pearson,
        "spearman_r": r_spearman,
        "invariant_holds": holds,
        "per_language": [
            {"language": l, "x": round(xs[i], 4), "y": round(ys[i], 4)}
            for i, l in enumerate(langs)
        ],
    }


# ── Printing ─────────────────────────────────────────────────────────────────

def print_results(
    centroids: dict[str, dict[str, float]],
    hypothesis_results: list[dict],
) -> None:
    print("\n" + "═" * 70)
    print("  MORPHOSYNTAX TRADEOFF PROBE")
    print("═" * 70)

    axes = [
        "inflectional_load", "function_word_scaffolding",
        "clause_subordination", "subject_explicitness", "lexical_variation",
    ]
    short = ["infl_load", "fn_word", "subord", "subj_expl", "lex_var"]

    print("\n── Language Axis Values ────────────────────────────────────────────")
    print(f"  {'Language':<14} {'Class':<16} " + "  ".join(f"{s:>9}" for s in short))
    print("  " + "─" * 70)
    for lang in sorted(centroids):
        row_vals = "  ".join(f"{centroids[lang].get(ax, 0.0):>9.4f}" for ax in axes)
        print(f"  {lang:<14} {CLUSTERS.get(lang, '?'):<16} {row_vals}")

    print("\n── Hypothesis Tests ────────────────────────────────────────────────")
    all_hold = True
    for hr in hypothesis_results:
        mark = "✓" if hr["invariant_holds"] else "✗"
        if not hr["invariant_holds"]:
            all_hold = False
        sign_str = f"expected {hr['expected_sign']}"
        print(f"\n  {mark}  {sign_str}")
        print(f"     {hr['x_axis']}  ↔  {hr['y_axis']}")
        print(f"     Pearson r = {hr['pearson_r']:+.4f}  |  Spearman ρ = {hr['spearman_r']:+.4f}")

        # Mini scatter text chart
        xs = [p["x"] for p in hr["per_language"]]
        ys = [p["y"] for p in hr["per_language"]]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = 30, 6
        grid = [[" "] * w for _ in range(h)]
        for p in hr["per_language"]:
            xi = int((p["x"] - min_x) / (max_x - min_x + 1e-9) * (w - 1))
            yi = int((p["y"] - min_y) / (max_y - min_y + 1e-9) * (h - 1))
            yi = h - 1 - yi  # flip y
            label = p["language"][:1].upper()
            if 0 <= xi < w and 0 <= yi < h:
                grid[yi][xi] = label
        x_label = hr["x_axis"][:12]
        y_label = hr["y_axis"][:10]
        print(f"\n     {y_label} ↑")
        for row in grid:
            print(f"     │ {''.join(row)}")
        print(f"     └{'─' * w}→ {x_label}")

    print(f"\n── Summary ─────────────────────────────────────────────────────────")
    n_hold = sum(1 for hr in hypothesis_results if hr["invariant_holds"])
    print(f"  {n_hold}/{len(hypothesis_results)} hypotheses confirmed")
    print(f"  Overall invariant status: {'✓ SUPPORTED' if all_hold else '◑ PARTIAL' if n_hold > 0 else '✗ REJECTED'}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Morphosyntax Tradeoff Probe")
    print("━" * 70)
    print("\nHypothesis: inflectional morphology and syntactic scaffolding")
    print("           trade off across languages (encoding budget redistribution).\n")

    print("[1] Computing structural vector centroids from UD data...")
    centroids: dict[str, dict[str, float]] = {}
    for language in sorted(_UD_REGISTRY):
        centroid = fetch_centroid(language)
        if centroid:
            centroids[language] = centroid

    if len(centroids) < 4:
        print("Insufficient languages. Aborting.")
        return

    print(f"\n[2] Testing {len(HYPOTHESES)} tradeoff hypotheses across {len(centroids)} languages...")
    hypothesis_results: list[dict] = []
    for x_axis, y_axis, expected_sign, label in HYPOTHESES:
        print(f"  {label}")
        result = test_hypothesis(x_axis, y_axis, expected_sign, centroids)
        hypothesis_results.append({**result, "label": label})

    print_results(centroids, hypothesis_results)

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "probe": "morphosyntax_tradeoff",
        "hypothesis": "inflectional_load negatively correlates with function_word_scaffolding across languages",
        "language_count": len(centroids),
        "languages": sorted(centroids.keys()),
        "clusters": {lang: CLUSTERS[lang] for lang in centroids if lang in CLUSTERS},
        "centroids": centroids,
        "hypothesis_results": hypothesis_results,
        "summary": {
            "hypotheses_tested": len(hypothesis_results),
            "hypotheses_confirmed": sum(1 for hr in hypothesis_results if hr["invariant_holds"]),
        },
    }
    out_path = ARTIFACT_DIR / "morphosyntax_tradeoff_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()

