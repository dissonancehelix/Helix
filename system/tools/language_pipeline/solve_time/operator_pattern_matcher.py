"""
Operator pattern matcher — Phase 1.4.

Matches a live snippet or issue description against:
  1. The static pattern library (WikiPattern objects)
  2. Mined patterns from the operator's JSONL history (MinedPattern objects, if available)

Keeps the two sources separate in output so the caller knows the provenance:
  - library_matches   — from patterns.py (curated, has before/after examples)
  - mined_matches     — from edit_pattern_mining_report.json (historical, comment-cluster evidence)

The three-truth distinction is maintained here:
  Operator truth = what can be inferred from the operator's own prior behaviour.
  Rule truth     = not resolved here (see rule_engine).
  Mechanical truth = not resolved here (see reasoner.py / sandbox).

Usage:
    matcher = OperatorPatternMatcher()
    result = matcher.match(snippet="{{#if:{{{name}}}|{{{name}}}|}}")
    for m in result.library_matches:
        print(m.pattern.id, m.score)
    for m in result.mined_matches:
        print(m.pattern_id, m.confidence)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from system.tools.language_pipeline.pattern_library import PATTERN_LIBRARY, WikiPattern

_ARTIFACTS = (
    Path(__file__).resolve().parents[5]
    / "domains" / "language" / "wikipedia" / "data"
)
_MINING_REPORT = _ARTIFACTS / "edit_pattern_mining_report.json"

# ---------------------------------------------------------------------------
# Match result types
# ---------------------------------------------------------------------------

@dataclass
class LibraryMatch:
    """A match from the static pattern library."""
    pattern: WikiPattern
    score: int                  # number of keywords matched
    matched_keywords: list[str]

    def display(self) -> str:
        return (
            f"[{self.pattern.risk.upper():6s}] {self.pattern.name}  "
            f"(matched: {', '.join(self.matched_keywords[:4])})"
        )


@dataclass
class MinedMatch:
    """A match from the mined operator history."""
    pattern_id: str
    name: str
    cluster: str
    confidence: str              # "high" | "medium" | "low"
    evidence_count: int
    likely_purpose: str
    risk_notes: str
    score: int                   # keyword overlap score
    matched_keywords: list[str]

    def display(self) -> str:
        return (
            f"[{self.confidence.upper():6s}] {self.name}  "
            f"cluster={self.cluster}  evidence={self.evidence_count}  "
            f"(matched: {', '.join(self.matched_keywords[:4])})"
        )


@dataclass
class PatternMatchResult:
    """Full result of a pattern match operation."""
    query: str                       # the input text
    library_matches: list[LibraryMatch]
    mined_matches: list[MinedMatch]
    top_recommendation: str          # summary of best match, if any

    def has_matches(self) -> bool:
        return bool(self.library_matches or self.mined_matches)

    def display(self) -> str:
        lines: list[str] = []
        if self.library_matches:
            lines.append("Pattern library matches:")
            for m in self.library_matches[:5]:
                lines.append(f"  {m.display()}")
        if self.mined_matches:
            lines.append("Operator history matches:")
            for m in self.mined_matches[:5]:
                lines.append(f"  {m.display()}")
        if self.top_recommendation:
            lines.append(f"Top recommendation: {self.top_recommendation}")
        if not lines:
            lines.append("No pattern matches found.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mined pattern keywords (cluster name → keywords used for matching)
# These parallel the comment clusters in miner.py but allow snippet-matching.
# ---------------------------------------------------------------------------

_CLUSTER_KEYWORDS: dict[str, list[str]] = {
    "infobox_update":     ["infobox", "ibox", "{{infobox", "|image=", "|name=", "|birth_date="],
    "template_fix":       ["template", "{{", "}}", "#if", "#switch", "#ifeq"],
    "stat_update":        ["stat", "statistic", "career", "rushing", "passing", "touchdown", "sack"],
    "link_fix":           ["[[", "]]", "wikilink", "|link=", "piped"],
    "date_fix":           ["date", "born", "died", "birth_date", "death_date", "age"],
    "ref_fix":            ["<ref", "cite", "citation", "refname", "|url="],
    "copyedit":           ["typo", "grammar", "prose", "wording"],
    "lead_section":       ["lead", "lede", "intro", "opening"],
    "nfl_specific":       ["nfl", "draft", "commander", "quarterback", "linebacker"],
    "vg_specific":        ["game", "vg", "video game", "dota", "platform", "genre"],
    "whitespace_cleanup": ["whitespace", "spacing", "blank line", "empty"],
    "deprecated_param":   ["deprecated", "remove", "clean", "param", "alias"],
    "fallback_add":       ["fallback", "alias", "default", "|{{#if:", "empty guard"],
}


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class OperatorPatternMatcher:
    """
    Matches a snippet/issue against the static pattern library and mined history.

    Lazy-loads the mined pattern report on first use.
    Gracefully handles the case where no mining report exists yet.
    """

    def __init__(self):
        self._mined_patterns: list[dict] | None = None

    def match(
        self,
        snippet: str,
        top_n: int = 5,
    ) -> PatternMatchResult:
        """
        Match snippet against library and mined patterns.
        Returns top_n matches from each source, sorted by score.
        """
        text = snippet.lower()

        library_matches = self._match_library(text, top_n)
        mined_matches   = self._match_mined(text, top_n)

        # Top recommendation: highest-scoring library match if risk is safe/review;
        # else note that operator history suggests a cluster.
        top_rec = ""
        if library_matches:
            best_lib = library_matches[0]
            top_rec = (
                f"Library pattern '{best_lib.pattern.name}' [{best_lib.pattern.risk}] — "
                f"{best_lib.pattern.purpose}"
            )
        elif mined_matches:
            best_mine = mined_matches[0]
            top_rec = (
                f"Operator history cluster '{best_mine.cluster}' — "
                f"{best_mine.likely_purpose} "
                f"({best_mine.evidence_count} edits, {best_mine.confidence} confidence)"
            )

        return PatternMatchResult(
            query=snippet[:200],
            library_matches=library_matches,
            mined_matches=mined_matches,
            top_recommendation=top_rec,
        )

    def _match_library(self, text: str, top_n: int) -> list[LibraryMatch]:
        results: list[LibraryMatch] = []
        for pattern in PATTERN_LIBRARY:
            kw_hits = [kw for kw in pattern.keywords if kw.lower() in text]
            if kw_hits:
                results.append(LibraryMatch(
                    pattern=pattern,
                    score=len(kw_hits),
                    matched_keywords=kw_hits,
                ))
        results.sort(key=lambda m: -m.score)
        return results[:top_n]

    def _match_mined(self, text: str, top_n: int) -> list[MinedMatch]:
        mined = self._load_mined_patterns()
        if not mined:
            return []

        results: list[MinedMatch] = []
        for p in mined:
            # Score by cluster keyword overlap
            cluster = p.get("cluster", "")
            cluster_kws = _CLUSTER_KEYWORDS.get(cluster, [])
            # Also score by top_pages presence (article name in context)
            kw_hits = [kw for kw in cluster_kws if kw in text]
            # Also score by evidence_samples keyword overlap
            for sample in p.get("evidence_samples", [])[:3]:
                sample_words = [w for w in sample.lower().split() if len(w) > 4]
                for w in sample_words:
                    if w in text and w not in kw_hits:
                        kw_hits.append(w)
            if kw_hits:
                results.append(MinedMatch(
                    pattern_id=p.get("id", ""),
                    name=p.get("name", cluster),
                    cluster=cluster,
                    confidence=p.get("confidence", "low"),
                    evidence_count=p.get("evidence_count", 0),
                    likely_purpose=p.get("likely_purpose", ""),
                    risk_notes=p.get("risk_notes", ""),
                    score=len(kw_hits),
                    matched_keywords=kw_hits[:8],
                ))

        results.sort(key=lambda m: (-m.score, m.confidence == "high", m.evidence_count))
        return results[:top_n]

    def _load_mined_patterns(self) -> list[dict]:
        if self._mined_patterns is not None:
            return self._mined_patterns
        if _MINING_REPORT.exists():
            try:
                with open(_MINING_REPORT, encoding="utf-8") as f:
                    data = json.load(f)
                self._mined_patterns = data.get("patterns_found", [])
            except Exception:
                self._mined_patterns = []
        else:
            self._mined_patterns = []
        return self._mined_patterns

    def leave_alone_candidates(self) -> list[str]:
        """Pages that have revert evidence — be cautious with edits."""
        mined = self._load_mined_patterns()
        # The mining report stores this at the top level; load from file if needed
        if _MINING_REPORT.exists():
            try:
                with open(_MINING_REPORT, encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("leave_alone_candidates", [])
            except Exception:
                return []
        return []

