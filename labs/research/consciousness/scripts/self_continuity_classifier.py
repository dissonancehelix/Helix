"""
self_continuity_classifier.py
Labs: inhabited_interiority
Purpose: Load all self-continuity YAML fixtures and classify each case using the
         extended self-continuity formula.

Standard:   S = C · P · O · B · K · N
Suspended:  S_suspended = P · O · B · K · N · R  (used when field_status = field_suspended_resumable)

Classification rules:
  - If N = 0.0     → classification cannot be self_continuity_preserved (branching is fatal)
  - If C = 0.0     → self cannot persist (no phenomenal field base)
  - If K high but C = 0.0 and O = 0.0  → pattern_continuity_only or symbolic_continuity_only
  - If K high but C/O/N uncertain       → pattern_continuity_only or self_continuity_candidate
  - If suspension case (R available)    → use suspended formula; classify suspended_self_restart_candidate
  - If branching                        → branching_descendant_not_single_self
  - Destructive transfer / upload       → pattern_continuity_only unless explicit field carrier is specified
  - Soul/reincarnation without carrier  → unproven_portable_carrier

Key language:
  - Pattern survival is not field survival.
  - Field survival is not automatically self survival.
  - Self-continuity requires inhabited ownership carried through time.
  - Branching is fatal to singular self-continuity.

Usage:
    python self_continuity_classifier.py
    python self_continuity_classifier.py --show-scores
    python self_continuity_classifier.py --show-breaks
    python self_continuity_classifier.py --output-json
    python self_continuity_classifier.py --case ordinary_life_change
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
SELF_CONTINUITY_FIXTURES_DIR = LAB_DIR / "fixtures" / "self_continuity"
REPORTS_DIR = LAB_DIR / "reports"

# Try to import YAML; fall back to a minimal parser for this specific file format
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_yaml_fixture(path: Path) -> dict | None:
    """Parse a self-continuity YAML fixture."""
    if HAS_YAML:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    # Minimal fallback parser for the structured YAML format used in this lab
    # Handles: scalars, null, floats, strings, lists (simple), nested objects (scores/evidence)
    content = path.read_text(encoding="utf-8")
    result: dict = {}
    current_key: str | None = None
    current_subkey: str | None = None
    in_block_scalar = False
    block_scalar_key: tuple[str | None, str | None] = (None, None)
    block_lines: list[str] = []
    indent_stack: list[tuple[str, int]] = []  # (key, indent)

    def parse_scalar(val: str):
        val = val.strip()
        if val in ("null", "~", ""):
            return None
        if val in ("true", "True"):
            return True
        if val in ("false", "False"):
            return False
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val.strip("'\"")

    for line in content.splitlines():
        if in_block_scalar:
            stripped = line.rstrip()
            if stripped == "" or stripped[0] == " ":
                block_lines.append(stripped.strip())
            else:
                # End block scalar
                bk_parent, bk_child = block_scalar_key
                block_text = " ".join(block_lines).strip()
                if bk_parent and bk_child:
                    if bk_parent not in result:
                        result[bk_parent] = {}
                    result[bk_parent][bk_child] = block_text
                elif bk_parent:
                    result[bk_parent] = block_text
                in_block_scalar = False
                block_lines = []
                block_scalar_key = (None, None)
                # Fall through to process current line
            if in_block_scalar:
                continue

        stripped_line = line.rstrip()
        if not stripped_line or stripped_line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if ":" in stripped_line:
            colon_pos = stripped_line.index(":")
            key_part = stripped_line[:colon_pos].strip()
            val_part = stripped_line[colon_pos + 1:].strip()

            if indent == 0:
                current_key = key_part
                current_subkey = None
                if val_part == ">":
                    in_block_scalar = True
                    block_scalar_key = (current_key, None)
                    block_lines = []
                elif val_part:
                    result[current_key] = parse_scalar(val_part)
                else:
                    result[current_key] = {}
            elif indent == 2 and current_key:
                current_subkey = key_part
                if val_part == ">":
                    in_block_scalar = True
                    block_scalar_key = (current_key, current_subkey)
                    block_lines = []
                elif val_part:
                    if isinstance(result.get(current_key), dict):
                        result[current_key][current_subkey] = parse_scalar(val_part)
                    else:
                        result[current_key] = {current_subkey: parse_scalar(val_part)}
                else:
                    if not isinstance(result.get(current_key), dict):
                        result[current_key] = {}

    return result if result else None


def load_self_continuity_fixtures() -> list[dict]:
    fixtures = []
    if not SELF_CONTINUITY_FIXTURES_DIR.exists():
        return fixtures
    for yaml_file in sorted(SELF_CONTINUITY_FIXTURES_DIR.glob("*.yaml")):
        try:
            data = parse_yaml_fixture(yaml_file)
            if data and "case_id" in data:
                data["_source_file"] = yaml_file.name
                fixtures.append(data)
        except Exception as e:
            print(f"  [warn] {yaml_file.name}: {e}", file=sys.stderr)
    return fixtures


def is_suspension_case(fixture: dict) -> bool:
    return fixture.get("field_status") in ("field_suspended_resumable",)


def compute_s_score(fixture: dict) -> tuple[float | None, str]:
    """Compute S score using appropriate formula."""
    scores = fixture.get("scores", {})
    if not scores:
        return None, "no_scores"

    if is_suspension_case(fixture):
        # S_suspended = P · O · B · K · N · R
        components = ["P_perspective", "O_ownership", "B_boundary",
                      "K_carried_constraint", "N_non_branching", "R_restart_continuity"]
        formula = "suspended_S = P·O·B·K·N·R"
    else:
        # Standard S = C · P · O · B · K · N
        components = ["C_fielding", "P_perspective", "O_ownership",
                      "B_boundary", "K_carried_constraint", "N_non_branching"]
        formula = "standard_S = C·P·O·B·K·N"

    vals = {k: scores.get(k) for k in components}
    if any(v is None for v in vals.values()):
        return None, f"unresolvable ({formula})"

    product = 1.0
    for v in vals.values():
        product *= v
    return round(product, 6), formula


def classify(fixture: dict, s_score: float | None) -> tuple[str, str, bool]:
    """Returns (classification, rationale, n_override_applied)."""
    scores = fixture.get("scores", {})
    branching = fixture.get("branching_status", "")
    field_status = fixture.get("field_status", "")
    owned = fixture.get("ownership_status", "")
    carried = fixture.get("carried_constraint_status", "")
    expected = fixture.get("expected_classification", "")

    N = scores.get("N_non_branching")
    C = scores.get("C_fielding")
    O = scores.get("O_ownership")
    K = scores.get("K_carried_constraint", 0)
    R = scores.get("R_restart_continuity")

    n_override = False

    # Rule: N = 0 → branching_descendant_not_single_self (overrides everything)
    if N is not None and N == 0.0:
        n_override = True
        return ("branching_descendant_not_single_self",
                "N = 0.0 override: branching is fatal to singular self-continuity regardless of other scores.",
                n_override)

    # Rule: suspension case with R available
    if is_suspension_case(fixture) and R is not None and R > 0:
        if s_score is not None and s_score > 0.5:
            return ("suspended_self_restart_candidate",
                    f"Suspension case with R = {R:.2f}. Suspended formula S = {s_score:.4f}. "
                    "Same causal process resumes. Self-continuity candidate across gap.",
                    n_override)
        return ("suspended_self_restart_candidate",
                f"Suspension case but low S_suspended = {s_score}. "
                "Gap may be problematic even with resuming causal process.",
                n_override)

    # Rule: C = 0 and O = 0 → no phenomenal base for self
    if C is not None and C == 0.0:
        if K is not None and K > 0.7:
            if carried in ("constraint_symbolically_transmitted",):
                return ("symbolic_continuity_only",
                        "C = 0.0 and K is symbolically transmitted. No phenomenal base for self-continuity. "
                        "Symbolic/operational K persists without field.",
                        n_override)
            return ("pattern_continuity_only",
                    "C = 0.0: no phenomenal field. K is preserved but K without C = operational continuity only.",
                    n_override)
        return ("failed_self_continuity",
                "C = 0.0 and K is also low or absent. Self-continuity fails.",
                n_override)

    # Rule: O = 0 → ownership terminated
    if O is not None and O == 0.0:
        if K is not None and K > 0.7:
            return ("pattern_continuity_only",
                    "O = 0.0: ownership-stream terminated. K preserved but K without O = pattern continuity only.",
                    n_override)
        return ("failed_self_continuity",
                "O = 0.0: owned self is absent. Self-continuity fails.",
                n_override)

    # Rule: all null → unproven portable carrier
    if C is None and O is None and R is None:
        if fixture.get("transformation_type") in ("claimed_metaphysical_transfer",):
            return ("unproven_portable_carrier",
                    "All key components null. Metaphysical transfer claimed without specifiable mechanism. "
                    "Carrier is unproven.",
                    n_override)
        return ("unresolved",
                "Key components null. Cannot classify without resolving substrate and field questions.",
                n_override)

    # Rule: branching occurs
    if branching in ("branching_occurs",):
        return ("branching_descendant_not_single_self",
                "branching_status = branching_occurs. Multiple ownership streams. N fails.",
                n_override)

    # Rule: high S score with all components defined
    if s_score is not None:
        if s_score >= 0.7:
            return ("self_continuity_preserved",
                    f"S = {s_score:.4f}. All required components above threshold. "
                    "Self-continuity is preserved under current formula.",
                    n_override)
        if s_score >= 0.2:
            return ("self_continuity_candidate",
                    f"S = {s_score:.4f}. Components partially satisfied. "
                    "Self-continuity is a candidate but not strongly supported.",
                    n_override)
        return ("self_continuity_candidate",
                f"S = {s_score:.4f}. Low but non-zero. Partial self-continuity remains candidate.",
                n_override)

    # Rule: C or O are null (unresolvable key component)
    if C is None or O is None:
        return ("unresolved",
                "C_fielding or O_ownership is null. Self-continuity cannot be resolved without "
                "establishing the phenomenal field and ownership status.",
                n_override)

    # Fallback
    return ("unresolved", "Cannot classify with available data.", n_override)


def bar(score: float | None, width: int = 18) -> str:
    if score is None:
        return "?" * width
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


def print_report(fixtures: list[dict], show_scores: bool, show_breaks: bool,
                 case_filter: str | None) -> list[dict]:
    print("\n" + "=" * 80)
    print("SELF-CONTINUITY CLASSIFIER")
    print("Standard:   S = C · P · O · B · K · N")
    print("Suspended:  S_suspended = P · O · B · K · N · R")
    print("Status: candidate analysis only. No classification is stable or proven.")
    print("=" * 80)
    print()

    results = []
    for fixture in fixtures:
        case_id = fixture.get("case_id", "?")
        if case_filter and case_id != case_filter:
            continue

        s_score, formula = compute_s_score(fixture)
        classification, rationale, n_override = classify(fixture, s_score)
        expected = fixture.get("expected_classification", "")
        match = "✓" if classification == expected else "≠" if expected else "–"

        result = {
            "case_id": case_id,
            "s_score": s_score,
            "formula_used": formula,
            "classification": classification,
            "classification_rationale": rationale,
            "expected_classification": expected,
            "expected_match": classification == expected,
            "n_override_applied": n_override,
            "pattern_survives": fixture.get("carried_constraint_status", "") not in ("constraint_lost",),
            "field_survives": fixture.get("field_status") in ("field_continuous",),
            "ownership_survives": fixture.get("ownership_status") in ("ownership_continuous",),
            "breaks_preserved": fixture.get("breaks_preserved", []),
            "revision_pressure": fixture.get("revision_pressure", ""),
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        score_str = f"{s_score:.6f}" if s_score is not None else "null   "
        print(f"  [{case_id}]")
        print(f"    S score       : {score_str}  [{bar(s_score)}]")
        print(f"    Formula       : {formula}")
        print(f"    Classification: {classification}")
        if n_override:
            print(f"    ⚠ N=0 OVERRIDE: Branching is fatal. Classification forced regardless of other scores.")
        print(f"    Expected      : {expected or '—'}  {match}")

        if show_scores:
            scores = fixture.get("scores", {})
            score_parts = []
            for k in ["C_fielding", "P_perspective", "O_ownership", "B_boundary",
                       "K_carried_constraint", "N_non_branching", "R_restart_continuity"]:
                v = scores.get(k)
                abbrev = {"C_fielding": "C", "P_perspective": "P", "O_ownership": "O",
                          "B_boundary": "B", "K_carried_constraint": "K",
                          "N_non_branching": "N", "R_restart_continuity": "R"}[k]
                v_str = f"{v:.2f}" if v is not None else "null"
                flag = " [!]" if v == 0.0 else " [n/a]" if (k == "R_restart_continuity" and v is None and not is_suspension_case(fixture)) else " [?]" if v is None else ""
                score_parts.append(f"{abbrev}={v_str}{flag}")
            print(f"    Scores        : {' · '.join(score_parts)}")

        rp = fixture.get("revision_pressure", "")
        if rp:
            print(f"    ⟳ Revision    : {rp[:110].strip()}{'...' if len(rp) > 110 else ''}")

        if show_breaks:
            for b in fixture.get("breaks_preserved", []):
                print(f"    ✗ BREAK: {b[:110].strip()}{'...' if len(b) > 110 else ''}")

        print()

    # Summary
    print("─" * 80)
    classifications: dict[str, int] = {}
    for r in results:
        classifications[r["classification"]] = classifications.get(r["classification"], 0) + 1

    print("Classification distribution:")
    ordered = [
        "self_continuity_preserved",
        "self_continuity_candidate",
        "suspended_self_restart_candidate",
        "pattern_continuity_only",
        "symbolic_continuity_only",
        "branching_descendant_not_single_self",
        "partitioned_or_layered_self",
        "personic_rewrite_or_fracture",
        "unproven_portable_carrier",
        "failed_self_continuity",
        "unresolved",
    ]
    for cl in ordered:
        count = classifications.get(cl, 0)
        if count:
            print(f"  {cl}: {count}")
    print()

    expected_mismatches = [r for r in results if r.get("expected_classification") and not r["expected_match"]]
    if expected_mismatches:
        print(f"⚠ Classification mismatches (got ≠ expected): {len(expected_mismatches)}")
        for m in expected_mismatches:
            print(f"  [{m['case_id']}] got: {m['classification']}  expected: {m['expected_classification']}")
        print()

    print("Key rules:")
    print("  — Pattern survival is not field survival.")
    print("  — Field survival is not automatically self survival.")
    print("  — Branching is fatal to singular self-continuity.")
    print("  — A portable carrier must preserve inhabited ownership, not merely information.")
    print()

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Self-continuity classifier: score and classify all self-continuity fixtures."
    )
    parser.add_argument("--show-scores", "-s", action="store_true",
                        help="Show individual component scores.")
    parser.add_argument("--show-breaks", "-b", action="store_true",
                        help="Show preserved theory breaks for each case.")
    parser.add_argument("--output-json", "-j", action="store_true",
                        help="Save classification results to reports/self_continuity_results.json")
    parser.add_argument("--case", "-c", metavar="CASE_ID",
                        help="Show only a single case by ID.")
    args = parser.parse_args()

    if not HAS_YAML:
        print("  [info] PyYAML not installed. Using built-in minimal YAML parser.", file=sys.stderr)
        print("         For full YAML support: pip install pyyaml --break-system-packages", file=sys.stderr)
        print(file=sys.stderr)

    fixtures = load_self_continuity_fixtures()
    if not fixtures:
        print("No self-continuity fixtures found.", file=sys.stderr)
        print(f"Expected at: {SELF_CONTINUITY_FIXTURES_DIR}", file=sys.stderr)
        sys.exit(1)

    results = print_report(fixtures, args.show_scores, args.show_breaks, args.case)

    if args.output_json:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = REPORTS_DIR / "self_continuity_results.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
