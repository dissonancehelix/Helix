"""Cross-domain discovery probe.

Three independent measurements, then cross-correlation:

  1. Grammar resolution k_eff  — from UD-calibrated fixtures (HHI of weights)
  2. Null model signal_gap     — from token-shuffling on construction maps (independent)
  3. Kuramoto transition zone  — from simulated oscillator synchronization (independent)

None of these three share a formula. If they converge on the same ordering or
the same numeric range, that's something the design didn't force.

Usage:
    python core/probes/discovery_probe.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DATASET_ROOT = REPO_ROOT / "domains" / "language" / "data" / "datasets"

from domains.language.research.grammar_resolution import analyze_grammar_resolution
from domains.language.research.null_model import NullModelProbe
from domains.language.ingestion.corpus_loader import CorpusLoader

LANGUAGES = [
    "english", "spanish", "french", "italian", "portuguese",
    "german", "russian", "mandarin", "japanese", "korean",
    "arabic", "hindi", "turkish", "finnish", "indonesian", "tagalog",
]


# ---------------------------------------------------------------------------
# Probe 1: Grammar resolution k_eff from calibrated fixtures
# ---------------------------------------------------------------------------

def probe_grammar_resolution() -> dict[str, dict]:
    results = {}
    for lang in LANGUAGES:
        path = DATASET_ROOT / f"grammar_resolution_{lang}.json"
        if not path.exists():
            continue
        fixture = json.loads(path.read_text(encoding="utf-8"))
        result = analyze_grammar_resolution(fixture)
        ud_diag = fixture.get("ud_diagnostics", {})
        results[lang] = {
            "mean_k_eff": result["mean_k_eff"],
            "dominant_mass": result["dominant_mass_top2"],
            "collapse_sharpness": result["collapse_sharpness"],
            "entropy": result["mean_entropy"],
            "supports_dcp": result["supports_dcp"],
            "ud_k_eff": ud_diag.get("ud_k_eff"),
            "compression_density": ud_diag.get("compression_density"),
            "dominant_rule": ud_diag.get("dominant_rule"),
            "case_density": ud_diag.get("case_density"),
            "agreement_density": ud_diag.get("agreement_density"),
            "order_rigidity": ud_diag.get("order_rigidity"),
        }
    return results


# ---------------------------------------------------------------------------
# Probe 2: Null model signal_gap (token-shuffle test, independent of fixtures)
# ---------------------------------------------------------------------------

def probe_null_model(seed: int = 42) -> dict[str, dict]:
    loader = CorpusLoader()
    results = {}
    for lang in LANGUAGES:
        corpus = f"{lang}_construction_map"
        try:
            records = loader.load_records(language=lang, corpus=corpus)
        except Exception as exc:
            results[lang] = {"error": str(exc)}
            continue
        if not records:
            results[lang] = {"error": "no_records"}
            continue
        probe = NullModelProbe(language=lang, seed=seed, n_trials=24)
        out = probe.evaluate(records)
        results[lang] = {
            "signal_gap": out["signal_gap"],
            "frame_gap": out["frame_gap"],
            "confidence": out["confidence"],
            "passes": out["passes"],
        }
    return results


# ---------------------------------------------------------------------------
# Probe 3: Kuramoto oscillator — k_eff across coupling strengths
# Pure Python implementation, no external dependencies.
# ---------------------------------------------------------------------------

def _kuramoto_r(n: int, K: float, steps: int, dt: float, seed: int) -> float:
    """Compute final order parameter r for N Kuramoto oscillators."""
    rng = random.Random(seed)
    # Natural frequencies from N(0,1) (Gaussian; K_c ≈ 1.596 for N→∞)
    omega = [rng.gauss(0, 1) for _ in range(n)]
    theta = [rng.uniform(0, 2 * math.pi) for _ in range(n)]

    for _ in range(steps):
        # Mean field: R exp(iΨ) = (1/N) Σ exp(iθⱼ)
        re = sum(math.cos(t) for t in theta) / n
        im = sum(math.sin(t) for t in theta) / n
        r_field = math.sqrt(re ** 2 + im ** 2)
        psi = math.atan2(im, re)
        # dθᵢ/dt = ωᵢ + K·r·sin(Ψ - θᵢ)
        theta = [
            theta[i] + dt * (omega[i] + K * r_field * math.sin(psi - theta[i]))
            for i in range(n)
        ]

    re = sum(math.cos(t) for t in theta) / n
    im = sum(math.sin(t) for t in theta) / n
    return math.sqrt(re ** 2 + im ** 2)


def probe_kuramoto(
    n: int = 50,
    k_values: list[float] | None = None,
    steps: int = 2000,
    dt: float = 0.02,
    seed: int = 42,
) -> dict[str, object]:
    """Sweep K and record r(K) and derived k_eff_osc(K)."""
    if k_values is None:
        k_values = [round(0.5 + 0.25 * i, 2) for i in range(20)]  # 0.5 to 5.25

    sweep = []
    for K in k_values:
        r = _kuramoto_r(n, K, steps, dt, seed)
        # k_eff_osc: measure of trajectory concentration using HHI on (r, 1-r) split.
        # r² = fraction of "coherent state" weight
        # (1-r)² ≈ fraction of incoherent residual
        # k_eff = 1 / (r² + (1-r)²) — ranges from 1 (fully locked or fully incoherent) to 2 (equal split)
        hhi = r ** 2 + (1 - r) ** 2
        k_eff_osc = round(1.0 / hhi if hhi > 0 else 1.0, 4)
        sweep.append({"K": K, "r": round(r, 4), "k_eff_osc": k_eff_osc})

    # Find the transition zone: where r moves from < 0.2 to > 0.6
    low_K = None
    high_K = None
    for entry in sweep:
        if entry["r"] > 0.2 and low_K is None:
            low_K = entry["K"]
        if entry["r"] > 0.6 and high_K is None:
            high_K = entry["K"]

    # Find K_c (analytic estimate for Lorentzian/Gaussian mixed)
    # For Gaussian ω ~ N(0,1): K_c ≈ 2/sqrt(2π) × sqrt(π) ≈ 2.0 (Strogatz 2000)
    # For this simulation K_c is empirically around 1.6-2.0

    # k_eff in the transition zone (language overlap region)
    transition_k_effs = [
        entry["k_eff_osc"]
        for entry in sweep
        if entry["r"] > 0.15 and entry["r"] < 0.85
    ]

    return {
        "n_oscillators": n,
        "sweep": sweep,
        "transition_low_K": low_K,
        "transition_high_K": high_K,
        "transition_k_eff_range": [
            round(min(transition_k_effs), 4) if transition_k_effs else None,
            round(max(transition_k_effs), 4) if transition_k_effs else None,
        ],
    }


# ---------------------------------------------------------------------------
# Cross-correlation analysis
# ---------------------------------------------------------------------------

def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return round(num / (sx * sy), 4) if sx * sy > 0 else float("nan")


def cross_correlate(
    gr_results: dict[str, dict],
    nm_results: dict[str, dict],
) -> dict[str, object]:
    common = [
        lang for lang in LANGUAGES
        if lang in gr_results and lang in nm_results
        and "error" not in nm_results[lang]
        and gr_results[lang].get("ud_k_eff") is not None
    ]

    ud_k_effs = [gr_results[lang]["ud_k_eff"] for lang in common]
    gr_k_effs = [gr_results[lang]["mean_k_eff"] for lang in common]
    signal_gaps = [nm_results[lang]["signal_gap"] for lang in common]
    compressions = [gr_results[lang]["compression_density"] for lang in common]

    # Spearman rank correlation (robust to non-linearity)
    def rank(xs: list[float]) -> list[float]:
        sorted_idx = sorted(range(len(xs)), key=lambda i: xs[i])
        ranks = [0.0] * len(xs)
        for rank_pos, idx in enumerate(sorted_idx):
            ranks[idx] = float(rank_pos + 1)
        return ranks

    ud_ranks = rank(ud_k_effs)
    gap_ranks = rank(signal_gaps)
    comp_ranks = rank(compressions)

    return {
        "languages": common,
        "n": len(common),
        "pearson_ud_k_eff_vs_signal_gap": _pearson(ud_k_effs, signal_gaps),
        "pearson_ud_k_eff_vs_compression": _pearson(ud_k_effs, compressions),
        "spearman_ud_k_eff_vs_signal_gap": _pearson(ud_ranks, gap_ranks),
        "spearman_compression_vs_signal_gap": _pearson(comp_ranks, gap_ranks),
        "per_language": {
            lang: {
                "ud_k_eff": gr_results[lang]["ud_k_eff"],
                "gr_mean_k_eff": gr_results[lang]["mean_k_eff"],
                "null_signal_gap": nm_results[lang].get("signal_gap"),
                "compression_density": gr_results[lang]["compression_density"],
                "dominant_rule": gr_results[lang]["dominant_rule"],
            }
            for lang in common
        },
    }


# ---------------------------------------------------------------------------
# Cluster analysis
# ---------------------------------------------------------------------------

def cluster_analysis(gr_results: dict[str, dict]) -> dict[str, object]:
    """Measure within-vs-across family variance for k_eff."""
    # Typological families
    families = {
        "case_dominant":    ["hindi", "russian", "arabic", "finnish", "turkish", "german"],
        "agreement_dominant": ["french", "spanish", "italian", "english"],
        "word_order":       ["japanese", "mandarin", "korean", "indonesian", "portuguese", "tagalog"],
    }

    family_k_effs: dict[str, list[float]] = {}
    for family, members in families.items():
        vals = [
            gr_results[lang]["ud_k_eff"]
            for lang in members
            if lang in gr_results and gr_results[lang].get("ud_k_eff") is not None
        ]
        family_k_effs[family] = vals

    def mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    def variance(xs: list[float]) -> float:
        if len(xs) < 2:
            return 0.0
        m = mean(xs)
        return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)

    all_vals = [v for vals in family_k_effs.values() for v in vals]
    grand_mean = mean(all_vals)
    total_variance = variance(all_vals)

    within_variances = {f: variance(v) for f, v in family_k_effs.items()}
    mean_within = mean(list(within_variances.values()))

    family_means = {f: round(mean(v), 4) for f, v in family_k_effs.items()}
    between_variance = variance([family_means[f] for f in family_means])

    # F-ratio: between-group / within-group
    f_ratio = round(between_variance / mean_within, 4) if mean_within > 0 else float("inf")

    return {
        "grand_mean_k_eff": round(grand_mean, 4),
        "total_variance": round(total_variance, 4),
        "family_means": family_means,
        "within_family_variance": {f: round(v, 4) for f, v in within_variances.items()},
        "between_family_variance": round(between_variance, 4),
        "mean_within_variance": round(mean_within, 4),
        "f_ratio": f_ratio,
        "family_k_effs": {f: [round(v, 4) for v in vals] for f, vals in family_k_effs.items()},
    }


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print(f"\n{'═'*64}")
    print(f"  {title}")
    print(f"{'═'*64}")


def print_findings(
    gr: dict,
    nm: dict,
    kur: dict,
    corr: dict,
    clusters: dict,
) -> None:
    print_section("PROBE 1 — Grammar Resolution k_eff (UD-calibrated)")
    print(f"  {'Language':<14} {'GR k_eff':>8} {'UD k_eff':>8} {'Entropy':>8} {'Dom Rule':<12} {'DCP':>5}")
    print(f"  {'─'*62}")
    sorted_langs = sorted(gr.keys(), key=lambda l: gr[l].get("ud_k_eff") or 99)
    for lang in sorted_langs:
        r = gr[lang]
        print(
            f"  {lang:<14} {r['mean_k_eff']:>8.3f} {(r['ud_k_eff'] or 0.0):>8.3f}"
            f" {r['entropy']:>8.4f} {(r['dominant_rule'] or '?'):<12} {str(r['supports_dcp']):>5}"
        )

    print_section("PROBE 2 — Null Model Signal Gap (token-shuffle, independent)")
    print(f"  {'Language':<14} {'Signal Gap':>12} {'Frame Gap':>10} {'Passes':>8}")
    print(f"  {'─'*48}")
    sorted_by_gap = sorted(
        [l for l in nm if "error" not in nm[l]],
        key=lambda l: nm[l]["signal_gap"],
        reverse=True,
    )
    for lang in sorted_by_gap:
        r = nm[lang]
        print(
            f"  {lang:<14} {r['signal_gap']:>12.4f} {r['frame_gap']:>10.4f} {str(r['passes']):>8}"
        )

    print_section("PROBE 3 — Kuramoto Oscillator Transition Zone")
    print(f"  N oscillators: {kur['n_oscillators']}")
    print(f"  Transition zone K: [{kur['transition_low_K']}, {kur['transition_high_K']}]")
    print(f"  k_eff_osc in transition: {kur['transition_k_eff_range']}")
    print(f"\n  Language k_eff range:  [{min(r['ud_k_eff'] for r in gr.values() if r.get('ud_k_eff')):.2f},"
          f" {max(r['ud_k_eff'] for r in gr.values() if r.get('ud_k_eff')):.2f}]")
    print()
    print(f"  K sweep sample:")
    for entry in kur["sweep"][::2]:
        bar = "█" * int(entry["r"] * 20)
        print(f"    K={entry['K']:4.2f}  r={entry['r']:.3f}  k_eff_osc={entry['k_eff_osc']:.3f}  {bar}")

    print_section("CROSS-CORRELATION — UD k_eff vs Null Model Signal Gap")
    print(f"  n = {corr['n']} languages")
    print(f"  Pearson  (ud_k_eff × signal_gap):      {corr['pearson_ud_k_eff_vs_signal_gap']:>8.4f}")
    print(f"  Spearman (ud_k_eff × signal_gap):      {corr['spearman_ud_k_eff_vs_signal_gap']:>8.4f}")
    print(f"  Pearson  (ud_k_eff × compression):     {corr['pearson_ud_k_eff_vs_compression']:>8.4f}")
    print(f"  Spearman (compression × signal_gap):   {corr['spearman_compression_vs_signal_gap']:>8.4f}")
    print()
    print(f"  {'Language':<14} {'UD k_eff':>10} {'Signal Gap':>12} {'Dom Rule':<14}")
    print(f"  {'─'*54}")
    sorted_corr = sorted(corr["per_language"], key=lambda l: corr["per_language"][l]["ud_k_eff"])
    for lang in sorted_corr:
        r = corr["per_language"][lang]
        print(
            f"  {lang:<14} {r['ud_k_eff']:>10.3f} {(r['null_signal_gap'] or 0.0):>12.4f}"
            f" {(r['dominant_rule'] or '?'):<14}"
        )

    print_section("CLUSTER ANALYSIS — k_eff Variance Within/Between Typological Families")
    print(f"  Family means:       {clusters['family_means']}")
    print(f"  Within variance:    {clusters['within_family_variance']}")
    print(f"  Between variance:   {clusters['between_family_variance']:.4f}")
    print(f"  Mean within:        {clusters['mean_within_variance']:.4f}")
    print(f"  F-ratio (between/within): {clusters['f_ratio']:.4f}")
    print()
    for family, vals in clusters["family_k_effs"].items():
        bar_mean = clusters["family_means"][family]
        print(f"  {family:<24} mean={bar_mean:.3f}  vals={vals}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Helix Discovery Probe — three independent measurements")
    print("━" * 64)

    print("\n[1/4] Running grammar resolution analysis on all 16 fixtures...")
    gr = probe_grammar_resolution()
    print(f"      {len(gr)} languages loaded.")

    print("\n[2/4] Running null model probes (token-shuffle × 24 trials per language)...")
    nm = probe_null_model()
    ok = sum(1 for v in nm.values() if "error" not in v)
    print(f"      {ok}/{len(nm)} languages completed.")

    print("\n[3/4] Running Kuramoto oscillator sweep (N=50, K=0.5–5.25)...")
    kur = probe_kuramoto(n=50, steps=2000, dt=0.02)
    print(f"      Transition zone: K=[{kur['transition_low_K']}, {kur['transition_high_K']}]")

    print("\n[4/4] Cross-correlating measurements...")
    corr = cross_correlate(gr, nm)
    clusters = cluster_analysis(gr)

    print_findings(gr, nm, kur, corr, clusters)

    # Write raw results for further analysis
    out_path = REPO_ROOT / "domains" / "language" / "artifacts" / "discovery_probe_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({
            "grammar_resolution": gr,
            "null_model": nm,
            "kuramoto": kur,
            "cross_correlation": corr,
            "cluster_analysis": clusters,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n  Raw results → {out_path}")


if __name__ == "__main__":
    main()
