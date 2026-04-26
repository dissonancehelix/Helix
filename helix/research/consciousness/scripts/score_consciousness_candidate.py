"""
score_consciousness_candidate.py
Labs: inhabited_interiority
Purpose: Score all phenomenal candidates using C = A · U · D · T · F.
         If any component is 0.0, C collapses. If any is null, score is unresolvable.
         Output is a ranked list — not a ranking of consciousness, but of stress-test posture.

Usage:
    python score_consciousness_candidate.py
    python score_consciousness_candidate.py --candidates-only
    python score_consciousness_candidate.py --show-breaks
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

COMPONENTS = ["A", "U", "D", "T", "F"]
COMPONENT_LABELS = {
    "A": "appearance-from-within",
    "U": "local unity / co-presence",
    "D": "differentiation / internal contrast",
    "T": "temporal thickness",
    "F": "field inclusion",
}


def load_field_cases() -> list[dict]:
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if "field_type" in item and "components" in item:
                    cases.append(item)
        except Exception as e:
            print(f"  [warn] {json_file.name}: {e}", file=sys.stderr)
    return cases


def compute_c_score(components: dict) -> tuple[float | None, str]:
    """
    Returns (score, status) where status is:
      'computed'      — all components present and non-null
      'unresolvable'  — at least one component is null
      'collapsed'     — at least one component is 0.0
    """
    vals = {k: components.get(k) for k in COMPONENTS}
    if any(v is None for v in vals.values()):
        return None, "unresolvable"
    product = 1.0
    for k in COMPONENTS:
        product *= vals[k]
    if product == 0.0:
        return 0.0, "collapsed"
    return round(product, 6), "computed"


def collapsed_components(components: dict) -> list[str]:
    return [k for k in COMPONENTS if components.get(k) == 0.0]


def null_components(components: dict) -> list[str]:
    return [k for k in COMPONENTS if components.get(k) is None]


def bar(score: float | None, width: int = 20) -> str:
    if score is None:
        return "?" * width
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


def verdict_label(case: dict, score: float | None, status: str) -> str:
    v = case.get("verdict", "")
    if v:
        return v
    if status == "collapsed":
        return "non_phenomenal"
    if status == "unresolvable":
        return "unresolved"
    return "phenomenal_candidate" if case.get("phenomenal_candidate") else "non_phenomenal"


def rank_cases(cases: list[dict]) -> list[dict]:
    """Attach computed score and sort descending. Null and zero go to bottom."""
    enriched = []
    for case in cases:
        comps = case.get("components", {})
        score, status = compute_c_score(comps)
        enriched.append({**case, "_c_computed": score, "_c_status": status})

    def sort_key(c):
        s = c["_c_computed"]
        if s is None:
            return -2.0
        return s

    return sorted(enriched, key=sort_key, reverse=True)


def print_report(cases: list[dict], candidates_only: bool, show_breaks: bool) -> None:
    print("\n" + "=" * 80)
    print("CONSCIOUSNESS CANDIDATE SCORING — C = A · U · D · T · F")
    print("Status: candidate scores only. No score constitutes a consciousness proof.")
    print("If any term = 0, C collapses. If any term = null, score is unresolvable.")
    print("=" * 80)
    print()

    ranked = rank_cases(cases)
    if candidates_only:
        ranked = [c for c in ranked if c.get("phenomenal_candidate")]

    shown = 0
    for case in ranked:
        score = case["_c_computed"]
        status = case["_c_status"]

        # Skip non-candidates if flag set
        if candidates_only and not case.get("phenomenal_candidate"):
            continue

        shown += 1
        verdict = verdict_label(case, score, status)
        comps = case.get("components", {})
        collapsed = collapsed_components(comps)
        null_comps = null_components(comps)

        score_str = f"{score:.6f}" if score is not None else "null"
        bar_str = bar(score)

        print(f"  {case.get('id', '?')}")
        print(f"    Name     : {case.get('name', '?')}")
        print(f"    C score  : {score_str}  [{bar_str}]  ({status})")
        print(f"    Verdict  : {verdict}")

        # Component detail
        comp_parts = []
        for k in COMPONENTS:
            v = comps.get(k)
            v_str = f"{v:.2f}" if v is not None else "null"
            flag = " [COLLAPSED]" if v == 0.0 else " [NULL]" if v is None else ""
            comp_parts.append(f"{k}={v_str}{flag}")
        print(f"    Components: {' · '.join(comp_parts)}")

        if collapsed:
            print(f"    ⚠ Collapse: {', '.join(collapsed)} ({', '.join(COMPONENT_LABELS[k] for k in collapsed)})")
        if null_comps:
            print(f"    ? Unresolvable: {', '.join(null_comps)} ({', '.join(COMPONENT_LABELS[k] for k in null_comps)})")

        rp = case.get("revision_pressure", "")
        if rp:
            print(f"    ⟳ Revision pressure: {rp[:120]}{'...' if len(rp) > 120 else ''}")

        if show_breaks:
            breaks = case.get("breaks_preserved", [])
            for i, b in enumerate(breaks, 1):
                print(f"    ✗ Break {i}: {b[:120]}{'...' if len(b) > 120 else ''}")

        print()

    print("─" * 80)
    print(f"Cases shown: {shown}")
    print()
    print("Reminder: C score is a stress-test proxy for falsification, not a measurement.")
    print("Threshold values for any component are currently unspecified — a known theory gap.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score consciousness candidates using C = A·U·D·T·F. Not a proof — a stress-test harness."
    )
    parser.add_argument("--candidates-only", "-c", action="store_true",
                        help="Show only phenomenal_candidate = true cases.")
    parser.add_argument("--show-breaks", "-b", action="store_true",
                        help="Show preserved theory breaks for each case.")
    args = parser.parse_args()

    cases = load_field_cases()
    if not cases:
        print("No fixtures found.", file=sys.stderr)
        sys.exit(1)

    print_report(cases, args.candidates_only, args.show_breaks)


if __name__ == "__main__":
    main()
