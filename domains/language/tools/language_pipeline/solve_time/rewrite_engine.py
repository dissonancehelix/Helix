"""
Family-aware rewrite engine — Phase 1.5.

Upgrades rewrite suggestion and patch proposal to use template family context.

Key departure from Phase 1.4:
  - suggest_safe_rewrite / propose_patch in IssueSolver match patterns by keyword
    and run PatchCritic, but they are family-blind.
  - This engine filters, demotes, and blocks patterns based on whether they are
    compatible with the detected template family.

Three-truth discipline is maintained:
  rule_truth    — policies still applied per archetype priority
  mech_truth    — fragile params, alias behavior, branch logic still checked
  op_truth      — operator patterns are used as ranked hints AFTER safety gates

Core model:
  1. Detect family (from Phase 1.3 extractor)
  2. Filter candidate patterns by family compatibility (_FAMILY_PATTERN_COMPAT)
  3. Block patterns that touch known fragile params incorrectly for this family
  4. Rank remaining options: family_safety > mech_safety > policy_fit > op_style > readability
  5. Attach family-specific validation advice to each proposal

Advisory-only. No live Wikipedia edits under any code path.
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Literal

from domains.language.tools.language_pipeline.pattern_library import PATTERN_LIBRARY, WikiPattern
from domains.language.tools.language_pipeline.anti_patterns import find_anti_patterns
from domains.language.tools.language_pipeline.patch_critic import PatchCritic, CritiqueResult
from domains.language.tools.language_pipeline.rule_engine import RuleEngine
from domains.language.tools.language_pipeline.template_families.extractor import (
    assign_family, FAMILY_POLICIES,
)
from domains.language.tools.language_pipeline.solve_time.archetype_detector import (
    detect_archetype, ARCHETYPE_POLICY_PRIORITY,
)
from domains.language.tools.language_pipeline.solve_time.operator_pattern_matcher import (
    OperatorPatternMatcher,
)

FamilyCompat = Literal["allow", "demote", "block"]
FamilyPatchClass = Literal["family-safe", "family-review", "family-risky", "insufficient-confidence"]

# ---------------------------------------------------------------------------
# Family compatibility table
#
# Maps each pattern_id → {family_id → FamilyCompat}.
# "allow"  — pattern is family-appropriate; recommend normally.
# "demote" — pattern may work but carries elevated family-specific risk; note clearly.
# "block"  — pattern conflicts with known fragile family behavior; must not suggest.
#
# Reasoning notes are in _FAMILY_PATTERN_REASONS below.
# ---------------------------------------------------------------------------

_FAMILY_PATTERN_COMPAT: dict[str, dict[str, FamilyCompat]] = {

    "if_empty_guard": {
        # Universal fix — always safe, especially for families with many optional params.
        "nfl_biography":  "allow",
        "vg_infobox":     "allow",
        "executive_bio":  "allow",
        "venue_project":  "allow",
    },

    "fallback_chain": {
        # NFL infobox has many renamed/deprecated params still in active transclusion.
        # Adding fallback chains is the correct compatibility move.
        "nfl_biography":  "allow",
        # VG infobox params tend to be stable; legacy fallback adds confusion.
        "vg_infobox":     "demote",
        # executive_bio params renamed occasionally; fallback is reasonable.
        "executive_bio":  "allow",
        # Venue/project infoboxes rarely have renamed params in active use.
        "venue_project":  "demote",
    },

    "ifeq_switch_collapse": {
        # NFL infoboxes use ifeq chains in ways that must be sandbox-tested
        # before collapsing — branch semantics may differ for numeric or
        # whitespace-padded values.
        "nfl_biography":  "demote",
        "vg_infobox":     "allow",
        "executive_bio":  "allow",
        "venue_project":  "allow",
    },

    "switch_default_required": {
        # Adding explicit #default is universally safe.
        "nfl_biography":  "allow",
        "vg_infobox":     "allow",
        "executive_bio":  "allow",
        "venue_project":  "allow",
    },

    "infobox_label_data_cleanup": {
        # Whitespace normalization — safe everywhere, but can interact with
        # infobox row rendering if label/data alignment was intentional.
        "nfl_biography":  "allow",
        "vg_infobox":     "allow",
        "executive_bio":  "allow",
        "venue_project":  "allow",
    },

    "infobox_blank_row_suppress": {
        # Critical for NFL player infoboxes — draft/career rows must suppress
        # cleanly when params are absent. This is the correct pattern.
        "nfl_biography":  "allow",
        # VG infobox already handles blank-row suppression internally via its
        # template logic. Wrapping in an additional #if can break that coupling.
        "vg_infobox":     "demote",
        # executive_bio infoboxes (|alma_mater=, |net_worth=) benefit from this.
        "executive_bio":  "allow",
        "venue_project":  "allow",
    },

    "pluralization_ifexpr": {
        # NFL stats use numeric counts — year counts, game counts, etc.
        "nfl_biography":  "allow",
        # VG articles don't typically need numeric pluralization in infobox.
        "vg_infobox":     "demote",
        # executive_bio rarely has numeric plural contexts.
        "executive_bio":  "demote",
        # Venue templates may use capacity numbers.
        "venue_project":  "allow",
    },

    "deprecated_param_alias": {
        # NFL infobox has many renamed/deprecated params that old transclusions
        # still use. This is the RIGHT pattern for this family.
        "nfl_biography":  "allow",
        # VG infobox has occasional deprecated params (|engine= removal history).
        "vg_infobox":     "allow",
        # executive_bio similarly.
        "executive_bio":  "allow",
        # Venue templates have fewer legacy transclusions — demote but allow.
        "venue_project":  "demote",
    },

    "ref_consolidation": {
        # Citation cleanup is always safe across families.
        "nfl_biography":  "allow",
        "vg_infobox":     "allow",
        "executive_bio":  "allow",
        "venue_project":  "allow",
    },

    "nowiki_template_display": {
        # This pattern is for /doc pages and talk-page examples, not live infoboxes.
        # Applying it to a live template is almost always wrong.
        "nfl_biography":  "block",
        "vg_infobox":     "block",
        "executive_bio":  "block",
        "venue_project":  "block",
    },
}

# Reasons explaining each demote/block decision.
# Shown in FamilyPatchProposal.family_reasoning when the option is not "allow".
_FAMILY_PATTERN_REASONS: dict[str, dict[str, str]] = {
    "fallback_chain": {
        "vg_infobox": (
            "VG infobox params (|image=, |released=, |platforms=) tend to be stable. "
            "Adding a fallback chain for a non-existent legacy param adds noise without "
            "benefit. Verify that old transclusions actually use the legacy name before adding."
        ),
        "venue_project": (
            "Venue/project infoboxes rarely have renamed params in active transclusion. "
            "Confirm there is actual evidence of legacy param use before adding a fallback."
        ),
    },
    "ifeq_switch_collapse": {
        "nfl_biography": (
            "NFL player infobox ifeq chains sometimes test for numeric equality or whitespace "
            "variants that behave differently under #switch (which is exact string match). "
            "Sandbox both forms before collapsing. The before/after output must be identical "
            "across all known transclusion patterns (empty, numeric, whitespace-padded)."
        ),
    },
    "infobox_blank_row_suppress": {
        "vg_infobox": (
            "{{Infobox video game}} handles row suppression internally. "
            "Adding an outer #if wrapper over the |data= field can break the template's "
            "own suppression logic, causing double-blank or rendering differences. "
            "Test both with and without the wrapper before applying."
        ),
    },
    "pluralization_ifexpr": {
        "vg_infobox":    "VG infoboxes do not typically require numeric pluralization.",
        "executive_bio": "executive_bio articles rarely have numeric plural contexts in infobox.",
    },
    "deprecated_param_alias": {
        "venue_project": (
            "Venue templates have fewer active legacy transclusions than NFL player infoboxes. "
            "Check transclusion count before adding deprecated param aliases — low-traffic "
            "templates may not need them."
        ),
    },
    "nowiki_template_display": {
        "nfl_biography":  "nowiki wrapping is for /doc and talk pages — not live infoboxes.",
        "vg_infobox":     "nowiki wrapping is for /doc and talk pages — not live infoboxes.",
        "executive_bio":  "nowiki wrapping is for /doc and talk pages — not live infoboxes.",
        "venue_project":  "nowiki wrapping is for /doc and talk pages — not live infoboxes.",
    },
}

# ---------------------------------------------------------------------------
# Family-specific fragile-param rules for rewrite filtering.
#
# If a candidate rewrite REMOVES or SIMPLIFIES a param that is in this set,
# the engine flags it as a family-safety concern.
# ---------------------------------------------------------------------------

_FRAGILE_PARAMS: dict[str, list[str]] = {
    "nfl_biography":  ["teams", "birth_date", "draft_round", "draft_pick", "number", "position"],
    "vg_infobox":     ["image", "released", "platforms", "genre", "developer", "publisher"],
    "executive_bio":  ["birth_date", "birth_place", "death_date", "alma_mater", "net_worth"],
    "venue_project":  ["capacity", "coordinates", "opened", "surface", "tenants"],
}

# Behaviors that must be preserved per family (surfaced in proposal output).
_PRESERVED_BEHAVIOR_NOTES: dict[str, list[str]] = {
    "nfl_biography": [
        "{{NFL team}} wrapper in |teams= must be preserved",
        "{{birth date and age|YYYY|MM|DD}} pipe format in |birth_date= must be preserved",
        "Draft row blank-suppression logic must remain intact",
        "Deprecated param aliases (legacy NFL infobox param names) must be preserved",
    ],
    "vg_infobox": [
        "No File: prefix in |image= (template adds it internally)",
        "{{Video game release}} wrapper in |released= must be preserved",
        "{{unbulleted list}} wrapper in |platforms= must be preserved",
        "Genre values must remain from MOS:VG canonical list",
    ],
    "executive_bio": [
        "{{birth date and age|YYYY|MM|DD}} with pipe separator (not hyphens)",
        "No unsourced claims about living person — BLP applies",
        "{{short description}} ≤40 chars, no leading article word",
    ],
    "venue_project": [
        "{{formatnum:}} wrapper on large capacity numbers",
        "{{coord}} in correct format (decimal or DMS, not mixed)",
        "{{start date}} wrapper on |opened= if present",
    ],
}

# Family-specific validation steps (concrete, not generic "run sandbox").
_FAMILY_VALIDATION_STEPS: dict[str, list[str]] = {
    "nfl_biography": [
        "Test |teams= with {{NFL team|Washington Commanders}} vs bare city name → confirm rendering",
        "Test |birth_date= with {{birth date and age|YYYY|MM|DD}} vs bare date → confirm age shown",
        "Test empty |draft_round= / |draft_pick= → confirm no blank infobox row appears",
        "Test |number= with single value and comma-separated multi-value",
        "Run: python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'  (with --tags nfl blp)",
        "Verify WP:BLP: no unsourced contract, salary, or injury claim in result",
    ],
    "vg_infobox": [
        "Test |image= without File: prefix → confirm image renders correctly",
        "Test |released= with {{Video game release|NA|YYYY-MM-DD}} → confirm regional metadata",
        "Test |platforms= as {{unbulleted list|...}} vs comma-separated → confirm layout",
        "Test |genre= against MOS:VG canonical list (action-adventure, role-playing, etc.)",
        "Run: python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'",
    ],
    "executive_bio": [
        "Test {{birth date and age|YYYY|MM|DD}} with pipe separator — NOT {{birth date and age|YYYY-MM-DD}}",
        "Test {{short description|...}} length ≤40 chars, does not start with A/An/The",
        "Verify all claims about the living subject have inline citations",
        "Run: python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'  (with --tags blp)",
    ],
    "venue_project": [
        "Test |capacity= with {{formatnum:75000}} vs bare 75000",
        "Test |coordinates= with decimal degrees vs DMS — confirm geo-tag renders",
        "Test |opened= with {{start date|YYYY|MM|DD}} wrapper",
        "Run: python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'",
    ],
    "unknown": [
        "Identify template family first: python domains/language/model/tools/wiki/wiki_tool.py find-family '<template>'",
        "Run: python domains/language/model/tools/wiki/wiki_tool.py solve '<snippet>'",
        "Run: python domains/language/model/tools/wiki/wiki_tool.py validate '<snippet>'",
    ],
}

# ---------------------------------------------------------------------------
# Output data classes
# ---------------------------------------------------------------------------

@dataclass
class FamilyRewriteOption:
    """
    A single ranked rewrite option with full family-aware context.
    Used inside FamilyPatchProposal and also returned by rank_rewrite_options().
    """
    pattern_id: str
    pattern_name: str
    family_id: str
    family_compat: FamilyCompat          # allow / demote / block
    family_reasoning: str                # why this compat rating was assigned
    preserved_behaviors: list[str]       # family behaviors this option explicitly preserves
    before: str
    after: str
    patch_class: FamilyPatchClass        # family-aware risk class
    rule_concerns: list[str]             # rule names that fire against this option
    operator_overlap: str                # operator pattern match summary
    validation_steps: list[str]          # concrete family-specific steps
    rank_score: int                      # higher = better (see _score_option())
    notes: list[str]                     # extra notes from critic / fragility scan

    def display(self) -> str:
        lines = [
            f"[{self.family_compat.upper():6s}] [{self.patch_class.upper()}] {self.pattern_name}",
            f"  Family: {self.family_id}  Score: {self.rank_score}",
            f"  Reasoning: {self.family_reasoning}" if self.family_compat != "allow" else "",
            "",
            "  BEFORE:",
            textwrap.indent(self.before, "    "),
            "  AFTER:",
            textwrap.indent(self.after, "    "),
            "",
        ]
        if self.preserved_behaviors:
            lines.append("  Preserved behaviors:")
            for pb in self.preserved_behaviors:
                lines.append(f"    ✓ {pb}")
        if self.rule_concerns:
            lines.append(f"  Rule concerns: {', '.join(self.rule_concerns)}")
        if self.operator_overlap:
            lines.append(f"  Operator overlap: {self.operator_overlap}")
        lines.append("  Validation:")
        for step in self.validation_steps[:4]:
            lines.append(f"    · {step}")
        for note in self.notes:
            lines.append(f"  Note: {note}")
        return "\n".join(l for l in lines if l != "")


@dataclass
class FamilyPatchProposal:
    """
    Top-level family-aware patch proposal.
    Produced by propose_family_patch() and suggest_family_safe_rewrite().

    Explicitly distinguishes:
      - why this rewrite is appropriate for the detected family
      - what family-specific behaviors are preserved
      - what family-specific risks remain
      - what concrete validation steps to take
    """
    issue_summary: str
    family_id: str
    archetype: str
    relevant_policies: list[str]

    # The selected top option
    top_option: FamilyRewriteOption | None
    # All ranked options (including demoted/blocked, with reasons)
    all_options: list[FamilyRewriteOption]

    # Cross-cutting summary
    family_safe_count: int               # options rated "allow"
    family_demoted_count: int            # options rated "demote"
    family_blocked_count: int            # options rated "block"

    preserved_behaviors: list[str]       # from top option or family defaults
    family_risks_remaining: list[str]    # risks that cannot be resolved by any option
    validation_advice: list[str]         # family-specific steps

    # Operator style
    operator_style_note: str

    def display(self) -> str:
        lines = [
            "=" * 60,
            "FAMILY-AWARE PATCH PROPOSAL",
            "=" * 60,
            f"Issue:    {self.issue_summary}",
            f"Family:   {self.family_id}",
            f"Archetype:{self.archetype}",
            f"Policies: {' > '.join(self.relevant_policies[:4])}",
            f"Options:  {self.family_safe_count} safe, "
            f"{self.family_demoted_count} demoted, "
            f"{self.family_blocked_count} blocked",
            "",
        ]
        if self.top_option:
            lines.append("── TOP RECOMMENDATION ──")
            lines.append(self.top_option.display())
        else:
            lines.append("No family-safe option found. Manual review required.")
        if self.preserved_behaviors:
            lines.append("── PRESERVED BEHAVIORS ──")
            for pb in self.preserved_behaviors:
                lines.append(f"  ✓ {pb}")
        if self.family_risks_remaining:
            lines.append("── REMAINING FAMILY RISKS ──")
            for r in self.family_risks_remaining:
                lines.append(f"  ! {r}")
        if self.validation_advice:
            lines.append("── VALIDATION STEPS ──")
            for step in self.validation_advice:
                lines.append(f"  · {step}")
        if self.operator_style_note:
            lines.append(f"Operator style: {self.operator_style_note}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "issue_summary":         self.issue_summary,
            "family_id":             self.family_id,
            "archetype":             self.archetype,
            "relevant_policies":     self.relevant_policies,
            "family_safe_count":     self.family_safe_count,
            "family_demoted_count":  self.family_demoted_count,
            "family_blocked_count":  self.family_blocked_count,
            "preserved_behaviors":   self.preserved_behaviors,
            "family_risks_remaining": self.family_risks_remaining,
            "validation_advice":     self.validation_advice,
            "operator_style_note":   self.operator_style_note,
            "top_option": self.top_option.display() if self.top_option else None,
            "all_options": [
                {
                    "pattern_id":    o.pattern_id,
                    "family_compat": o.family_compat,
                    "patch_class":   o.patch_class,
                    "rank_score":    o.rank_score,
                    "pattern_name":  o.pattern_name,
                }
                for o in self.all_options
            ],
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class FamilyAwareRewriteEngine:
    """
    Phase 1.5 rewrite engine.

    Takes SolveTimeInput (with family + archetype already available) and produces
    family-filtered, ranked patch proposals.

    Does NOT replace IssueSolver — it wraps and augments it with family context.
    Advisory-only. No live Wikipedia edits.
    """

    def __init__(self):
        self._critic  = PatchCritic()
        self._rules   = RuleEngine()
        self._matcher = OperatorPatternMatcher()

    # ------------------------------------------------------------------
    # Part I: public interface
    # ------------------------------------------------------------------

    def suggest_family_safe_rewrite(
        self,
        snippet: str,
        family_id: str = "",
        archetype: str = "",
        context: str = "",
        tags: list[str] | None = None,
    ) -> FamilyPatchProposal:
        """
        Suggest rewrites filtered and ranked by template family.

        This is the primary replacement for the generic suggest_safe_rewrite().
        """
        family_id  = family_id  or assign_family(snippet) or "unknown"
        archetype  = archetype  or detect_archetype(snippet=snippet).archetype
        policies   = FAMILY_POLICIES.get(family_id, []) or ARCHETYPE_POLICY_PRIORITY.get(archetype, [])
        tags_used  = tags or _tags_for_family(family_id, archetype)

        options = self.rank_rewrite_options(
            snippet=snippet,
            family_id=family_id,
            archetype=archetype,
            context=context,
            tags=tags_used,
        )

        return self._build_proposal(
            issue_summary=f"Rewrite suggestion for: {repr(snippet[:60])}",
            family_id=family_id,
            archetype=archetype,
            policies=policies,
            options=options,
            snippet=snippet,
        )

    def propose_family_patch(
        self,
        issue_description: str,
        snippet: str = "",
        template_name: str = "",
        family_id: str = "",
        archetype: str = "",
        tags: list[str] | None = None,
    ) -> FamilyPatchProposal:
        """
        Propose a patch for a described issue with full family-aware reasoning.

        Upgrade of IssueSolver.propose_patch() that filters by family compatibility.
        """
        text       = snippet or issue_description
        family_id  = family_id  or assign_family(template_name) or assign_family(text) or "unknown"
        archetype  = archetype  or detect_archetype(
            template_name=template_name,
            snippet=text,
            context=issue_description,
        ).archetype
        policies   = FAMILY_POLICIES.get(family_id, []) or ARCHETYPE_POLICY_PRIORITY.get(archetype, [])
        tags_used  = tags or _tags_for_family(family_id, archetype)

        options = self.rank_rewrite_options(
            snippet=text,
            family_id=family_id,
            archetype=archetype,
            context=issue_description,
            tags=tags_used,
        )

        return self._build_proposal(
            issue_summary=issue_description or repr(text[:60]),
            family_id=family_id,
            archetype=archetype,
            policies=policies,
            options=options,
            snippet=snippet,
        )

    def rank_rewrite_options(
        self,
        snippet: str,
        family_id: str = "",
        archetype: str = "",
        context: str = "",
        tags: list[str] | None = None,
        candidates: list[WikiPattern] | None = None,
    ) -> list[FamilyRewriteOption]:
        """
        Score and rank all candidate patterns against the family and archetype.

        Returns all options (including demoted/blocked) in descending score order.
        Blocked options have score 0 and appear last.
        """
        family_id = family_id or assign_family(snippet) or "unknown"
        archetype = archetype or detect_archetype(snippet=snippet, context=context).archetype
        tags_used = tags or _tags_for_family(family_id, archetype)
        patterns  = candidates or PATTERN_LIBRARY

        # Pre-compute operator match for snippet (used in scoring)
        pm_result  = self._matcher.match(snippet)
        lib_ids    = {m.pattern.id for m in pm_result.library_matches}
        mine_names = {m.name for m in pm_result.mined_matches}

        options: list[FamilyRewriteOption] = []
        for pattern in patterns:
            if not pattern.matches(snippet):
                # Still include but with score=0 if compat is allow/demote
                # (needed for explain_rewrite_choice to show full picture)
                compat = _get_compat(pattern.id, family_id)
                if compat == "block":
                    continue  # never include blocked patterns regardless

            compat    = _get_compat(pattern.id, family_id)
            reason    = _get_reason(pattern.id, family_id, compat)

            # Rule check for the after-text
            rule_check = self._rules.check(
                f"{context} {pattern.after}",
                tags=tags_used,
            )
            rule_concerns = [r.name for r in rule_check.hard_blocks + rule_check.soft_concerns]

            # Fragile-param check
            fragile_hit = _check_fragile_params(snippet, pattern.after, family_id)

            # Operator overlap
            op_overlap = ""
            if pattern.id in lib_ids:
                op_overlap = f"matches library pattern '{pattern.name}'"
            elif any(n in mine_names for n in pattern.keywords[:3]):
                op_overlap = "overlaps with mined edit history"

            # Preserved behaviors
            preserved = _preserved_for_option(pattern, family_id)

            # Family patch class
            patch_class = _family_patch_class(
                compat, pattern.risk, bool(rule_check.hard_blocks), fragile_hit
            )

            # Score
            score = _score_option(compat, pattern.risk, rule_check, bool(op_overlap), fragile_hit)

            # Extra notes
            notes: list[str] = []
            if fragile_hit:
                notes.append(
                    f"Fragile param(s) touched: {', '.join(fragile_hit)} — verify behavior"
                )
            if rule_check.hard_blocks:
                notes.append(
                    f"Rule hard block: {rule_check.hard_blocks[0].name}"
                )

            options.append(FamilyRewriteOption(
                pattern_id=pattern.id,
                pattern_name=pattern.name,
                family_id=family_id,
                family_compat=compat,
                family_reasoning=reason,
                preserved_behaviors=preserved,
                before=pattern.before,
                after=pattern.after,
                patch_class=patch_class,
                rule_concerns=rule_concerns,
                operator_overlap=op_overlap,
                validation_steps=_FAMILY_VALIDATION_STEPS.get(family_id, _FAMILY_VALIDATION_STEPS["unknown"]),
                rank_score=score,
                notes=notes,
            ))

        options.sort(key=lambda o: -o.rank_score)
        return options

    def explain_rewrite_choice(
        self,
        chosen: FamilyRewriteOption,
        all_options: list[FamilyRewriteOption],
    ) -> str:
        """
        Produce a natural-language explanation of why the top option was chosen
        over alternatives (showing the ranked decision).
        """
        lines = [
            f"Rewrite choice explanation — {chosen.pattern_name}",
            f"Family: {chosen.family_id}  Compatibility: {chosen.family_compat}  "
            f"Score: {chosen.rank_score}",
            "",
        ]
        if chosen.family_reasoning and chosen.family_compat != "allow":
            lines.append(f"Family note: {chosen.family_reasoning}")

        if len(all_options) > 1:
            lines.append(f"Ranked against {len(all_options)} candidate option(s):")
            for opt in all_options[:5]:
                marker = "→ SELECTED" if opt.pattern_id == chosen.pattern_id else "  skipped"
                lines.append(
                    f"  {marker}  [{opt.family_compat.upper():6s}] "
                    f"[{opt.patch_class:22s}] score={opt.rank_score:2d}  {opt.pattern_name}"
                )

        lines.append("")
        if chosen.preserved_behaviors:
            lines.append("The selected rewrite preserves:")
            for pb in chosen.preserved_behaviors:
                lines.append(f"  ✓ {pb}")

        if chosen.rule_concerns:
            lines.append(f"Remaining rule concerns: {', '.join(chosen.rule_concerns)}")

        if chosen.notes:
            for n in chosen.notes:
                lines.append(f"Note: {n}")

        lines.append("")
        lines.append("The best patch may be slightly more verbose than alternatives")
        lines.append(
            "if that verbosity preserves family-specific legacy or fragile behavior."
        )
        return "\n".join(lines)

    def get_family_validation_advice(
        self,
        family_id: str = "",
        snippet: str = "",
        archetype: str = "",
    ) -> list[str]:
        """
        Return concrete family-specific validation steps.
        Falls back to unknown-family steps if family cannot be determined.
        """
        fid = family_id or assign_family(snippet) or "unknown"
        steps = list(_FAMILY_VALIDATION_STEPS.get(fid, _FAMILY_VALIDATION_STEPS["unknown"]))

        # Add archetype-specific BLP note if applicable
        arch = archetype or detect_archetype(snippet=snippet).archetype
        blp_archetypes = {
            "athlete_biography_nfl", "nfl_front_office", "executive_biography",
        }
        if arch in blp_archetypes and fid != "unknown":
            steps.append("BLP: verify all content about living person has inline citation (WP:BLP)")

        return steps

    def compare_family_safe_patches(
        self,
        snippet: str,
        candidates: list[str],
        family_id: str = "",
        context: str = "",
    ) -> list[FamilyRewriteOption]:
        """
        Compare multiple concrete after-text candidates (not patterns) against the family.
        Each string in candidates is a proposed rewrite of snippet.

        Returns ranked FamilyRewriteOption-like objects (using a synthetic pattern wrapper).
        """
        family_id = family_id or assign_family(snippet) or "unknown"
        archetype = detect_archetype(snippet=snippet, context=context).archetype
        tags      = _tags_for_family(family_id, archetype)

        options: list[FamilyRewriteOption] = []
        for i, candidate in enumerate(candidates):
            # Build a synthetic WikiPattern for this candidate
            synthetic = WikiPattern(
                id=f"candidate_{i}",
                name=f"Candidate {i + 1}",
                purpose=f"User-provided rewrite candidate {i + 1}",
                before=snippet,
                after=candidate,
                risk="review",
                risk_notes="User-provided candidate — risk unknown without pattern library context.",
                use_when="",
                avoid_when="",
                keywords=candidate.lower().split()[:5],
            )

            compat = _get_compat_from_text(snippet, candidate, family_id)
            reason = _get_reason_from_text(snippet, candidate, family_id, compat)

            rule_check   = self._rules.check(f"{context} {candidate}", tags=tags)
            fragile_hit  = _check_fragile_params(snippet, candidate, family_id)
            preserved    = _preserved_for_text(candidate, family_id)
            patch_class  = _family_patch_class(
                compat, "review", bool(rule_check.hard_blocks), fragile_hit
            )
            score = _score_option(compat, "review", rule_check, False, fragile_hit)

            notes: list[str] = []
            if fragile_hit:
                notes.append(f"Fragile param(s) touched: {', '.join(fragile_hit)}")

            options.append(FamilyRewriteOption(
                pattern_id=synthetic.id,
                pattern_name=synthetic.name,
                family_id=family_id,
                family_compat=compat,
                family_reasoning=reason,
                preserved_behaviors=preserved,
                before=snippet,
                after=candidate,
                patch_class=patch_class,
                rule_concerns=[r.name for r in rule_check.hard_blocks + rule_check.soft_concerns],
                operator_overlap="",
                validation_steps=_FAMILY_VALIDATION_STEPS.get(family_id, _FAMILY_VALIDATION_STEPS["unknown"]),
                rank_score=score,
                notes=notes,
            ))

        options.sort(key=lambda o: -o.rank_score)
        return options

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_proposal(
        self,
        issue_summary: str,
        family_id: str,
        archetype: str,
        policies: list[str],
        options: list[FamilyRewriteOption],
        snippet: str,
    ) -> FamilyPatchProposal:

        # Select top option (highest score among non-blocked)
        allowed_options = [o for o in options if o.family_compat != "block"]
        top_option = allowed_options[0] if allowed_options else None

        # Count by compat
        safe_count    = sum(1 for o in options if o.family_compat == "allow")
        demoted_count = sum(1 for o in options if o.family_compat == "demote")
        blocked_count = sum(1 for o in options if o.family_compat == "block")

        # Preserved behaviors
        preserved = (
            top_option.preserved_behaviors
            if top_option
            else _PRESERVED_BEHAVIOR_NOTES.get(family_id, [])
        )

        # Remaining family risks — fragile params still in snippet after rewrite
        fragile_remaining: list[str] = []
        after_text = top_option.after if top_option else snippet
        for param in _FRAGILE_PARAMS.get(family_id, []):
            if param in snippet and param in after_text:
                fragile_remaining.append(
                    f"|{param}= is a fragile param for {family_id} — verify format preserved"
                )

        # Validation advice
        validation = _FAMILY_VALIDATION_STEPS.get(family_id, _FAMILY_VALIDATION_STEPS["unknown"])

        # Operator style note
        pm_result = self._matcher.match(snippet)
        op_note = pm_result.top_recommendation or ""

        return FamilyPatchProposal(
            issue_summary=issue_summary,
            family_id=family_id,
            archetype=archetype,
            relevant_policies=policies[:5],
            top_option=top_option,
            all_options=options,
            family_safe_count=safe_count,
            family_demoted_count=demoted_count,
            family_blocked_count=blocked_count,
            preserved_behaviors=preserved,
            family_risks_remaining=fragile_remaining,
            validation_advice=validation,
            operator_style_note=op_note,
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _get_compat(pattern_id: str, family_id: str) -> FamilyCompat:
    family_map = _FAMILY_PATTERN_COMPAT.get(pattern_id, {})
    return family_map.get(family_id, "allow")


def _get_reason(pattern_id: str, family_id: str, compat: FamilyCompat) -> str:
    if compat == "allow":
        return ""
    reasons = _FAMILY_PATTERN_REASONS.get(pattern_id, {})
    return reasons.get(family_id, f"Elevated risk for {family_id} — verify before applying.")


def _get_compat_from_text(before: str, after: str, family_id: str) -> FamilyCompat:
    """
    Heuristic compat rating for a raw text candidate (not a named pattern).
    Checks if the rewrite removes fragile params or shortens in suspicious ways.
    """
    fragile = _FRAGILE_PARAMS.get(family_id, [])
    for param in fragile:
        if param in before and param not in after:
            return "block"   # removing a fragile param is a hard block
        if param in before and param in after:
            # param survives — check it wasn't mangled
            pass
    # If after is much shorter, demote as potential over-simplification
    if len(after) < len(before) * 0.6:
        return "demote"
    return "allow"


def _get_reason_from_text(before: str, after: str, family_id: str, compat: FamilyCompat) -> str:
    if compat == "allow":
        return ""
    fragile = _FRAGILE_PARAMS.get(family_id, [])
    removed = [p for p in fragile if p in before and p not in after]
    if removed:
        return (
            f"Rewrite removes fragile param(s) for {family_id}: {', '.join(removed)}. "
            "Removal of fragile params requires manual verification that all transclusions "
            "use the new form before this is safe."
        )
    if len(after) < len(before) * 0.6:
        return (
            f"Rewrite is significantly shorter ({len(after)} vs {len(before)} chars). "
            "Aggressive simplification is demoted for this family — "
            "verify legacy transclusion behavior is preserved."
        )
    return f"Elevated risk for {family_id} family — verify before applying."


def _check_fragile_params(before: str, after: str, family_id: str) -> list[str]:
    """Return fragile params that are present in before but changed/removed in after."""
    fragile = _FRAGILE_PARAMS.get(family_id, [])
    hits: list[str] = []
    for param in fragile:
        if param in before and param not in after:
            hits.append(param)
    return hits


def _preserved_for_option(pattern: WikiPattern, family_id: str) -> list[str]:
    """
    Determine which family behaviors the pattern explicitly preserves.
    Uses known notes + pattern semantics.
    """
    family_notes = _PRESERVED_BEHAVIOR_NOTES.get(family_id, [])
    preserved: list[str] = []

    # Patterns that add/maintain fallback chains preserve alias behavior
    if pattern.id in ("fallback_chain", "deprecated_param_alias"):
        preserved.append("deprecated/alias parameter compatibility preserved")
    # Empty-guard and blank-row suppression preserve optional-param safety
    if pattern.id in ("if_empty_guard", "infobox_blank_row_suppress"):
        preserved.append("optional-param blank-row suppression behavior preserved")
    # Switch default preserves explicit fallback intent
    if pattern.id == "switch_default_required":
        preserved.append("explicit #default fallback intent preserved")
    # Whitespace cleanup preserves all behavior
    if pattern.id == "infobox_label_data_cleanup":
        preserved.append("all parser behavior preserved (whitespace-only change)")

    # Add relevant family notes that apply
    for note in family_notes:
        for kw in ["teams", "birth_date", "image", "released", "platforms", "capacity", "coordinates"]:
            if kw in pattern.after.lower() and kw in note.lower():
                preserved.append(note)
                break

    return list(dict.fromkeys(preserved))[:5]


def _preserved_for_text(after: str, family_id: str) -> list[str]:
    """Preserved behaviors for a raw text candidate."""
    family_notes = _PRESERVED_BEHAVIOR_NOTES.get(family_id, [])
    preserved: list[str] = []
    for note in family_notes:
        for kw in ["teams", "birth_date", "image", "released", "platforms", "capacity", "coordinates"]:
            if kw in after.lower() and kw in note.lower():
                preserved.append(note)
                break
    return list(dict.fromkeys(preserved))[:4]


def _family_patch_class(
    compat: FamilyCompat,
    pattern_risk: str,
    has_hard_block: bool,
    fragile_hit: list[str],
) -> FamilyPatchClass:
    if compat == "block" or has_hard_block:
        return "family-risky"
    if fragile_hit:
        return "family-risky"
    if compat == "demote" or pattern_risk in ("review", "risky"):
        return "family-review"
    if pattern_risk == "safe" and compat == "allow":
        return "family-safe"
    return "insufficient-confidence"


def _score_option(
    compat: FamilyCompat,
    pattern_risk: str,
    rule_check,
    has_operator_overlap: bool,
    fragile_hit: list[str],
) -> int:
    """
    Score a rewrite option. Higher = better.
    Priority: family_safety > mechanical_safety > policy_fit > operator_style > tiebreak
    """
    if compat == "block":
        return 0

    score = 0

    # 1. Family safety (weight: 30)
    if compat == "allow":
        score += 30
    elif compat == "demote":
        score += 10

    # 2. Mechanical safety (weight: 20)
    score += {"safe": 20, "review": 10, "risky": 2}.get(pattern_risk, 0)

    # 3. Policy fit (weight: 15)
    if not rule_check.hard_blocks and not rule_check.soft_concerns:
        score += 15
    elif not rule_check.hard_blocks:
        score += 8

    # 4. Operator style (weight: 5)
    if has_operator_overlap:
        score += 5

    # 5. No fragile param issues (weight: 10)
    if not fragile_hit:
        score += 10

    return score


def _tags_for_family(family_id: str, archetype: str = "") -> list[str]:
    mapping: dict[str, list[str]] = {
        "nfl_biography":  ["nfl", "blp"],
        "vg_infobox":     ["vg"],
        "executive_bio":  ["blp"],
        "venue_project":  ["nfl"],
    }
    base = mapping.get(family_id, [])
    if "blp" in archetype or archetype in {
        "athlete_biography_nfl", "nfl_front_office", "executive_biography"
    }:
        if "blp" not in base:
            base = list(base) + ["blp"]
    return base

