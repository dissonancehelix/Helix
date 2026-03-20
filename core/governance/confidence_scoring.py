"""
Confidence Scoring — 03_engines/codex/atlas/confidence_scoring.py

Compute confidence class for an invariant from its run history.
"""

from __future__ import annotations
from typing import Any


def aggregate_run_results(run_results: list[dict]) -> dict[str, Any]:
    """
    Summarise a list of probe run result dicts.

    Returns:
        pass_rate, mean_signal, observed_domains, run_count
    """
    n = len(run_results)
    if n == 0:
        return {"pass_rate": 0.0, "mean_signal": 0.0, "observed_domains": [], "run_count": 0}

    n_passed = sum(1 for r in run_results if r.get("passed", False))
    signals = [float(r.get("signal", r.get("signal_strength", 0.0))) for r in run_results]
    domains: list[str] = []
    for r in run_results:
        d = r.get("domain", r.get("lab_name", "unknown"))
        if d and d not in domains:
            domains.append(d)

    return {
        "pass_rate": round(n_passed / n, 4),
        "mean_signal": round(sum(signals) / n, 4),
        "observed_domains": sorted(domains),
        "run_count": n,
    }


def score_confidence(
    observed_domains: list[str],
    pass_rate: float,
    mean_signal: float,
) -> str:
    """
    Assign a confidence class based on domain coverage and pass rate.

    | Domains | Pass Rate | Class       |
    |---------|-----------|-------------|
    | ≥4      | ≥90%      | Structural  |
    | ≥3      | ≥75%      | Verified    |
    | ≥2      | ≥50%      | Candidate   |
    | ≥1      | any       | Exploratory |
    """
    n = len(set(observed_domains))

    if n >= 4 and pass_rate >= 0.90:
        return "Structural"
    if n >= 3 and pass_rate >= 0.75:
        return "Verified"
    if n >= 2 and pass_rate >= 0.50:
        return "Candidate"
    return "Exploratory"
