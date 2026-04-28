"""
Rule precedence engine — WP:NFL, MOS:VG, MOS:GNG, MOS:BLP.

Not a flat list of rules. A structured layer that can:
  - surface relevant rules for a given context
  - detect conflicts between applicable rules
  - assign precedence when rules conflict
  - annotate a proposed patch with rule-level commentary

Design:
  Each rule has a policy_code, domain tags, and a severity level.
  Conflicts are detected when two rules with incompatible recommendations
  both apply to the same context.
  Precedence order (highest → lowest): BLP > RS/V > GNG > domain MOS > style guides.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["hard", "soft", "advisory"]
# hard     — violation; should not proceed without resolution
# soft     — concern; proceed with care and citation
# advisory — style preference; may be overridden with justification


@dataclass
class PolicyRule:
    id: str
    policy_code: str          # e.g. "WP:BLP", "MOS:VG"
    name: str
    description: str
    severity: Severity
    domain_tags: list[str]    # e.g. ["nfl", "blp", "living_person"]
    triggers: list[str]       # keywords that activate this rule in a context check
    recommendation: str
    conflicts_with: list[str] = field(default_factory=list)  # other rule IDs


@dataclass
class PolicyConflict:
    rule_a: PolicyRule
    rule_b: PolicyRule
    description: str
    resolution: str


@dataclass
class RuleCheckResult:
    context: str
    applicable_rules: list[PolicyRule]
    conflicts: list[PolicyConflict]
    hard_blocks: list[PolicyRule]
    soft_concerns: list[PolicyRule]
    advisories: list[PolicyRule]
    verdict: str   # "clear" | "concerns" | "blocked"

    def display(self) -> str:
        lines = [f"Rule check: {self.context}", f"Verdict: {self.verdict.upper()}", ""]
        if self.hard_blocks:
            lines.append("HARD BLOCKS:")
            for r in self.hard_blocks:
                lines.append(f"  [{r.policy_code}] {r.name}: {r.recommendation}")
        if self.soft_concerns:
            lines.append("CONCERNS:")
            for r in self.soft_concerns:
                lines.append(f"  [{r.policy_code}] {r.name}: {r.recommendation}")
        if self.advisories:
            lines.append("ADVISORIES:")
            for r in self.advisories:
                lines.append(f"  [{r.policy_code}] {r.name}: {r.recommendation}")
        if self.conflicts:
            lines.append("CONFLICTS:")
            for c in self.conflicts:
                lines.append(f"  {c.rule_a.policy_code} vs {c.rule_b.policy_code}: {c.resolution}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rule catalog
# ---------------------------------------------------------------------------

_RULES: list[PolicyRule] = [

    # ---- BLP ----
    PolicyRule(
        id="blp_citation_required",
        policy_code="WP:BLP",
        name="Contentious claims require citation",
        description="Any contentious or potentially damaging claim about a living person requires an inline citation from a reliable source.",
        severity="hard",
        domain_tags=["blp", "living_person", "nfl", "vg"],
        triggers=["living", "blp", "salary", "contract", "arrest", "criminal", "allegation",
                  "birth_date", "nationality", "religion", "spouse", "net_worth"],
        recommendation="Add inline citation before adding or restoring this content.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="blp_err_toward_omission",
        policy_code="WP:BLP",
        name="When in doubt, omit",
        description="BLP errs toward omitting sensitive information rather than including it with weak sourcing.",
        severity="hard",
        domain_tags=["blp", "living_person"],
        triggers=["unsourced", "unverified", "probably", "reportedly", "allegedly"],
        recommendation="Remove or defer the claim until a reliable source is identified.",
        conflicts_with=["mos_completeness"],
    ),
    PolicyRule(
        id="blp_no_original_research",
        policy_code="WP:BLP",
        name="No original research in BLP",
        description="Inferences, calculations, or synthesized claims about living persons are prohibited.",
        severity="hard",
        domain_tags=["blp", "living_person"],
        triggers=["calculated", "estimated", "inferred", "synthesized", "therefore"],
        recommendation="Use only what reliable sources state directly.",
        conflicts_with=[],
    ),

    # ---- Verifiability ----
    PolicyRule(
        id="v_reliable_source",
        policy_code="WP:V",
        name="Verifiable from reliable sources",
        description="All content must be verifiable from reliable, published sources.",
        severity="hard",
        domain_tags=["general", "nfl", "vg", "blp"],
        triggers=["citation needed", "unreferenced", "source", "cite"],
        recommendation="Add a reliable source citation.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="v_no_primary_only",
        policy_code="WP:V",
        name="Primary sources require secondary source support",
        description="Primary sources alone are insufficient for contentious or BLP content.",
        severity="soft",
        domain_tags=["blp", "nfl"],
        triggers=["primary source", "official", "press release", "team website"],
        recommendation="Supplement with independent secondary source.",
        conflicts_with=[],
    ),

    # ---- GNG ----
    PolicyRule(
        id="gng_significant_coverage",
        policy_code="WP:GNG",
        name="Subject requires significant coverage",
        description="Notability requires significant coverage in reliable sources independent of the subject.",
        severity="hard",
        domain_tags=["general", "nfl", "vg"],
        triggers=["notability", "notable", "gng", "significant coverage"],
        recommendation="Ensure multiple independent reliable sources provide significant coverage.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="gng_not_passing_mention",
        policy_code="WP:GNG",
        name="Passing mentions do not establish notability",
        description="Brief or incidental mentions in sources do not count toward GNG.",
        severity="soft",
        domain_tags=["general"],
        triggers=["mentioned in", "listed in", "appears in"],
        recommendation="Identify sources that focus specifically on the subject.",
        conflicts_with=[],
    ),

    # ---- WP:NFL ----
    PolicyRule(
        id="nfl_playing_in_game",
        policy_code="WP:NFL",
        name="NFL notability requires game participation",
        description="A player must have appeared in at least one regular-season or postseason NFL game.",
        severity="hard",
        domain_tags=["nfl"],
        triggers=["nfl player", "practice squad", "undrafted", "waived before playing"],
        recommendation="Verify the player appeared in a regular-season or postseason game before asserting notability.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="nfl_stats_sourcing",
        policy_code="WP:NFL",
        name="Stats must be sourced to NFL.com or Pro Football Reference",
        description="Career statistics should cite NFL.com or Pro Football Reference as the primary source.",
        severity="soft",
        domain_tags=["nfl"],
        triggers=["career stat", "rushing yard", "passing yard", "touchdown", "reception", "sack"],
        recommendation="Cite Pro Football Reference or NFL.com for statistics.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="nfl_contract_blp",
        policy_code="WP:NFL",
        name="Contract/salary values require reliable sourcing",
        description="Contract values, signing bonuses, and salary cap figures are BLP-sensitive and require reliable sourcing.",
        severity="hard",
        domain_tags=["nfl", "blp"],
        triggers=["contract", "salary", "signing bonus", "cap hit", "million", "deal"],
        recommendation="Cite Spotrac, Over The Cap, or official NFL/team announcements.",
        conflicts_with=[],
    ),

    # ---- MOS:VG ----
    PolicyRule(
        id="mosvg_title_italics",
        policy_code="MOS:VG",
        name="Game titles must be italicized",
        description="Video game titles in prose must be italicized using ''Title'' markup.",
        severity="soft",
        domain_tags=["vg"],
        triggers=["game title", "title", "italic"],
        recommendation="Use ''Title'' markup in prose; {{italic title}} in article.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="mosvg_genre_taxonomy",
        policy_code="MOS:VG",
        name="Use standardized VG genre taxonomy",
        description="Genre labels must come from the MOS:VG approved list. Invented or commercial genre names are not acceptable.",
        severity="soft",
        domain_tags=["vg"],
        triggers=["genre", "action", "rpg", "shooter", "platformer", "strategy"],
        recommendation="Use MOS:VG genre taxonomy: 'action-adventure', 'role-playing', 'first-person shooter', etc.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="mosvg_gameplay_before_plot",
        policy_code="MOS:VG",
        name="Gameplay section precedes Plot section",
        description="Per MOS:VG, the Gameplay section should appear before the Plot/Story section.",
        severity="advisory",
        domain_tags=["vg"],
        triggers=["gameplay", "plot", "story", "section order"],
        recommendation="Place Gameplay before Plot in article structure.",
        conflicts_with=[],
    ),
    PolicyRule(
        id="mosvg_no_peacock",
        policy_code="MOS:VG",
        name="Avoid peacock terms",
        description="Terms like 'groundbreaking', 'revolutionary', 'iconic' require citation or must be removed.",
        severity="soft",
        domain_tags=["vg"],
        triggers=["groundbreaking", "revolutionary", "iconic", "landmark", "seminal", "defining"],
        recommendation="Remove peacock term or attribute it to a cited source.",
        conflicts_with=[],
    ),

    # ---- Style cross-cutting ----
    PolicyRule(
        id="mos_completeness",
        policy_code="MOS",
        name="Articles should be complete",
        description="General MOS preference for completeness and coverage.",
        severity="advisory",
        domain_tags=["general"],
        triggers=["incomplete", "missing", "should include"],
        recommendation="Add missing content with appropriate sourcing.",
        conflicts_with=["blp_err_toward_omission"],
    ),
]

_RULE_INDEX: dict[str, PolicyRule] = {r.id: r for r in _RULES}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    """
    Applies policy rules to a given context and detects conflicts.

    Usage:
        engine = RuleEngine()
        result = engine.check("living NFL player, adding salary info", tags=["nfl", "blp"])
        print(result.display())

        result = engine.check_snippet(wikitext_snippet)
    """

    def check(self, context: str, tags: list[str] | None = None) -> RuleCheckResult:
        """
        Check a free-text context description against all rules.
        Tags (e.g. ["nfl", "blp"]) narrow the applicable rule set.
        """
        context_lower = context.lower()
        applicable: list[PolicyRule] = []

        for rule in _RULES:
            # Domain tag match
            if tags:
                tag_match = any(t in rule.domain_tags for t in tags) or "general" in rule.domain_tags
            else:
                tag_match = True

            if not tag_match:
                continue

            # Trigger keyword match
            if any(kw in context_lower for kw in rule.triggers):
                applicable.append(rule)

        conflicts = self._detect_conflicts(applicable)
        hard = [r for r in applicable if r.severity == "hard"]
        soft = [r for r in applicable if r.severity == "soft"]
        adv  = [r for r in applicable if r.severity == "advisory"]

        if hard:
            verdict = "blocked"
        elif soft:
            verdict = "concerns"
        else:
            verdict = "clear"

        return RuleCheckResult(
            context=context,
            applicable_rules=applicable,
            conflicts=conflicts,
            hard_blocks=hard,
            soft_concerns=soft,
            advisories=adv,
            verdict=verdict,
        )

    def check_snippet(self, wikitext: str, tags: list[str] | None = None) -> RuleCheckResult:
        """Check wikitext snippet directly — uses snippet as context."""
        return self.check(wikitext, tags=tags)

    def rules_for_policy(self, policy_code: str) -> list[PolicyRule]:
        """Return all rules under a given policy code."""
        return [r for r in _RULES if r.policy_code == policy_code]

    def rules_for_domain(self, domain_tag: str) -> list[PolicyRule]:
        """Return all rules tagged for a domain."""
        return [r for r in _RULES if domain_tag in r.domain_tags]

    def _detect_conflicts(self, applicable: list[PolicyRule]) -> list[PolicyConflict]:
        conflicts: list[PolicyConflict] = []
        ids = {r.id for r in applicable}
        for rule in applicable:
            for conflict_id in rule.conflicts_with:
                if conflict_id in ids:
                    other = _RULE_INDEX.get(conflict_id)
                    if other:
                        conflicts.append(PolicyConflict(
                            rule_a=rule,
                            rule_b=other,
                            description=f"{rule.policy_code} and {other.policy_code} give conflicting guidance.",
                            resolution=(
                                f"{rule.policy_code} takes precedence when severity is higher. "
                                f"BLP > RS/V > GNG > domain MOS > style advisories."
                            ),
                        ))
        return conflicts


# Singleton
_ENGINE = RuleEngine()


def RuleSet(policy_code: str) -> list[PolicyRule]:
    """Convenience: get all rules for a policy."""
    return _ENGINE.rules_for_policy(policy_code)
