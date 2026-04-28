"""
classify_field_type.py
Labs: inhabited_interiority
Purpose: Load all field-case fixtures and produce a classification table by field type.
         Not a consciousness claim — field organization does not imply phenomenal fielding.

Usage:
    python classify_field_type.py
    python classify_field_type.py --verbose
    python classify_field_type.py --type action_field
"""

from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# ROOT resolution — required per AGENT_RULES
ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists()),
    Path(__file__).resolve().parent.parent.parent,
)
LAB_DIR = ROOT / "labs" / "inhabited_interiority"
FIXTURES_DIR = LAB_DIR / "fixtures"

FIELD_TYPES = [
    "constraint_field",
    "closure_field",
    "viability_field",
    "phenomenal_field",
    "action_field",
    "symbolic_field",
    "operational_field",
    "governance_field",
    "aesthetic_field",
    "export_field",
    "hybrid_agent_field",
]

FIELD_TYPE_DESCRIPTIONS = {
    "constraint_field":   "Lawful possibility-space. Not phenomenal by itself.",
    "closure_field":      "Self-maintaining pattern (autocatalytic). Not phenomenal by itself.",
    "viability_field":    "Living regulation. Not automatically phenomenal.",
    "phenomenal_field":   "Lived co-presence. Phenomenal candidate if A > 0.",
    "action_field":       "Agents coordinated by constraints. Field ≠ consciousness; agents may be.",
    "symbolic_field":     "Meanings persist across agents. No unified subject.",
    "operational_field":  "Claims tested and preserved. No phenomenal fielding.",
    "governance_field":   "Rules update rules. Not phenomenal by itself.",
    "aesthetic_field":    "Structures experience. Listener/inhabitant may be phenomenal; structure is not.",
    "export_field":       "Symbolic output (speech, text). Not phenomenal by itself.",
    "hybrid_agent_field": "Contested/mixed case. Requires case-by-case analysis.",
}


def load_field_cases() -> list[dict]:
    """Load all JSON fixtures that conform to the field_case schema."""
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if "field_type" in item and "id" in item:
                    item["_source_file"] = json_file.relative_to(LAB_DIR).as_posix()
                    cases.append(item)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  [warn] Could not load {json_file.name}: {e}", file=sys.stderr)
    return cases


def group_by_field_type(cases: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for case in cases:
        grouped[case.get("field_type", "unknown")].append(case)
    return dict(grouped)


def verdict_symbol(verdict: str | None) -> str:
    mapping = {
        "phenomenal_candidate": "◈",
        "non_phenomenal": "○",
        "false_positive_confirmed": "✗",
        "demoted": "↓",
        "unresolved": "?",
        None: "–",
    }
    return mapping.get(verdict, "–")


def c_score_display(case: dict) -> str:
    score = case.get("c_score")
    if score is None:
        comps = case.get("components", {})
        if any(v is None for v in comps.values()):
            return "null (unresolvable component)"
        vals = [v for v in comps.values() if v is not None]
        if vals and 0.0 in vals:
            return "0.0 (component collapsed)"
        return "–"
    return f"{score:.4f}"


def print_table(grouped: dict[str, list[dict]], filter_type: str | None, verbose: bool) -> None:
    types_to_show = [filter_type] if filter_type else FIELD_TYPES

    total = 0
    phenomenal_candidates = 0

    print("\n" + "=" * 80)
    print("FIELD TYPE CLASSIFICATION — Inhabited Interiority / Perturbable Phenomenal Field")
    print("Status: candidate / stress-test only. No claims are stable.")
    print("=" * 80)
    print()
    print("Legend: ◈ = phenomenal_candidate  ○ = non_phenomenal  ✗ = false_positive_confirmed")
    print("        ↓ = demoted  ? = unresolved  – = not classified")
    print()

    for ftype in types_to_show:
        cases_in_type = grouped.get(ftype, [])
        if not cases_in_type and filter_type:
            print(f"No fixtures found for field type: {ftype}")
            continue
        if not cases_in_type:
            continue

        desc = FIELD_TYPE_DESCRIPTIONS.get(ftype, "")
        print(f"  ┌─ {ftype.upper().replace('_', ' ')} ({len(cases_in_type)} cases)")
        print(f"  │  {desc}")
        print("  │")

        for case in sorted(cases_in_type, key=lambda c: c.get("id", "")):
            verd = case.get("verdict")
            sym = verdict_symbol(verd)
            pc = "★ phenomenal_candidate" if case.get("phenomenal_candidate") else ""
            c_disp = c_score_display(case)
            print(f"  │  {sym}  [{case.get('id', '?')}]  {case.get('name', '?')}")
            if verbose:
                print(f"  │     desc: {case.get('description', '')[:80]}{'...' if len(case.get('description','')) > 80 else ''}")
                print(f"  │     C score: {c_disp}   {pc}")
                src = case.get("_source_file", "")
                print(f"  │     source: {src}")
                rp = case.get("revision_pressure", "")
                if rp:
                    print(f"  │     revision pressure: {rp[:100]}{'...' if len(rp) > 100 else ''}")
            total += 1
            if case.get("phenomenal_candidate"):
                phenomenal_candidates += 1

        print("  └" + "─" * 50)
        print()

    print("─" * 80)
    print(f"Total cases loaded: {total}")
    print(f"Phenomenal candidates: {phenomenal_candidates}")
    print(f"Non-candidates / false-positive controls: {total - phenomenal_candidates}")
    print()
    print("Anti-bloat rule: Field-like organization is not automatically phenomenal.")
    print("If this output promotes a non-candidate to consciousness, the theory has failed.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify all field cases by field type. Not a consciousness proof — a classification harness."
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show description and C score for each case.")
    parser.add_argument("--type", "-t", metavar="FIELD_TYPE", help=f"Filter to one field type. Options: {', '.join(FIELD_TYPES)}")
    args = parser.parse_args()

    if args.type and args.type not in FIELD_TYPES:
        print(f"Unknown field type: {args.type}. Valid types: {', '.join(FIELD_TYPES)}", file=sys.stderr)
        sys.exit(1)

    cases = load_field_cases()
    if not cases:
        print("No field-case fixtures found. Run from the workspace root or ensure fixtures/ is populated.", file=sys.stderr)
        sys.exit(1)

    grouped = group_by_field_type(cases)
    print_table(grouped, args.type, args.verbose)


if __name__ == "__main__":
    main()
