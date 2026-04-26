"""
Typology Cluster Probe — non-DCP structural invariant test.

Hypothesis
----------
The Helix 8-axis structural vector space recovers language typological
family membership WITHOUT being given typological labels. Structural distance
between languages of the same morphological class should be less than
structural distance between languages of different classes.

This is distinct from DCP, which tests a compression DYNAMIC. This probe
tests whether the feature space is a FAITHFUL PROJECTION of linguistic
structure — a representation-quality check.

Typological ground truth (morphological class):
  Agglutinative : Finnish, Turkish, Korean, Japanese
  Fusional      : Spanish, Russian, German, Arabic, Hindi
  Analytic      : Mandarin, English (partially analytic), Vietnamese

Invariant claim
---------------
mean(intra-cluster distance) < mean(inter-cluster distance)
cluster_separation_ratio = inter / intra > 1.0

If this fails, the 8-axis space is not typologically grounded and its
distances are not interpretable as structural proximity.

Run
---
    python domains/language/probes/typology_cluster_probe.py
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

from domains.language.feature_extraction.structural_vector import (
    StructuralVectorExtractor,
    vector_distance,
)

# ── UD treebank registry ────────────────────────────────────────────────────

_UD_REGISTRY: dict[str, tuple[str, str, str]] = {
    # Agglutinative
    "finnish":    ("UD_Finnish-TDT",    "fi_tdt",   "dev"),
    "turkish":    ("UD_Turkish-BOUN",   "tr_boun",  "dev"),
    "korean":     ("UD_Korean-GSD",     "ko_gsd",   "dev"),
    "japanese":   ("UD_Japanese-GSD",   "ja_gsd",   "dev"),
    # Fusional
    "spanish":    ("UD_Spanish-GSD",    "es_gsd",   "dev"),
    "russian":    ("UD_Russian-GSD",    "ru_gsd",   "dev"),
    "german":     ("UD_German-GSD",     "de_gsd",   "dev"),
    "arabic":     ("UD_Arabic-PADT",    "ar_padt",  "dev"),
    # Analytic / Isolating
    "mandarin":   ("UD_Chinese-GSD",    "zh_gsd",   "dev"),
    "english":    ("UD_English-EWT",    "en_ewt",   "dev"),
}

_UD_TEMPLATE = (
    "https://raw.githubusercontent.com/UniversalDependencies"
    "/{repo}/{branch}/{lang}-ud-{split}.conllu"
)

# Ground-truth morphological cluster labels
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


# ── UD fetching ─────────────────────────────────────────────────────────────

def _fetch_ud_raw(language: str, timeout: int = 20) -> str | None:
    """Download CoNLL-U text from UD GitHub. Uses on-disk cache."""
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
                headers={"User-Agent": "Helix-Research/1.0 (typology_cluster_probe.py)"},
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
    """Extract sentence texts from CoNLL-U # text = lines."""
    sentences = []
    for line in raw.splitlines():
        if line.startswith("# text = "):
            text = line[len("# text = "):].strip()
            if len(text.split()) >= min_tokens:
                sentences.append({"text": text, "language": language})
            if len(sentences) >= n:
                break
    return sentences


def fetch_language_sentences(language: str) -> list[dict]:
    print(f"  [{language}] ", end="", flush=True)
    raw = _fetch_ud_raw(language)
    if not raw:
        print("FAILED")
        return []
    sentences = _parse_sentences(raw, language, SENTENCES_PER_LANG, MIN_TOKENS)
    source = "cache" if (CACHE_DIR / f"{language}.conllu").exists() else "network"
    print(f"{len(sentences)} sentences ({source})")
    return sentences


# ── Structural vector computation ────────────────────────────────────────────

def compute_centroid(language: str, sentences: list[dict]) -> dict[str, float] | None:
    if not sentences:
        return None
    try:
        extractor = StructuralVectorExtractor(language=language)
        summary = extractor.summarize(sentences)
        return summary["centroid"]
    except Exception as exc:
        print(f"  [{language}] vectorizer error: {exc}")
        return None


# ── Distance / clustering ────────────────────────────────────────────────────

def pairwise_distances(
    centroids: dict[str, dict[str, float]],
) -> dict[tuple[str, str], float]:
    langs = sorted(centroids)
    distances: dict[tuple[str, str], float] = {}
    for i, a in enumerate(langs):
        for b in langs[i + 1:]:
            d = vector_distance(centroids[a], centroids[b])
            distances[(a, b)] = round(d, 5)
    return distances


def cluster_stats(
    distances: dict[tuple[str, str], float],
    clusters: dict[str, str],
) -> dict:
    intra: list[float] = []
    inter: list[float] = []

    for (a, b), d in distances.items():
        if clusters.get(a) == clusters.get(b):
            intra.append(d)
        else:
            inter.append(d)

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
    centroids: dict[str, dict[str, float]],
    clusters: dict[str, str],
) -> str:
    """Which cluster label would a nearest-centroid classifier assign?"""
    cluster_centroids: dict[str, list[dict[str, float]]] = {}
    for lang, cen in centroids.items():
        if lang == language:
            continue
        cluster = clusters.get(lang)
        if cluster:
            cluster_centroids.setdefault(cluster, []).append(cen)

    # Average centroid per cluster
    cluster_means: dict[str, dict[str, float]] = {}
    for cluster, vecs in cluster_centroids.items():
        axes = vecs[0].keys()
        cluster_means[cluster] = {
            ax: round(sum(float(v.get(ax, 0.0)) for v in vecs) / len(vecs), 5)
            for ax in axes
        }

    my_centroid = centroids[language]
    best_cluster = min(
        cluster_means,
        key=lambda cl: vector_distance(my_centroid, cluster_means[cl]),
    )
    return best_cluster


# ── Output / printing ────────────────────────────────────────────────────────

def print_results(
    centroids: dict[str, dict[str, float]],
    distances: dict[tuple[str, str], float],
    stats: dict,
    classifications: dict[str, tuple[str, str, bool]],
) -> None:
    print("\n" + "═" * 70)
    print("  TYPOLOGY CLUSTER PROBE — STRUCTURAL VECTOR SPACE")
    print("═" * 70)

    print("\n── Language Centroids (8 axes) ─────────────────────────────────────")
    axes = ["inflectional_load", "subject_explicitness", "clause_subordination",
            "function_word_scaffolding", "tense_aspect_marking",
            "mood_polarity", "frame_stability", "lexical_variation"]
    short = ["infl", "subj", "subord", "fn_wd", "tense", "mood", "frame", "lex_v"]
    header = f"  {'Language':<14} " + "  ".join(f"{s:>6}" for s in short)
    print(header)
    print("  " + "─" * (len(header) - 2))
    for lang in sorted(centroids):
        row = f"  {lang:<14} "
        row += "  ".join(f"{centroids[lang].get(ax, 0.0):>6.3f}" for ax in axes)
        row += f"   [{CLUSTERS.get(lang, '?')}]"
        print(row)

    print("\n── Pairwise Distances ──────────────────────────────────────────────")
    langs = sorted(centroids)
    header2 = "  " + " " * 14 + "  ".join(f"{l[:7]:>7}" for l in langs)
    print(header2)
    for a in langs:
        row = f"  {a:<14}"
        for b in langs:
            if a == b:
                row += f"  {'·':>7}"
            elif (a, b) in distances:
                row += f"  {distances[(a, b)]:>7.4f}"
            else:
                row += f"  {distances[(b, a)]:>7.4f}"
        print(row)

    print("\n── Cluster Separation ──────────────────────────────────────────────")
    print(f"  Mean intra-cluster distance:  {stats['mean_intra_cluster_distance']:.5f}")
    print(f"  Mean inter-cluster distance:  {stats['mean_inter_cluster_distance']:.5f}")
    print(f"  Separation ratio (inter/intra): {stats['cluster_separation_ratio']:.4f}")
    result_str = "✓ HOLDS" if stats["invariant_holds"] else "✗ FAILS"
    print(f"  Invariant (ratio > 1.0):  {result_str}")

    print("\n── Nearest-Cluster Classification ──────────────────────────────────")
    print(f"  {'Language':<14} {'True cluster':<18} {'Predicted':<18} {'Correct'}")
    print("  " + "─" * 56)
    correct = sum(1 for _, (true, pred, ok) in classifications.items() if ok)
    total = len(classifications)
    for lang in sorted(classifications):
        true, pred, ok = classifications[lang]
        mark = "✓" if ok else "✗"
        print(f"  {lang:<14} {true:<18} {pred:<18} {mark}")
    print(f"\n  Accuracy: {correct}/{total} = {correct/total*100:.0f}%")

    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Typology Cluster Probe")
    print("━" * 70)
    print("\nHypothesis: structural vector space recovers morphological family membership.")
    print("Invariant: mean intra-cluster distance < mean inter-cluster distance.\n")

    print("[1] Fetching UD sentences...")
    all_sentences: dict[str, list[dict]] = {}
    for language in sorted(_UD_REGISTRY):
        sentences = fetch_language_sentences(language)
        if sentences:
            all_sentences[language] = sentences

    print(f"\n[2] Computing structural vector centroids ({len(all_sentences)} languages)...")
    centroids: dict[str, dict[str, float]] = {}
    for language, sentences in all_sentences.items():
        centroid = compute_centroid(language, sentences)
        if centroid:
            centroids[language] = centroid
            print(f"  [{language}] OK")
        else:
            print(f"  [{language}] FAILED — skipped")

    if len(centroids) < 4:
        print("\nInsufficient languages for cluster test. Aborting.")
        return

    print(f"\n[3] Computing pairwise distances ({len(centroids)} languages)...")
    distances = pairwise_distances(centroids)

    print("[4] Computing cluster statistics...")
    stats = cluster_stats(distances, CLUSTERS)

    print("[5] Nearest-cluster classification...")
    classifications: dict[str, tuple[str, str, bool]] = {}
    for lang in centroids:
        true_cluster = CLUSTERS.get(lang, "unknown")
        pred_cluster = nearest_cluster(lang, centroids, CLUSTERS)
        ok = true_cluster == pred_cluster
        classifications[lang] = (true_cluster, pred_cluster, ok)

    print_results(centroids, distances, stats, classifications)

    # Save results
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "probe": "typology_cluster",
        "hypothesis": "structural vector space recovers morphological family membership",
        "invariant": "mean intra-cluster distance < mean inter-cluster distance",
        "language_count": len(centroids),
        "languages": sorted(centroids.keys()),
        "centroids": centroids,
        "clusters": {lang: CLUSTERS[lang] for lang in centroids if lang in CLUSTERS},
        "pairwise_distances": {f"{a}|{b}": d for (a, b), d in distances.items()},
        "cluster_stats": stats,
        "nearest_cluster_accuracy": {
            "correct": sum(1 for _, (_, _, ok) in classifications.items() if ok),
            "total": len(classifications),
            "detail": {lang: {"true": t, "predicted": p, "correct": ok}
                       for lang, (t, p, ok) in classifications.items()},
        },
    }
    out_path = ARTIFACT_DIR / "typology_cluster_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()
