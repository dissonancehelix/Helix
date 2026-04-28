"""
Article archetype detector — Phase 1.4.

Infers the most likely article archetype from:
  - A template name (e.g. "Infobox NFL player" → athlete_biography_nfl)
  - A wikitext snippet (keywords, infobox calls, section headings)
  - An article title hint (e.g. "Chase Young" → athlete_biography_nfl)
  - An explicit context string

Archetypes match the gold corpus classifications from Phase 1.2:
  athlete_biography_nfl   — NFL player biography
  executive_biography     — business/executive/team executive biography
  nfl_front_office        — NFL front-office personnel (GM, coach, owner)
  video_game_article      — video game article (MOS:VG)
  infrastructure_article  — stadium/venue/project article
  unknown                 — cannot determine

Archetype affects which rules matter most and what structural norms are expected.
This is used at solve-time to prioritise rule checks and pattern suggestions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Archetype = Literal[
    "athlete_biography_nfl",
    "executive_biography",
    "nfl_front_office",
    "video_game_article",
    "infrastructure_article",
    "unknown",
]

# ---------------------------------------------------------------------------
# Archetype signal tables
# ---------------------------------------------------------------------------

# Template name → archetype (first match wins, most specific first)
_TEMPLATE_SIGNALS: list[tuple[re.Pattern, Archetype]] = [
    (re.compile(r"(?i)infobox\s+nfl\s+player"), "athlete_biography_nfl"),
    (re.compile(r"(?i)infobox\s+american\s+football\s+player"), "athlete_biography_nfl"),
    (re.compile(r"(?i)infobox\s+american\s+football\s+(biography|career)"), "athlete_biography_nfl"),
    (re.compile(r"(?i)nfl\s+player\s+stat"), "athlete_biography_nfl"),

    (re.compile(r"(?i)infobox\s+nfl\s+(coach|official|staff|executive)"), "nfl_front_office"),
    (re.compile(r"(?i)infobox\s+nfl\s+(general\s+manager|owner)"), "nfl_front_office"),

    (re.compile(r"(?i)infobox\s+video\s+game"), "video_game_article"),
    (re.compile(r"(?i)video\s+game\s+release"), "video_game_article"),
    (re.compile(r"(?i)infobox\s+game"), "video_game_article"),

    (re.compile(r"(?i)infobox\s+stadium"), "infrastructure_article"),
    (re.compile(r"(?i)infobox\s+(arena|venue|building|structure)"), "infrastructure_article"),

    (re.compile(r"(?i)infobox\s+(officeholder|politician)"), "executive_biography"),
    (re.compile(r"(?i)infobox\s+person"), "executive_biography"),
    (re.compile(r"(?i)infobox\s+(businessman|executive)"), "executive_biography"),
]

# Free-text keyword signals → archetype (scored; highest score wins)
_KEYWORD_SIGNALS: dict[Archetype, list[str]] = {
    "athlete_biography_nfl": [
        "nfl", "quarterback", "wide receiver", "running back", "linebacker",
        "safety", "cornerback", "draft pick", "rookie", "super bowl",
        "career statistics", "rushing yards", "passing yards", "touchdowns",
        "sack", "interception", "pro bowl", "all-pro", "trade", "waived",
        "infobox nfl player", "nflplayer", "nfl player",
    ],
    "nfl_front_office": [
        "general manager", "head coach", "offensive coordinator",
        "defensive coordinator", "owner", "team president",
        "front office", "gm", "coaching staff", "nfl executive",
    ],
    "executive_biography": [
        "ceo", "entrepreneur", "businessman", "investor",
        "chairman", "billionaire", "net worth", "founded",
        "private equity", "venture capital", "alma mater", "education",
        "born in", "nationality", "spouse",
    ],
    "video_game_article": [
        "video game", "dota", "steam", "pc game", "console", "playstation",
        "xbox", "nintendo", "developer", "publisher", "gameplay", "plot",
        "reception", "metacritic", "game engine", "genre", "multiplayer",
        "single-player", "open world", "role-playing", "action game",
    ],
    "infrastructure_article": [
        "stadium", "arena", "venue", "capacity", "construction",
        "opened", "surface", "tenants", "seating", "coordinates",
        "architect", "renovation", "naming rights", "location",
    ],
}

# Gold corpus article → archetype (fast path for known articles)
_GOLD_ARTICLE_MAP: dict[str, Archetype] = {
    "Chase Young":              "athlete_biography_nfl",
    "Jayden Daniels":           "athlete_biography_nfl",
    "Josh Harris (businessman)":"executive_biography",
    "Adam Peters":              "nfl_front_office",
    "Brandon Sosna":            "nfl_front_office",
    "Dota 2":                   "video_game_article",
    "New Commanders Stadium":   "infrastructure_article",
}

# Policy priority per archetype (ordered, highest precedence first)
ARCHETYPE_POLICY_PRIORITY: dict[Archetype, list[str]] = {
    "athlete_biography_nfl":  ["WP:NFL", "WP:BLP", "MOS:Biography", "WP:V", "MOS"],
    "nfl_front_office":       ["WP:NFL", "WP:BLP", "MOS:Biography", "WP:V", "MOS"],
    "executive_biography":    ["WP:BLP", "MOS:Biography", "WP:GNG", "WP:V", "MOS"],
    "video_game_article":     ["MOS:VG", "WP:GNG", "WP:V", "MOS"],
    "infrastructure_article": ["WP:NFL", "WP:V", "MOS"],
    "unknown":                ["WP:V", "WP:BLP", "WP:GNG", "MOS"],
}

# Structural norms per archetype (used in reasoning output)
ARCHETYPE_NORMS: dict[Archetype, dict] = {
    "athlete_biography_nfl": {
        "expected_sections": ["Early life", "College career", "Professional career",
                              "Career statistics", "References"],
        "expected_infoboxes": ["Infobox NFL player"],
        "chronology_type": "forward",
        "blp_sensitive": True,
        "stats_table_expected": True,
    },
    "nfl_front_office": {
        "expected_sections": ["Early life", "Career", "References"],
        "expected_infoboxes": ["Infobox person", "Infobox NFL coach"],
        "chronology_type": "forward",
        "blp_sensitive": True,
        "stats_table_expected": False,
    },
    "executive_biography": {
        "expected_sections": ["Early life", "Career", "Personal life", "References"],
        "expected_infoboxes": ["Infobox person", "Infobox businessman"],
        "chronology_type": "forward",
        "blp_sensitive": True,
        "stats_table_expected": False,
    },
    "video_game_article": {
        "expected_sections": ["Gameplay", "Plot", "Development", "Reception", "References"],
        "expected_infoboxes": ["Infobox video game"],
        "chronology_type": "topical",
        "blp_sensitive": False,
        "stats_table_expected": False,
    },
    "infrastructure_article": {
        "expected_sections": ["History", "Design", "Capacity", "Events", "References"],
        "expected_infoboxes": ["Infobox stadium", "Infobox building"],
        "chronology_type": "forward",
        "blp_sensitive": False,
        "stats_table_expected": False,
    },
    "unknown": {
        "expected_sections": [],
        "expected_infoboxes": [],
        "chronology_type": "unknown",
        "blp_sensitive": False,
        "stats_table_expected": False,
    },
}


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ArchetypeResult:
    archetype: Archetype
    confidence: str             # "high" | "medium" | "low"
    signal_source: str          # "template" | "article_title" | "keywords" | "context" | "none"
    matched_signals: list[str]  # the specific signals that triggered this
    policy_priority: list[str]  # ordered policy list for this archetype
    norms: dict                 # structural norms for this archetype

    def is_blp(self) -> bool:
        return self.norms.get("blp_sensitive", False)

    def display(self) -> str:
        lines = [
            f"Archetype: {self.archetype}  [{self.confidence} confidence]",
            f"  Source: {self.signal_source}",
            f"  Matched: {', '.join(self.matched_signals[:5]) or 'none'}",
            f"  Policy priority: {' > '.join(self.policy_priority)}",
        ]
        if self.is_blp():
            lines.append("  BLP sensitive: YES")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def detect_archetype(
    template_name: str = "",
    snippet: str = "",
    context: str = "",
    article_title: str = "",
) -> ArchetypeResult:
    """
    Infer article archetype from any combination of inputs.

    Priority order:
    1. Known gold article title (fast path, high confidence)
    2. Template name match (high confidence)
    3. Keyword scoring of snippet + context (medium/low confidence)
    """
    combined_text = f"{snippet} {context}".lower()

    # 1. Gold article fast path
    if article_title and article_title in _GOLD_ARTICLE_MAP:
        arch = _GOLD_ARTICLE_MAP[article_title]
        return _make_result(arch, "high", "article_title", [article_title])

    # 2. Template name match
    if template_name:
        name = template_name.removeprefix("Template:").strip()
        for pattern, arch in _TEMPLATE_SIGNALS:
            if pattern.search(name):
                return _make_result(arch, "high", "template", [name])
        # Also check if template name appears in snippet
        for pattern, arch in _TEMPLATE_SIGNALS:
            if pattern.search(combined_text):
                return _make_result(arch, "high", "template", [f"inferred from snippet: {name}"])

    # 3. Keyword scoring
    scores: dict[Archetype, int] = {a: 0 for a in _KEYWORD_SIGNALS}
    matched: dict[Archetype, list[str]] = {a: [] for a in _KEYWORD_SIGNALS}
    for arch, keywords in _KEYWORD_SIGNALS.items():
        for kw in keywords:
            if kw in combined_text:
                scores[arch] += 1
                matched[arch].append(kw)

    # Also check template signals against snippet
    for pattern, arch in _TEMPLATE_SIGNALS:
        if pattern.search(combined_text):
            scores[arch] += 5  # strong bonus for infobox name appearing in snippet

    best_arch = max(scores, key=lambda a: scores[a])
    best_score = scores[best_arch]

    if best_score == 0:
        return _make_result("unknown", "low", "none", [])

    if best_score >= 4:
        confidence = "high"
    elif best_score >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    return _make_result(best_arch, confidence, "keywords", matched[best_arch][:8])


def _make_result(
    archetype: Archetype,
    confidence: str,
    source: str,
    signals: list[str],
) -> ArchetypeResult:
    return ArchetypeResult(
        archetype=archetype,
        confidence=confidence,
        signal_source=source,
        matched_signals=signals,
        policy_priority=ARCHETYPE_POLICY_PRIORITY.get(archetype, ARCHETYPE_POLICY_PRIORITY["unknown"]),
        norms=ARCHETYPE_NORMS.get(archetype, ARCHETYPE_NORMS["unknown"]),
    )
