"""
Anti-pattern library — things that commonly go wrong in wikitext/template work.

Each entry captures:
  - what it looks like (symptom)
  - why it happens (cause)
  - concrete example
  - safer alternative
  - whether sandbox validation is mandatory before fixing

These inform the patch critic and issue solver.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["high", "medium", "low"]


@dataclass
class AntiPattern:
    id: str
    name: str
    symptom: str
    likely_cause: str
    example: str
    safer_alternative: str
    severity: Severity
    sandbox_required: bool
    policy_refs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def matches(self, text: str | list[str]) -> bool:
        if isinstance(text, list):
            text = " ".join(text)
        low = text.lower()
        return any(k.lower() in low for k in self.keywords)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "symptom": self.symptom,
            "likely_cause": self.likely_cause,
            "example": self.example,
            "safer_alternative": self.safer_alternative,
            "severity": self.severity,
            "sandbox_required": self.sandbox_required,
            "policy_refs": self.policy_refs,
        }


ANTI_PATTERN_LIBRARY: list[AntiPattern] = [

    AntiPattern(
        id="bare_param_no_pipe",
        name="Bare parameter reference without fallback pipe",
        symptom="Template renders literal '{{{param_name}}}' when parameter is absent.",
        likely_cause="Author used {{{name}}} instead of {{{name|}}} — no empty fallback defined.",
        example="{{{birth_date}}}",
        safer_alternative="{{{birth_date|}}}  or  {{{birth_date|unknown}}}",
        severity="high",
        sandbox_required=False,
        policy_refs=[],
        keywords=["{{{", "}}}"],
    ),

    AntiPattern(
        id="missing_switch_default",
        name="#switch without #default",
        symptom="Template outputs nothing (empty string) for any value not explicitly listed in #switch.",
        likely_cause="Author forgot to add |#default= branch.",
        example="{{#switch:{{{status|}}}\n |active=Active\n |retired=Retired\n}}",
        safer_alternative="Add |#default= (even if empty) to make no-match behavior explicit.",
        severity="medium",
        sandbox_required=False,
        policy_refs=[],
        keywords=["#switch:", "#default"],
    ),

    AntiPattern(
        id="ifexpr_with_nonnumeric",
        name="#ifexpr on potentially non-numeric parameter",
        symptom="Parser error: '#ifexpr: invalid expression' when parameter contains text like 'N/A' or empty string.",
        likely_cause="#ifexpr requires a numeric expression; text input causes an error.",
        example="{{#ifexpr:{{{games_played|}}} > 0|...}}",
        safer_alternative="Guard with #if first: {{#if:{{{games_played|}}}|{{#ifexpr:{{{games_played}}} > 0|...}}}}",
        severity="high",
        sandbox_required=True,
        policy_refs=[],
        keywords=["#ifexpr:", "games_played", "count", "number", "total"],
    ),

    AntiPattern(
        id="deprecated_param_removal",
        name="Removing deprecated parameter breaks legacy transclusions",
        symptom="Pages that still use the old parameter name now show nothing or the parameter name literally.",
        likely_cause="Template was 'cleaned up' by removing the old param without adding an alias.",
        example="Old: |birth_city= removed. Pages using |birth_city= now render blank.",
        safer_alternative="Keep deprecated param as alias: {{{birth_city|{{{birthplace|}}}}}}} until all transclusions are updated.",
        severity="high",
        sandbox_required=True,
        policy_refs=[],
        keywords=["deprecated", "removed", "old param", "legacy", "alias"],
    ),

    AntiPattern(
        id="empty_infobox_row",
        name="Optional infobox row renders blank instead of hiding",
        symptom="Infobox shows empty label/data rows when optional parameters are absent.",
        likely_cause="Row not guarded with #if — always renders even when value is empty.",
        example="| label8 = Draft\n| data8  = {{{draft_year|}}}",
        safer_alternative="Wrap in #if: {{#if:{{{draft_year|}}}|label8=Draft|data8={{{draft_year|}}}}}}",
        severity="medium",
        sandbox_required=True,
        policy_refs=[],
        keywords=["label", "data", "infobox", "draft", "blank row"],
    ),

    AntiPattern(
        id="hard_coded_plural",
        name="Hard-coded plural regardless of count",
        symptom="'1 touchdowns' or '0 seasons' — plural form used even for singular/zero.",
        likely_cause="Author used plain '{{{count}}} items' without conditional pluralization.",
        example="{{{seasons|}}} seasons",
        safer_alternative="{{#ifexpr:{{{seasons|0}}}=1|{{{seasons|}}} season|{{{seasons|}}} seasons}}",
        severity="low",
        sandbox_required=False,
        policy_refs=[],
        keywords=["season", "touchdown", "year", "game", "win", "loss", "point"],
    ),

    AntiPattern(
        id="ref_name_collision",
        name="Named ref collision on same page",
        symptom="Multiple <ref name='x'> definitions on the same page — second definition silently ignored.",
        likely_cause="Same ref name used by two different citations.",
        example="<ref name='pfr'>...</ref> used twice with different content.",
        safer_alternative="Use unique ref names; reuse only the self-closing form: <ref name='pfr'/> for the same source.",
        severity="medium",
        sandbox_required=False,
        policy_refs=["WP:V"],
        keywords=["<ref", "name=", "citation", "ref name"],
    ),

    AntiPattern(
        id="blp_unsourced_negative",
        name="BLP: unsourced negative content about living person",
        symptom="Contentious claim about a living person added without inline citation.",
        likely_cause="Editor treated the claim as obvious or common knowledge.",
        example="Adding arrest record, salary figure, or health condition without citation.",
        safer_alternative="Remove content or add inline citation from reliable independent source before restoring.",
        severity="high",
        sandbox_required=False,
        policy_refs=["WP:BLP", "WP:V"],
        keywords=["arrest", "convicted", "allegedly", "reportedly", "salary", "net worth", "health"],
    ),

    AntiPattern(
        id="overaggressive_simplification",
        name="Simplification changes rendered behavior",
        symptom="Rewrite looks cleaner in source but changes what the template renders.",
        likely_cause="Author optimized for source readability without verifying output equivalence.",
        example="Collapsing {{#if:{{{a|}}}|{{#if:{{{b|}}}|...}}}} into {{#if:{{{a|}}}{{{b|}}}|...}} — semantics differ when one param is '0'.",
        safer_alternative="Run sandbox compare before/after. Prefer explicit logic over clever one-liners.",
        severity="high",
        sandbox_required=True,
        policy_refs=[],
        keywords=["simplify", "clean up", "refactor", "#if:", "collapse"],
    ),

    AntiPattern(
        id="image_prefix_in_infobox",
        name="File:/Image: prefix in |image= parameter",
        symptom="Broken image in infobox — shows red link or filename text instead of image.",
        likely_cause="Infobox image parameters expect bare filename; prefixes are added automatically.",
        example="| image = File:PlayerName.jpg",
        safer_alternative="| image = PlayerName.jpg",
        severity="medium",
        sandbox_required=False,
        policy_refs=[],
        keywords=["| image", "File:", "Image:", "infobox", ".jpg", ".png", ".svg"],
    ),

    AntiPattern(
        id="nfl_teams_wrong_format",
        name="NFL |teams= parameter wrong format",
        symptom="Infobox shows malformed team list or ignores some entries.",
        likely_cause="Teams listed as plain text or comma-separated instead of using {{NFL link}} per-line format.",
        example="| teams = New York Giants (2018-2020), Dallas Cowboys (2021)",
        safer_alternative=(
            "| teams = {{NFL link|New York Giants}} ({{ny|2018}}–{{ny|2020}})\n"
            "  {{NFL link|Dallas Cowboys}} ({{ny|2021}}–)"
        ),
        severity="medium",
        sandbox_required=True,
        policy_refs=["WP:NFL"],
        keywords=["| teams", "nfl link", "team", "giants", "cowboys", "commanders"],
    ),

    AntiPattern(
        id="ifeq_chain_no_default",
        name="Chained #ifeq without final fallback",
        symptom="Template outputs nothing when input doesn't match any case in the chain.",
        likely_cause="Author added #ifeq cases but forgot a terminal else clause.",
        example="{{#ifeq:{{{x}}}|A|Result A|{{#ifeq:{{{x}}}|B|Result B}}}}",
        safer_alternative="Add explicit fallback: {{#ifeq:{{{x}}}|A|Result A|{{#ifeq:{{{x}}}|B|Result B|Default}}}}",
        severity="medium",
        sandbox_required=False,
        policy_refs=[],
        keywords=["#ifeq:", "chain", "else", "fallback"],
    ),
]

_INDEX: dict[str, AntiPattern] = {ap.id: ap for ap in ANTI_PATTERN_LIBRARY}


def find_anti_patterns(text: str) -> list[AntiPattern]:
    """Return anti-patterns whose keywords appear in the text."""
    return [ap for ap in ANTI_PATTERN_LIBRARY if ap.matches(text)]


def get_anti_pattern(ap_id: str) -> AntiPattern | None:
    return _INDEX.get(ap_id)
