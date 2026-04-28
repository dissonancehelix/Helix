"""
Lexical Entropy Probe — non-DCP information-rate invariant test.

Hypothesis
----------
Morphological type predicts per-token lexical entropy: languages that encode
meaning through word-internal morphology (agglutinative/fusional) will have
higher Shannon entropy over their surface form distribution than languages that
encode meaning through word order and free morphemes (analytic/isolating).

Agglutinative (Finnish, Turkish, Korean, Japanese):
  High form variety — each root × affix combination is a unique surface token.
  Expected: HIGH entropy, HIGH type-token ratio.

Fusional (Spanish, Russian, German, Arabic):
  Moderate form variety — inflectional categories fuse into fewer dense endings.
  Expected: MODERATE entropy.

Analytic/Isolating (Mandarin, English, Vietnamese):
  Low form variety — words are stable, meaning carried by word order.
  Expected: LOW entropy (smaller unique-form set, many function words repeat).

Invariant claim
---------------
mean(H_agglutinative) > mean(H_fusional) > mean(H_analytic)

This is measured as:
  H(language) = -Σ p(form) * log2(p(form))   [Shannon entropy, bits/type]
  TTR = |unique forms| / |total tokens|         [type-token ratio]

Both H and TTR should be ordered by morphological complexity. A failure
means the surface form distribution is NOT correlated with morphological type,
which would challenge the interpretability of the inflectional_load axis.

Run
---
    python model/domains/language/probes/lexical_entropy_probe.py
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

CACHE_DIR = REPO_ROOT / "domains" / "language" / "data" / "ud_cache"
ARTIFACT_DIR = REPO_ROOT / "domains" / "language" / "artifacts"

# ── UD treebank registry ─────────────────────────────────────────────────────

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

MAX_TOKENS = 10_000   # tokens per language for entropy computation


# ── UD fetching ──────────────────────────────────────────────────────────────

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
                headers={"User-Agent": "Helix-Research/1.0 (lexical_entropy_probe.py)"},
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


# ── CoNLL-U parsing ──────────────────────────────────────────────────────────

def parse_conllu_forms(raw: str, max_tokens: int) -> list[str]:
    """
    Extract surface word forms (column 1) from CoNLL-U text.

    Skips:
      - Comment lines (# ...)
      - Empty lines (sentence separators)
      - Multiword tokens (e.g. '1-2' range IDs)
      - Empty nodes (e.g. '1.1' decimal IDs)

    Returns a flat list of lowercase surface forms.
    """
    forms: list[str] = []
    for line in raw.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        token_id = parts[0]
        # Skip multiword tokens and empty nodes
        if "-" in token_id or "." in token_id:
            continue
        form = parts[1].strip().lower()
        if form and form != "_":
            forms.append(form)
        if len(forms) >= max_tokens:
            break
    return forms


# ── Entropy computation ──────────────────────────────────────────────────────

def shannon_entropy(forms: list[str]) -> float:
    """Shannon entropy in bits over the surface form distribution."""
    if not forms:
        return 0.0
    counts = Counter(forms)
    total = len(forms)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 5)


def type_token_ratio(forms: list[str]) -> float:
    if not forms:
        return 0.0
    return round(len(set(forms)) / len(forms), 5)


def hapax_ratio(forms: list[str]) -> float:
    """Proportion of forms that appear exactly once (hapax legomena)."""
    if not forms:
        return 0.0
    counts = Counter(forms)
    hapax = sum(1 for c in counts.values() if c == 1)
    return round(hapax / len(counts), 5)


def compute_language_stats(language: str) -> dict | None:
    print(f"  [{language}] ", end="", flush=True)
    raw = _fetch_ud_raw(language)
    if not raw:
        print("FAILED")
        return None

    forms = parse_conllu_forms(raw, MAX_TOKENS)
    if len(forms) < 100:
        print(f"too few tokens ({len(forms)})")
        return None

    H = shannon_entropy(forms)
    ttr = type_token_ratio(forms)
    hapax = hapax_ratio(forms)
    unique = len(set(forms))
    total = len(forms)

    source = "cache" if (CACHE_DIR / f"{language}.conllu").exists() else "network"
    print(f"H={H:.3f}b  TTR={ttr:.4f}  tokens={total:,}  unique={unique:,}  ({source})")

    return {
        "language": language,
        "morphological_class": CLUSTERS.get(language, "unknown"),
        "total_tokens": total,
        "unique_forms": unique,
        "shannon_entropy_bits": H,
        "type_token_ratio": ttr,
        "hapax_ratio": hapax,
    }


# ── Cluster comparison ───────────────────────────────────────────────────────

def cluster_means(stats_by_lang: dict[str, dict]) -> dict[str, dict]:
    by_cluster: dict[str, list[dict]] = {}
    for lang, s in stats_by_lang.items():
        cluster = s["morphological_class"]
        by_cluster.setdefault(cluster, []).append(s)

    result: dict[str, dict] = {}
    for cluster, members in by_cluster.items():
        n = len(members)
        result[cluster] = {
            "languages": [m["language"] for m in members],
            "n": n,
            "mean_entropy": round(sum(m["shannon_entropy_bits"] for m in members) / n, 5),
            "mean_ttr": round(sum(m["type_token_ratio"] for m in members) / n, 5),
            "mean_hapax_ratio": round(sum(m["hapax_ratio"] for m in members) / n, 5),
        }
    return result


def test_ordering(means: dict[str, dict]) -> dict:
    """
    Test: agglutinative > fusional > analytic for Shannon entropy.
    Returns whether the ordering holds and the direction of each comparison.
    """
    order = ["agglutinative", "fusional", "analytic"]
    available = [c for c in order if c in means]

    results: list[dict] = []
    invariant_holds = True

    for i in range(len(available) - 1):
        hi_cluster = available[i]
        lo_cluster = available[i + 1]
        hi_H = means[hi_cluster]["mean_entropy"]
        lo_H = means[lo_cluster]["mean_entropy"]
        holds = hi_H > lo_H
        if not holds:
            invariant_holds = False
        results.append({
            "comparison": f"{hi_cluster} > {lo_cluster}",
            "values": f"{hi_H:.4f} vs {lo_H:.4f}",
            "holds": holds,
        })

    return {
        "ordering_tested": " > ".join(available),
        "invariant_holds": invariant_holds,
        "comparisons": results,
    }


# ── Printing ─────────────────────────────────────────────────────────────────

def print_results(
    stats_by_lang: dict[str, dict],
    means: dict[str, dict],
    ordering: dict,
) -> None:
    print("\n" + "═" * 70)
    print("  LEXICAL ENTROPY PROBE — INFORMATION RATE BY MORPHOLOGICAL TYPE")
    print("═" * 70)

    cluster_order = ["agglutinative", "fusional", "analytic"]

    print("\n── Per-Language Results ────────────────────────────────────────────")
    print(f"  {'Language':<14} {'Class':<16} {'H (bits)':>9} {'TTR':>8} {'Hapax':>8} {'Tokens':>8}")
    print("  " + "─" * 66)
    for cluster in cluster_order:
        langs_in_cluster = [
            lang for lang, s in stats_by_lang.items()
            if s["morphological_class"] == cluster
        ]
        for lang in sorted(langs_in_cluster):
            s = stats_by_lang[lang]
            print(
                f"  {lang:<14} {cluster:<16} "
                f"{s['shannon_entropy_bits']:>9.4f} "
                f"{s['type_token_ratio']:>8.4f} "
                f"{s['hapax_ratio']:>8.4f} "
                f"{s['total_tokens']:>8,}"
            )
        if langs_in_cluster:
            m = means.get(cluster, {})
            print(
                f"  {'  mean →':<14} {cluster:<16} "
                f"{m.get('mean_entropy', 0.0):>9.4f} "
                f"{m.get('mean_ttr', 0.0):>8.4f} "
                f"{m.get('mean_hapax_ratio', 0.0):>8.4f}"
            )
            print()

    print("── Cluster Mean Entropy (bits/type) ────────────────────────────────")
    bar_scale = 40.0
    max_H = max(m["mean_entropy"] for m in means.values()) if means else 1.0
    for cluster in cluster_order:
        if cluster not in means:
            continue
        H = means[cluster]["mean_entropy"]
        bar = "█" * int((H / max_H) * bar_scale)
        print(f"  {cluster:<18} {H:>7.4f}b  {bar}")

    print("\n── Ordering Test ───────────────────────────────────────────────────")
    print(f"  Expected: agglutinative > fusional > analytic")
    for comp in ordering["comparisons"]:
        mark = "✓" if comp["holds"] else "✗"
        print(f"  {mark}  {comp['comparison']}: {comp['values']}")
    overall = "✓ HOLDS" if ordering["invariant_holds"] else "✗ FAILS"
    print(f"\n  Invariant: {overall}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Lexical Entropy Probe")
    print("━" * 70)
    print("\nHypothesis: agglutinative > fusional > analytic for Shannon entropy")
    print("           over surface form distribution (morphological complexity")
    print("           expands the type space, raising entropy per token).\n")

    print("[1] Fetching UD token streams...")
    stats_by_lang: dict[str, dict] = {}
    for language in sorted(_UD_REGISTRY):
        result = compute_language_stats(language)
        if result:
            stats_by_lang[language] = result

    if len(stats_by_lang) < 4:
        print("Insufficient languages. Aborting.")
        return

    print("\n[2] Computing cluster means...")
    means = cluster_means(stats_by_lang)

    print("[3] Testing ordering invariant...")
    ordering = test_ordering(means)

    print_results(stats_by_lang, means, ordering)

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "probe": "lexical_entropy",
        "hypothesis": "agglutinative > fusional > analytic for Shannon entropy over surface form distribution",
        "invariant": "H(agglutinative) > H(fusional) > H(analytic)",
        "language_stats": stats_by_lang,
        "cluster_means": means,
        "ordering_test": ordering,
    }
    out_path = ARTIFACT_DIR / "lexical_entropy_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()

