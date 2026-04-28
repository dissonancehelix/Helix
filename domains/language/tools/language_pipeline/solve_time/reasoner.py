"""
Solve-time reasoner — Phase 1.4.

Unified coordinator for Wikipedia template/wikitext issue resolution.
Takes user-fed inputs and produces structured solve-time diagnostics.

Core design principle:
    Three truths are kept SEPARATE in all outputs.

    rule_truth      — what the policies/rules say about this input
    mechanical_truth — what the code/template actually does (sandbox-backed where possible)
    operator_truth  — how the operator (Dissident93) typically solves this class of problem

This separation prevents the common failure of collapsing policy citation,
parser behavior, and personal preference into a single vague answer.

Entry points (Part J interface):
    inspect_issue(input)                  — full diagnostic
    explain_template_behavior(template_or_snippet) — parser-backed explanation
    classify_patch_risk(old, new, context) — risk classification
    find_related_family(template_or_snippet) — template family lookup
    resolve_rule_priority(context)         — rule precedence
    suggest_safe_rewrite(input)            — filtered patch proposals
    compare_behavior(before, after, context) — behavior diff
    find_operator_style_matches(input)     — operator pattern match

All operations are read-only with respect to Wikipedia.
No autonomous editing. Advisory-only.
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any, Literal

from domains.language.tools.language_pipeline.issue_solver import IssueSolver, PatchProposal, TemplateSummary
from domains.language.tools.language_pipeline.rule_engine import RuleEngine
from domains.language.tools.language_pipeline.rule_engine.rules import RuleCheckResult, PolicyRule
from domains.language.tools.language_pipeline.patch_critic import PatchCritic, CritiqueResult
from domains.language.tools.language_pipeline.anti_patterns import find_anti_patterns, AntiPattern
from domains.language.tools.language_pipeline.template_families.extractor import assign_family, FAMILY_POLICIES
from domains.language.tools.language_pipeline.solve_time.archetype_detector import (
    detect_archetype, ArchetypeResult, ARCHETYPE_POLICY_PRIORITY,
)
from domains.language.tools.language_pipeline.solve_time.operator_pattern_matcher import (
    OperatorPatternMatcher, PatternMatchResult,
)

PatchRiskClass = Literal["safe", "review-preferred", "risky", "insufficient-confidence"]

# ---------------------------------------------------------------------------
# Input / Output data classes
# ---------------------------------------------------------------------------

@dataclass
class SolveTimeInput:
    """
    Normalised input to the solve-time reasoner.
    All fields are optional — the reasoner degrades gracefully when some are absent.
    """
    template_name: str = ""       # e.g. "Infobox NFL player"
    snippet: str = ""             # wikitext fragment to analyse
    before: str = ""              # before-patch text (for risk classification)
    after: str = ""               # after-patch text
    context: str = ""             # free-text context / issue description
    article_title: str = ""       # article being worked on (if known)
    tags: list[str] = field(default_factory=list)  # domain tags e.g. ["nfl", "blp"]
    run_sandbox: bool = True      # whether to make live API calls

    @property
    def primary_text(self) -> str:
        """The most content-rich field — used for keyword-based matching."""
        return self.snippet or self.before or self.context or self.template_name

    @classmethod
    def from_snippet(cls, snippet: str, **kwargs) -> "SolveTimeInput":
        return cls(snippet=snippet, **kwargs)

    @classmethod
    def from_patch(cls, before: str, after: str, context: str = "", **kwargs) -> "SolveTimeInput":
        return cls(before=before, after=after, context=context, **kwargs)

    @classmethod
    def from_template(cls, template_name: str, **kwargs) -> "SolveTimeInput":
        return cls(template_name=template_name, **kwargs)


@dataclass
class RuleTruth:
    """What the policies and rules say about this input."""
    primary_policy: str               # single dominant policy code
    all_applicable: list[str]         # policy codes, precedence order
    hard_blocks: list[str]            # rule names that are hard blocks
    soft_concerns: list[str]          # rule names that are soft concerns
    advisories: list[str]             # advisory rule names
    conflicts: list[str]              # detected policy conflicts
    verdict: str                      # "clear" | "concerns" | "blocked"
    raw: RuleCheckResult | None = None

    def display(self) -> str:
        lines = [
            f"Rule truth — primary: {self.primary_policy}  verdict: {self.verdict.upper()}",
            f"  Applicable policies: {', '.join(self.all_applicable)}",
        ]
        if self.hard_blocks:
            lines.append(f"  HARD BLOCKS: {', '.join(self.hard_blocks)}")
        if self.soft_concerns:
            lines.append(f"  CONCERNS: {', '.join(self.soft_concerns)}")
        if self.advisories:
            lines.append(f"  Advisories: {', '.join(self.advisories)}")
        if self.conflicts:
            lines.append(f"  Conflicts: {', '.join(self.conflicts)}")
        return "\n".join(lines)


@dataclass
class MechanicalTruth:
    """What the code/template actually does."""
    source_shape: list[str]           # structural analysis (parser functions, bare params)
    expanded_behavior: str            # sandbox expand result (empty-param test)
    rendered_behavior: str            # action=parse result (if requested)
    anti_pattern_names: list[str]     # anti-patterns detected in snippet
    fragility_notes: list[str]        # from family dossier / family extractor
    alias_params: list[str]           # alias params detected
    branch_summary: str               # which branches / fallback chains present
    sandbox_ok: bool                  # whether sandbox returned without errors

    def display(self) -> str:
        lines = ["Mechanical truth:"]
        for line in self.source_shape:
            lines.append(f"  {line}")
        if self.expanded_behavior:
            lines.append(f"  Expanded (no params): {self.expanded_behavior[:120]}")
        if self.anti_pattern_names:
            lines.append(f"  Anti-patterns: {', '.join(self.anti_pattern_names)}")
        if self.fragility_notes:
            lines.append("  Fragility notes:")
            for fn in self.fragility_notes[:4]:
                lines.append(f"    ! {fn}")
        return "\n".join(lines)


@dataclass
class OperatorTruth:
    """How the operator (Dissident93) typically handles this class of problem."""
    library_pattern_matches: list[str]   # matched pattern names from pattern library
    mined_pattern_matches: list[str]     # matched cluster names from history
    top_recommendation: str              # best operator-style suggestion
    compatibility_warning: str           # if evidence suggests "leave it alone"
    operator_style_notes: list[str]      # inferred style preferences

    def display(self) -> str:
        lines = ["Operator truth:"]
        if self.library_pattern_matches:
            lines.append(f"  Library matches: {', '.join(self.library_pattern_matches[:4])}")
        if self.mined_pattern_matches:
            lines.append(f"  History matches: {', '.join(self.mined_pattern_matches[:4])}")
        if self.top_recommendation:
            lines.append(f"  Recommendation: {self.top_recommendation}")
        if self.compatibility_warning:
            lines.append(f"  Compatibility: {self.compatibility_warning}")
        for note in self.operator_style_notes[:3]:
            lines.append(f"  Style: {note}")
        return "\n".join(lines)


@dataclass
class SolveTimeResult:
    """
    Full solve-time diagnostic.

    The three-truth structure is preserved at the top level.
    Fields below are cross-cutting summary/action items.
    """
    # Input echo
    input_summary: str

    # Three truths (kept separate)
    rule_truth: RuleTruth
    mechanical_truth: MechanicalTruth
    operator_truth: OperatorTruth

    # Cross-cutting
    template_family: str              # e.g. "nfl_biography" | "unknown"
    article_archetype: ArchetypeResult
    issue_type: str                   # "template_logic" | "policy" | "style" | "patch" | "unknown"
    recommended_action: str           # concise action recommendation
    patch_risk_class: PatchRiskClass | None  # None when no patch provided
    validation_advice: str            # concrete next step for validation

    # Optional extras
    patch_proposals: list[PatchProposal] = field(default_factory=list)
    critique: CritiqueResult | None = None

    def display(self, compact: bool = False) -> str:
        lines = [
            "=" * 60,
            f"SOLVE-TIME DIAGNOSTIC",
            "=" * 60,
            f"Input:    {self.input_summary}",
            f"Family:   {self.template_family}",
            f"Archetype:{self.article_archetype.archetype}  "
            f"[{self.article_archetype.confidence}]",
            f"Issue:    {self.issue_type}",
            "",
            self.rule_truth.display(),
            "",
            self.mechanical_truth.display(),
            "",
            self.operator_truth.display(),
            "",
            "─" * 40,
            f"RECOMMENDED ACTION: {self.recommended_action}",
        ]
        if self.patch_risk_class:
            lines.append(f"PATCH RISK CLASS: {self.patch_risk_class.upper()}")
        lines.append(f"VALIDATION ADVICE: {self.validation_advice}")
        if self.critique and not compact:
            lines.append("")
            lines.append("Critic output:")
            lines.append(textwrap.indent(self.critique.display(), "  "))
        if self.patch_proposals and not compact:
            lines.append("")
            lines.append("Patch proposals:")
            for p in self.patch_proposals[:3]:
                lines.append(textwrap.indent(p.display(), "  "))
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "input_summary": self.input_summary,
            "template_family": self.template_family,
            "article_archetype": {
                "archetype": self.article_archetype.archetype,
                "confidence": self.article_archetype.confidence,
                "policy_priority": self.article_archetype.policy_priority,
            },
            "issue_type": self.issue_type,
            "rule_truth": {
                "primary_policy": self.rule_truth.primary_policy,
                "applicable_policies": self.rule_truth.all_applicable,
                "verdict": self.rule_truth.verdict,
                "hard_blocks": self.rule_truth.hard_blocks,
                "soft_concerns": self.rule_truth.soft_concerns,
                "conflicts": self.rule_truth.conflicts,
            },
            "mechanical_truth": {
                "source_shape": self.mechanical_truth.source_shape,
                "expanded_behavior": self.mechanical_truth.expanded_behavior,
                "anti_patterns": self.mechanical_truth.anti_pattern_names,
                "fragility_notes": self.mechanical_truth.fragility_notes,
                "sandbox_ok": self.mechanical_truth.sandbox_ok,
            },
            "operator_truth": {
                "library_matches": self.operator_truth.library_pattern_matches,
                "mined_matches": self.operator_truth.mined_pattern_matches,
                "top_recommendation": self.operator_truth.top_recommendation,
                "style_notes": self.operator_truth.operator_style_notes,
            },
            "recommended_action": self.recommended_action,
            "patch_risk_class": self.patch_risk_class,
            "validation_advice": self.validation_advice,
        }


# ---------------------------------------------------------------------------
# Reasoner
# ---------------------------------------------------------------------------

class SolveTimeReasoner:
    """
    Phase 1.4 solve-time reasoning coordinator.

    Orchestrates all existing Wikipedia operator subsystems around
    a unified three-truth output model.

    All operations are read-only with respect to Wikipedia.
    No autonomous editing. Advisory-only.
    """

    def __init__(self, run_sandbox_by_default: bool = True):
        self._solver  = IssueSolver()
        self._rules   = RuleEngine()
        self._critic  = PatchCritic()
        self._matcher = OperatorPatternMatcher()
        self._run_sandbox_default = run_sandbox_by_default

    # ------------------------------------------------------------------
    # Part J: public interface methods
    # ------------------------------------------------------------------

    def inspect_issue(self, inp: SolveTimeInput) -> SolveTimeResult:
        """
        Full solve-time diagnostic for any user-fed input.
        Coordinates all subsystems and returns a three-truth SolveTimeResult.
        """
        run_sandbox = inp.run_sandbox and self._run_sandbox_default

        # Archetype detection
        archetype = detect_archetype(
            template_name=inp.template_name,
            snippet=inp.primary_text,
            context=inp.context,
            article_title=inp.article_title,
        )

        # Merge tags with archetype-derived domain tags
        tags = list(inp.tags) or _tags_from_archetype(archetype.archetype)

        # Family detection
        family_id = assign_family(inp.template_name) or assign_family(inp.primary_text) or "unknown"

        # Rule truth
        rule_truth = self._build_rule_truth(inp.primary_text, archetype, tags)

        # Mechanical truth
        mechanical_truth = self._build_mechanical_truth(
            inp.primary_text, inp.template_name, family_id, run_sandbox=run_sandbox
        )

        # Operator truth
        operator_truth = self._build_operator_truth(inp.primary_text)

        # Patch critique if before/after provided
        critique: CritiqueResult | None = None
        patch_risk_class: PatchRiskClass | None = None
        if inp.before and inp.after:
            critique = self._critic.critique(
                before=inp.before,
                after=inp.after,
                context=inp.context,
                tags=tags,
                template_name=inp.template_name,
                run_sandbox=run_sandbox,
            )
            patch_risk_class = critique.patch_class

        # Issue type classification
        issue_type = self._classify_issue_type(inp, archetype, rule_truth)

        # Recommended action
        recommended_action = self._recommend_action(
            inp, rule_truth, mechanical_truth, operator_truth, critique, patch_risk_class
        )

        # Validation advice
        validation_advice = self._validation_advice(inp, run_sandbox, mechanical_truth, critique)

        # Input summary for display
        input_summary = _summarise_input(inp)

        return SolveTimeResult(
            input_summary=input_summary,
            rule_truth=rule_truth,
            mechanical_truth=mechanical_truth,
            operator_truth=operator_truth,
            template_family=family_id,
            article_archetype=archetype,
            issue_type=issue_type,
            recommended_action=recommended_action,
            patch_risk_class=patch_risk_class,
            validation_advice=validation_advice,
            critique=critique,
        )

    def explain_template_behavior(
        self,
        template_or_snippet: str,
        template_name: str = "",
        run_sandbox: bool = True,
    ) -> str:
        """
        Parser-backed explanation distinguishing:
          - source shape (structural analysis)
          - expanded behavior (action=expandtemplates)
          - rendered behavior (action=parse, if snippet is a full template call)
        """
        inp = SolveTimeInput(
            snippet=template_or_snippet,
            template_name=template_name,
            run_sandbox=run_sandbox,
        )
        # Use existing IssueSolver explanation (already sandbox-backed)
        explanation = self._solver.explain_template_logic(
            template_or_snippet,
            use_sandbox=run_sandbox,
        )
        # Add family + archetype context
        family_id = assign_family(template_name) or assign_family(template_or_snippet) or "unknown"
        archetype = detect_archetype(
            template_name=template_name,
            snippet=template_or_snippet,
        )
        header = (
            f"[Template family: {family_id}]  "
            f"[Archetype context: {archetype.archetype}  {archetype.confidence} confidence]\n"
        )
        return header + explanation

    def classify_patch_risk(
        self,
        before: str,
        after: str,
        context: str = "",
        template_name: str = "",
        tags: list[str] | None = None,
        run_sandbox: bool = True,
    ) -> CritiqueResult:
        """
        Classify patch risk using anti-pattern + rule + sandbox (optional).
        Returns a full CritiqueResult with patch_class and dossier notes.
        """
        archetype = detect_archetype(snippet=before + after, context=context)
        effective_tags = tags or _tags_from_archetype(archetype.archetype)
        return self._critic.critique(
            before=before,
            after=after,
            context=context,
            tags=effective_tags,
            template_name=template_name,
            run_sandbox=run_sandbox,
        )

    def find_related_family(self, template_or_snippet: str) -> dict:
        """
        Return template family info for a template name or snippet.

        Returns:
            {
                "family_id": str,
                "policy_codes": list[str],
                "fragile_params": list[str],  (from static extractor knowledge)
            }
        """
        family_id = assign_family(template_or_snippet) or "unknown"
        policy_codes = FAMILY_POLICIES.get(family_id, [])

        # Pull fragile params from Phase 1.3 family meta (via ingestor static data)
        fragile: list[str] = []
        try:
            from domains.language.tools.language_pipeline.template_families.ingestor import _FRAGILE_PARAMS
            fragile = _FRAGILE_PARAMS.get(family_id, [])
        except ImportError:
            pass

        return {
            "family_id": family_id,
            "policy_codes": policy_codes,
            "fragile_params": fragile,
        }

    def resolve_rule_priority(
        self,
        context: str,
        archetype_hint: str = "",
        tags: list[str] | None = None,
    ) -> RuleTruth:
        """
        Resolve rule precedence for a context, optionally anchored to an archetype.
        Produces a RuleTruth with primary policy identified.
        """
        archetype = detect_archetype(context=context)
        if archetype_hint:
            # Override with explicit hint
            from domains.language.tools.language_pipeline.solve_time.archetype_detector import _make_result
            archetype = _make_result(archetype_hint, "high", "explicit", [archetype_hint])

        effective_tags = tags or _tags_from_archetype(archetype.archetype)
        return self._build_rule_truth(context, archetype, effective_tags)

    def suggest_safe_rewrite(self, inp: SolveTimeInput) -> list[PatchProposal]:
        """
        Suggest safe rewrites for a snippet, filtered through:
        - Pattern library matches
        - Patch critic (each proposal is evaluated)
        - Operator pattern matcher (surfaces additional options)
        """
        text = inp.primary_text
        proposals = self._solver.suggest_safe_rewrite(text)

        # Add operator-pattern-backed notes to each proposal
        pm_result = self._matcher.match(text)
        for proposal in proposals:
            if pm_result.mined_matches:
                top_mine = pm_result.mined_matches[0]
                proposal.risk_notes += (
                    f" | Operator history: '{top_mine.name}' cluster "
                    f"({top_mine.evidence_count} edits, {top_mine.confidence})"
                )

        return proposals

    def compare_behavior(
        self,
        before: str,
        after: str,
        context: str = "",
        template_name: str = "",
        run_sandbox: bool = True,
    ) -> CritiqueResult:
        """
        Compare before/after behavior using sandbox + rule + anti-pattern checks.
        Wraps classify_patch_risk with a result that includes sandbox diff.
        """
        return self.classify_patch_risk(
            before=before,
            after=after,
            context=context,
            template_name=template_name,
            run_sandbox=run_sandbox,
        )

    def find_operator_style_matches(self, inp: SolveTimeInput) -> PatternMatchResult:
        """
        Find patterns from both the static library and mined operator history
        that match the input. Returns both sources separately.
        """
        return self._matcher.match(inp.primary_text)

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_rule_truth(
        self,
        text: str,
        archetype: ArchetypeResult,
        tags: list[str],
    ) -> RuleTruth:
        rule_check = self._rules.check(text, tags=tags)

        # Primary policy = first in archetype priority list that is also applicable,
        # else first in archetype priority list, else first applicable
        archetype_priority = archetype.policy_priority
        applicable_codes   = list({r.policy_code for r in rule_check.applicable_rules})
        ordered_applicable = [p for p in archetype_priority if p in applicable_codes]
        ordered_applicable += [p for p in applicable_codes if p not in ordered_applicable]

        primary_policy = (
            archetype_priority[0] if archetype_priority else (
                applicable_codes[0] if applicable_codes else "MOS"
            )
        )

        conflict_descs = [
            f"{c.rule_a.policy_code} vs {c.rule_b.policy_code}"
            for c in rule_check.conflicts
        ]

        return RuleTruth(
            primary_policy=primary_policy,
            all_applicable=ordered_applicable or archetype_priority[:3],
            hard_blocks=[r.name for r in rule_check.hard_blocks],
            soft_concerns=[r.name for r in rule_check.soft_concerns],
            advisories=[r.name for r in rule_check.advisories],
            conflicts=conflict_descs,
            verdict=rule_check.verdict,
            raw=rule_check,
        )

    def _build_mechanical_truth(
        self,
        text: str,
        template_name: str,
        family_id: str,
        run_sandbox: bool = True,
    ) -> MechanicalTruth:
        # Source shape (structural / regex-based)
        source_shape = self._solver._structural_explanation(text)

        # Anti-pattern scan
        aps = find_anti_patterns(text)
        ap_names = [ap.name for ap in aps]

        # Fragility notes from family
        fragility_notes: list[str] = []
        try:
            from domains.language.tools.language_pipeline.template_families.ingestor import (
                _FRAGILE_PARAMS, _FAMILY_META,
            )
            for param in _FRAGILE_PARAMS.get(family_id, []):
                if param in text:
                    meta = _FAMILY_META.get(family_id, {})
                    for bp in meta.get("breakage_patterns", []):
                        if param in bp.get("id", ""):
                            fragility_notes.append(f"{param}: {bp['description'][:80]}")
                            break
                    else:
                        fragility_notes.append(f"Fragile param present: |{param}=")
        except ImportError:
            pass

        # Alias detection (bare alternatives in snippet)
        alias_params: list[str] = []
        import re as _re
        aliases_found = _re.findall(r"\|\s*(\w+)\s*=", text)
        alias_params = list(dict.fromkeys(aliases_found))[:10]

        # Branch summary
        branch_parts: list[str] = []
        if "{{#if:" in text:
            branch_parts.append("#if conditional")
        if "{{#ifeq:" in text:
            branch_parts.append("#ifeq equality test")
        if "{{#switch:" in text:
            branch_parts.append("#switch multi-branch")
        if "{{#ifexpr:" in text:
            branch_parts.append("#ifexpr numeric expression")
        branch_summary = ", ".join(branch_parts) or "no parser-function branches"

        # Sandbox expand
        expanded_behavior = ""
        sandbox_ok = True
        if run_sandbox and text.strip():
            try:
                from domains.language.tools.language_pipeline.sandbox import SandboxValidator
                sb = SandboxValidator()
                result = sb.expand(text, "Sandbox")
                if result.success:
                    expanded_behavior = (result.expanded_wikitext or "").strip()[:200]
                else:
                    sandbox_ok = False
                    expanded_behavior = f"Sandbox error: {', '.join(result.errors[:2])}"
            except Exception as e:
                sandbox_ok = False
                expanded_behavior = f"Sandbox unavailable: {e}"

        return MechanicalTruth(
            source_shape=source_shape,
            expanded_behavior=expanded_behavior,
            rendered_behavior="",   # parse (heavier) is opt-in via explain_template_behavior
            anti_pattern_names=ap_names,
            fragility_notes=fragility_notes,
            alias_params=alias_params,
            branch_summary=branch_summary,
            sandbox_ok=sandbox_ok,
        )

    def _build_operator_truth(self, text: str) -> OperatorTruth:
        pm_result = self._matcher.match(text)
        lib_names  = [m.pattern.name for m in pm_result.library_matches]
        mine_names = [m.name for m in pm_result.mined_matches]

        # Leave-alone check
        leave_alone = self._matcher.leave_alone_candidates()
        compat_warning = ""
        # Only flag if an article title appears literally in the text
        for page in leave_alone[:20]:
            if page.lower() in text.lower() and len(page) > 5:
                compat_warning = (
                    f"'{page}' has revert evidence in operator history — "
                    "consider leaving current state unless issue is clear."
                )
                break

        # Style notes from top mined patterns
        style_notes: list[str] = []
        for mine_match in pm_result.mined_matches[:3]:
            if mine_match.likely_purpose:
                style_notes.append(
                    f"[{mine_match.cluster}] {mine_match.likely_purpose} "
                    f"({mine_match.evidence_count} edits)"
                )

        return OperatorTruth(
            library_pattern_matches=lib_names,
            mined_pattern_matches=mine_names,
            top_recommendation=pm_result.top_recommendation,
            compatibility_warning=compat_warning,
            operator_style_notes=style_notes,
        )

    # ------------------------------------------------------------------
    # Internal classifiers / advisors
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_issue_type(
        inp: SolveTimeInput,
        archetype: ArchetypeResult,
        rule_truth: RuleTruth,
    ) -> str:
        has_patch   = bool(inp.before and inp.after)
        has_snippet = bool(inp.snippet)
        has_tmpl    = bool(inp.template_name)

        if has_patch:
            return "patch"
        if rule_truth.verdict in ("blocked", "concerns"):
            return "policy"
        if has_tmpl and not has_snippet:
            return "template_logic"
        if has_snippet:
            return "template_logic"
        if inp.context:
            return "style"
        return "unknown"

    @staticmethod
    def _recommend_action(
        inp: SolveTimeInput,
        rule_truth: RuleTruth,
        mechanical_truth: MechanicalTruth,
        operator_truth: OperatorTruth,
        critique: CritiqueResult | None,
        patch_risk_class: PatchRiskClass | None,
    ) -> str:
        if patch_risk_class == "risky":
            return "Do not apply patch without sandbox validation and rule review."
        if patch_risk_class == "insufficient-confidence":
            return "Insufficient confidence — manual review required."
        if rule_truth.hard_blocks:
            return f"Resolve rule hard blocks first: {rule_truth.hard_blocks[0]}"
        if mechanical_truth.anti_pattern_names:
            return (
                f"Address anti-pattern(s): {', '.join(mechanical_truth.anti_pattern_names[:2])}. "
                "Check fragility notes before rewriting."
            )
        if operator_truth.top_recommendation:
            return operator_truth.top_recommendation
        if patch_risk_class == "review-preferred":
            return "Verify rendered output in sandbox before applying."
        if patch_risk_class == "safe":
            return "Safe to apply. Sandbox validation still recommended for template namespace edits."
        if rule_truth.soft_concerns:
            return f"Soft concern from {rule_truth.primary_policy} — review before proceeding."
        return "No immediate action required. Review source shape notes."

    @staticmethod
    def _validation_advice(
        inp: SolveTimeInput,
        run_sandbox: bool,
        mechanical_truth: MechanicalTruth,
        critique: CritiqueResult | None,
    ) -> str:
        if inp.before and inp.after:
            if run_sandbox:
                return (
                    "Sandbox comparison was run — review critic output. "
                    "Run python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'"
                )
            else:
                return (
                    "Sandbox not run — run: "
                    "python domains/language/model/tools/wiki/wiki_tool.py validate '<after_text>'"
                )
        if inp.template_name:
            return (
                f"Inspect live template: "
                f"python domains/language/model/tools/wiki/wiki_tool.py inspect '{inp.template_name}'"
            )
        if inp.snippet:
            return (
                "Validate snippet: "
                "python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'"
            )
        return "No specific validation path identified — provide snippet or before/after patch."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tags_from_archetype(archetype_name: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "athlete_biography_nfl": ["nfl", "blp"],
        "nfl_front_office":      ["nfl", "blp"],
        "executive_biography":   ["blp"],
        "video_game_article":    ["vg"],
        "infrastructure_article": ["nfl"],
        "unknown":               [],
    }
    return mapping.get(archetype_name, [])


def _summarise_input(inp: SolveTimeInput) -> str:
    parts: list[str] = []
    if inp.template_name:
        parts.append(f"template='{inp.template_name}'")
    if inp.article_title:
        parts.append(f"article='{inp.article_title}'")
    if inp.snippet:
        parts.append(f"snippet={repr(inp.snippet[:60])}")
    if inp.before:
        parts.append(f"patch (before={len(inp.before)}ch, after={len(inp.after)}ch)")
    if inp.context:
        parts.append(f"context={repr(inp.context[:60])}")
    return ", ".join(parts) or "(no input)"

