"""
score_self_continuity.py
Labs: inhabited_interiority
Purpose: Score all continuity cases using S = C · P · O · B · K · N.
         If N = 0, self-continuity collapses regardless of other scores.
         If C = 0, no self is possible.

Usage:
    python score_self_continuity.py
    python score_self_continuity.py --show-topology
    python score_self_continuity.py --show-breaks
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

S_COMPONENTS = ["C", "P", "O", "B", "K", "N"]
S_LABELS = {
    "C": "consciousness / fielded appearance",
    "P": "perspective / from-here",
    "O": "ownership / mineness",
    "B": "self-boundary",
    "K": "carried constraint through time",
    "N": "non-branching continuity",
}

VERDICTS_ORDERED = [
    "self_continuous",
    "self_suspended_pending",
    "self_broken",
    "branching_descendants",
    "pattern_only",
    "unresolved",
]


def load_continuity_cases() -> list[dict]:
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if "continuity_components" in item and "id" in item:
                    cases.append(item)
        except Exception as e:
            print(f"  [warn] {json_file.name}: {e}", file=sys.stderr)
    return cases


def compute_s_score(components: dict) -> tuple[float | None, str, list[str]]:
    """Returns (score, status, collapsed_dims)."""
    vals = {k: components.get(k) for k in S_COMPONENTS}
    null_dims = [k for k, v in vals.items() if v is None]
    collapsed_dims = [k for k, v in vals.items() if v == 0.0]

    if null_dims:
        return None, "unresolvable", collapsed_dims

    product = 1.0
    for k in S_COMPONENTS:
        product *= vals[k]
    return round(product, 6), "computed", collapsed_dims


def bar(score: float | None, width: int = 20) -> str:
    if score is None:
        return "?" * width
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


def self_integrity_flags(comps: dict) -> list[str]:
    """Return human-readable flags for critical component failures."""
    flags = []
    if comps.get("N") == 0.0:
        flags.append("BRANCHING: N=0 → singular self-continuity impossible")
    if comps.get("C") == 0.0:
        flags.append("NO BASE: C=0 → no phenomenal field → self cannot persist")
    if comps.get("O") == 0.0:
        flags.append("NO OWNERSHIP: O=0 → mineness has collapsed")
    return flags


def print_report(cases: list[dict], show_topology: bool, show_breaks: bool) -> None:
    print("\n" + "=" * 80)
    print("SELF-CONTINUITY SCORING — S = C · P · O · B · K · N")
    print("Status: candidate analysis only. No score proves self-continuity.")
    print("N=0 is fatal: branching collapses singular self regardless of other scores.")
    print("=" * 80)
    print()

    enriched = []
    for case in cases:
        comps = case.get("continuity_components", {})
        score, status, collapsed = compute_s_score(comps)
        enriched.append({**case, "_s_computed": score, "_s_status": status, "_collapsed": collapsed})

    def sort_key(c):
        s = c["_s_computed"]
        return s if s is not None else -1.0

    enriched = sorted(enriched, key=sort_key, reverse=True)

    for case in enriched:
        score = case["_s_computed"]
        status = case["_s_status"]
        collapsed = case["_collapsed"]
        comps = case.get("continuity_components", {})

        score_str = f"{score:.6f}" if score is not None else "null"
        bar_str = bar(score)
        verdict = case.get("verdict", "unresolved")
        causal = case.get("causal_lineage")
        topology = case.get("temporal_topology", "unknown")

        print(f"  {case.get('id', '?')}")
        print(f"    Name     : {case.get('name', '?')}")
        print(f"    S score  : {score_str}  [{bar_str}]  ({status})")
        print(f"    Verdict  : {verdict}")

        comp_parts = []
        for k in S_COMPONENTS:
            v = comps.get(k)
            v_str = f"{v:.2f}" if v is not None else "null"
            flag = " [!]" if v == 0.0 else " [?]" if v is None else ""
            comp_parts.append(f"{k}={v_str}{flag}")
        print(f"    Components: {' · '.join(comp_parts)}")

        flags = self_integrity_flags(comps)
        for flag in flags:
            print(f"    ⚠ {flag}")

        if causal is not None:
            causal_str = "yes" if causal else "NO (causal lineage absent — pattern-only transfer risk)"
            print(f"    Causal lineage: {causal_str}")

        if show_topology:
            print(f"    Temporal topology: {topology}")

        rp = case.get("revision_pressure", "")
        if rp:
            print(f"    ⟳ {rp[:120]}{'...' if len(rp) > 120 else ''}")

        if show_breaks:
            for b in case.get("breaks_preserved", []):
                print(f"    ✗ BREAK: {b[:120]}{'...' if len(b) > 120 else ''}")

        print()

    # Summary statistics
    verdicts: dict[str, int] = {}
    for case in enriched:
        v = case.get("verdict", "unresolved")
        verdicts[v] = verdicts.get(v, 0) + 1

    print("─" * 80)
    print("Verdict summary:")
    for v in VERDICTS_ORDERED:
        count = verdicts.get(v, 0)
        if count:
            print(f"  {v}: {count}")
    for v, count in verdicts.items():
        if v not in VERDICTS_ORDERED:
            print(f"  {v}: {count}")
    print()
    print("Key rule: Pattern survival is not self survival.")
    print("Key rule: Self-continuity requires C > 0, N > 0, and causal lineage.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score self-continuity cases using S = C·P·O·B·K·N. Falsification harness."
    )
    parser.add_argument("--show-topology", "-t", action="store_true",
                        help="Show temporal topology for each case.")
    parser.add_argument("--show-breaks", "-b", action="store_true",
                        help="Show preserved theory breaks.")
    args = parser.parse_args()

    cases = load_continuity_cases()
    if not cases:
        print("No continuity-case fixtures found.", file=sys.stderr)
        sys.exit(1)

    print_report(cases, args.show_topology, args.show_breaks)


if __name__ == "__main__":
    main()
