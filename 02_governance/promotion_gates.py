"""
Promotion Gates — 02_governance/promotion_gates.py

Six-criterion Atlas promotion scaffold. Loaded by the promotion engine in 03_engines.
Each criterion function returns (passed: bool, reason: str).
"""

from __future__ import annotations


def criterion_domain_coverage(atlas_entry: dict) -> tuple[bool, str]:
    """Requires ≥3 distinct domains observed."""
    domains = atlas_entry.get("observed_in", [])
    n = len(set(domains))
    if n >= 3:
        return True, f"domain_coverage: {n} domains (≥3 required)"
    return False, f"domain_coverage: only {n} domain(s) — need ≥3"


def criterion_pass_rate(atlas_entry: dict) -> tuple[bool, str]:
    """Requires ≥75% pass rate."""
    rate = float(atlas_entry.get("pass_rate", 0.0))
    if rate >= 0.75:
        return True, f"pass_rate: {rate:.0%} (≥75% required)"
    return False, f"pass_rate: {rate:.0%} — need ≥75%"


def criterion_run_count(atlas_entry: dict) -> tuple[bool, str]:
    """Requires ≥3 independent probe runs."""
    count = int(atlas_entry.get("run_count", 0))
    if count >= 3:
        return True, f"run_count: {count} runs (≥3 required)"
    return False, f"run_count: {count} run(s) — need ≥3"


def criterion_signal_strength(atlas_entry: dict) -> tuple[bool, str]:
    """Requires mean signal > 0.3."""
    signal = float(atlas_entry.get("mean_signal", 0.0))
    if signal > 0.3:
        return True, f"signal_strength: mean={signal:.3f} (>0.3 required)"
    return False, f"signal_strength: mean={signal:.3f} — need >0.3"


def criterion_no_degradation(atlas_entry: dict) -> tuple[bool, str]:
    """Requires no NON_REPRODUCIBLE flag."""
    flag = atlas_entry.get("reproducibility_flag", "OK")
    if flag != "DEGRADED":
        return True, f"reproducibility: {flag}"
    return False, f"reproducibility: DEGRADED — non-reproducible runs detected"


def criterion_confidence_class(atlas_entry: dict) -> tuple[bool, str]:
    """Requires confidence class of Verified or Structural."""
    cls = atlas_entry.get("confidence", "Exploratory")
    if cls in ("Verified", "Structural"):
        return True, f"confidence_class: {cls}"
    return False, f"confidence_class: {cls} — need Verified or Structural"


ALL_CRITERIA = [
    criterion_domain_coverage,
    criterion_pass_rate,
    criterion_run_count,
    criterion_signal_strength,
    criterion_no_degradation,
    criterion_confidence_class,
]


def evaluate_promotion(atlas_entry: dict) -> dict:
    """
    Run all 6 criteria against an atlas entry.

    Returns:
        dict with keys: passed (bool), criteria (list of {name, passed, reason})
    """
    results = []
    all_passed = True

    for fn in ALL_CRITERIA:
        passed, reason = fn(atlas_entry)
        results.append({"name": fn.__name__, "passed": passed, "reason": reason})
        if not passed:
            all_passed = False

    return {"passed": all_passed, "criteria": results}
