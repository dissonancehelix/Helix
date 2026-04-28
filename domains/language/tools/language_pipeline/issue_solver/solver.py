"""
Issue solver — operator-facing tools for Wikipedia template/wikitext work.

Phase 2 upgrade: wired into pattern mining, template family dossiers,
rule precedence engine, anti-pattern library, and patch critic.
All operations remain read-only with respect to Wikipedia.

Available operations:
  inspect_template(name)               — fetch + summarize a template with dossier context
  explain_template_logic(snippet)      — parser-backed + structural explanation
  validate_snippet(wikitext)           — sandbox + anti-pattern + rule check
  compare_before_after(old, new)       — sandbox diff + patch critic
  suggest_safe_rewrite(snippet)        — pattern library + critic-filtered proposals
  find_similar_past_patterns(snippet)  — pattern library + mined history patterns
  propose_patch(issue_description)     — full patch proposal with critic review
"""
from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from typing import Literal

from domains.language.tools.language_pipeline.template_index import TemplateIndexer
from domains.language.tools.language_pipeline.sandbox import SandboxValidator, ValidationResult, CompareResult
from domains.language.tools.language_pipeline.pattern_library import (
    PATTERN_LIBRARY, WikiPattern, find_matching_patterns,
)
from domains.language.tools.language_pipeline.anti_patterns import (
    ANTI_PATTERN_LIBRARY, AntiPattern, find_anti_patterns,
)
from domains.language.tools.language_pipeline.dossiers import (
    find_dossiers_for_template, TemplateFamilyDossier,
)
from domains.language.tools.language_pipeline.rule_engine import RuleEngine, RuleCheckResult
from domains.language.tools.language_pipeline.patch_critic import PatchCritic, CritiqueResult

PatchClass = Literal["safe", "review-preferred", "risky", "needs-sandbox"]


@dataclass
class TemplateSummary:
    name: str
    description: str
    param_count: int
    required_params: list[str]
    optional_params: list[str]
    dependencies: list[str]
    has_templatedata: bool
    has_doc: bool
    dossier_families: list[str]         # e.g. ["NFL", "BLP"]
    fragile_zones: list[str]            # from dossier
    relevant_policies: list[str]        # from dossier
    notes: list[str]

    def display(self) -> str:
        lines = [
            f"Template: {self.name}",
            f"Description: {self.description or '(none)'}",
            f"Parameters: {self.param_count} total, "
            f"{len(self.required_params)} required, "
            f"{len(self.optional_params)} optional",
        ]
        if self.required_params:
            lines.append(f"  Required: {', '.join(self.required_params)}")
        if self.optional_params[:10]:
            lines.append(f"  Optional (first 10): {', '.join(self.optional_params[:10])}")
        if self.dependencies:
            lines.append(f"Dependencies: {', '.join(self.dependencies[:10])}")
        if self.dossier_families:
            lines.append(f"Dossier families: {', '.join(self.dossier_families)}")
        if self.fragile_zones:
            lines.append("Fragile zones:")
            for fz in self.fragile_zones[:3]:
                lines.append(f"  ! {fz}")
        if self.relevant_policies:
            lines.append(f"Policies: {', '.join(self.relevant_policies)}")
        lines.append(f"TemplateData: {'yes' if self.has_templatedata else 'no'}")
        lines.append(f"Has /doc: {'yes' if self.has_doc else 'no'}")
        for n in self.notes:
            lines.append(f"Note: {n}")
        return "\n".join(lines)


@dataclass
class PatchProposal:
    title: str
    patch_class: PatchClass
    description: str
    before: str
    after: str
    risk_notes: str
    validation_recommended: bool
    pattern_used: str | None
    critique: CritiqueResult | None = None

    def display(self) -> str:
        lines = [
            f"[{self.patch_class.upper()}] {self.title}",
            "",
            self.description,
            "",
            "BEFORE:",
            textwrap.indent(self.before, "  "),
            "",
            "AFTER:",
            textwrap.indent(self.after, "  "),
            "",
            f"Risk: {self.risk_notes}",
        ]
        if self.validation_recommended:
            lines.append("Sandbox validation recommended before applying.")
        if self.pattern_used:
            lines.append(f"Pattern: {self.pattern_used}")
        if self.critique:
            lines.append("")
            lines.append("Critic:")
            lines.append(textwrap.indent(self.critique.display(), "  "))
        return "\n".join(lines)


class IssueSolver:
    """
    Operator-facing Wikipedia issue solver.
    Phase 2: wired into dossiers, rule engine, anti-patterns, and patch critic.
    """

    def __init__(self):
        self._indexer  = TemplateIndexer()
        self._sandbox  = SandboxValidator()
        self._rules    = RuleEngine()
        self._critic   = PatchCritic()

    # ------------------------------------------------------------------
    # inspect_template — Phase 2: adds dossier + anti-pattern context
    # ------------------------------------------------------------------

    def inspect_template(self, template_name: str) -> TemplateSummary:
        name = template_name.removeprefix("Template:")
        record = self._indexer.load_cached(name)
        if record is None:
            record = self._indexer.fetch(name)

        notes: list[str] = []
        if record.fetch_error:
            notes.append(f"Fetch error: {record.fetch_error}")
        if not record.source_wikitext and not record.fetch_error:
            notes.append("Template source not available")
        if not record.templatedata and not record.doc_wikitext:
            notes.append("No TemplateData or /doc — parameter behavior undocumented")

        # Dossier enrichment
        dossiers = find_dossiers_for_template(name)
        dossier_families = [d.family_name for d in dossiers]
        fragile_zones = []
        relevant_policies: list[str] = []
        for d in dossiers:
            fragile_zones.extend(d.fragile_zones)
            relevant_policies.extend(d.relevant_policies)

        # Anti-pattern scan of template source
        if record.source_wikitext:
            aps = find_anti_patterns(record.source_wikitext)
            for ap in aps[:3]:
                notes.append(f"Anti-pattern in source: {ap.name}")

        req = [p.name for p in record.params if p.required]
        opt = [p.name for p in record.params if not p.required]

        return TemplateSummary(
            name=record.name,
            description=record.description,
            param_count=len(record.params),
            required_params=req,
            optional_params=opt,
            dependencies=record.dependencies,
            has_templatedata=bool(record.templatedata),
            has_doc=bool(record.doc_wikitext),
            dossier_families=dossier_families,
            fragile_zones=list(dict.fromkeys(fragile_zones))[:5],
            relevant_policies=sorted(set(relevant_policies)),
            notes=notes,
        )

    # ------------------------------------------------------------------
    # explain_template_logic — Phase 2: sandbox-backed where possible
    # ------------------------------------------------------------------

    def explain_template_logic(
        self,
        snippet: str,
        use_sandbox: bool = True,
        test_params: dict[str, str] | None = None,
    ) -> str:
        """
        Explain what a wikitext snippet does.

        Phase 2 improvement:
          - First runs structural analysis (regex-based shape description)
          - Then runs sandbox to show actual behavior under test params
          - Distinguishes source-shape from rendered-behavior
        """
        lines: list[str] = ["── Source shape ──"]
        lines.extend(self._structural_explanation(snippet))

        # Anti-pattern check
        aps = find_anti_patterns(snippet)
        if aps:
            lines.append("")
            lines.append("── Anti-patterns detected ──")
            for ap in aps:
                lines.append(f"  [{ap.severity.upper()}] {ap.name}: {ap.symptom}")

        # Sandbox-backed behavior
        if use_sandbox:
            lines.append("")
            lines.append("── Rendered behavior (sandbox) ──")

            # Test with empty params
            result_empty = self._sandbox.expand(snippet, "Sandbox")
            if result_empty.success:
                expanded = (result_empty.expanded_wikitext or "").strip()
                lines.append(f"With no params:   {repr(expanded[:120]) if expanded else '(empty)'}")
            elif result_empty.errors:
                lines.append(f"Error (no params): {result_empty.errors[0]}")

            # Test with provided params if given
            if test_params:
                # Build a test transclusion by substituting params into snippet
                test_snippet = snippet
                for k, v in test_params.items():
                    test_snippet = test_snippet.replace(f"{{{{{k}|", f"PARAM_START_{v}_")
                # Actually just show what params were tested
                lines.append(f"Test params: {test_params}")
                result_test = self._sandbox.expand(test_snippet, "Sandbox")
                if result_test.success:
                    expanded = (result_test.expanded_wikitext or "").strip()
                    lines.append(f"With test params: {repr(expanded[:120]) if expanded else '(empty)'}")

        return "\n".join(lines)

    def _structural_explanation(self, snippet: str) -> list[str]:
        """Static structural analysis — shape only, not behavior."""
        lines: list[str] = []

        if "{{#if:" in snippet:
            lines.append("#if: conditional — non-empty/non-zero → first branch, else second.")
            if re.search(r"\{\{\{[^|{}]+\}\}\}", snippet):
                lines.append("  Warning: bare parameter(s) without fallback pipe detected.")

        if "{{#ifeq:" in snippet:
            lines.append("#ifeq: string equality test (case-sensitive).")

        if "{{#switch:" in snippet:
            lines.append("#switch: multi-branch string match.")
            if "#default" not in snippet:
                lines.append("  Warning: no #default — unmatched values produce empty output.")

        if "{{#ifexpr:" in snippet:
            lines.append("#ifexpr: numeric expression. Non-numeric input causes parser error.")

        if "{{#expr:" in snippet:
            lines.append("#expr: arithmetic expression output.")

        bare = re.findall(r"\{\{\{([^|{}]+)\}\}\}", snippet)
        if bare:
            lines.append(f"Bare parameter refs (no fallback): {', '.join(set(bare))}")

        if "{{PAGENAME}}" in snippet or "{{FULLPAGENAME}}" in snippet:
            lines.append("Uses PAGENAME magic word — output varies by transclusion context.")

        if not lines:
            lines.append("Standard wikitext or transclusion — no parser function logic detected.")

        return lines

    # ------------------------------------------------------------------
    # validate_snippet — Phase 2: adds anti-pattern + rule check
    # ------------------------------------------------------------------

    def validate_snippet(
        self,
        wikitext: str,
        title: str = "Sandbox",
        tags: list[str] | None = None,
    ) -> dict:
        """
        Validate a wikitext snippet.
        Returns sandbox result + anti-patterns + rule check combined.
        """
        sandbox_result = self._sandbox.expand(wikitext, title)
        aps = find_anti_patterns(wikitext)
        rule_check = self._rules.check(wikitext, tags=tags)

        return {
            "sandbox": sandbox_result,
            "anti_patterns": aps,
            "rule_check": rule_check,
            "verdict": self._combined_verdict(sandbox_result, aps, rule_check),
        }

    # ------------------------------------------------------------------
    # compare_before_after — Phase 2: runs full patch critic
    # ------------------------------------------------------------------

    def compare_before_after(
        self,
        old_text: str,
        new_text: str,
        context: str = "",
        tags: list[str] | None = None,
        template_name: str = "",
        run_sandbox: bool = True,
    ) -> CritiqueResult:
        """
        Compare before/after through patch critic (sandbox + rules + anti-patterns).
        """
        return self._critic.critique(
            before=old_text,
            after=new_text,
            context=context,
            tags=tags,
            template_name=template_name,
            run_sandbox=run_sandbox,
        )

    # ------------------------------------------------------------------
    # suggest_safe_rewrite — Phase 2: critic-filtered
    # ------------------------------------------------------------------

    def suggest_safe_rewrite(self, snippet: str) -> list[PatchProposal]:
        matching = find_matching_patterns(snippet)
        proposals: list[PatchProposal] = []

        for pattern in matching:
            critique = self._critic.critique(
                before=snippet,
                after=pattern.after,
                run_sandbox=False,
            )
            proposals.append(PatchProposal(
                title=pattern.name,
                patch_class=self._risk_to_patch_class(pattern.risk),
                description=pattern.purpose,
                before=pattern.before,
                after=pattern.after,
                risk_notes=pattern.risk_notes,
                validation_recommended=(pattern.risk != "safe"),
                pattern_used=pattern.id,
                critique=critique,
            ))

        return proposals

    # ------------------------------------------------------------------
    # find_similar_past_patterns
    # ------------------------------------------------------------------

    def find_similar_past_patterns(self, snippet: str) -> list[WikiPattern]:
        return find_matching_patterns(snippet)

    # ------------------------------------------------------------------
    # propose_patch — Phase 2: full critic review on proposal
    # ------------------------------------------------------------------

    def propose_patch(
        self,
        issue_description: str,
        snippet: str = "",
        template_name: str = "",
        tags: list[str] | None = None,
    ) -> PatchProposal:
        issue_lower = issue_description.lower()

        # Route to pattern
        matched_pattern: WikiPattern | None = None
        for pattern in PATTERN_LIBRARY:
            if any(k.lower() in issue_lower for k in pattern.keywords):
                matched_pattern = pattern
                break

        if matched_pattern:
            before = snippet or matched_pattern.before
            after = matched_pattern.after
            critique = self._critic.critique(
                before=before,
                after=after,
                context=issue_description,
                tags=tags,
                template_name=template_name,
                run_sandbox=False,
            )
            return PatchProposal(
                title=f"Proposed: {matched_pattern.name}",
                patch_class=self._risk_to_patch_class(matched_pattern.risk),
                description=matched_pattern.purpose,
                before=before,
                after=after,
                risk_notes=matched_pattern.risk_notes,
                validation_recommended=(matched_pattern.risk != "safe"),
                pattern_used=matched_pattern.id,
                critique=critique,
            )

        # Check rule engine for context-based guidance
        rule_check = self._rules.check(issue_description, tags=tags)
        rule_notes = ""
        if rule_check.hard_blocks:
            rule_notes = f"Hard blocks: {', '.join(r.name for r in rule_check.hard_blocks)}"
        elif rule_check.soft_concerns:
            rule_notes = f"Concerns: {', '.join(r.name for r in rule_check.soft_concerns)}"

        return PatchProposal(
            title="Insufficient confidence — manual review required",
            patch_class="needs-sandbox",
            description=(
                f"No pattern matched '{issue_description}'. "
                + (f"Rule engine notes: {rule_notes}. " if rule_notes else "")
                + "Run validate_snippet() or compare_before_after() to inspect manually."
            ),
            before=snippet,
            after="",
            risk_notes="Cannot classify without pattern match.",
            validation_recommended=True,
            pattern_used=None,
            critique=None,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _risk_to_patch_class(risk: str) -> PatchClass:
        return {
            "safe": "safe",
            "review": "review-preferred",
            "risky": "risky",
        }.get(risk, "needs-sandbox")

    @staticmethod
    def _combined_verdict(
        sandbox_result,
        aps: list[AntiPattern],
        rule_check: RuleCheckResult,
    ) -> str:
        issues = []
        if not sandbox_result.success:
            issues.append("sandbox errors")
        if any(ap.severity == "high" for ap in aps):
            issues.append("high-severity anti-patterns")
        if rule_check.hard_blocks:
            issues.append("rule hard blocks")
        if issues:
            return f"BLOCKED: {', '.join(issues)}"
        soft = []
        if any(ap.severity == "medium" for ap in aps):
            soft.append("medium anti-patterns")
        if rule_check.soft_concerns:
            soft.append("rule concerns")
        if sandbox_result.warnings:
            soft.append("sandbox warnings")
        if soft:
            return f"CONCERNS: {', '.join(soft)}"
        return "CLEAR"

