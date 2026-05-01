"""Validate the Appearance-Ownership-Continuity core harness.

This check is intentionally small and read-only. It guards the active text
harness against schema drift, broken local links, accidental promotion of
reports into canon, and failure to preserve report-level negative controls.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "labs" / "appearance_ownership_continuity"
CORE = LAB / "core"

REQUIRED_FILES = [
    "README.md",
    "A_SPLIT.md",
    "PRIMITIVES.md",
    "CLAIM_LEDGER.yaml",
    "TEST_REGISTRY.yaml",
    "FOLLOWUP_CASES.yaml",
    "THEORY_COMPARISON.md",
    "THOUGHT_EXPERIMENTS.md",
    "EMPIRICAL_CONTACTS.md",
    "FALSIFIERS.md",
]

REQUIRED_PRIMITIVES = [
    "field",
    "boundary",
    "interior",
    "ownership",
    "continuity",
    "transformation",
    "branching",
    "reportability",
    "self-model",
    "embodiment",
    "appearance-from-within",
]

COMPARISON_THEORIES = [
    "iit",
    "gnwt",
    "gwt",
    "recurrent processing",
    "higher-order",
    "predictive processing",
    "active inference",
    "self-model theory",
]

CLAIM_REQUIRED = [
    "id",
    "claim",
    "status",
    "owner_location",
    "promotion_state",
]

TEST_REQUIRED = [
    "id",
    "target_claims",
    "test_type",
    "expected_support_pattern",
    "expected_weakening_pattern",
    "output_location",
]

FOLLOWUP_REQUIRED = [
    "id",
    "source_report",
    "target_guardrail",
    "shortcut_under_test",
    "description",
    "observed_features",
    "absent_or_unestablished",
    "forbidden_inferences",
    "expected_result",
]

A_SPLIT_SECTIONS = [
    "## 0. Source Lineage",
    "## 1. Why Split A?",
    "## 2. A0",
    "## 3. A1",
    "## 4. A2",
    "## 5. A3",
    "## 6. A4",
    "## 7. A5",
    "## 8. Bridge Candidate Coverage Matrix",
    "## 9. False-Positive Battery",
    "## 10. Empirical Pressure Points",
    "## 11. AOC/OCH Claim Boundary",
    "## 12. DCP / LIP / EIP Boundary Note",
    "## 13. Next Tests",
]

FORBIDDEN_CLAIM_STATUSES = {"proven", "settled", "final", "confirmed", "solved"}
FORBIDDEN_FOLLOWUP_RESULTS = {"shortcut_allowed", "canon_promoted", "a0_closed", "owner_proven"}
DEFERRED_GUARDRAILS = {"WANTING_NOT_LIKING_DEFERRED", "VALENCE_NONUNITARY_DEFERRED"}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_required_files(errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (CORE / name).is_file():
            fail(errors, f"missing required file: {CORE / name}")
    if not (CORE / "reports").is_dir():
        fail(errors, f"missing reports directory: {CORE / 'reports'}")


def validate_primitives(errors: list[str]) -> None:
    text = (CORE / "PRIMITIVES.md").read_text(encoding="utf-8").lower()
    for primitive in REQUIRED_PRIMITIVES:
        if primitive not in text:
            fail(errors, f"missing primitive definition handle: {primitive}")


def validate_claims(errors: list[str]) -> None:
    data = load_yaml(CORE / "CLAIM_LEDGER.yaml") or {}
    claims = data.get("claims", [])
    if not isinstance(claims, list) or not claims:
        fail(errors, "CLAIM_LEDGER.yaml has no claims list")
        return
    seen: set[str] = set()
    for idx, claim in enumerate(claims, 1):
        cid = claim.get("id")
        if cid in seen:
            fail(errors, f"duplicate claim id: {cid}")
        seen.add(cid)
        for field in CLAIM_REQUIRED:
            if not claim.get(field):
                fail(errors, f"claim {cid or idx} missing field: {field}")
        status = str(claim.get("status", "")).lower()
        if status in FORBIDDEN_CLAIM_STATUSES:
            fail(errors, f"claim {cid or idx} uses forbidden status: {status}")
        if not (claim.get("notes") or claim.get("evidence") or claim.get("rationale")):
            fail(errors, f"claim {cid or idx} missing evidence/rationale handle")
        if not (claim.get("weakens_if") or claim.get("falsifier") or claim.get("relevant_tests")):
            fail(errors, f"claim {cid or idx} missing falsifier/pressure-test handle")


def validate_tests(errors: list[str]) -> None:
    data = load_yaml(CORE / "TEST_REGISTRY.yaml") or {}
    groups = data.get("test_groups", {})
    if not isinstance(groups, dict) or not groups:
        fail(errors, "TEST_REGISTRY.yaml has no test_groups mapping")
        return
    seen: set[str] = set()
    allowed_types = {
        "conceptual",
        "empirical",
        "simulation",
        "analogy",
        "falsifier",
        "operational",
        "mixed",
        "thought_experiment",
        "theory_comparison",
    }
    for group, tests in groups.items():
        if not isinstance(tests, list):
            fail(errors, f"test group {group} is not a list")
            continue
        for idx, test in enumerate(tests, 1):
            tid = test.get("id")
            if tid in seen:
                fail(errors, f"duplicate test id: {tid}")
            seen.add(tid)
            for field in TEST_REQUIRED:
                if not test.get(field):
                    fail(errors, f"test {tid or group + ':' + str(idx)} missing field: {field}")
            if test.get("test_type") not in allowed_types:
                fail(errors, f"test {tid or idx} has unsupported test_type: {test.get('test_type')}")
            if not (test.get("target_claims") or test.get("target_primitives")):
                fail(errors, f"test {tid or idx} missing target claim or primitive")


def validate_followup_cases(errors: list[str]) -> None:
    """Validate executable follow-up cases for report-level guardrails.

    This is intentionally not an empirical classifier. It enforces negative-control
    structure: shortcut-only cases must be blocked, and deferred claims must not
    be promoted by a follow-up case file.
    """
    data = load_yaml(CORE / "FOLLOWUP_CASES.yaml") or {}
    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        fail(errors, "FOLLOWUP_CASES.yaml has no cases list")
        return

    seen: set[str] = set()
    for idx, case in enumerate(cases, 1):
        cid = case.get("id") or f"case:{idx}"
        if cid in seen:
            fail(errors, f"duplicate follow-up case id: {cid}")
        seen.add(cid)
        for field in FOLLOWUP_REQUIRED:
            if not case.get(field):
                fail(errors, f"follow-up case {cid} missing field: {field}")

        observed = set(case.get("observed_features") or [])
        missing = set(case.get("absent_or_unestablished") or [])
        forbidden = set(case.get("forbidden_inferences") or [])
        expected = case.get("expected_result")
        guardrail = str(case.get("target_guardrail") or "")

        if expected in FORBIDDEN_FOLLOWUP_RESULTS:
            fail(errors, f"follow-up case {cid} allows forbidden result: {expected}")
        if expected != "shortcut_blocked":
            fail(errors, f"follow-up case {cid} must currently expect shortcut_blocked, got: {expected}")
        if not observed:
            fail(errors, f"follow-up case {cid} has no observed shortcut features")
        if not missing:
            fail(errors, f"follow-up case {cid} has no absent/unestablished target fields")
        if not forbidden:
            fail(errors, f"follow-up case {cid} has no forbidden inferences")
        if observed & missing:
            fail(errors, f"follow-up case {cid} marks same feature observed and absent: {sorted(observed & missing)}")
        if "appearance_from_within" not in missing and "a0_closure" in forbidden:
            fail(errors, f"follow-up case {cid} forbids A0 closure but does not mark appearance_from_within unestablished")
        if any(item in forbidden for item in {"owner", "owner_preservation", "same_owner_continuity"}):
            if not ({"mineness", "same_owner_continuity"} & missing):
                fail(errors, f"follow-up case {cid} forbids owner inference without missing mineness/continuity")
        if guardrail in DEFERRED_GUARDRAILS and case.get("promotion_allowed", True) is not False:
            fail(errors, f"deferred follow-up case {cid} must set promotion_allowed: false")

    required_shortcuts = {
        "nociception_equals_pain",
        "homeostasis_equals_lived_mattering",
        "self_maintenance_equals_owner",
        "reward_signal_equals_pleasure",
        "pursuit_equals_liking",
    }
    present_shortcuts = {case.get("shortcut_under_test") for case in cases}
    missing_shortcuts = sorted(required_shortcuts - present_shortcuts)
    if missing_shortcuts:
        fail(errors, f"FOLLOWUP_CASES.yaml missing required shortcut tests: {missing_shortcuts}")


def validate_theory_comparison(errors: list[str]) -> None:
    text = (CORE / "THEORY_COMPARISON.md").read_text(encoding="utf-8").lower()
    for theory in COMPARISON_THEORIES:
        if theory not in text:
            fail(errors, f"THEORY_COMPARISON.md missing comparison theory: {theory}")
    replacement_guards = [
        "not replacement",
        "not a replacement",
        "not as a total replacement",
        "comparison pressure, not replacements",
    ]
    if "replacement" in text and not any(guard in text for guard in replacement_guards):
        fail(errors, "THEORY_COMPARISON.md may frame external theories as replacements")


def validate_a_split(errors: list[str]) -> None:
    text = (CORE / "A_SPLIT.md").read_text(encoding="utf-8")
    lower = text.lower()
    for section in A_SPLIT_SECTIONS:
        if section.lower() not in lower:
            fail(errors, f"A_SPLIT.md missing section: {section}")
    for layer in ["a0", "a1", "a2", "a3", "a4", "a5"]:
        if layer not in lower:
            fail(errors, f"A_SPLIT.md missing layer handle: {layer}")
    allowed_statuses = [
        "direct",
        "partial",
        "neighbor",
        "pressure-test",
        "false-positive risk",
        "no coverage",
    ]
    if "| bridge candidate | a0 | a1 | a2 | a3 | a4 | a5 |" not in lower:
        fail(errors, "A_SPLIT.md missing bridge coverage matrix header")
    for status in allowed_statuses:
        if status not in lower:
            fail(errors, f"A_SPLIT.md bridge matrix missing allowed status: {status}")
    for battery_item in [
        "report without ownership",
        "ownership without report",
        "integration without owner",
        "memory without continuity",
        "self-model without a",
        "temporal coding without lived duration",
        "data persistence without i",
        "access without appearance",
        "field without mineness",
    ]:
        if battery_item not in lower:
            fail(errors, f"A_SPLIT.md false-positive battery missing: {battery_item}")
    for boundary in ["aoc may currently claim", "aoc may not claim"]:
        if boundary not in lower:
            fail(errors, f"A_SPLIT.md missing AOC/OCH boundary text: {boundary}")


def validate_active_naming(errors: list[str]) -> None:
    old_terms = [
        "Temporal Ownership Model",
        "Inhabited Continuity Theory",
        "TOM",
        "ICT",
        "temporal_ownership",
    ]
    allowed_alias_markers = [
        "Deprecated working titles",
        "Temporal Ownership Model / TOM",
        "Inhabited Continuity Theory / ICT",
        "historical",
        "deprecated",
        "older",
    ]
    active_files = [
        LAB / "README.md",
        LAB / "THEORY.md",
        CORE / "README.md",
        CORE / "A_SPLIT.md",
        CORE / "CLAIM_LEDGER.yaml",
        CORE / "TEST_REGISTRY.yaml",
        CORE / "THEORY_COMPARISON.md",
    ]
    for path in active_files:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            if not any(term in line for term in old_terms):
                continue
            if any(marker in line for marker in allowed_alias_markers):
                continue
            fail(errors, f"active old umbrella name outside alias section: {path.relative_to(ROOT)}:{line_no}")


def validate_links(errors: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in CORE.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            target = match.group(1).strip()
            if re.match(r"^[a-z]+://", target) or target.startswith("#") or target.startswith("mailto:"):
                continue
            target_path = (path.parent / target.split("#", 1)[0]).resolve()
            if target_path == path.parent.resolve():
                continue
            try:
                target_path.relative_to(ROOT)
            except ValueError:
                fail(errors, f"{path.relative_to(ROOT)} links outside repo: {target}")
                continue
            if target.split("#", 1)[0] and not target_path.exists():
                fail(errors, f"{path.relative_to(ROOT)} has broken link: {target}")


def validate_report_boundaries(errors: list[str]) -> None:
    for path in (CORE / "reports").glob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        suspicious = [
            "promoted to canon",
            "proves aoc",
            "proves och",
            "proves tom",
            "proves ict",
            "proves dcp",
            "proves consciousness",
        ]
        for phrase in suspicious:
            if phrase in text:
                fail(errors, f"report appears to promote claim directly: {path.relative_to(ROOT)} contains '{phrase}'")


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    validate_primitives(errors)
    validate_claims(errors)
    validate_tests(errors)
    validate_followup_cases(errors)
    validate_a_split(errors)
    validate_active_naming(errors)
    validate_theory_comparison(errors)
    validate_links(errors)
    validate_report_boundaries(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Appearance–Ownership–Continuity core check failed ({len(errors)} error(s)).")
        return 1
    print("Appearance–Ownership–Continuity core check passed (0 warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
