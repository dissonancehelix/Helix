"""
Cross-Probe Analysis — 03_engines/analysis/cross_probe_analysis.py

Compare and correlate results across multiple probe instruments.
Computes per-domain coverage, per-probe signal statistics, and
Pearson correlations of mean signal per shared domain.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all_probe_results(
    artifacts_root: str | Path | None = None,
) -> dict[str, list[dict]]:
    """
    Scan execution/artifacts/probes/ and return {probe_name: [result_dicts]}.

    Each result dict is the probe_result.json enriched with lab_name from
    the run_manifest.json when available.
    """
    _root = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
    if artifacts_root is None:
        artifacts_root = _root / "execution/artifacts"
    else:
        artifacts_root = Path(artifacts_root)

    probes_root = artifacts_root / "probes"
    results: dict[str, list[dict]] = {}

    if not probes_root.exists():
        return results

    for probe_dir in sorted(probes_root.iterdir()):
        if not probe_dir.is_dir():
            continue
        probe_name = probe_dir.name
        runs: list[dict] = []

        for run_dir in sorted(probe_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            result_path = run_dir / "probe_result.json"
            if not result_path.exists():
                continue
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue

            # Enrich with manifest fields
            manifest_path = run_dir / "run_manifest.json"
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    result.setdefault("lab_name", manifest.get("lab_name", ""))
                    result.setdefault("run_id", manifest.get("run_id", run_dir.name))
                    result.setdefault("probe_version", manifest.get("probe_version", "1.0.0"))
                except Exception:  # noqa: BLE001
                    pass

            runs.append(result)

        if runs:
            results[probe_name] = runs

    return results


# ---------------------------------------------------------------------------
# Domain coverage
# ---------------------------------------------------------------------------

def domain_coverage(
    results_by_probe: dict[str, list[dict]],
) -> dict[str, dict]:
    """
    Return {domain: {probes: [...], run_count: N, pass_rate: float}} for
    all domains observed across all probes.
    """
    domain_map: dict[str, dict] = {}

    for probe_name, runs in results_by_probe.items():
        for run in runs:
            domain = run.get("domain") or run.get("lab_name") or "unknown"
            if domain not in domain_map:
                domain_map[domain] = {"probes": [], "runs": 0, "passed": 0}
            entry = domain_map[domain]
            if probe_name not in entry["probes"]:
                entry["probes"].append(probe_name)
            entry["runs"] += 1
            if run.get("passed"):
                entry["passed"] += 1

    coverage = {}
    for domain, data in sorted(domain_map.items()):
        runs = data["runs"]
        passed = data["passed"]
        coverage[domain] = {
            "probes": sorted(data["probes"]),
            "run_count": runs,
            "pass_rate": round(passed / runs, 4) if runs > 0 else 0.0,
        }
    return coverage


# ---------------------------------------------------------------------------
# Per-probe signal statistics
# ---------------------------------------------------------------------------

def probe_signal_stats(runs: list[dict]) -> dict:
    """
    Return {mean_signal, min_signal, max_signal, pass_rate, run_count,
            domains_observed} for a list of probe runs.
    """
    if not runs:
        return {
            "run_count": 0, "pass_rate": 0.0,
            "mean_signal": 0.0, "min_signal": 0.0, "max_signal": 0.0,
            "domains_observed": [],
        }

    signals = []
    passed = 0
    domains: list[str] = []

    for r in runs:
        s = r.get("signal") or r.get("signal_strength") or 0.0
        try:
            signals.append(float(s))
        except (TypeError, ValueError):
            signals.append(0.0)
        if r.get("passed"):
            passed += 1
        domain = r.get("domain") or r.get("lab_name") or ""
        if domain and domain not in domains:
            domains.append(domain)

    n = len(signals)
    mean_s = sum(signals) / n if n else 0.0

    return {
        "run_count": n,
        "pass_rate": round(passed / n, 4) if n > 0 else 0.0,
        "mean_signal": round(mean_s, 6),
        "min_signal": round(min(signals), 6),
        "max_signal": round(max(signals), 6),
        "domains_observed": sorted(domains),
    }


# ---------------------------------------------------------------------------
# Pearson correlation
# ---------------------------------------------------------------------------

def probe_signal_correlation(
    runs_a: list[dict],
    runs_b: list[dict],
) -> dict:
    """
    Compute Pearson correlation of mean signal per shared domain between
    two probe run sets.

    Returns {pearson_r, shared_domains, n_shared, interpretation}.
    """
    def _domain_mean(runs: list[dict]) -> dict[str, float]:
        by_domain: dict[str, list[float]] = {}
        for r in runs:
            d = r.get("domain") or r.get("lab_name") or "unknown"
            s = r.get("signal") or r.get("signal_strength") or 0.0
            try:
                s = float(s)
            except (TypeError, ValueError):
                s = 0.0
            by_domain.setdefault(d, []).append(s)
        return {d: sum(vs) / len(vs) for d, vs in by_domain.items()}

    means_a = _domain_mean(runs_a)
    means_b = _domain_mean(runs_b)

    shared = sorted(set(means_a) & set(means_b))
    n = len(shared)

    if n < 2:
        return {
            "pearson_r": None,
            "shared_domains": shared,
            "n_shared": n,
            "interpretation": "insufficient shared domains for correlation (need ≥ 2)",
        }

    xs = [means_a[d] for d in shared]
    ys = [means_b[d] for d in shared]

    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))

    if sx == 0 or sy == 0:
        pearson_r = None
        interp = "zero variance in one or both probes — correlation undefined"
    else:
        pearson_r = round(cov / (sx * sy), 4)
        if pearson_r is not None:
            if pearson_r > 0.7:
                interp = "strong positive correlation — probes co-detect similar domain structure"
            elif pearson_r > 0.3:
                interp = "moderate positive correlation"
            elif pearson_r > -0.3:
                interp = "weak / no correlation — probes capture independent signals"
            else:
                interp = "negative correlation — probes diverge across domains"
        else:
            interp = "undefined"

    return {
        "pearson_r": pearson_r,
        "shared_domains": shared,
        "n_shared": n,
        "interpretation": interp,
    }


# ---------------------------------------------------------------------------
# Full analysis run
# ---------------------------------------------------------------------------

def run_cross_probe_analysis(
    artifacts_root: str | Path | None = None,
    probe_filter: list[str] | None = None,
    lab_filter: str | None = None,
    verbose: bool = True,
) -> dict:
    """
    Run a complete cross-probe analysis.

    Parameters
    ----------
    artifacts_root  Path to execution/artifacts/ (default: auto-detect)
    probe_filter    If set, analyse only these probe names
    lab_filter      If set, restrict to runs from this lab (domain)
    verbose         Print summary to stdout

    Returns
    -------
    dict with keys:
        probes_analyzed, probe_stats, domain_coverage,
        correlation_matrix, summary
    """
    _root = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
    if artifacts_root is None:
        artifacts_root = _root / "execution/artifacts"

    if verbose:
        print("[cross-probe-analysis] Loading probe results …")

    all_results = load_all_probe_results(artifacts_root)

    # Apply filters
    if probe_filter:
        all_results = {p: r for p, r in all_results.items() if p in probe_filter}

    if lab_filter:
        filtered = {}
        for probe_name, runs in all_results.items():
            kept = [
                r for r in runs
                if (r.get("domain") or r.get("lab_name") or "") == lab_filter
            ]
            if kept:
                filtered[probe_name] = kept
        all_results = filtered

    probes_analyzed = sorted(all_results.keys())

    if verbose:
        print(f"[cross-probe-analysis] Probes: {probes_analyzed}")

    # Per-probe stats
    probe_stats = {
        p: probe_signal_stats(runs) for p, runs in all_results.items()
    }

    # Domain coverage
    coverage = domain_coverage(all_results)

    # Correlation matrix (all pairs)
    correlation_matrix: dict[str, dict] = {}
    for i, pa in enumerate(probes_analyzed):
        for pb in probes_analyzed[i + 1:]:
            pair_key = f"{pa} × {pb}"
            correlation_matrix[pair_key] = probe_signal_correlation(
                all_results[pa], all_results[pb]
            )

    # Summary
    total_runs = sum(s["run_count"] for s in probe_stats.values())
    overall_pass_rate = (
        sum(s["pass_rate"] * s["run_count"] for s in probe_stats.values()) / total_runs
        if total_runs > 0 else 0.0
    )

    summary = {
        "total_runs": total_runs,
        "overall_pass_rate": round(overall_pass_rate, 4),
        "probes_analyzed": len(probes_analyzed),
        "domains_covered": len(coverage),
        "correlation_pairs": len(correlation_matrix),
    }

    result = {
        "probes_analyzed": probes_analyzed,
        "probe_stats": probe_stats,
        "domain_coverage": coverage,
        "correlation_matrix": correlation_matrix,
        "summary": summary,
    }

    if verbose:
        print(f"\n{'='*55}")
        print("CROSS-PROBE ANALYSIS REPORT")
        print(f"{'='*55}")
        print(f"Probes:      {', '.join(probes_analyzed)}")
        print(f"Total runs:  {total_runs}")
        print(f"Pass rate:   {overall_pass_rate:.1%}")
        print(f"Domains:     {', '.join(coverage)}")
        print()
        for probe_name, stats in probe_stats.items():
            print(f"  [{probe_name}]  runs={stats['run_count']}  "
                  f"pass={stats['pass_rate']:.0%}  "
                  f"signal={stats['mean_signal']:.4f}  "
                  f"domains={stats['domains_observed']}")
        if correlation_matrix:
            print()
            for pair, corr in correlation_matrix.items():
                r = corr["pearson_r"]
                r_str = f"{r:.4f}" if r is not None else "N/A"
                print(f"  Correlation {pair}: r={r_str}  "
                      f"({corr['interpretation']})")
        print(f"{'='*55}\n")

    # Write report to execution/artifacts/
    artifacts_path = Path(artifacts_root)
    report_path = artifacts_path / "cross_probe_report.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if verbose:
        print(f"[cross-probe-analysis] Report written: {report_path}")

    return result
