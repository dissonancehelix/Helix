"""
run_domain_matrix.py
Labs: inhabited_interiority
Purpose: Produce a matrix of all loaded fixtures across domains, showing their
         field type, C-score (if computable), verdict, and key flags.
         Used to survey the full fixture set and identify gaps.

Usage:
    python run_domain_matrix.py
    python run_domain_matrix.py --domain games_action_fields
    python run_domain_matrix.py --csv
"""

from __future__ import annotations
import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists()),
    Path(__file__).resolve().parent.parent.parent,
)
LAB_DIR = ROOT / "labs" / "inhabited_interiority"
FIXTURES_DIR = LAB_DIR / "fixtures"

COMPONENTS = ["A", "U", "D", "T", "F"]


def load_all_cases() -> list[dict]:
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if "id" in item:
                    domain = json_file.parent.relative_to(FIXTURES_DIR).as_posix()
                    item["_domain"] = domain
                    item["_source_file"] = json_file.name
                    cases.append(item)
        except Exception as e:
            print(f"  [warn] {json_file.name}: {e}", file=sys.stderr)
    return sorted(cases, key=lambda c: (c.get("_domain", ""), c.get("id", "")))


def compute_c(comps: dict) -> tuple[str, str]:
    """Returns (score_str, status)."""
    vals = {k: comps.get(k) for k in COMPONENTS}
    if not vals:
        return "—", "no_components"
    if any(v is None for v in vals.values()):
        return "null", "unresolvable"
    product = 1.0
    for k in COMPONENTS:
        product *= vals[k]
    return f"{product:.4f}", "computed" if product > 0 else "collapsed"


def verdict_abbrev(v: str | None) -> str:
    if not v:
        return "—"
    abbrevs = {
        "phenomenal_candidate": "PhenCand",
        "non_phenomenal": "NonPhen",
        "false_positive_confirmed": "FalsePos",
        "demoted": "Demoted",
        "unresolved": "Unresvd",
        "false_positive": "FalsePos",
    }
    return abbrevs.get(v, v[:10])


def get_case_type(case: dict) -> str:
    if "transfer_type" in case:
        return "transfer"
    if "continuity_components" in case:
        return "continuity"
    if "structure_score" in case and "why_false_positive" in case:
        return "false_pos"
    if "field_type" in case:
        return "field"
    return "other"


def print_matrix(cases: list[dict], domain_filter: str | None) -> None:
    print("\n" + "=" * 100)
    print("DOMAIN MATRIX — All fixtures across the inhabited_interiority lab")
    print("C score = A·U·D·T·F stress proxy. Not a consciousness measurement.")
    print("=" * 100)
    print()

    # Gather domains
    all_domains = sorted(set(c.get("_domain", "?") for c in cases))
    if domain_filter:
        all_domains = [d for d in all_domains if domain_filter in d]
        cases = [c for c in cases if domain_filter in c.get("_domain", "")]

    if not cases:
        print(f"No fixtures found for domain filter: {domain_filter}")
        return

    # Column widths
    ID_W = 36
    TYPE_W = 18
    C_W = 9
    V_W = 10
    DOMAIN_W = 28

    header = (
        f"  {'ID':<{ID_W}} {'FieldType':<{TYPE_W}} {'C':<{C_W}} "
        f"{'Verdict':<{V_W}} {'PC':<3} {'Domain':<{DOMAIN_W}}"
    )
    sep = "  " + "─" * (ID_W + TYPE_W + C_W + V_W + DOMAIN_W + 20)

    print(header)
    print(sep)

    current_domain = None
    for case in cases:
        domain = case.get("_domain", "?")
        if domain != current_domain:
            if current_domain is not None:
                print()
            print(f"  ── {domain.upper()}")
            current_domain = domain

        case_id = case.get("id", "?")[:ID_W - 1]
        field_type = case.get("field_type", case.get("transfer_type", "—"))[:TYPE_W - 1]
        comps = case.get("components", {})
        c_score, c_status = compute_c(comps)
        if c_status == "unresolvable":
            c_display = "null"
        elif c_status == "collapsed":
            c_display = "0 (col)"
        else:
            c_display = c_score
        verdict = verdict_abbrev(case.get("verdict") or case.get("classification"))
        pc = "★" if case.get("phenomenal_candidate") else " "

        # Flags
        flags = []
        if case.get("breaks_preserved"):
            flags.append(f"[{len(case['breaks_preserved'])}brk]")
        if case.get("branching_occurs"):
            flags.append("[branch]")

        print(
            f"  {case_id:<{ID_W}} {field_type:<{TYPE_W}} {c_display:<{C_W}} "
            f"{verdict:<{V_W}} {pc:<3} {domain:<{DOMAIN_W}} {' '.join(flags)}"
        )

    print(sep)
    print()

    # Summary statistics
    total = len(cases)
    candidates = sum(1 for c in cases if c.get("phenomenal_candidate"))
    non_cands = total - candidates
    with_breaks = sum(1 for c in cases if c.get("breaks_preserved"))
    branching = sum(1 for c in cases if c.get("branching_occurs"))
    unresolved = sum(1 for c in cases if (c.get("verdict") or c.get("classification")) in ("unresolved", ""))

    print(f"  Domains:              {len(all_domains)}")
    print(f"  Total fixtures:       {total}")
    print(f"  Phenomenal candidates:  {candidates}")
    print(f"  Non-candidates:         {non_cands}")
    print(f"  Fixtures with breaks:   {with_breaks}")
    print(f"  Branching cases:        {branching}")
    print(f"  Unresolved verdicts:    {unresolved}")
    print()
    print("Legend: ★ = phenomenal_candidate  [Nbrk] = N preserved breaks  [branch] = branching occurs")
    print()


def export_csv(cases: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "name", "domain", "field_type", "phenomenal_candidate",
        "A", "U", "D", "T", "F", "c_score", "verdict", "breaks_count", "branching",
    ])
    writer.writeheader()
    for case in cases:
        comps = case.get("components", {})
        c_str, _ = compute_c(comps)
        writer.writerow({
            "id": case.get("id", ""),
            "name": case.get("name", case.get("description", ""))[:60],
            "domain": case.get("_domain", ""),
            "field_type": case.get("field_type", case.get("transfer_type", "")),
            "phenomenal_candidate": case.get("phenomenal_candidate", ""),
            "A": comps.get("A", ""),
            "U": comps.get("U", ""),
            "D": comps.get("D", ""),
            "T": comps.get("T", ""),
            "F": comps.get("F", ""),
            "c_score": c_str,
            "verdict": case.get("verdict") or case.get("classification", ""),
            "breaks_count": len(case.get("breaks_preserved", [])),
            "branching": case.get("branching_occurs", ""),
        })
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Domain matrix: all fixtures with scores, verdicts, and flags."
    )
    parser.add_argument("--domain", "-d", metavar="DOMAIN",
                        help="Filter to one domain directory (e.g. games_action_fields).")
    parser.add_argument("--csv", "-c", action="store_true",
                        help="Export results as CSV to stdout.")
    args = parser.parse_args()

    cases = load_all_cases()
    if not cases:
        print("No fixtures found.", file=sys.stderr)
        sys.exit(1)

    if args.csv:
        print(export_csv(cases))
    else:
        print_matrix(cases, args.domain)


if __name__ == "__main__":
    main()
