"""
transfer_test.py
Labs: inhabited_interiority
Purpose: Evaluate transfer scenarios using the formula:
         Transfer(X_t → Y_t+1) preserves S iff it preserves C, P, O, B, K, and N.
         Pattern survival is necessary but not sufficient.

Usage:
    python transfer_test.py
    python transfer_test.py --type destructive_teleportation
    python transfer_test.py --show-carriers
    python transfer_test.py --show-breaks
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

TRANSFER_TYPES = [
    "ordinary_biological_change",
    "sleep_anesthesia",
    "gradual_neural_replacement",
    "destructive_teleportation",
    "non_destructive_copy",
    "mind_upload",
    "reincarnation_claim",
    "soul_claim",
    "genetic_lineage",
    "symbolic_legacy",
]

CLASSIFICATIONS_ORDERED = [
    "identity_preserving_transformation",
    "field_suspension_resumable",
    "possible_self_carrying",
    "pattern_copy_field_break_risk",
    "branching_descendants_only",
    "symbolic_survival_only",
    "unresolved",
]

CLASSIFICATION_DESCRIPTIONS = {
    "identity_preserving_transformation": "Self-continuity preserved through causal continuity.",
    "field_suspension_resumable":          "Field may suspend; resumes via same causal process. Not destruction.",
    "possible_self_carrying":              "Depends on unresolved substrate questions. Cannot yet classify.",
    "pattern_copy_field_break_risk":       "Pattern survives; field continuity is at break risk.",
    "branching_descendants_only":          "N=0: multiple heirs. No singular continuing ownership-stream.",
    "symbolic_survival_only":             "K-structure survives symbolically. C, O, N do not.",
    "unresolved":                          "Theory cannot classify without resolving open questions.",
}

S_COMPONENTS = ["C", "P", "O", "B", "K", "N"]


def load_transfer_cases() -> list[dict]:
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if "transfer_type" in item and "classification" in item:
                    cases.append(item)
        except Exception as e:
            print(f"  [warn] {json_file.name}: {e}", file=sys.stderr)
    return cases


def bool_display(val) -> str:
    if val is True:
        return "yes"
    if val is False:
        return "NO"
    return "?"


def component_table(comps: dict | None) -> str:
    if not comps:
        return "not specified"
    parts = []
    for k in S_COMPONENTS:
        v = comps.get(k)
        parts.append(f"{k}:{bool_display(v)}")
    return "  ".join(parts)


def self_survives_verdict(case: dict) -> str:
    s = case.get("s_survives")
    if s is True:
        return "PRESERVED"
    if s is False:
        return "FAILS"
    branching = case.get("branching_occurs", False)
    if branching:
        return "FAILS (branching)"
    return "UNRESOLVED"


def print_report(cases: list[dict], filter_type: str | None,
                 show_carriers: bool, show_breaks: bool) -> None:
    print("\n" + "=" * 80)
    print("TRANSFER CASE EVALUATION")
    print("Formula: Transfer(X_t → Y_t+1) preserves S iff C, P, O, B, K, N all preserved.")
    print("Copy(pattern) ≠ Preserve(Self)")
    print("Status: candidate analysis. No transfer case is classified as proven.")
    print("=" * 80)
    print()

    if filter_type:
        cases = [c for c in cases if c.get("transfer_type") == filter_type]

    if not cases:
        print(f"No transfer cases found{' for type: ' + filter_type if filter_type else ''}.")
        return

    # Group by classification
    by_class: dict[str, list[dict]] = {}
    for case in cases:
        cl = case.get("classification", "unresolved")
        by_class.setdefault(cl, []).append(case)

    for cl in CLASSIFICATIONS_ORDERED:
        group = by_class.get(cl, [])
        if not group:
            continue
        print(f"  ── {cl.upper().replace('_', ' ')} ({len(group)})")
        print(f"     {CLASSIFICATION_DESCRIPTIONS.get(cl, '')}")
        print()

        for case in group:
            s_verdict = self_survives_verdict(case)
            branching = case.get("branching_occurs", False)

            print(f"     [{case.get('id', '?')}]  {case.get('description', '')[:70]}{'...' if len(case.get('description','')) > 70 else ''}")
            print(f"       Transfer type : {case.get('transfer_type', '?')}")
            print(f"       Pattern survives: {bool_display(case.get('pattern_survives'))}   "
                  f"C survives: {bool_display(case.get('c_survives'))}   "
                  f"S survives: {s_verdict}")
            print(f"       Branching: {bool_display(branching)}")

            comps = case.get("components_preserved")
            if comps:
                print(f"       Components: {component_table(comps)}")

            if show_carriers:
                carrier = case.get("portable_carrier_required", "")
                if carrier:
                    print(f"       Carrier required: {carrier[:100]}{'...' if len(carrier) > 100 else ''}")
                fmech = case.get("field_continuity_mechanism", "")
                if fmech:
                    print(f"       Field mechanism: {fmech[:100]}{'...' if len(fmech) > 100 else ''}")

            rp = case.get("revision_pressure", "")
            if rp:
                print(f"       ⟳ {rp[:100]}{'...' if len(rp) > 100 else ''}")

            if show_breaks:
                for b in case.get("breaks_preserved", []):
                    print(f"       ✗ BREAK: {b[:100]}{'...' if len(b) > 100 else ''}")

            oqs = case.get("open_questions", [])
            if oqs and show_breaks:
                for q in oqs:
                    print(f"       ? {q[:100]}{'...' if len(q) > 100 else ''}")

            print()

        print()

    # Summary table
    print("─" * 80)
    print("CLASSIFICATION SUMMARY")
    print()
    print(f"  {'Classification':<40} {'Count':>5}")
    print(f"  {'─' * 40} {'─' * 5}")
    for cl in CLASSIFICATIONS_ORDERED:
        count = len(by_class.get(cl, []))
        marker = " ← pattern-only or branching" if cl in ("branching_descendants_only", "symbolic_survival_only", "pattern_copy_field_break_risk") else ""
        print(f"  {cl:<40} {count:>5}{marker}")
    print()
    print("Key rules:")
    print("  — Pattern survival is not field survival.")
    print("  — Field survival is not self survival.")
    print("  — Branching is fatal to singular self-continuity (N collapses).")
    print("  — A portable carrier must preserve inhabited ownership, not merely information.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate transfer cases: does the self survive the transition?"
    )
    parser.add_argument("--type", "-t", metavar="TRANSFER_TYPE",
                        help=f"Filter to one transfer type. Options: {', '.join(TRANSFER_TYPES)}")
    parser.add_argument("--show-carriers", "-c", action="store_true",
                        help="Show portable carrier requirements and field continuity mechanisms.")
    parser.add_argument("--show-breaks", "-b", action="store_true",
                        help="Show preserved theory breaks and open questions.")
    args = parser.parse_args()

    cases = load_transfer_cases()
    if not cases:
        print("No transfer case fixtures found.", file=sys.stderr)
        sys.exit(1)

    print_report(cases, args.type, args.show_carriers, args.show_breaks)


if __name__ == "__main__":
    main()
