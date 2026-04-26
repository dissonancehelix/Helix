"""
branching_detector.py
Labs: inhabited_interiority
Purpose: Scan all fixtures and identify cases where branching occurs or N collapses.
         Branching is fatal to singular self-continuity. If two future streams inherit
         the same present self equally, the original self cannot be numerically identical
         to both. Both may be legitimate descendants. Neither is uniquely the same
         ongoing ownership-stream.

Usage:
    python branching_detector.py
    python branching_detector.py --severity critical
    python branching_detector.py --show-all
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


class BranchingCase:
    def __init__(
        self,
        case_id: str,
        name: str,
        source: str,
        n_score: float | None,
        branching_flag: bool | None,
        verdict: str,
        description: str,
        notes: str,
        breaks: list[str],
    ):
        self.case_id = case_id
        self.name = name
        self.source = source
        self.n_score = n_score
        self.branching_flag = branching_flag
        self.verdict = verdict
        self.description = description
        self.notes = notes
        self.breaks = breaks

    @property
    def severity(self) -> str:
        if self.branching_flag is True and self.n_score == 0.0:
            return "critical"
        if self.branching_flag is True:
            return "high"
        if self.n_score is not None and self.n_score < 0.5:
            return "medium"
        return "low"

    @property
    def branching_summary(self) -> str:
        parts = []
        if self.branching_flag is True:
            parts.append("branching_occurs=true")
        if self.n_score == 0.0:
            parts.append("N=0.0 (collapsed)")
        elif self.n_score is not None and self.n_score < 1.0:
            parts.append(f"N={self.n_score:.2f} (degraded)")
        elif self.n_score is None:
            parts.append("N=null (unresolvable)")
        return " | ".join(parts) if parts else "no branching detected"


def extract_n_score(case: dict) -> float | None:
    """Try both field_case components and continuity_case continuity_components."""
    # field_case schema
    comps = case.get("components", {})
    if "N" in comps:
        return comps["N"]
    # continuity_case schema
    cont_comps = case.get("continuity_components", {})
    if "N" in cont_comps:
        return cont_comps["N"]
    return None


def extract_branching_flag(case: dict) -> bool | None:
    # transfer_case schema
    val = case.get("branching_occurs")
    return val


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


def detect_branching(cases: list[dict]) -> list[BranchingCase]:
    detected = []
    for case in cases:
        n_score = extract_n_score(case)
        branching_flag = extract_branching_flag(case)

        # Include if: N=0, N<1 and not 1.0 explicitly, branching_flag=True, or verdict is branching
        verdict = case.get("verdict", "") or case.get("classification", "")
        is_branching_verdict = verdict in (
            "branching_descendants",
            "branching_descendants_only",
        )

        if (
            n_score == 0.0
            or branching_flag is True
            or is_branching_verdict
            or (n_score is not None and n_score < 1.0 and n_score > 0.0)
        ):
            detected.append(BranchingCase(
                case_id=case.get("id", "?"),
                name=case.get("name", case.get("description", "?")[:60]),
                source=case.get("_source_file", "?"),
                n_score=n_score,
                branching_flag=branching_flag,
                verdict=verdict,
                description=case.get("description", "")[:100],
                notes=case.get("notes", ""),
                breaks=case.get("breaks_preserved", []),
            ))
    return detected


def severity_rank(s: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(s, 4)


def print_report(cases: list[BranchingCase], severity_filter: str | None, show_all: bool) -> None:
    print("\n" + "=" * 80)
    print("BRANCHING DETECTOR — Non-branching continuity (N) analysis")
    print("Branching is fatal to singular self-continuity.")
    print("If two streams inherit the same self equally, N=0, and no singular heir exists.")
    print("=" * 80)
    print()

    if severity_filter:
        cases = [c for c in cases if c.severity == severity_filter]

    cases_sorted = sorted(cases, key=lambda c: severity_rank(c.severity))

    if not cases_sorted:
        print("No branching cases detected with current filters.")
        return

    severity_groups: dict[str, list[BranchingCase]] = {}
    for case in cases_sorted:
        severity_groups.setdefault(case.severity, []).append(case)

    for sev in ["critical", "high", "medium", "low"]:
        group = severity_groups.get(sev, [])
        if not group:
            continue
        print(f"  ── SEVERITY: {sev.upper()} ({len(group)} cases)")
        print()
        for case in group:
            print(f"     [{case.case_id}]  {case.name}")
            print(f"       Branching status  : {case.branching_summary}")
            print(f"       Classification    : {case.verdict or 'not classified'}")
            if show_all:
                print(f"       Source            : {case.source}")
                if case.description:
                    print(f"       Description       : {case.description}")
                if case.notes:
                    print(f"       Notes             : {case.notes[:100]}")
            for b in case.breaks:
                print(f"       ✗ BREAK: {b[:110]}{'...' if len(b) > 110 else ''}")
            print()

    print("─" * 80)
    counts = {sev: len(severity_groups.get(sev, [])) for sev in ["critical", "high", "medium", "low"]}
    print("Severity summary:")
    for sev, count in counts.items():
        if count:
            print(f"  {sev}: {count}")
    print()
    print("Invariant: Inhabited ownership-stream cannot branch without losing numerical singularity.")
    print("           pattern continuity can branch")
    print("           symbolic continuity can branch")
    print("           social identity can branch")
    print("           inhabited ownership-stream cannot")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect branching failures across all fixtures. Branching = N=0 = singular self-continuity impossible."
    )
    parser.add_argument("--severity", "-s", metavar="LEVEL",
                        choices=["critical", "high", "medium", "low"],
                        help="Filter to one severity level.")
    parser.add_argument("--show-all", "-a", action="store_true",
                        help="Show source file, description, and notes for each case.")
    args = parser.parse_args()

    raw_cases = load_all_cases()
    detected = detect_branching(raw_cases)
    print_report(detected, args.severity, args.show_all)


if __name__ == "__main__":
    main()
