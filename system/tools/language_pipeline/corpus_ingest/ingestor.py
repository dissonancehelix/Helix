"""
Corpus ingestor — fetches the operator's Wikipedia profile and the targeted
rule/style corpus via the official MediaWiki API.

Phase 1.1 targeted corpus:
  Profile:
    - User:Dissident93

  Rule / style:
    - Wikipedia:Manual_of_Style/Video_games     (MOS:VG)
    - Wikipedia:WikiProject_National_Football_League  (WP:NFL)
    - Wikipedia:Manual_of_Style/Biography       (MOS:Biography)
    - Wikipedia:Manual_of_Style                 (MOS)
    - Wikipedia:Notability                      (WP:GNG / Notability)

All fetches use action=query&prop=revisions (official API).
No HTML scraping.
No live Wikipedia edits.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_USER_AGENT = "HelixWikiOperator/1.0 (Research; User:Dissident93)"
_ENWIKI_API = "https://en.wikipedia.org/w/api.php"

_ARTIFACTS = (
    Path(__file__).resolve().parents[1]
    / "data"
)

# ---------------------------------------------------------------------------
# Target corpus definition
# ---------------------------------------------------------------------------

PROFILE_TARGETS = [
    {"title": "User:Dissident93", "layer": "profile", "label": "Operator user page"},
]

RULE_TARGETS = [
    {
        "title": "Wikipedia:Manual of Style/Video games",
        "layer": "rule",
        "policy_code": "MOS:VG",
        "label": "Manual of Style — Video games",
        "domain_tags": ["vg"],
        "priority": 1,
    },
    {
        "title": "Wikipedia:WikiProject National Football League",
        "layer": "rule",
        "policy_code": "WP:NFL",
        "label": "WikiProject National Football League",
        "domain_tags": ["nfl"],
        "priority": 1,
    },
    {
        "title": "Wikipedia:Manual of Style/Biography",
        "layer": "rule",
        "policy_code": "MOS:Biography",
        "label": "Manual of Style — Biography",
        "domain_tags": ["blp", "nfl", "vg"],
        "priority": 2,
    },
    {
        "title": "Wikipedia:Manual of Style",
        "layer": "rule",
        "policy_code": "MOS",
        "label": "Manual of Style (main)",
        "domain_tags": ["general"],
        "priority": 3,
    },
    {
        "title": "Wikipedia:Notability",
        "layer": "rule",
        "policy_code": "WP:GNG",
        "label": "Notability guideline",
        "domain_tags": ["general", "nfl", "vg"],
        "priority": 2,
    },
    {
        "title": "Wikipedia:Manual of Style/Words to watch",
        "layer": "rule",
        "policy_code": "MOS:WORDS",
        "label": "Manual of Style — Words to watch",
        "domain_tags": ["general", "blp", "nfl", "vg"],
        "priority": 1,
    },
    {
        "title": "Wikipedia:Manual of Style/Lead section",
        "layer": "rule",
        "policy_code": "MOS:LEAD",
        "label": "Manual of Style — Lead section",
        "domain_tags": ["general"],
        "priority": 2,
    },
    {
        "title": "Wikipedia:Manual of Style/Layout",
        "layer": "rule",
        "policy_code": "MOS:LAYOUT",
        "label": "Manual of Style — Layout",
        "domain_tags": ["general"],
        "priority": 3,
    },
    {
        "title": "Wikipedia:Manual of Style/Tables",
        "layer": "rule",
        "policy_code": "MOS:TABLES",
        "label": "Manual of Style — Tables",
        "domain_tags": ["general"],
        "priority": 3,
    },
    {
        "title": "Wikipedia:Manual of Style/Infoboxes",
        "layer": "rule",
        "policy_code": "MOS:INFOBOX",
        "label": "Manual of Style — Infoboxes",
        "domain_tags": ["general"],
        "priority": 2,
    },
    {
        "title": "Wikipedia:Manual of Style/Text formatting",
        "layer": "rule",
        "policy_code": "MOS:TEXT",
        "label": "Manual of Style — Text formatting",
        "domain_tags": ["general"],
        "priority": 3,
    },
    {
        "title": "Wikipedia:WikiProject National Football League/Player pages format",
        "layer": "rule",
        "policy_code": "WP:NFL/P",
        "label": "NFL Player pages format",
        "domain_tags": ["nfl"],
        "priority": 1,
    },
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OperatorProfile:
    username: str
    page_title: str
    wikitext: str | None
    editing_domains: list[str]
    key_wikiprojects: list[str]
    template_competence_signals: list[str]
    contribution_signals: list[str]
    primary_areas: list[str]
    raw_sections: dict[str, str]   # section heading → text
    fetch_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "page_title": self.page_title,
            "editing_domains": self.editing_domains,
            "key_wikiprojects": self.key_wikiprojects,
            "template_competence_signals": self.template_competence_signals,
            "contribution_signals": self.contribution_signals,
            "primary_areas": self.primary_areas,
            "section_count": len(self.raw_sections),
            "wikitext_length": len(self.wikitext) if self.wikitext else 0,
            "fetch_error": self.fetch_error,
        }


@dataclass
class RuleCorpusEntry:
    title: str
    policy_code: str
    label: str
    domain_tags: list[str]
    priority: int
    wikitext: str | None
    sections: list[str]           # section headings
    key_statements: list[str]     # extracted rule-like sentences
    dos: list[str]                # explicit "SHOULD/MUST" directives
    donts: list[str]              # explicit "AVOID/NEVER/DO NOT" directives
    scope: str                    # one-line scope summary
    overlap_codes: list[str]      # other policy codes this overlaps with
    fetch_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "policy_code": self.policy_code,
            "label": self.label,
            "domain_tags": self.domain_tags,
            "priority": self.priority,
            "sections": self.sections[:30],
            "key_statements": self.key_statements[:20],
            "dos": self.dos[:15],
            "donts": self.donts[:15],
            "scope": self.scope,
            "overlap_codes": self.overlap_codes,
            "wikitext_length": len(self.wikitext) if self.wikitext else 0,
            "fetch_error": self.fetch_error,
        }


# ---------------------------------------------------------------------------
# Applicability map (Part C of Phase 1.1)
# ---------------------------------------------------------------------------

RULE_APPLICABILITY_MAP: dict[str, list[dict]] = {
    "video_game_article": [
        {"policy": "MOS:VG",       "priority": 1, "reason": "Primary MOS for VG articles"},
        {"policy": "MOS",          "priority": 2, "reason": "General style fallback"},
        {"policy": "WP:GNG",       "priority": 3, "reason": "Notability if topic is borderline"},
    ],
    "nfl_biography": [
        {"policy": "WP:NFL",       "priority": 1, "reason": "Domain notability + style"},
        {"policy": "MOS:Biography","priority": 2, "reason": "Biography formatting"},
        {"policy": "WP:BLP",       "priority": 2, "reason": "Living person protection"},
        {"policy": "MOS",          "priority": 3, "reason": "General style fallback"},
    ],
    "living_person_biography": [
        {"policy": "WP:BLP",       "priority": 1, "reason": "Living person protection — supersedes other editorial considerations"},
        {"policy": "MOS:Biography","priority": 2, "reason": "Biography formatting"},
        {"policy": "MOS",          "priority": 3, "reason": "General style fallback"},
        {"policy": "WP:GNG",       "priority": 3, "reason": "Notability if subject is borderline"},
    ],
    "article_naming_or_style": [
        {"policy": "MOS",          "priority": 1, "reason": "Main style authority"},
        {"policy": "MOS:VG",       "priority": 2, "reason": "If VG context"},
        {"policy": "MOS:Biography","priority": 2, "reason": "If biography context"},
    ],
    "notability_or_significance": [
        {"policy": "WP:GNG",       "priority": 1, "reason": "Primary notability guideline"},
        {"policy": "WP:NFL",       "priority": 2, "reason": "Domain-specific notability for NFL"},
        {"policy": "WP:VG",        "priority": 2, "reason": "Domain-specific notability for games"},
    ],
    "template_editing": [
        {"policy": "MOS",          "priority": 1, "reason": "Formatting conventions"},
        {"policy": "WP:BLP",       "priority": 1, "reason": "If template used in BLP articles"},
        {"policy": "MOS:VG",       "priority": 2, "reason": "If VG infobox/navbox"},
        {"policy": "WP:NFL",       "priority": 2, "reason": "If NFL infobox/stats template"},
    ],
}

# ---------------------------------------------------------------------------
# Operator-to-rule crosswalk (Part D)
# ---------------------------------------------------------------------------

OPERATOR_RULE_CROSSWALK: dict[str, Any] = {
    "operator": "Dissident93",
    "primary_editing_domains": ["NFL biographies", "Video game articles", "Sports biographies", "VGM composers"],
    "crosswalk": [
        {
            "editing_domain": "NFL player biographies",
            "articles_like": ["Jayden Daniels", "Josh Harris", "Washington Commanders"],
            "most_relevant_policies": ["WP:NFL", "WP:BLP", "MOS:Biography", "MOS"],
            "notes": "High edit volume. BLP applies to all active players. Contract/stats require RS.",
        },
        {
            "editing_domain": "Video game articles",
            "articles_like": ["Dota 2", "Persona 5", "FromSoftware games"],
            "most_relevant_policies": ["MOS:VG", "WP:GNG", "MOS"],
            "notes": "MOS:VG is primary authority. Peacock terms are a recurring issue.",
        },
        {
            "editing_domain": "VGM composer articles",
            "articles_like": ["Yoko Shimomura", "Motoi Sakuraba", "Yuzo Koshiro"],
            "most_relevant_policies": ["MOS:Biography", "WP:BLP", "WP:GNG", "MOS"],
            "notes": "Biography + music domain. BLP applies if living. Discography formatting varies.",
        },
        {
            "editing_domain": "Template namespace (infobox/stats cleanup)",
            "articles_like": ["Template:Infobox NFL player", "Template:NFL player stats"],
            "most_relevant_policies": ["MOS:VG", "WP:NFL", "WP:BLP"],
            "notes": "Template changes affect all transclusions. Anti-pattern risk is high. Sandbox required.",
        },
        {
            "editing_domain": "Category and structural maintenance",
            "articles_like": ["Category:NFL players", "Category:Video game composers"],
            "most_relevant_policies": ["MOS"],
            "notes": "Low BLP risk. Category naming follows MOS conventions.",
        },
    ],
}


# ---------------------------------------------------------------------------
# Ingestor
# ---------------------------------------------------------------------------

class CorpusIngestor:
    """
    Fetches and structures the targeted Wikipedia rule/profile corpus.

    Usage:
        ci = CorpusIngestor()
        profile = ci.ingest_profile()
        rules   = ci.ingest_rules()
        ci.save_all(profile, rules)
    """

    def __init__(self, api: str = _ENWIKI_API):
        self.api = api
        self.headers = {"User-Agent": _USER_AGENT}

    def ingest_profile(self) -> OperatorProfile:
        """Fetch User:Dissident93 and structure into an editor profile."""
        target = PROFILE_TARGETS[0]
        wikitext = self._fetch_wikitext(target["title"])

        if wikitext is None:
            return OperatorProfile(
                username="Dissident93",
                page_title=target["title"],
                wikitext=None,
                editing_domains=[],
                key_wikiprojects=[],
                template_competence_signals=[],
                contribution_signals=[],
                primary_areas=[],
                raw_sections={},
                fetch_error="Page not found or access denied",
            )

        sections   = self._extract_sections(wikitext)
        domains    = self._extract_editing_domains(wikitext)
        projects   = self._extract_wikiprojects(wikitext)
        template_c = self._extract_template_competence(wikitext)
        contrib_s  = self._extract_contribution_signals(wikitext)
        primary    = self._infer_primary_areas(wikitext)

        return OperatorProfile(
            username="Dissident93",
            page_title=target["title"],
            wikitext=wikitext,
            editing_domains=domains,
            key_wikiprojects=projects,
            template_competence_signals=template_c,
            contribution_signals=contrib_s,
            primary_areas=primary,
            raw_sections=sections,
        )

    def _fetch_wikitext(self, title: str) -> str | None:
        """Fetch a single page's wikitext."""
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
        }
        url = f"{self.api}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if "missing" in page:
                    return None
                slots = page.get("revisions", [{}])[0].get("slots", {})
                return slots.get("main", {}).get("*") or slots.get("main", {}).get("content")
        except Exception:
            return None

    def _fetch_wikitext_batch(self, titles: list[str]) -> dict[str, str]:
        """Fetch multiple pages in one API call."""
        results: dict[str, str] = {}
        for i in range(0, len(titles), 50):
            batch = titles[i : i + 50]
            params = {
                "action": "query",
                "prop": "revisions",
                "titles": "|".join(batch),
                "rvprop": "content",
                "rvslots": "main",
                "format": "json",
            }
            url = f"{self.api}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    title = page.get("title")
                    if "missing" in page:
                        continue
                    slots = page.get("revisions", [{}])[0].get("slots", {})
                    content = slots.get("main", {}).get("*") or slots.get("main", {}).get("content")
                    if content:
                        results[title] = content
            except Exception:
                continue
            time.sleep(0.5)
        return results

    def discover_mos_pages(self) -> list[str]:
        """Discover all MOS subpages via API."""
        params = {
            "action": "query",
            "list": "allpages",
            "apnamespace": 4, # Wikipedia namespace
            "aplimit": 500,
            "apprefix": "Manual_of_Style/",
            "format": "json"
        }
        url = f"{self.api}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            return [p["title"] for p in data.get("query", {}).get("allpages", [])]
        except Exception:
            return []

    def ingest_rules(self, titles: list[str] | None = None) -> list[RuleCorpusEntry]:
        """Fetch and structure rules. If titles is None, uses discovery + defaults."""
        if titles is None:
            discovery = self.discover_mos_pages()
            # De-dupe and combine with hardcoded high-priority targets
            core_titles = [t["title"] for t in RULE_TARGETS]
            all_titles = list(set(core_titles + discovery))
        else:
            all_titles = titles

        batch_data = self._fetch_wikitext_batch(all_titles)
        entries: list[RuleCorpusEntry] = []

        # Map for quick lookup of RULE_TARGETS metadata
        meta_map = {t["title"]: t for t in RULE_TARGETS}

        for title in all_titles:
            wikitext = batch_data.get(title)
            meta = meta_map.get(title, {
                "policy_code": title.split("/")[-1] if "/" in title else "MOS",
                "label": title.replace("Wikipedia:", ""),
                "domain_tags": ["general"],
                "priority": 3
            })

            if not wikitext:
                entries.append(RuleCorpusEntry(
                    title=title,
                    policy_code=meta["policy_code"],
                    label=meta["label"],
                    domain_tags=meta["domain_tags"],
                    priority=meta["priority"],
                    wikitext=None,
                    sections=[],
                    key_statements=[],
                    dos=[],
                    donts=[],
                    scope="",
                    overlap_codes=[],
                    fetch_error="Fetch failed",
                ))
            else:
                sections   = list(self._extract_sections(wikitext).keys())
                statements = self._extract_key_statements(wikitext, meta["policy_code"])
                dos, donts = self._extract_dos_donts(wikitext)
                scope      = self._infer_scope(wikitext, meta["policy_code"])
                overlaps   = self._infer_overlaps(meta["policy_code"])
                entries.append(RuleCorpusEntry(
                    title=title,
                    policy_code=meta["policy_code"],
                    label=meta["label"],
                    domain_tags=meta["domain_tags"],
                    priority=meta["priority"],
                    wikitext=wikitext,
                    sections=sections,
                    key_statements=statements,
                    dos=dos,
                    donts=donts,
                    scope=scope,
                    overlap_codes=overlaps,
                ))
        return entries

    def save_all(
        self,
        profile: OperatorProfile,
        rules: list[RuleCorpusEntry],
        out_dir: Path | None = None,
    ) -> dict[str, Path]:
        target = out_dir or _ARTIFACTS
        target.mkdir(parents=True, exist_ok=True)
        written: dict[str, Path] = {}

        # Operator profile
        p = target / "operator_profile_report.json"
        p.write_text(json.dumps(profile.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        written["operator_profile"] = p

        # Rule corpus
        p = target / "wikipedia_rule_corpus_report.json"
        p.write_text(
            json.dumps({"rules": [r.to_dict() for r in rules]}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        written["rule_corpus"] = p

        # Applicability map
        p = target / "rule_applicability_map.json"
        p.write_text(json.dumps(RULE_APPLICABILITY_MAP, indent=2, ensure_ascii=False), encoding="utf-8")
        written["applicability_map"] = p

        # Operator-rule crosswalk
        p = target / "operator_rule_crosswalk.json"
        p.write_text(json.dumps(OPERATOR_RULE_CROSSWALK, indent=2, ensure_ascii=False), encoding="utf-8")
        written["crosswalk"] = p

        return written

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_sections(wikitext: str) -> dict[str, str]:
        """Split wikitext into {heading: body} dict."""
        sections: dict[str, str] = {}
        current_heading = "__preamble__"
        current_lines: list[str] = []
        for line in wikitext.splitlines():
            m = re.match(r"^(={2,5})\s*(.+?)\s*\1\s*$", line)
            if m:
                sections[current_heading] = "\n".join(current_lines).strip()
                current_heading = m.group(2)
                current_lines = []
            else:
                current_lines.append(line)
        sections[current_heading] = "\n".join(current_lines).strip()
        return sections

    @staticmethod
    def _extract_editing_domains(wikitext: str) -> list[str]:
        domains: list[str] = []
        low = wikitext.lower()
        if "nfl" in low or "football" in low or "commander" in low:
            domains.append("NFL / American football")
        if "video game" in low or "vg" in low or "dota" in low or "gaming" in low:
            domains.append("Video games")
        if "composer" in low or "music" in low or "soundtrack" in low:
            domains.append("Video game music / composers")
        if "biography" in low or "blp" in low or "born" in low:
            domains.append("Biographies")
        if "template" in low or "infobox" in low or "mediawiki" in low:
            domains.append("Template / MediaWiki editing")
        return domains

    @staticmethod
    def _extract_wikiprojects(wikitext: str) -> list[str]:
        return re.findall(r"WikiProject\s+([\w\s]+?)(?:\||\})", wikitext)[:15]

    @staticmethod
    def _extract_template_competence(wikitext: str) -> list[str]:
        signals: list[str] = []
        low = wikitext.lower()
        for term in ["template", "infobox", "lua", "module", "parser function",
                     "#if", "#switch", "transclusion", "navbox"]:
            if term in low:
                signals.append(term)
        return signals

    @staticmethod
    def _extract_contribution_signals(wikitext: str) -> list[str]:
        signals: list[str] = []
        # Look for edit count / year mentions
        counts = re.findall(r"[\d,]+\s*edits?", wikitext, re.IGNORECASE)
        signals.extend(counts[:3])
        years = re.findall(r"since\s+20\d\d|joined\s+20\d\d|editing\s+since", wikitext, re.IGNORECASE)
        signals.extend(years[:3])
        return signals

    @staticmethod
    def _infer_primary_areas(wikitext: str) -> list[str]:
        areas: list[str] = []
        low = wikitext.lower()
        if "commander" in low or "washington" in low:
            areas.append("Washington Commanders")
        if "jayden" in low or "daniels" in low:
            areas.append("Jayden Daniels")
        if "dota" in low:
            areas.append("Dota 2")
        if "shimomura" in low or "sakuraba" in low or "koshiro" in low:
            areas.append("VGM composers")
        if "fromsoft" in low or "souls" in low or "elden" in low:
            areas.append("FromSoftware")
        return areas

    @staticmethod
    def _extract_key_statements(wikitext: str, policy_code: str) -> list[str]:
        """
        Extract rule-like sentences from a policy page.
        """
        sentences = re.split(r"(?<=[.!?])\s+", wikitext)
        keywords = ["should", "must", "do not", "avoid", "never", "always",
                    "required", "preferred", "recommend"]
        results: list[str] = []
        for s in sentences:
            s = s.strip()
            if len(s) < 30 or len(s) > 300:
                continue
            # Strip wikitext markup for readability
            s_clean = re.sub(r"\[\[(?:[^|]*\|)?([^\]]+)\]\]", r"\1", s)
            s_clean = re.sub(r"'{2,3}", "", s_clean)
            s_clean = re.sub(r"\{\{[^}]+\}\}", "", s_clean).strip()
            if any(kw in s_clean.lower() for kw in keywords):
                results.append(s_clean)
            if len(results) >= 40:
                break
        return results

    @staticmethod
    def _extract_dos_donts(wikitext: str) -> tuple[list[str], list[str]]:
        """
        Explicitly extract DOs (should/must) and DON'Ts (avoid/never/do not).
        """
        sentences = re.split(r"(?<=[.!?])\s+", wikitext)
        dos: list[str] = []
        donts: list[str] = []
        
        do_keywords = ["should", "must", "always", "required", "preferred", "recommend"]
        dont_keywords = ["avoid", "never", "do not", "should not", "must not", "prohibited"]
        
        for s in sentences:
            s_clean = re.sub(r"\[\[(?:[^|]*\|)?([^\]]+)\]\]", r"\1", s)
            s_clean = re.sub(r"'{2,3}", "", s_clean)
            s_clean = re.sub(r"\{\{[^}]+\}\}", "", s_clean).strip()
            
            low = s_clean.lower()
            if any(kw in low for kw in dont_keywords):
                if s_clean not in donts:
                    donts.append(s_clean)
            elif any(kw in low for kw in do_keywords):
                if s_clean not in dos:
                    dos.append(s_clean)
                    
            if len(dos) >= 20 and len(donts) >= 20:
                break
                
        return dos, donts

    @staticmethod
    def _infer_scope(wikitext: str, policy_code: str) -> str:
        scope_map = {
            "MOS:VG": "Formatting and content guidelines specific to video game articles.",
            "WP:NFL": "Notability criteria and style guidance for NFL-related articles.",
            "MOS:Biography": "Formatting conventions for biographical articles, with BLP considerations.",
            "MOS": "General formatting and style rules applicable to all Wikipedia articles.",
            "WP:GNG": "General notability guideline: significant coverage in reliable independent sources.",
            "MOS:WORDS": "Guidelines on 'Peacock terms' (puffery) and 'Weasel words' to avoid.",
            "MOS:LEAD": "Structural and content requirements for article lead sections.",
            "MOS:LAYOUT": "Standardized section ordering and layout structure.",
            "MOS:TABLES": "Accessibility and formatting rules for wikia tables.",
            "MOS:INFOBOX": "Standardized approach to infobox usage and parameter rendering.",
        }
        return scope_map.get(policy_code, "Wikipedia editorial guideline.")

    @staticmethod
    def _infer_overlaps(policy_code: str) -> list[str]:
        overlap_map = {
            "MOS:VG":        ["MOS", "WP:GNG"],
            "WP:NFL":        ["WP:BLP", "WP:V", "MOS:Biography"],
            "MOS:Biography": ["WP:BLP", "MOS"],
            "MOS":           ["MOS:VG", "MOS:Biography"],
            "WP:GNG":        ["WP:NFL", "WP:V"],
        }
        return overlap_map.get(policy_code, [])
