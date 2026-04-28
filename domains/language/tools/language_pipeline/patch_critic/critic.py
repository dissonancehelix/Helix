"""
Patch critic — evaluates proposed wikitext patches before the operator applies them.

For any proposed rewrite the critic:
  1. Checks anti-patterns in the before and after text
  2. Checks rule engine against the context
  3. Runs sandbox compare (if available)
  4. Classifies overall risk
  5. States whether no-action is the better choice

Patch classes:
  safe                 — apply freely
  review-preferred     — likely fine, but verify rendered output
  risky                — sandbox validation required; real breakage risk
  insufficient-confidence — cannot classify; manual review only
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from domains.language.tools.language_pipeline.anti_patterns import (
    ANTI_PATTERN_LIBRARY, AntiPattern, find_anti_patterns,
)
from domains.language.tools.language_pipeline.rule_engine import RuleEngine
from domains.language.tools.language_pipeline.rule_engine.rules import RuleCheckResult
from domains.language.tools.language_pipeline.sandbox import SandboxValidator, CompareResult
from domains.language.tools.language_pipeline.dossiers import find_dossiers_for_template

PatchClass = Literal["safe", "review-preferred", "risky", "insufficient-confidence"]


@dataclass
class CritiqueResult:
    before: str
    after: str
    patch_class: PatchClass
    risk_summary: str
    anti_patterns_before: list[AntiPattern]    # problems in the before text
    anti_patterns_after: list[AntiPattern]     # problems INTRODUCED by the after text
    anti_patterns_fixed: list[AntiPattern]     # problems RESOLVED by the after text
    rule_check: RuleCheckResult | None
    sandbox_compare: CompareResult | None
    dossier_notes: list[str]
    recommend_no_action: bool
    notes: list[str]

    def display(self) -> str:
        lines = [
            f"[{self.patch_class.upper()}] {self.risk_summary}",
            "",
        ]

        if self.anti_patterns_fixed:
            lines.append("Fixes:")
            for ap in self.anti_patterns_fixed:
                lines.append(f"  ✓ {ap.name}")

        if self.anti_patterns_after:
            lines.append("Introduced problems:")
            for ap in self.anti_patterns_after:
                lines.append(f"  ✗ {ap.name}: {ap.symptom}")

        if self.rule_check and self.rule_check.verdict != "clear":
            lines.append(f"\nRule check ({self.rule_check.verdict.upper()}):")
            for r in self.rule_check.hard_blocks:
                lines.append(f"  BLOCK [{r.policy_code}] {r.name}")
            for r in self.rule_check.soft_concerns:
                lines.append(f"  WARN  [{r.policy_code}] {r.name}")

        if self.sandbox_compare:
            lines.append(f"\nSandbox: {self.sandbox_compare.risk_level.upper()}")
            if self.sandbox_compare.html_changed:
                lines.append("  Output changed.")
            if self.sandbox_compare.sections_added or self.sandbox_compare.sections_removed:
                lines.append(f"  Sections added: {self.sandbox_compare.sections_added}")
                lines.append(f"  Sections removed: {self.sandbox_compare.sections_removed}")

        if self.dossier_notes:
            lines.append("\nDossier notes:")
            for n in self.dossier_notes:
                lines.append(f"  · {n}")

        if self.notes:
            lines.append("\nNotes:")
            for n in self.notes:
                lines.append(f"  - {n}")

        if self.recommend_no_action:
            lines.append("\n⚠ Recommendation: no action — current state may be safer.")

        return "\n".join(lines)


class PatchCritic:
    """
    Evaluates proposed patches before application.

    Usage:
        critic = PatchCritic()
        result = critic.critique(before, after, context="NFL player infobox", tags=["nfl", "blp"])
        print(result.display())

        # With sandbox validation (requires network):
        result = critic.critique(before, after, run_sandbox=True)
    """

    def __init__(self):
        self._rules   = RuleEngine()
        self._sandbox = SandboxValidator()

    def critique(
        self,
        before: str,
        after: str,
        context: str = "",
        tags: list[str] | None = None,
        template_name: str = "",
        run_sandbox: bool = False,
        sandbox_mode: str = "expand",
    ) -> CritiqueResult:

        # 1. Anti-pattern scan
        aps_before = find_anti_patterns(before)
        aps_after  = find_anti_patterns(after)
        ids_before = {ap.id for ap in aps_before}
        ids_after  = {ap.id for ap in aps_after}
        fixed   = [ap for ap in aps_before if ap.id not in ids_after]
        new_aps = [ap for ap in aps_after  if ap.id not in ids_before]

        # 2. Rule check
        full_context = f"{context} {before} {after}".strip()
        rule_check = self._rules.check(full_context, tags=tags)

        # 3. Sandbox compare
        sandbox_cmp: CompareResult | None = None
        if run_sandbox:
            sandbox_cmp = self._sandbox.compare(before, after, mode=sandbox_mode)

        # 4. Dossier notes
        dossier_notes: list[str] = []
        if template_name:
            dossiers = find_dossiers_for_template(template_name)
            for d in dossiers:
                for fz in d.fragile_zones:
                    # Check if any fragile zone keyword appears in the diff text
                    fz_keywords = fz.lower().split()[:4]
                    combined = (before + after).lower()
                    if any(kw in combined for kw in fz_keywords if len(kw) > 3):
                        dossier_notes.append(f"[{d.family_name}] Fragile zone: {fz[:100]}")

        # 5. Risk classification
        notes: list[str] = []
        patch_class, risk_summary = self._classify(
            new_aps, rule_check, sandbox_cmp, notes
        )

        # 6. No-action recommendation
        no_action = (
            patch_class in ("risky", "insufficient-confidence")
            and not fixed
            and (not sandbox_cmp or sandbox_cmp.risk_level != "safe")
        )

        return CritiqueResult(
            before=before,
            after=after,
            patch_class=patch_class,
            risk_summary=risk_summary,
            anti_patterns_before=aps_before,
            anti_patterns_after=new_aps,
            anti_patterns_fixed=fixed,
            rule_check=rule_check,
            sandbox_compare=sandbox_cmp,
            dossier_notes=dossier_notes,
            recommend_no_action=no_action,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _classify(
        new_aps: list[AntiPattern],
        rule_check: RuleCheckResult,
        sandbox_cmp: CompareResult | None,
        notes: list[str],
    ) -> tuple[PatchClass, str]:

        # Hard blocks → risky
        if rule_check.hard_blocks:
            notes.append("Rule engine flagged hard blocks — resolve before applying.")
            return "risky", "Policy hard block present."

        # New high-severity anti-patterns introduced
        high_new = [ap for ap in new_aps if ap.severity == "high"]
        if high_new:
            notes.append(f"Patch introduces {len(high_new)} high-severity anti-pattern(s).")
            return "risky", f"Introduces known anti-pattern(s): {', '.join(ap.name for ap in high_new)}."

        # Sandbox says risky
        if sandbox_cmp and sandbox_cmp.risk_level == "risky":
            notes.append("Sandbox detected structural output change.")
            return "risky", "Sandbox: structural output change detected."

        # Soft concerns or review-level sandbox
        if rule_check.soft_concerns or (sandbox_cmp and sandbox_cmp.risk_level == "review"):
            if rule_check.soft_concerns:
                notes.append(f"Rule concerns: {', '.join(r.name for r in rule_check.soft_concerns)}.")
            return "review-preferred", "Minor concerns — verify rendered output."

        # Medium anti-patterns introduced
        if new_aps:
            notes.append(f"Patch introduces {len(new_aps)} medium/low anti-pattern(s).")
            return "review-preferred", "Medium-risk issues introduced — review before applying."

        # Sandbox clean or not run
        if sandbox_cmp and sandbox_cmp.risk_level == "safe":
            return "safe", "Sandbox confirmed no output change."

        # No signals — safe by absence of evidence
        return "safe", "No anti-patterns, rule blocks, or sandbox issues detected."

