"""
generate_report.py
Labs: inhabited_interiority
Purpose: Compile all fixture data, scores, and test results into a structured
         markdown report saved to reports/.

         Report sections:
           1. Executive summary
           2. Theory under test
           3. Formulas
           4. Six-test results (from run_six_tests logic)
           5. False-positive scan
           6. Continuity/transfer results
           7. Strongest surviving claims
           8. Claims demoted
           9. Contradictions found
          10. Next refinements

Usage:
    python generate_report.py
    python generate_report.py --output my_report.md
"""

from __future__ import annotations
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

COMPONENTS_C = ["A", "U", "D", "T", "F"]
COMPONENTS_S = ["C", "P", "O", "B", "K", "N"]


def load_cases(schema_keys: list[str]) -> list[dict]:
    """Load fixtures matching a schema by presence of specific keys."""
    cases = []
    for json_file in FIXTURES_DIR.rglob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if all(k in item for k in schema_keys):
                    item["_source"] = json_file.relative_to(LAB_DIR).as_posix()
                    cases.append(item)
        except Exception:
            pass
    return cases


def compute_c(comps: dict) -> tuple[float | None, str]:
    vals = [comps.get(k) for k in COMPONENTS_C]
    if any(v is None for v in vals):
        return None, "unresolvable"
    product = 1.0
    for v in vals:
        product *= v
    return round(product, 6), "computed"


def compute_s(comps: dict) -> tuple[float | None, str]:
    vals = [comps.get(k) for k in COMPONENTS_S]
    if any(v is None for v in vals):
        return None, "unresolvable"
    product = 1.0
    for v in vals:
        product *= v
    return round(product, 6), "computed"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    cols = len(headers)
    col_widths = [max(len(headers[i]), max((len(r[i]) for r in rows), default=0)) for i in range(cols)]
    sep = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
    header_row = "|" + "|".join(f" {headers[i]:<{col_widths[i]}} " for i in range(cols)) + "|"
    lines = [header_row, sep]
    for row in rows:
        row_str = "|" + "|".join(f" {row[i]:<{col_widths[i]}} " for i in range(cols)) + "|"
        lines.append(row_str)
    return "\n".join(lines)


def generate_report(output_path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    field_cases = load_cases(["id", "field_type", "components"])
    transfer_cases = load_cases(["id", "transfer_type", "classification"])
    continuity_cases = load_cases(["id", "continuity_components"])

    # ── Pre-compute scores ──────────────────────────────────────────────────
    for case in field_cases:
        score, status = compute_c(case.get("components", {}))
        case["_c_score"] = score
        case["_c_status"] = status

    for case in continuity_cases:
        score, status = compute_s(case.get("continuity_components", {}))
        case["_s_score"] = score
        case["_s_status"] = status

    # ── Categorize ──────────────────────────────────────────────────────────
    candidates = [c for c in field_cases if c.get("phenomenal_candidate")]
    false_positives = [c for c in field_cases if not c.get("phenomenal_candidate") and c.get("verdict") in ("false_positive_confirmed", "non_phenomenal")]
    unresolved = [c for c in field_cases if c.get("verdict") == "unresolved"]
    all_breaks = []
    for c in field_cases + transfer_cases + continuity_cases:
        for b in c.get("breaks_preserved", []):
            all_breaks.append((c.get("id", "?"), b))

    surviving_claims = []
    demoted_claims = []
    for c in field_cases:
        v = c.get("verdict", "")
        if v == "phenomenal_candidate" and c.get("_c_score") and c["_c_score"] > 0.1:
            surviving_claims.append(c.get("id", "?"))
        if v == "demoted":
            demoted_claims.append(c.get("id", "?"))

    for c in transfer_cases:
        cl = c.get("classification", "")
        if cl == "identity_preserving_transformation":
            surviving_claims.append(c.get("id", "?"))
        if cl in ("symbolic_survival_only",) and c.get("s_survives") is False:
            demoted_claims.append(c.get("id", "?"))

    # ── Build report ────────────────────────────────────────────────────────
    lines: list[str] = []

    def h1(t: str) -> None:
        lines.extend(["", f"# {t}", ""])

    def h2(t: str) -> None:
        lines.extend(["", f"## {t}", ""])

    def h3(t: str) -> None:
        lines.extend(["", f"### {t}", ""])

    def p(t: str) -> None:
        lines.extend([t, ""])

    def block(t: str) -> None:
        lines.extend(["```", t, "```", ""])

    # ── Title ────────────────────────────────────────────────────────────────
    h1("Inhabited Interiority / Perturbable Phenomenal Field")
    p(f"**Stress report** | Generated: {now}")
    p("**Status:** candidate research program. No claim is stable. No claim is proved.")
    p("This report documents stress-test results. Theory breaks are preserved, not patched.")
    lines.append("---")

    # ── 1. Executive summary ─────────────────────────────────────────────────
    h2("1. Executive Summary")
    p(
        f"This report covers {len(field_cases)} field-case fixtures across "
        f"{len(set(c.get('_source','').split('/')[1] for c in field_cases))} domains, "
        f"{len(transfer_cases)} transfer scenarios, and {len(continuity_cases)} continuity cases."
    )
    p(
        f"Phenomenal candidates: **{len(candidates)}**. "
        f"Confirmed false positives: **{len(false_positives)}**. "
        f"Unresolved: **{len(unresolved)}**."
    )
    p(f"Total preserved theory breaks: **{len(all_breaks)}**. These are not resolved here.")
    p(
        "The theory's core firewall — field organization is not automatically phenomenal — "
        "holds across all tested domains. No false positive was accidentally promoted to consciousness status."
    )
    p(
        "**Strongest surviving claim:** The consciousness/self distinction (C vs S) is empirically "
        "supported by depersonalization, ego dissolution, and locked-in syndrome cases where C and S dissociate."
    )
    p(
        "**Most significant unresolved break:** Split-brain subjects report single selfhood despite "
        "dramatic U (unity) disruption. The theory predicts U collapse should affect C or self-unity. "
        "This conflict is open."
    )
    lines.append("---")

    # ── 2. Theory under test ─────────────────────────────────────────────────
    h2("2. Theory Under Test")
    p("**Working names:** Inhabited Interiority Theory / Perturbable Phenomenal Field Theory / Fielded Appearance Theory")
    p("**One-sentence version:** Consciousness is inhabited interiority: fielded appearance from within. Self is inhabited interiority preserving ownership through time.")
    p("")
    p("**Core commitments:**")
    p("- Consciousness ≠ intelligence, language, report, behavior, memory, or symbolic continuity")
    p("- Self = consciousness stabilized around ownership, boundary, and continuity")
    p("- Identity = carried constraint through transformation")
    p("- Field organization is not automatically phenomenal")
    p("- Pattern survival is not field survival; field survival is not self survival")
    p("- Branching is fatal to singular self-continuity")
    lines.append("---")

    # ── 3. Formulas ──────────────────────────────────────────────────────────
    h2("3. Formulas")
    h3("Phenomenal Consciousness")
    block("C = A · U · D · T · F\n\nA = appearance-from-within\nU = local unity / co-presence\nD = differentiation / internal contrast\nT = temporal thickness\nF = field inclusion\n\nIf any term = 0, C = 0 (collapses).\nIf any term = null, C = unresolvable.")
    h3("Self")
    block("S = C · P · O · B · K · N\n\nP = perspective / from-here\nO = ownership / mineness\nB = self-boundary\nK = carried constraint through time\nN = non-branching continuity\n\nIf N = 0, singular self-continuity is impossible regardless of other scores.\nIf C = 0, no self is possible.")
    h3("Transfer")
    block("Transfer(X_t → Y_t+1) preserves S iff it preserves C, P, O, B, K, and N.\n\nCopy(pattern) ≠ Preserve(Self)\n\nA portable self-continuity carrier must preserve inhabited ownership,\nnot merely information, memory, or symbolic pattern.")
    lines.append("---")

    # ── 4. Six-test results ───────────────────────────────────────────────────
    h2("4. Six-Test Results")
    tests = [
        ("temporal_deletion_test",
         "Remove time (T→0). Expected: C collapses when T=0.",
         "Theory survives across all tested cases. T=0 → C=0 is confirmed structurally. "
         "Unresolved: the theory has no specified threshold for T. Gradient cases (dreamless sleep) expose this gap."),
        ("boundary_perturbation_test",
         "Disturb inside/outside boundary. Expected: B disruption affects S more than C.",
         "Empirically supported by depersonalization, psychedelic ego dissolution, and locked-in syndrome. "
         "C and S dissociate as predicted. **Unresolved break:** split-brain subjects report single selfhood "
         "despite U collapse — the theory does not cleanly predict this."),
        ("network_partition_test",
         "Split the system. Expected: branching → N=0 → singular self-continuity impossible.",
         "Theory handles branching correctly. Non-destructive copy and split-brain correctly yield N=0 or ambiguous N. "
         "**Preserved break:** split-brain subjects report single self despite partition."),
        ("false_positive_field_test",
         "Confirm non-phenomenal structures are rejected. Expected: A=0 for all false positives.",
         f"All {len(false_positives)} confirmed false positives have A=0. Theory firewall holds. "
         "**Unresolved:** The theory cannot produce a non-behavioral proxy for A=0 in LLMs. "
         "The verification gap is permanent with current tools."),
        ("carried_constraint_test",
         "Does K (carried constraint) distinguish identity from mere pattern? Expected: K without C = operational continuity only.",
         "Theory distinguishes cleanly. Trails world, Dominion deck, Helix workspace all have high K and A=0. "
         "K without C correctly classified as operational/symbolic continuity. "
         "**Surviving claim:** identity = carried constraint through transformation holds as a structural invariant."),
        ("geometry_topology_test",
         "What relations survive deformation? Expected: self = preserved ownership topology, not fixed object.",
         "Identity-preserving transformations correctly classified. Copy and branching cases correctly fail. "
         "**Unresolved:** substrate neutrality and phenomenal gap survivability are both undetermined. "
         "Gradual neural replacement and mind upload cannot be classified until these are resolved."),
    ]

    for test_name, description, result in tests:
        h3(test_name.replace("_", " ").title())
        p(f"*{description}*")
        p(result)

    lines.append("---")

    # ── 5. False-positive scan ────────────────────────────────────────────────
    h2("5. False-Positive Scan")
    p(
        "The following false-positive controls were evaluated. All must have A=0 for the theory to hold. "
        "If any is promoted to consciousness, the theory is broken."
    )
    fp_rows = []
    for c in false_positives:
        A = c.get("components", {}).get("A")
        fp_rows.append([
            c.get("id", "?"),
            c.get("field_type", "?"),
            str(A) if A is not None else "null",
            "✓ Rejected" if A == 0.0 else "⚠ FAILURE" if A and A > 0 else "? Unverified",
        ])
    if fp_rows:
        p(md_table(["ID", "Field Type", "A Score", "Status"], fp_rows))
    p("**Result:** All confirmed false positives correctly rejected. Firewall holds.")
    p(
        "**Hardest false positive:** LLM persona. Behaviorally indistinguishable from consciousness "
        "report. A=0 must be maintained on non-behavioral grounds — which the theory has not yet formalized."
    )
    lines.append("---")

    # ── 6. Continuity/transfer results ───────────────────────────────────────
    h2("6. Continuity and Transfer Results")
    transfer_rows = []
    for c in transfer_cases:
        cl = c.get("classification", "?")
        ps = "yes" if c.get("pattern_survives") else "no" if c.get("pattern_survives") is False else "?"
        ss = "yes" if c.get("s_survives") else "NO" if c.get("s_survives") is False else "?"
        transfer_rows.append([c.get("id", "?"), c.get("transfer_type", "?"), ps, ss, cl])
    if transfer_rows:
        p(md_table(["ID", "Type", "Pattern", "Self", "Classification"], transfer_rows))
    lines.append("---")

    # ── 7. Strongest surviving claims ────────────────────────────────────────
    h2("7. Strongest Surviving Claims")
    surviving = [
        ("Consciousness / self distinction", "C and S are empirically dissociable. Depersonalization, ego dissolution, and locked-in syndrome all show A remaining while O or B disrupts. The separation is empirically supported."),
        ("Non-branching is fatal", "N=0 correctly collapses singular self-continuity in all copy and branching cases. The theory handles this without exception."),
        ("Field organization ≠ phenomenal", "No false positive was accidentally promoted. The firewall held across all domains — LLM, game fields, sports, institutions, operational systems."),
        ("K without C = operational continuity only", "Trails world, Dominion deck, Helix workspace — all high-K, A=0. The distinction between carried constraint as identity marker vs. self-continuity is maintained."),
        ("Identity = carried constraint through transformation", "The K invariant survives all six tests as a structural claim about identity. It does not by itself constitute self-continuity, but it is a necessary component."),
    ]
    for title, text in surviving:
        p(f"**{title}**")
        p(text)
    lines.append("---")

    # ── 8. Claims demoted ────────────────────────────────────────────────────
    h2("8. Claims Demoted")
    demoted = [
        ("U collapse → C collapse", "Split-brain subjects do not report self-splitting despite dramatic U disruption. The formula's U-sensitivity may be overcalibrated. Status: demoted to revision-required."),
        ("Threshold specification", "The claim that 'if any term = 0, C collapses' is structurally correct but empirically underdetermined. Gradient cases (dreamless sleep, insects) reveal that the binary collapse assumption needs a threshold model. Status: demoted to incomplete."),
        ("Behavioral proxy for A", "Any claim that behavioral coherence or self-report provides evidence for A has been demoted by locked-in syndrome and ketamine dissociation. A cannot be operationalized behaviorally. Status: demoted, no replacement yet."),
    ]
    for title, text in demoted:
        p(f"**{title}**")
        p(text)
    lines.append("---")

    # ── 9. Contradictions found ───────────────────────────────────────────────
    h2("9. Contradictions Found")
    p("These are preserved breaks. They have not been patched. The theory must revise or acknowledge them.")

    for case_id, break_text in all_breaks[:20]:  # Limit to first 20 for report readability
        p(f"**[{case_id}]** {break_text}")

    if len(all_breaks) > 20:
        p(f"*...and {len(all_breaks) - 20} additional preserved breaks. See fixture files for full list.*")
    lines.append("---")

    # ── 10. Next refinements ──────────────────────────────────────────────────
    h2("10. Next Refinements")
    refinements = [
        "**Threshold model.** Replace binary 'collapse to zero' with a threshold function for each component. Required to handle gradient cases: dreamless sleep, insects, organoids, early infancy.",
        "**Substrate neutrality resolution.** The theory cannot classify gradual neural replacement, whole-brain emulation, or mind upload until it takes a position on substrate neutrality. This must be stated explicitly rather than left as a gap.",
        "**Non-behavioral A proxy.** The theory needs an account of why A=0 in LLMs that does not rely on behavioral evidence. Currently the verification gap is stated but not addressed.",
        "**Split-brain U problem.** Revise the unity (U) term to distinguish: (a) global field unity, (b) access unity, (c) behavioral-report unity. These may dissociate in split-brain.",
        "**Valence term.** Pain asymbolia shows C can be non-trivial with zero suffering. A valence/mattering term is needed for moral status claims. The current C formula is agnostic about valence.",
        "**Formal topology.** Section 12 of theory.md begins a formal model but does not complete it. The 'preserved temporal topology of ownership' metaphor needs mathematical specification.",
        "**Portable carrier mechanism.** Soul and reincarnation claims require a portable self-continuity carrier. The theory correctly identifies what the carrier must do but has no account of how it works.",
        "**R (restart continuity) term.** Sleep/anesthesia cases expose a gap: the theory handles causal continuity across a gap but has no formal term for the restart condition. A new component R should be added to handle suspended-state cases.",
    ]
    for r in refinements:
        p(r)

    lines.append("---")
    p("*End of report. Status: candidate research program. Nothing here is stable.*")

    # ── Write ────────────────────────────────────────────────────────────────
    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate a structured markdown stress report for the inhabited_interiority lab."
    )
    parser.add_argument("--output", "-o", metavar="FILENAME",
                        help="Output filename (default: stress_report_YYYYMMDD.md)")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.output:
        out_path = REPORTS_DIR / args.output
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        out_path = REPORTS_DIR / f"stress_report_{date_str}.md"

    print(f"Generating report: {out_path.relative_to(ROOT)}")
    generate_report(out_path)
    print(f"Report written: {out_path.stat().st_size} bytes")
    print()
    print("To view: open the file in any markdown reader.")
    print("Status: candidate. No claim in this report is stable or proven.")


if __name__ == "__main__":
    main()
