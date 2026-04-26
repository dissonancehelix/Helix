"""
Pattern library — reusable wikitext/template patterns derived from
Dissident93's edit history and known editing style.

Each pattern includes:
  - name / purpose
  - before/after example
  - risk notes
  - when to use / not use
  - keywords for matching

Patterns are classified as:
  safe        — parser output is identical; mechanical substitution is fine
  review      — functionally equivalent but check rendered output first
  risky       — behavior may depend on context; require sandbox validation

This library is NOT a code generator. It is a reference surface for the
issue_solver to draw on when proposing edits.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

RiskLevel = Literal["safe", "review", "risky"]


@dataclass
class WikiPattern:
    id: str
    name: str
    purpose: str
    before: str
    after: str
    risk: RiskLevel
    risk_notes: str
    use_when: str
    avoid_when: str
    keywords: list[str] = field(default_factory=list)

    def matches(self, snippet: str) -> bool:
        """Heuristic: does this snippet likely benefit from this pattern?"""
        low = snippet.lower()
        return any(k.lower() in low for k in self.keywords)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "purpose": self.purpose,
            "before": self.before,
            "after": self.after,
            "risk": self.risk,
            "risk_notes": self.risk_notes,
            "use_when": self.use_when,
            "avoid_when": self.avoid_when,
        }


# ---------------------------------------------------------------------------
# Core pattern catalog — derived from Dissident93's known edit patterns
# (infobox work, template namespace edits, chronology/NFL/games article style)
# ---------------------------------------------------------------------------

PATTERN_LIBRARY: list[WikiPattern] = [

    WikiPattern(
        id="if_empty_guard",
        name="Empty-guard: #if with pipe vs without",
        purpose=(
            "Distinguish {{#if:{{{param|}}}|...}} (safe empty-check) from "
            "{{#if:{{{param}}}|...}} (outputs literal {{{param}}} string when param absent). "
            "The bare form without the pipe is a common latent bug."
        ),
        before="{{#if:{{{param}}}|value|fallback}}",
        after="{{#if:{{{param|}}}|value|fallback}}",
        risk="safe",
        risk_notes=(
            "Functionally identical when the parameter is provided. "
            "When absent: bare form renders literal '{{{param}}}'; "
            "pipe form treats it as empty string → correct branch taken."
        ),
        use_when="Template uses #if on a parameter without a trailing pipe inside the braces.",
        avoid_when="Parameter intentionally uses a non-empty default (e.g., {{{param|N/A}}} — leave as-is).",
        keywords=["#if:", "{{{", "}}}"],
    ),

    WikiPattern(
        id="fallback_chain",
        name="Multi-level fallback parameter chain",
        purpose=(
            "Use nested fallback syntax to try multiple parameter names before "
            "resolving to empty. Common when templates have renamed parameters "
            "but must remain backward-compatible."
        ),
        before="{{{param}}}",
        after="{{{param|{{{legacy_param|}}}}}}",
        risk="review",
        risk_notes=(
            "Safe when the outer parameter is always defined. "
            "Adds legacy compatibility. Verify the legacy param name is actually "
            "in use in transclusions before adding it."
        ),
        use_when="A parameter was renamed and old transclusions still use the old name.",
        avoid_when="Both parameter names are actively in use and mean different things.",
        keywords=["{{{", "}}}", "legacy", "deprecated", "alias"],
    ),

    WikiPattern(
        id="ifeq_switch_collapse",
        name="Collapse repeated #ifeq chains into #switch",
        purpose=(
            "Replace chains of {{#ifeq:{{{x}}}|val1|...|{{#ifeq:{{{x}}}|val2|...|...}}}} "
            "with a cleaner {{#switch:{{{x}}}|val1=...|val2=...|#default=...}}."
        ),
        before=(
            "{{#ifeq:{{{type|}}}|A|Result A|{{#ifeq:{{{type|}}}|B|Result B|Default}}}}"
        ),
        after=(
            "{{#switch:{{{type|}}}\n"
            " |A=Result A\n"
            " |B=Result B\n"
            " |#default=Default\n"
            "}}"
        ),
        risk="safe",
        risk_notes=(
            "Semantically identical for string equality. #switch is more readable "
            "and slightly faster. Ensure #default is present if the original had a "
            "final fallback."
        ),
        use_when="Three or more chained #ifeq on the same variable.",
        avoid_when="Only two branches — #ifeq is fine at that scale.",
        keywords=["#ifeq:", "#switch:", "type", "|A=", "|B="],
    ),

    WikiPattern(
        id="switch_default_required",
        name="Ensure #switch has explicit #default",
        purpose=(
            "A #switch without #default silently outputs nothing for unmatched values. "
            "Add an explicit #default (even if empty) to make behavior intentional."
        ),
        before=(
            "{{#switch:{{{status|}}}\n"
            " |active=Active\n"
            " |retired=Retired\n"
            "}}"
        ),
        after=(
            "{{#switch:{{{status|}}}\n"
            " |active=Active\n"
            " |retired=Retired\n"
            " |#default=\n"
            "}}"
        ),
        risk="safe",
        risk_notes=(
            "No output change for matched values. For unmatched values, "
            "output was already empty — now it is explicitly empty. "
            "If unmatched values previously output something unexpected, "
            "run sandbox compare first."
        ),
        use_when="#switch has no #default and unmatched inputs should render nothing.",
        avoid_when="A meaningful catch-all value is needed — write the actual default content.",
        keywords=["#switch:", "#default"],
    ),

    WikiPattern(
        id="infobox_label_data_cleanup",
        name="Infobox label/data whitespace normalization",
        purpose=(
            "Remove trailing spaces from |label and |data parameter values in "
            "{{Infobox}} templates. Trailing spaces can cause subtle rendering "
            "differences and lint warnings."
        ),
        before="| label5 = Position   \n| data5  = {{{position|}}}   ",
        after="| label5 = Position\n| data5  = {{{position|}}}",
        risk="safe",
        risk_notes="Whitespace-only change. No parser behavior change.",
        use_when="Infobox parameters have trailing whitespace.",
        avoid_when="Never needs avoidance — always safe to trim trailing spaces.",
        keywords=["label", "data", "infobox", "| label", "| data"],
    ),

    WikiPattern(
        id="infobox_blank_row_suppress",
        name="Suppress blank infobox rows with #if guard",
        purpose=(
            "Wrap optional infobox rows in #if so they disappear entirely "
            "when the parameter is unprovided, rather than rendering a blank row."
        ),
        before=(
            "| label8 = Draft\n"
            "| data8  = {{{draft_year|}}} round {{{draft_round|}}}, "
            "pick {{{draft_pick|}}}"
        ),
        after=(
            "{{#if:{{{draft_year|}}}\n"
            " | label8 = Draft\n"
            " | data8  = {{{draft_year|}}} round {{{draft_round|}}}, "
            "pick {{{draft_pick|}}}\n"
            "}}"
        ),
        risk="review",
        risk_notes=(
            "Changes rendered output when parameter is absent (row hidden vs blank). "
            "Verify no downstream CSS targets the blank row before applying."
        ),
        use_when="Optional infobox row renders a blank/empty cell when parameter is absent.",
        avoid_when="Row must always be visible even when data is missing.",
        keywords=["label", "data", "{{{draft", "infobox", "#if:"],
    ),

    WikiPattern(
        id="pluralization_ifexpr",
        name="Pluralization via #ifexpr",
        purpose=(
            "Correctly pluralize a noun based on a numeric parameter using #ifexpr. "
            "Avoids hard-coding 'seasons' vs 'season' etc."
        ),
        before="{{{seasons|}}} seasons",
        after="{{#ifexpr:{{{seasons|0}}}=1|{{{seasons|}}} season|{{{seasons|}}} seasons}}",
        risk="review",
        risk_notes=(
            "Output changes from always-plural to singular when count=1. "
            "Validate that the parameter is always numeric; non-numeric input "
            "will cause an #ifexpr evaluation error."
        ),
        use_when="A count parameter is used inline and singular/plural distinction matters.",
        avoid_when=(
            "Parameter may be non-numeric (e.g., 'N/A', '?'). "
            "In that case use #ifeq or a safer #if guard."
        ),
        keywords=["#ifexpr:", "season", "year", "game", "win", "loss", "{{{count"],
    ),

    WikiPattern(
        id="deprecated_param_alias",
        name="Add alias for renamed/deprecated parameter",
        purpose=(
            "When a template parameter is renamed, add an alias so existing "
            "transclusions using the old name continue to work."
        ),
        before="{{{new_name|}}}",
        after="{{{new_name|{{{old_name|}}}}}}",
        risk="safe",
        risk_notes=(
            "No output change when new_name is provided. When only old_name is "
            "provided, output now resolves correctly instead of being blank. "
            "Safe to deploy immediately."
        ),
        use_when="A parameter was renamed in a template but old transclusions haven't been updated.",
        avoid_when="old_name and new_name have different semantics — don't alias them.",
        keywords=["deprecated", "renamed", "alias", "old_name", "legacy"],
    ),

    WikiPattern(
        id="ref_consolidation",
        name="Consolidate repeated inline references",
        purpose=(
            "Replace repeated identical <ref>...</ref> blocks with a named ref "
            "(<ref name='x'>...</ref> first use, <ref name='x'/> subsequent uses)."
        ),
        before=(
            "<ref>Smith, John. ''Title''. 2020. p. 5.</ref>\n"
            "...\n"
            "<ref>Smith, John. ''Title''. 2020. p. 5.</ref>"
        ),
        after=(
            "<ref name='smith2020'>Smith, John. ''Title''. 2020. p. 5.</ref>\n"
            "...\n"
            "<ref name='smith2020'/>"
        ),
        risk="safe",
        risk_notes=(
            "Identical citation text. Parser output is semantically equivalent. "
            "ref name must be unique on the page — check for collisions."
        ),
        use_when="The same citation appears two or more times on a page.",
        avoid_when="Citations differ in any detail (page numbers, access dates).",
        keywords=["<ref>", "</ref>", "cite", "citation", "footnote"],
    ),

    WikiPattern(
        id="nowiki_template_display",
        name="Use <nowiki/> to display template syntax literally",
        purpose=(
            "Use <nowiki/> (self-closing, zero-width) rather than {{}} escaping "
            "to show template syntax in documentation without triggering transclusion."
        ),
        before="{{{{template name}}}}",
        after="<nowiki/>{{template name}}",
        risk="safe",
        risk_notes=(
            "Display-only change in documentation contexts. "
            "Has no effect in main article space."
        ),
        use_when="Template /doc pages need to show example transclusion syntax.",
        avoid_when="Content is not in a documentation or talk context.",
        keywords=["<nowiki>", "doc", "example", "template name"],
    ),
]


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_pattern(pattern_id: str) -> WikiPattern | None:
    for p in PATTERN_LIBRARY:
        if p.id == pattern_id:
            return p
    return None


def find_matching_patterns(snippet: str) -> list[WikiPattern]:
    """Return patterns whose keywords appear in the snippet."""
    return [p for p in PATTERN_LIBRARY if p.matches(snippet)]
