"""Sentence-level k_eff compression trajectory probe.

For a given sentence, compute how parse ambiguity collapses token by token.
At each position i, we have seen tokens 0..i. We measure the structural
signal gap at that prefix length vs a shuffled version of the same prefix.

signal_gap(i) = how much information has been locked in by token i.

DCP predicts:
  - Case-dominant languages: gap rises EARLY (morpheme fires with its noun)
  - Agreement-dominant: gap rises at the VERB position (mid-sentence)
  - Word-order-dominant: gap rises LATE (at/after the final argument)

If trajectories differ in shape across typological clusters (not just level),
that's evidence that the TIMING claim in DCP is real, not just the final value.

Usage:
    python core/probes/sentence_trajectory_probe.py
"""
from __future__ import annotations

import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DATASET_ROOT = REPO_ROOT / "domains" / "language" / "data" / "datasets"

from domains.language.feature_extraction.structural_vector import (
    StructuralVectorExtractor,
    vector_distance,
)

# ---------------------------------------------------------------------------
# UD sentence fetcher — pulls real sentences from Universal Dependencies
# These are proper full sentences (15-35 tokens) unlike construction maps
# ---------------------------------------------------------------------------

_UD_SENTENCE_REGISTRY: dict[str, tuple[str, str, str]] = {
    "finnish":  ("UD_Finnish-TDT",    "fi_tdt",   "dev"),
    "spanish":  ("UD_Spanish-GSD",    "es_gsd",   "dev"),
    "mandarin": ("UD_Chinese-GSD",    "zh_gsd",   "dev"),
    "english":  ("UD_English-EWT",    "en_ewt",   "dev"),
    "japanese": ("UD_Japanese-GSD",   "ja_gsd",   "dev"),
    "hindi":    ("UD_Hindi-HDTB",     "hi_hdtb",  "dev"),
    "arabic":   ("UD_Arabic-PADT",    "ar_padt",  "dev"),
    "korean":   ("UD_Korean-GSD",     "ko_gsd",   "dev"),
}

_UD_TEMPLATE = (
    "https://raw.githubusercontent.com/UniversalDependencies"
    "/{repo}/{branch}/{lang}-ud-{split}.conllu"
)


def _fetch_ud_sentences(language: str, n: int = 20, min_tokens: int = 15) -> list[dict]:
    """
    Download UD CoNLL-U data and extract sentence texts from # text = lines.
    Returns list of records with {"text": sentence_text, "language": language}.
    Tries both main and master branches.
    """
    if language not in _UD_SENTENCE_REGISTRY:
        return []
    repo, lang, split = _UD_SENTENCE_REGISTRY[language]
    for branch in ("main", "master"):
        url = _UD_TEMPLATE.format(repo=repo, branch=branch, lang=lang, split=split)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Helix-Research/1.0 (sentence_trajectory_probe.py)"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            sentences = []
            for line in raw.splitlines():
                if line.startswith("# text = "):
                    text = line[len("# text = "):].strip()
                    tokens = text.split()
                    if len(tokens) >= min_tokens:
                        sentences.append({"text": text, "language": language})
                    if len(sentences) >= n:
                        break
            if sentences:
                print(f"  UD fetch OK: {len(sentences)} sentences ≥{min_tokens} tokens for {language}")
                return sentences
        except Exception:
            pass
    print(f"  UD fetch failed for {language} — falling back to construction map")
    return []


# ---------------------------------------------------------------------------
# Pick one representative language per typological cluster
# ---------------------------------------------------------------------------
REPRESENTATIVES = {
    "case_dominant":     "finnish",    # k_eff 1.52, clear case
    "agreement_dominant": "spanish",   # k_eff 1.79, clear agreement
    "word_order":        "mandarin",   # k_eff 2.75, pure word order
}

# How many tokens to sample per prefix position (we draw from all records)
MAX_RECORDS = 16
SHUFFLE_TRIALS = 12


def _vector_gap(real_records: list[dict], rng_seed: int, lang: str) -> float:
    """Signal gap between real records and one shuffled version."""
    extractor = StructuralVectorExtractor(language=lang)
    real_summary = extractor.summarize(real_records)

    import random
    rng = random.Random(rng_seed)
    token_pool = [
        t for rec in real_records
        for t in str(rec.get("text", "")).split()
    ]
    rng.shuffle(token_pool)

    cursor = 0
    shuffled = []
    for rec in real_records:
        length = max(len(str(rec.get("text", "")).split()), 1)
        if cursor + length > len(token_pool):
            rng.shuffle(token_pool)
            cursor = 0
        shuffled.append({**rec, "text": " ".join(token_pool[cursor:cursor + length])})
        cursor += length

    null_summary = extractor.summarize(shuffled)
    return vector_distance(real_summary["centroid"], null_summary["centroid"])


def compute_trajectory(language: str, corpus: str) -> dict:
    """Compute signal_gap as a function of prefix length (in tokens).

    Strategy: prefer real UD treebank sentences (15+ tokens) for meaningful
    trajectory shapes. Falls back to construction map if UD fetch fails.
    """
    # Try UD sentences first — these are proper full sentences
    records = _fetch_ud_sentences(language, n=MAX_RECORDS, min_tokens=12)

    # Fall back to construction map
    if not records:
        from domains.language.ingestion.corpus_loader import CorpusLoader
        loader = CorpusLoader()
        records = loader.load_records(language=language, corpus=corpus)
    if not records:
        return {"error": "no_records"}

    records = records[:MAX_RECORDS]

    # Find the range of prefix lengths to probe
    all_lengths = [len(str(r.get("text", "")).split()) for r in records]
    max_len = max(all_lengths) if all_lengths else 1
    # Probe at 20%, 40%, 60%, 80%, 100% of max length
    positions = [
        max(1, int(max_len * pct))
        for pct in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    ]
    # Remove duplicates while preserving order
    seen = set()
    positions = [p for p in positions if not (p in seen or seen.add(p))]

    trajectory = []
    for pos in positions:
        # Truncate each record to the first `pos` tokens
        prefix_records = []
        for rec in records:
            tokens = str(rec.get("text", "")).split()
            prefix_text = " ".join(tokens[:pos]) if tokens else ""
            if prefix_text.strip():
                prefix_records.append({**rec, "text": prefix_text})

        if not prefix_records:
            continue

        # Average signal_gap across multiple shuffle trials
        gaps = []
        for seed in range(SHUFFLE_TRIALS):
            try:
                gap = _vector_gap(prefix_records, rng_seed=seed * 37 + pos, lang=language)
                gaps.append(gap)
            except Exception:
                pass

        mean_gap = round(sum(gaps) / len(gaps), 5) if gaps else 0.0
        # Fraction of sentence revealed: 0=nothing, 1=full
        frac = round(pos / max_len, 3)
        trajectory.append({"position": pos, "fraction": frac, "signal_gap": mean_gap})

    # Compute the compression curve shape:
    # - Early compression: most gap gained in first 40% of sentence
    # - Late compression: most gap gained in last 40% of sentence
    if len(trajectory) >= 4:
        total_gain = trajectory[-1]["signal_gap"] - trajectory[0]["signal_gap"]
        midpoint = len(trajectory) // 2
        early_gain = trajectory[midpoint]["signal_gap"] - trajectory[0]["signal_gap"]
        early_fraction = round(early_gain / total_gain, 3) if total_gain > 0 else 0.5
    else:
        early_fraction = None

    return {
        "language": language,
        "max_token_length": max_len,
        "trajectory": trajectory,
        "final_gap": trajectory[-1]["signal_gap"] if trajectory else 0.0,
        "initial_gap": trajectory[0]["signal_gap"] if trajectory else 0.0,
        "total_gain": round(
            (trajectory[-1]["signal_gap"] - trajectory[0]["signal_gap"]) if len(trajectory) >= 2 else 0.0,
            5,
        ),
        "early_fraction": early_fraction,  # >0.5 = early compression, <0.5 = late
    }


def print_trajectory(result: dict) -> None:
    lang = result["language"]
    traj = result.get("trajectory", [])
    total = result.get("total_gain", 0)
    early = result.get("early_fraction")

    print(f"\n  {lang.upper()}")
    print(f"  {'─'*50}")
    print(f"  Max sentence length: {result.get('max_token_length')} tokens")
    print(f"  Initial gap: {result.get('initial_gap', 0):.4f}  Final: {result.get('final_gap', 0):.4f}  Total gain: {total:.4f}")
    if early is not None:
        timing = "EARLY" if early > 0.55 else "LATE" if early < 0.45 else "UNIFORM"
        print(f"  Early fraction (gain in first 50%): {early:.3f}  → compression timing: {timing}")
    print()
    print(f"  {'Frac':>6}  {'Gap':>8}  Bar")
    print(f"  {'─'*40}")
    max_gap = max((t["signal_gap"] for t in traj), default=0.01) or 0.01
    for t in traj:
        bar_len = int((t["signal_gap"] / max_gap) * 30)
        bar = "█" * bar_len
        print(f"  {t['fraction']:>6.2f}  {t['signal_gap']:>8.5f}  {bar}")


def main() -> None:
    print("Sentence-Level k_eff Compression Trajectory Probe")
    print("━" * 64)
    print("\nDCP timing prediction:")
    print("  case_dominant    → early compression (morpheme fires with each noun)")
    print("  agreement_dom    → mid-sentence compression (fires at verb)")
    print("  word_order       → late compression (fires at clause boundary)")

    results = {}
    for cluster, language in REPRESENTATIVES.items():
        corpus = f"{language}_construction_map"
        print(f"\n[{cluster}] Computing trajectory for {language}...")
        result = compute_trajectory(language, corpus)
        results[cluster] = result
        if "error" in result:
            print(f"  Error: {result['error']}")

    print("\n\n" + "═" * 64)
    print("  COMPRESSION TRAJECTORIES")
    print("═" * 64)

    for cluster, result in results.items():
        if "error" not in result:
            print_trajectory(result)

    # Summary comparison
    print("═" * 64)
    print("  TIMING COMPARISON")
    print("═" * 64)
    print(f"  {'Language':<16} {'Cluster':<22} {'Early frac':>12}  {'Prediction'}")
    print(f"  {'─'*62}")
    predictions = {
        "case_dominant": ("> 0.55", "early"),
        "agreement_dominant": ("0.45–0.55", "mid"),
        "word_order": ("< 0.45", "late"),
    }
    for cluster, result in results.items():
        if "error" in result:
            continue
        lang = result["language"]
        ef = result.get("early_fraction") or 0.0
        pred_range, pred_label = predictions[cluster]
        actual_timing = "EARLY" if ef > 0.55 else "LATE" if ef < 0.45 else "MID"
        match = "✓" if actual_timing.lower() == pred_label else "✗"
        print(f"  {lang:<16} {cluster:<22} {ef:>12.3f}  {pred_range}  {match}")

    print()

    # Write results
    out_path = REPO_ROOT / "domains" / "language" / "artifacts" / "sentence_trajectory_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Raw results → {out_path}")


if __name__ == "__main__":
    main()
