"""
false_positive_scan.py
Labs: inhabited_interiority
Purpose: Scan all fixtures for cases where the theory might accidentally promote a
         non-phenomenal structure to conscious status. If the scan finds a false positive
         that the theory has not correctly rejected, the theory is broken.

         A false positive is: high structure_score + low A + verdict incorrectly = phenomenal_candidate.
         The scan does NOT look for confirmed false positives — it looks for cases where
         the theory's classification machinery might fail.

Usage:
    python false_positive_scan.py
    python false_positive_scan.py --risk high
    python false_positive_scan.py --show-what-it-has
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists()),
    Path(__file__).resolve().parent.parent.parent,
)
LAB_DIR = ROOT / "labs" / "inhabited_interiority"
FIXTURES_DIR = LAB_DIR / "fixtures"

SAFE_VERDICTS = {
    "false_positive_confirmed",
    "non_phenomenal",
    "demoted",
}

RISKY_FIELD_TYPES = {
    # These field types are most likely to be confused with phenomenal fields
    "symbolic_field",
    "operational_field",
    "action_field",
    "governance_field",
    "aesthetic_field",
    "export_field",
    "hybrid_agent_field",
}


def load_all_cases() -> list[dict]:
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if "id" in item:
                    item["_source_file"] = json_file.relative_to(LAB_DIR).as_posix()
                    cases.append(item)
        except Exception as e:
            print(f"  [warn] {json_file.name}: {e}", file=sys.stderr)
    return cases


def get_a_score(case: dict) -> float | None:
    comps = case.get("components", {})
    return comps.get("A")


def get_structure_score(case: dict) -> float:
    """Approximate structure score from non-A components or explicit structure_score."""
    if "structure_score" in case:
        return case["structure_score"]
    comps = case.get("components", {})
    # Average of U, D, T as a proxy for structure (not A, not F)
    vals = [comps.get(k) for k in ["U", "D", "T"] if comps.get(k) is not None]
    if not vals:
        return 0.5  # Default if no data
    return sum(vals) / len(vals)


def classify_risk(case: dict) -> str:
    """Assess how likely the theory is to accidentally promote this case."""
    verdict = case.get("verdict", "")
    if verdict in SAFE_VERDICTS:
        return "safe"

    a_score = get_a_score(case)
    structure_score = get_structure_score(case)
    phenomenal_candidate = case.get("phenomenal_candidate", False)
    field_type = case.get("field_type", "")

    # Already correctly flagged as a candidate with A > 0 — these are fine
    if phenomenal_candidate and a_score is not None and a_score > 0:
        return "expected_candidate"

    # Non-candidate with A > 0 unexpectedly — theory failure
    if not phenomenal_candidate and a_score is not None and a_score > 0:
        return "critical"

    # Non-candidate in a risky field type with high structure
    if not phenomenal_candidate and field_type in RISKY_FIELD_TYPES and structure_score > 0.7:
        return "high"

    # Non-candidate in risky type with medium structure
    if not phenomenal_candidate and field_type in RISKY_FIELD_TYPES:
        return "medium"

    # Non-candidate not yet classified
    if not phenomenal_candidate and verdict not in SAFE_VERDICTS and verdict != "":
        return "medium"

    return "low"


def print_report(cases: list[dict], risk_filter: str | None, show_what_it_has: bool) -> None:
    print("\n" + "=" * 80)
    print("FALSE POSITIVE SCAN — Theory firewall verification")
    print("Purpose: Confirm the theory correctly rejects non-phenomenal structures.")
    print("If the theory promotes any of these to consciousness, it is broken.")
    print("=" * 80)
    print()

    scan_results: dict[str, list[tuple[dict, str]]] = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "safe": [],
        "expected_candidate": [],
    }

    for case in cases:
        risk = classify_risk(case)
        scan_results[risk].append((case, risk))

    # Filter if requested
    if risk_filter:
        display_levels = [risk_filter]
    else:
        display_levels = ["critical", "high", "medium"]

    total_issues = sum(len(scan_results[r]) for r in ["critical", "high", "medium"])
    total_safe = len(scan_results["safe"])

    print(f"  Total cases scanned  : {sum(len(v) for v in scan_results.values())}")
    print(f"  Correctly classified : {total_safe}")
    print(f"  Issues found         : {total_issues}")
    print()

    for level in display_levels:
        group = scan_results[level]
        if not group:
            continue

        if level == "critical":
            print(f"  ══ CRITICAL — Theory failure: A > 0 for non-candidate ({len(group)} cases)")
        elif level == "high":
            print(f"  ── HIGH RISK — Risky field type with high structure ({len(group)} cases)")
        elif level == "medium":
            print(f"  ── MEDIUM RISK — Non-candidate without clear rejection ({len(group)} cases)")
        print()

        for case, _ in group:
            a_score = get_a_score(case)
            structure_score = get_structure_score(case)
            verdict = case.get("verdict", "unclassified")

            print(f"     [{case.get('id', '?')}]  {case.get('name', '?')}")
            print(f"       Field type        : {case.get('field_type', '?')}")
            print(f"       A (appearance)    : {a_score if a_score is not None else 'null'}")
            print(f"       Structure score   : {structure_score:.2f}")
            print(f"       Current verdict   : {verdict}")
            print(f"       Phenomenal cand.  : {case.get('phenomenal_candidate', '?')}")

            if level == "critical":
                print(f"       ⛔ THEORY FAILURE: A={a_score} > 0 but phenomenal_candidate=False")
                print(f"          This means the theory has assigned appearance-from-within")
                print(f"          to a case it classifies as non-phenomenal. Contradiction.")

            theory_fail = case.get("theory_failure_condition", "")
            if theory_fail:
                print(f"       Failure condition : {theory_fail[:100]}{'...' if len(theory_fail) > 100 else ''}")

            if show_what_it_has:
                what_it_has = case.get("what_it_does_have", [])
                if what_it_has:
                    print(f"       Legitimate props  : {', '.join(what_it_has[:4])}")

            why_fp = case.get("why_false_positive", "")
            if why_fp:
                print(f"       Why rejected      : {why_fp[:100]}{'...' if len(why_fp) > 100 else ''}")

            breaks = case.get("breaks_preserved", [])
            for b in breaks:
                print(f"       ✗ BREAK: {b[:100]}{'...' if len(b) > 100 else ''}")

            print()

    print("─" * 80)
    if total_issues == 0:
        print("✓ False positive scan passed — no critical or high-risk classification failures.")
    else:
        print(f"⚠ {total_issues} issues require attention.")
    print()
    print("Anti-bloat rule: Field-like organization is not automatically phenomenal.")
    print("The hardest false positive is the LLM persona — it produces first-person output")
    print("that is behaviorally indistinguishable from consciousness report. A = 0 must hold.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan for false positives — cases where the theory might accidentally promote non-phenomenal structures."
    )
    parser.add_argument("--risk", "-r", metavar="LEVEL",
                        choices=["critical", "high", "medium", "low", "safe"],
                        help="Filter to one risk level.")
    parser.add_argument("--show-what-it-has", "-w", action="store_true",
                        help="Show legitimate field properties that each false positive does have.")
    args = parser.parse_args()

    cases = load_all_cases()
    if not cases:
        print("No fixtures found.", file=sys.stderr)
        sys.exit(1)

    print_report(cases, args.risk, args.show_what_it_has)


if __name__ == "__main__":
    main()
