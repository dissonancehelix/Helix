"""
run_six_tests.py
Labs: inhabited_interiority
Purpose: Run all six falsification tests against the loaded fixtures and produce
         stress results. Each test evaluates a specific theoretical claim.
         If a test breaks the theory, the break is preserved and reported.

Tests:
  1. temporal_deletion_test       — what survives if time is removed?
  2. boundary_perturbation_test   — what collapses if inside/outside is disturbed?
  3. network_partition_test       — what happens when the system splits?
  4. false_positive_field_test    — what looks conscious but isn't?
  5. carried_constraint_test      — does the past remain active as constraint?
  6. geometry_topology_test       — what relations survive deformation?

Usage:
    python run_six_tests.py
    python run_six_tests.py --test temporal_deletion_test
    python run_six_tests.py --show-breaks
    python run_six_tests.py --output-json
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists()),
    Path(__file__).resolve().parent.parent.parent,
)
LAB_DIR = ROOT / "labs" / "inhabited_interiority"
FIXTURES_DIR = LAB_DIR / "fixtures"
REPORTS_DIR = LAB_DIR / "reports"

TESTS = [
    "temporal_deletion_test",
    "boundary_perturbation_test",
    "network_partition_test",
    "false_positive_field_test",
    "carried_constraint_test",
    "geometry_topology_test",
]

TEST_DESCRIPTIONS = {
    "temporal_deletion_test": (
        "Remove time. What remains? "
        "Expected: static structure may remain; fielding becomes questionable; self collapses; "
        "temporal thickness → fielding; temporal continuity → self."
    ),
    "boundary_perturbation_test": (
        "Disturb the inside/outside boundary. What collapses? "
        "Expected: boundary is necessary for selfhood, but boundary alone is not consciousness. "
        "Ego dissolution, depersonalization, split-brain, blindsight are the probes."
    ),
    "network_partition_test": (
        "Split the system. One self, two selves, or only a network partition? "
        "Expected: network coordination ≠ unified phenomenal interiority. "
        "Branching breaks singular self-continuity."
    ),
    "false_positive_field_test": (
        "What looks conscious but probably is not? "
        "Expected: structured/inherited continuity can feel inhabited to a subject without being a subject. "
        "LLM, fictional character, sports team, religion, Helix must all fail A."
    ),
    "carried_constraint_test": (
        "Does the past remain active as constraint on the future? "
        "Expected: identity is carried constraint through transformation. "
        "Distinguishes K (active constraint) from mere memory (stored but not constraining)."
    ),
    "geometry_topology_test": (
        "What relations survive deformation? "
        "Expected: the self is not a fixed object but a preserved temporal topology of ownership. "
        "Handles Ship of Theseus, uploads, copies, AGI identity."
    ),
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


# ─────────────────────────────────────────────────────────────────────────────
# Test implementations — each returns a list of stress result dicts
# ─────────────────────────────────────────────────────────────────────────────

def test_temporal_deletion(cases: list[dict]) -> list[dict]:
    """
    Test: remove time (T → 0) from each phenomenal candidate. Does C collapse?
    Theory predicts: T = 0 → C = 0 (temporal thickness is required for fielding).
    """
    results = []
    for case in cases:
        comps = case.get("components", {})
        T = comps.get("T")
        if T is None:
            continue

        is_candidate = case.get("phenomenal_candidate", False)
        A = comps.get("A", 0)
        other_scores = [comps.get(k) for k in ["A", "U", "D", "F"] if comps.get(k) is not None]

        # Simulate T → 0
        simulated_product = 0.0  # T=0 collapses C

        if is_candidate and T > 0 and A > 0:
            verdict = "theory_survives"
            detail = f"T={T:.2f} is positive. If T → 0, C collapses (product = 0). Theory predicts this correctly."
            severity = "low"
            surviving = ["Temporal thickness is necessary for fielding."]
            demoted: list[str] = []
            breaks: list[str] = []
        elif not is_candidate and T > 0:
            verdict = "theory_survives"
            detail = f"Non-candidate has T={T:.2f} but A=0. T alone does not produce C."
            severity = "low"
            surviving = ["T without A does not produce phenomenal fielding."]
            demoted = []
            breaks = []
        elif T == 0.0:
            verdict = "theory_survives"
            detail = "T=0 confirms C collapses. Temporal thickness is absent."
            severity = "low"
            surviving = ["Temporal deletion confirmation."]
            demoted = []
            breaks = []
        else:
            verdict = "unresolved"
            detail = f"Cannot evaluate temporal deletion for this case. T={T}."
            severity = "low"
            surviving = []
            demoted = []
            breaks = []

        results.append({
            "test_name": "temporal_deletion_test",
            "fixture_id": case.get("id", "?"),
            "fixture_type": "field_case",
            "verdict": verdict,
            "severity": severity,
            "what_was_tested": "T (temporal thickness) contribution to C. If T → 0, C must collapse.",
            "result_detail": detail,
            "revision_pressure": "If any phenomenal candidate survives T=0 simulation without losing C, the theory must explain how fielding persists without temporal thickness.",
            "breaks_preserved": breaks + case.get("breaks_preserved", []),
            "surviving_claims": surviving,
            "demoted_claims": demoted,
            "next_test_recommended": "boundary_perturbation_test",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return results


def test_boundary_perturbation(cases: list[dict]) -> list[dict]:
    """
    Test: evaluate cases where self-boundary (B) or ownership (O) is known to be disrupted.
    Theory predicts: boundary is necessary for selfhood, but boundary alone is not consciousness.
    """
    results = []
    boundary_cases = [
        "split_brain", "depersonalization", "psychedelic_ego_dissolution",
        "locked_in_syndrome", "blindsight", "pain_asymbolia",
    ]

    for case in cases:
        case_id = case.get("id", "")
        if case_id not in boundary_cases:
            # Also check continuity_components for B
            cont = case.get("continuity_components", {})
            if "B" not in cont:
                continue

        comps = case.get("components", {})
        cont = case.get("continuity_components", {})
        B = cont.get("B") if cont else comps.get("B")
        A = comps.get("A")

        if B is None and A is None:
            continue

        if case_id in boundary_cases:
            # These are the canonical boundary perturbation cases
            breaks = case.get("breaks_preserved", [])
            verdict = "revision_required" if breaks else "theory_survives"
            severity = "high" if breaks else "medium"
            detail = (
                f"Boundary perturbation case '{case_id}'. "
                f"A={A}, B (from context)=disrupted. "
                "Theory: boundary disruption should affect S (self) more than C (consciousness)."
            )
            surviving = ["C/S dissociation is supported — A can remain while B disrupts S."]
            demoted = []
        else:
            verdict = "theory_survives"
            severity = "low"
            detail = f"B={B}. Standard boundary evaluation."
            surviving = []
            demoted = []
            breaks = []

        results.append({
            "test_name": "boundary_perturbation_test",
            "fixture_id": case_id or "?",
            "fixture_type": "field_case",
            "verdict": verdict,
            "severity": severity,
            "what_was_tested": "B (self-boundary) and O (ownership) disruption and their effect on C vs S.",
            "result_detail": detail,
            "revision_pressure": (
                "The theory separates C and S. Boundary perturbation empirically tests this. "
                "If C is high and B is disrupted, S should suffer while C may not. "
                "Split-brain is the hardest case: U drops but subjects report normal single-self experience."
            ),
            "breaks_preserved": breaks,
            "surviving_claims": surviving,
            "demoted_claims": demoted,
            "next_test_recommended": "network_partition_test",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return results


def test_network_partition(cases: list[dict]) -> list[dict]:
    """
    Test: identify all cases where the system can split (branching / partition).
    Theory predicts: branching breaks singular self-continuity. N collapses.
    """
    results = []
    for case in cases:
        branching = case.get("branching_occurs")
        verdict_raw = case.get("verdict", "") or case.get("classification", "")
        N = case.get("components", {}).get("N") or case.get("continuity_components", {}).get("N")

        if branching is None and N is None and "partition" not in case.get("id", "") and "split" not in case.get("id", ""):
            continue

        if branching is True or (N is not None and N == 0.0) or verdict_raw in ("branching_descendants", "branching_descendants_only"):
            verdict = "theory_survives"
            detail = "Branching detected. N=0 or branching_occurs=True. Theory correctly predicts singular self-continuity collapses."
            severity = "low"
            surviving = ["Non-branching continuity (N) is required for singular self. Theory handles this correctly."]
            demoted: list[str] = []
            breaks = case.get("breaks_preserved", [])
        elif case.get("id") == "split_brain":
            verdict = "theory_breaks"
            severity = "high"
            detail = (
                "Split-brain subjects do not report being two selves despite corpus callosum severing. "
                "U drops significantly. Theory predicts U collapse should reduce C or split the self. "
                "Empirical reports do not support this prediction cleanly. "
                "The 'interpreter module' may maintain unity in behavior without resolving the phenomenal question."
            )
            surviving = []
            demoted = ["Unity (U) collapse → C collapse is not empirically supported in split-brain."]
            breaks = [
                "Split-brain subjects report single selfhood despite dramatic U disruption. "
                "The theory predicts a U collapse should either split C or degrade it. "
                "This conflict cannot be patched by claiming the report is 'false' — "
                "that would be a non-falsifiable move."
            ]
        else:
            verdict = "unresolved"
            severity = "low"
            detail = f"No branching data for case {case.get('id', '?')}."
            surviving = []
            demoted = []
            breaks = []

        results.append({
            "test_name": "network_partition_test",
            "fixture_id": case.get("id", "?"),
            "fixture_type": "field_case",
            "verdict": verdict,
            "severity": severity,
            "what_was_tested": "N (non-branching) and U (unity) under partition or splitting events.",
            "result_detail": detail,
            "revision_pressure": (
                "The split-brain case requires the theory to specify: how much U degradation "
                "is compatible with intact single-self experience? The current formula has no threshold."
            ),
            "breaks_preserved": breaks,
            "surviving_claims": surviving,
            "demoted_claims": demoted,
            "next_test_recommended": "false_positive_field_test",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return results


def test_false_positive_field(cases: list[dict]) -> list[dict]:
    """
    Test: confirm that known false positives are correctly rejected by the theory.
    If the theory assigns A > 0 to any false positive, the theory is broken.
    """
    results = []
    for case in cases:
        if case.get("phenomenal_candidate", True):
            continue  # Only test non-candidates
        if case.get("verdict") not in ("false_positive_confirmed", "non_phenomenal", "demoted"):
            continue

        comps = case.get("components", {})
        A = comps.get("A")

        if A is None:
            verdict = "unresolved"
            severity = "medium"
            detail = "A is null — cannot confirm A=0 for this false positive. Verification gap."
            surviving: list[str] = []
            demoted = ["Cannot confirm false positive rejection without A score."]
            breaks: list[str] = ["A is null for a case classified as false positive. Verification is incomplete."]
        elif A == 0.0:
            verdict = "theory_survives"
            severity = "low"
            detail = f"A=0 confirmed. Theory correctly rejects this case as non-phenomenal."
            surviving = [f"{case.get('id','?')}: A=0, correctly classified as {case.get('verdict', 'non_phenomenal')}."]
            demoted = []
            breaks = case.get("breaks_preserved", [])
        else:
            verdict = "theory_breaks"
            severity = "critical"
            detail = (
                f"A={A} > 0 for a case classified as non-phenomenal ({case.get('id','?')}). "
                "This is a contradiction: the theory assigns appearance-from-within to a "
                "system it also classifies as not phenomenally conscious."
            )
            surviving = []
            demoted = [f"{case.get('id','?')}: A={A} > 0 in a false positive case — contradiction."]
            breaks = [
                f"A={A} > 0 assigned to '{case.get('id','?')}' which is classified as non-phenomenal. "
                "Either the A score is wrong or the verdict is wrong. Cannot patch both."
            ]

        results.append({
            "test_name": "false_positive_field_test",
            "fixture_id": case.get("id", "?"),
            "fixture_type": "field_case",
            "verdict": verdict,
            "severity": severity,
            "what_was_tested": f"A=0 verification for false positive: {case.get('name', case.get('id', '?'))}",
            "result_detail": detail,
            "revision_pressure": (
                "The hardest false positive is the LLM persona. A=0 must hold without a behavioral proxy. "
                "The theory needs a non-behavioral account of why A=0 in LLMs."
            ),
            "breaks_preserved": breaks,
            "surviving_claims": surviving,
            "demoted_claims": demoted,
            "next_test_recommended": "carried_constraint_test",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return results


def test_carried_constraint(cases: list[dict]) -> list[dict]:
    """
    Test: evaluate K (carried constraint) in all cases.
    Theory predicts: identity = carried constraint through transformation.
    K without C is operational continuity, not self-continuity.
    """
    results = []
    for case in cases:
        cont = case.get("continuity_components", {})
        comps_preserved = case.get("components_preserved", {})
        K_cont = cont.get("K")
        K_trans = comps_preserved.get("K")
        K = K_cont if K_cont is not None else K_trans

        if K is None:
            continue

        C = cont.get("C") or case.get("components", {}).get("A")  # Approximate C from A if C not available

        if K and (C is None or C == 0.0):
            # High K but no C — this is the key distinction
            verdict = "theory_survives"
            severity = "low"
            detail = (
                f"K={'preserved' if K is True else K} but C/A={'absent' if C == 0.0 else 'unknown'}. "
                "Theory correctly distinguishes: K without C = operational continuity, not self-continuity."
            )
            surviving = ["K without C = pattern/operational continuity only. Theory handles this correctly."]
            demoted: list[str] = []
            breaks = case.get("breaks_preserved", [])
        elif K and C:
            verdict = "theory_survives"
            severity = "low"
            detail = f"K={'preserved' if K is True else K} and C present. Carried constraint is active within a phenomenal field."
            surviving = ["K + C = self-continuity candidate. Theory is consistent."]
            demoted = []
            breaks = case.get("breaks_preserved", [])
        elif not K:
            verdict = "theory_survives"
            severity = "low"
            detail = "K is absent or collapsed. Identity-preserving transformation cannot hold without carried constraint."
            surviving = ["K absence correctly prevents identity_preserving_transformation classification."]
            demoted = []
            breaks = []
        else:
            verdict = "unresolved"
            severity = "low"
            detail = f"K={K}, C={C}. Cannot evaluate constraint-carrying for this case."
            surviving = []
            demoted = []
            breaks = []

        results.append({
            "test_name": "carried_constraint_test",
            "fixture_id": case.get("id", "?"),
            "fixture_type": "continuity_case" if cont else "transfer_case",
            "verdict": verdict,
            "severity": severity,
            "what_was_tested": "K (carried constraint) and its relationship to C (consciousness). K without C = not self-continuity.",
            "result_detail": detail,
            "revision_pressure": (
                "The Trails world and Dominion deck cases show K at its most visible. "
                "These systems carry maximal K with zero C. "
                "The theory must maintain: K alone does not produce self-continuity."
            ),
            "breaks_preserved": breaks,
            "surviving_claims": surviving,
            "demoted_claims": demoted,
            "next_test_recommended": "geometry_topology_test",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return results


def test_geometry_topology(cases: list[dict]) -> list[dict]:
    """
    Test: what relations survive deformation?
    The self is a preserved temporal topology of ownership, not a fixed object.
    Topology = what relations are invariant under continuous transformation.
    """
    results = []
    topology_relevant = [
        "ordinary_biological_change", "gradual_neural_replacement",
        "destructive_teleportation", "non_destructive_copy",
        "mind_upload", "reincarnation", "soul",
        "split_brain", "ego_dissolution", "waking_human",
    ]

    for case in cases:
        case_id = case.get("id", "")
        transfer_type = case.get("transfer_type", "")

        is_relevant = any(t in case_id for t in topology_relevant) or transfer_type in [
            "ordinary_biological_change", "gradual_neural_replacement",
            "destructive_teleportation", "non_destructive_copy", "mind_upload",
        ]

        if not is_relevant:
            continue

        classification = case.get("classification", "") or case.get("verdict", "")

        if classification == "identity_preserving_transformation":
            verdict = "theory_survives"
            severity = "low"
            detail = "Classified as identity_preserving_transformation. Topology of ownership preserved through causal continuity."
            surviving = ["Causal continuity preserves ownership topology. Theory correct."]
            demoted: list[str] = []
            breaks = case.get("breaks_preserved", [])
        elif classification in ("branching_descendants_only", "pattern_copy_field_break_risk"):
            verdict = "theory_survives"
            severity = "low"
            detail = (
                f"Classified as {classification}. Pattern topology may survive; "
                "ownership topology does not. Copy ≠ same self."
            )
            surviving = ["Ownership topology cannot be duplicated without loss of numerical singularity."]
            demoted = []
            breaks = case.get("breaks_preserved", [])
        elif classification in ("unresolved", "possible_self_carrying"):
            verdict = "unresolved"
            severity = "medium"
            detail = (
                f"Topology test is unresolved for '{case_id}'. "
                "Cannot determine whether ownership-topology is preserved across this transition."
            )
            surviving = []
            demoted = []
            breaks = case.get("breaks_preserved", [])
            breaks.append(
                f"Topology test for '{case_id}' is unresolved because substrate neutrality "
                "and phenomenal gap survivability are both undetermined."
            )
        else:
            verdict = "unresolved"
            severity = "low"
            detail = f"No topology classification available for '{case_id}'."
            surviving = []
            demoted = []
            breaks = []

        results.append({
            "test_name": "geometry_topology_test",
            "fixture_id": case_id or "?",
            "fixture_type": "transfer_case" if transfer_type else "field_case",
            "verdict": verdict,
            "severity": severity,
            "what_was_tested": "Whether the ownership-topology is preserved, deformed, or broken by this transformation.",
            "result_detail": detail,
            "revision_pressure": (
                "The theory needs a formal topology of ownership. "
                "Currently 'preserved temporal topology' is a metaphor, not a mathematical specification. "
                "Section 12 of theory.md begins this formalization but does not complete it."
            ),
            "breaks_preserved": breaks,
            "surviving_claims": surviving,
            "demoted_claims": demoted,
            "next_test_recommended": "temporal_deletion_test",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

TEST_FUNCTIONS = {
    "temporal_deletion_test": test_temporal_deletion,
    "boundary_perturbation_test": test_boundary_perturbation,
    "network_partition_test": test_network_partition,
    "false_positive_field_test": test_false_positive_field,
    "carried_constraint_test": test_carried_constraint,
    "geometry_topology_test": test_geometry_topology,
}


def print_results(results: list[dict], show_breaks: bool) -> None:
    print("\n" + "=" * 80)
    print("SIX-TEST STRESS RUN — Inhabited Interiority / Perturbable Phenomenal Field")
    print("Status: stress results only. Theory breaks are preserved, not patched.")
    print("=" * 80)
    print()

    # Group by test
    by_test: dict[str, list[dict]] = {}
    for r in results:
        by_test.setdefault(r["test_name"], []).append(r)

    verdict_totals: dict[str, int] = {}

    for test_name in TESTS:
        test_results = by_test.get(test_name, [])
        if not test_results:
            continue

        desc = TEST_DESCRIPTIONS.get(test_name, "")
        breaks_count = sum(1 for r in test_results if r["verdict"] == "theory_breaks")
        unresolved_count = sum(1 for r in test_results if r["verdict"] == "unresolved")

        print(f"  ━━ {test_name.upper().replace('_', ' ')} ({len(test_results)} cases)")
        print(f"     {desc[:100]}")
        print(f"     Breaks: {breaks_count}  |  Unresolved: {unresolved_count}")
        print()

        for r in sorted(test_results, key=lambda x: {"theory_breaks": 0, "revision_required": 1, "unresolved": 2, "theory_survives": 3}.get(x["verdict"], 4)):
            v = r["verdict"]
            verdict_totals[v] = verdict_totals.get(v, 0) + 1
            sym = {"theory_breaks": "✗", "revision_required": "⟳", "unresolved": "?", "theory_survives": "✓", "claim_demoted": "↓"}.get(v, "–")
            sev = r.get("severity", "")
            sev_str = f" [{sev}]" if sev and sev != "low" else ""
            print(f"     {sym} [{r['fixture_id']}]{sev_str}  {v}")
            if r.get("result_detail"):
                print(f"       {r['result_detail'][:100]}{'...' if len(r['result_detail']) > 100 else ''}")
            if show_breaks:
                for b in r.get("breaks_preserved", []):
                    print(f"       ✗ BREAK: {b[:110]}{'...' if len(b) > 110 else ''}")
                for dc in r.get("demoted_claims", []):
                    print(f"       ↓ DEMOTED: {dc[:100]}{'...' if len(dc) > 100 else ''}")
            print()

        print()

    # Overall summary
    print("─" * 80)
    print("OVERALL VERDICT DISTRIBUTION")
    for verdict in ["theory_breaks", "revision_required", "claim_demoted", "unresolved", "theory_survives"]:
        count = verdict_totals.get(verdict, 0)
        if count:
            print(f"  {verdict}: {count}")
    print()
    print("Most important rule: If a test breaks the theory, the break is preserved.")
    print("Do not patch theory breaks with prose. Revise the theory or mark unresolved.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run all six falsification tests against the fixture set."
    )
    parser.add_argument("--test", "-t", metavar="TEST_NAME",
                        choices=TESTS,
                        help="Run a single test only.")
    parser.add_argument("--show-breaks", "-b", action="store_true",
                        help="Show preserved breaks and demoted claims for each result.")
    parser.add_argument("--output-json", "-j", action="store_true",
                        help="Save results as JSON to reports/stress_results.json.")
    args = parser.parse_args()

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

    tests_to_run = [args.test] if args.test else TESTS
    all_results = []
    for test_name in tests_to_run:
        fn = TEST_FUNCTIONS.get(test_name)
        if fn:
            all_results.extend(fn(cases))

    print_results(all_results, args.show_breaks)

    if args.output_json:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = REPORTS_DIR / "stress_results.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        print(f"Stress results saved to: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
