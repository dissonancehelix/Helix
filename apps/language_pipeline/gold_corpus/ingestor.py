"""
Gold corpus ingestor — Phase 1.2.

Fetches live current revisions for the operator's targeted article corpus
and builds structured dossiers, archetype classifications, authorial pattern
evidence, rule-to-article crosswalks, and template-family prep.

Target corpus:
  A. Operator profile
     - User:Dissident93

  B. Rule / style corpus
     - Wikipedia:Manual of Style/Video games
     - Wikipedia:WikiProject National Football League
     - Wikipedia:Manual of Style/Biography
     - Wikipedia:Manual of Style
     - Wikipedia:Notability

  C. Gold article corpus (authored / major-contribution specimens)
     - New Commanders Stadium
     - Chase Young
     - Dota 2
     - Jayden Daniels
     - Josh Harris (businessman)
     - Adam Peters
     - Brandon Sosna

All fetches use action=query&prop=revisions (official MediaWiki API).
No HTML scraping. No live edits.
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
_ARTIFACTS  = (
    Path(__file__).resolve().parents[1]
    / "data"
)

# ---------------------------------------------------------------------------
# Corpus target definitions
# ---------------------------------------------------------------------------

PROFILE_CORPUS = [
    {"title": "User:Dissident93", "layer": "profile"},
]

RULE_CORPUS = [
    {"title": "Wikipedia:Manual of Style/Video games",               "policy_code": "MOS:VG",        "domain_tags": ["vg"]},
    {"title": "Wikipedia:WikiProject National Football League",       "policy_code": "WP:NFL",        "domain_tags": ["nfl"]},
    {"title": "Wikipedia:Manual of Style/Biography",                  "policy_code": "MOS:Biography", "domain_tags": ["blp", "nfl", "vg"]},
    {"title": "Wikipedia:Manual of Style",                            "policy_code": "MOS",           "domain_tags": ["general"]},
    {"title": "Wikipedia:Notability",                                  "policy_code": "WP:GNG",        "domain_tags": ["general", "nfl", "vg"]},
]

GOLD_ARTICLE_CORPUS = [
    {
        "title":        "New Commanders Stadium",
        "archetype_hints": ["infrastructure_article", "project_article"],
        "blp": False,
        "domain_tags": ["nfl"],
        "policy_priority": ["WP:NFL", "MOS"],
    },
    {
        "title":        "Chase Young",
        "archetype_hints": ["athlete_biography_nfl"],
        "blp": True,
        "domain_tags": ["nfl", "blp"],
        "policy_priority": ["WP:NFL", "WP:BLP", "MOS:Biography", "MOS"],
    },
    {
        "title":        "Dota 2",
        "archetype_hints": ["video_game_article"],
        "blp": False,
        "domain_tags": ["vg"],
        "policy_priority": ["MOS:VG", "WP:GNG", "MOS"],
    },
    {
        "title":        "Jayden Daniels",
        "archetype_hints": ["athlete_biography_nfl"],
        "blp": True,
        "domain_tags": ["nfl", "blp"],
        "policy_priority": ["WP:NFL", "WP:BLP", "MOS:Biography", "MOS"],
    },
    {
        "title":        "Josh Harris (businessman)",
        "archetype_hints": ["executive_biography"],
        "blp": True,
        "domain_tags": ["blp"],
        "policy_priority": ["MOS:Biography", "WP:BLP", "WP:GNG", "MOS"],
    },
    {
        "title":        "Adam Peters",
        "archetype_hints": ["executive_biography", "nfl_front_office"],
        "blp": True,
        "domain_tags": ["nfl", "blp"],
        "policy_priority": ["WP:NFL", "WP:BLP", "MOS:Biography", "MOS"],
    },
    {
        "title":        "Brandon Sosna",
        "archetype_hints": ["executive_biography", "nfl_front_office"],
        "blp": True,
        "domain_tags": ["nfl", "blp"],
        "policy_priority": ["WP:NFL", "WP:BLP", "MOS:Biography", "MOS"],
    },
]

ALL_TITLES = (
    [t["title"] for t in PROFILE_CORPUS]
    + [t["title"] for t in RULE_CORPUS]
    + [t["title"] for t in GOLD_ARTICLE_CORPUS]
)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LivePageRecord:
    """Raw ingested page — provenance-first."""
    title: str
    layer: str                   # "profile" | "rule" | "gold_article"
    pageid: int | None
    revid: int | None
    timestamp: str | None        # ISO 8601
    wikitext: str | None
    wikitext_length: int
    redirect_target: str | None  # if page is a redirect
    fetch_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "layer": self.layer,
            "pageid": self.pageid,
            "revid": self.revid,
            "timestamp": self.timestamp,
            "wikitext_length": self.wikitext_length,
            "redirect_target": self.redirect_target,
            "fetch_error": self.fetch_error,
        }


@dataclass
class ArticleDossier:
    """
    Structured dossier for a gold article specimen.
    Treats the article as a structural specimen, not just content.
    """
    title: str
    pageid: int | None
    revid: int | None
    timestamp: str | None
    archetype_tags: list[str]        # e.g. ["athlete_biography_nfl", "blp"]
    blp_sensitive: bool

    # Structure
    lead_paragraph_count: int
    lead_first_sentence: str         # opening sentence (structural signal)
    sections: list[str]              # ordered section headings
    section_count: int
    subsection_count: int

    # Template inventory
    infobox_names: list[str]         # e.g. ["Infobox NFL player"]
    navbox_names: list[str]
    other_templates: list[str]       # non-infobox, non-navbox templates (first 15)

    # Content structure signals
    has_stats_table: bool
    has_awards_section: bool
    has_chronology_section: bool
    has_references_section: bool
    table_count: int
    ref_count: int                   # estimated inline reference count
    image_count: int

    # Sequence / compression signals
    chronology_type: str             # "forward" | "reverse" | "topical" | "mixed"
    lead_compression: str            # "dense" | "moderate" | "sparse"
    source_density: str              # "high" | "medium" | "low"

    # Template families identified
    template_families: list[str]     # e.g. ["nfl", "vg", "person"]

    # Policy applicability
    policy_priority: list[str]

    # Authorial pattern notes (derived)
    authorial_notes: list[str]

    fetch_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "pageid": self.pageid,
            "revid": self.revid,
            "timestamp": self.timestamp,
            "archetype_tags": self.archetype_tags,
            "blp_sensitive": self.blp_sensitive,
            "lead_paragraph_count": self.lead_paragraph_count,
            "lead_first_sentence": self.lead_first_sentence,
            "sections": self.sections,
            "section_count": self.section_count,
            "subsection_count": self.subsection_count,
            "infobox_names": self.infobox_names,
            "navbox_names": self.navbox_names,
            "other_templates": self.other_templates,
            "has_stats_table": self.has_stats_table,
            "has_awards_section": self.has_awards_section,
            "has_chronology_section": self.has_chronology_section,
            "has_references_section": self.has_references_section,
            "table_count": self.table_count,
            "ref_count": self.ref_count,
            "image_count": self.image_count,
            "chronology_type": self.chronology_type,
            "lead_compression": self.lead_compression,
            "source_density": self.source_density,
            "template_families": self.template_families,
            "policy_priority": self.policy_priority,
            "authorial_notes": self.authorial_notes,
            "fetch_error": self.fetch_error,
        }


@dataclass
class GoldCorpusReport:
    """Full report from a Phase 1.2 ingest run."""
    live_pages: list[LivePageRecord]
    dossiers: list[ArticleDossier]
    archetype_map: dict[str, list[str]]       # title → archetype_tags
    authorial_patterns: list[dict]            # extracted cross-article patterns
    rule_to_article_crosswalk: dict[str, list[str]]  # policy_code → [titles]
    template_family_prep: dict[str, Any]
    fetch_summary: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "fetch_summary": self.fetch_summary,
            "live_pages": [p.to_dict() for p in self.live_pages],
            "dossiers": [d.to_dict() for d in self.dossiers],
            "archetype_map": self.archetype_map,
            "authorial_patterns": self.authorial_patterns,
            "rule_to_article_crosswalk": self.rule_to_article_crosswalk,
            "template_family_prep": self.template_family_prep,
        }


# ---------------------------------------------------------------------------
# Ingestor
# ---------------------------------------------------------------------------

class GoldCorpusIngestor:
    """
    Fetches and structures the Phase 1.2 gold corpus.

    Usage:
        ci = GoldCorpusIngestor()
        report = ci.run()
        ci.save(report)
    """

    def __init__(self, api: str = _ENWIKI_API, delay: float = 0.8):
        self.api = api
        self.delay = delay
        self.headers = {"User-Agent": _USER_AGENT}

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------

    def run(self) -> GoldCorpusReport:
        """Fetch all targets and build the full report."""
        live_pages: list[LivePageRecord] = []

        # A. Profile
        for target in PROFILE_CORPUS:
            live_pages.append(self._fetch_page(target["title"], "profile"))
            time.sleep(self.delay)

        # B. Rule corpus
        for target in RULE_CORPUS:
            live_pages.append(self._fetch_page(target["title"], "rule"))
            time.sleep(self.delay)

        # C. Gold articles
        for target in GOLD_ARTICLE_CORPUS:
            live_pages.append(self._fetch_page(target["title"], "gold_article"))
            time.sleep(self.delay)

        # Build page lookup
        page_map: dict[str, LivePageRecord] = {p.title: p for p in live_pages}

        # Build dossiers for gold articles
        dossiers: list[ArticleDossier] = []
        for target in GOLD_ARTICLE_CORPUS:
            rec = page_map.get(target["title"])
            if rec:
                dossiers.append(self._build_dossier(rec, target))

        # Archetype map
        archetype_map = {d.title: d.archetype_tags for d in dossiers}

        # Authorial patterns
        authorial_patterns = self._extract_authorial_patterns(dossiers)

        # Rule-to-article crosswalk
        crosswalk = self._build_crosswalk(dossiers)

        # Template-family prep
        template_prep = self._build_template_prep(dossiers)

        # Fetch summary
        ok    = sum(1 for p in live_pages if not p.fetch_error)
        err   = sum(1 for p in live_pages if p.fetch_error)
        total_chars = sum(p.wikitext_length for p in live_pages)
        fetch_summary = {
            "total_pages": len(live_pages),
            "ok": ok,
            "errors": err,
            "total_wikitext_chars": total_chars,
            "gold_articles": len(dossiers),
        }

        return GoldCorpusReport(
            live_pages=live_pages,
            dossiers=dossiers,
            archetype_map=archetype_map,
            authorial_patterns=authorial_patterns,
            rule_to_article_crosswalk=crosswalk,
            template_family_prep=template_prep,
            fetch_summary=fetch_summary,
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, report: GoldCorpusReport, out_dir: Path | None = None) -> dict[str, Path]:
        target = out_dir or _ARTIFACTS
        target.mkdir(parents=True, exist_ok=True)
        written: dict[str, Path] = {}

        def _w(name: str, data: Any) -> Path:
            p = target / name
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            written[name] = p
            return p

        _w("live_page_ingest_report.json",        [p.to_dict() for p in report.live_pages])
        _w("article_dossier_report.json",         [d.to_dict() for d in report.dossiers])
        _w("article_archetype_map.json",          report.archetype_map)
        _w("personal_authorial_pattern_report.json", report.authorial_patterns)
        _w("rule_to_article_crosswalk.json",      report.rule_to_article_crosswalk)
        _w("template_family_prep_report.json",    report.template_family_prep)

        return written

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def _fetch_page(self, title: str, layer: str) -> LivePageRecord:
        params = {
            "action": "query",
            "prop": "revisions|info",
            "titles": title,
            "rvprop": "content|ids|timestamp",
            "rvslots": "main",
            "redirects": "1",
            "formatversion": "2",
            "format": "json",
        }
        url = f"{self.api}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return LivePageRecord(
                title=title, layer=layer,
                pageid=None, revid=None, timestamp=None,
                wikitext=None, wikitext_length=0,
                redirect_target=None,
                fetch_error=str(e),
            )

        # Handle redirects
        redirects = data.get("query", {}).get("redirects", [])
        redirect_target = redirects[0].get("to") if redirects else None

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return LivePageRecord(
                title=title, layer=layer,
                pageid=None, revid=None, timestamp=None,
                wikitext=None, wikitext_length=0,
                redirect_target=redirect_target,
                fetch_error="No pages in response",
            )

        page = pages[0]
        if page.get("missing"):
            return LivePageRecord(
                title=title, layer=layer,
                pageid=page.get("pageid"), revid=None, timestamp=None,
                wikitext=None, wikitext_length=0,
                redirect_target=redirect_target,
                fetch_error="Page missing",
            )

        revisions = page.get("revisions", [])
        if not revisions:
            return LivePageRecord(
                title=title, layer=layer,
                pageid=page.get("pageid"), revid=None, timestamp=None,
                wikitext=None, wikitext_length=0,
                redirect_target=redirect_target,
                fetch_error="No revisions returned",
            )

        rev = revisions[0]
        slots = rev.get("slots", {})
        wikitext = slots.get("main", {}).get("content") or rev.get("content")

        return LivePageRecord(
            title=title,
            layer=layer,
            pageid=page.get("pageid"),
            revid=rev.get("revid"),
            timestamp=rev.get("timestamp"),
            wikitext=wikitext,
            wikitext_length=len(wikitext) if wikitext else 0,
            redirect_target=redirect_target,
            fetch_error=None,
        )

    # ------------------------------------------------------------------
    # Dossier building
    # ------------------------------------------------------------------

    def _build_dossier(self, rec: LivePageRecord, target: dict) -> ArticleDossier:
        wt = rec.wikitext or ""

        if rec.fetch_error:
            return ArticleDossier(
                title=rec.title, pageid=rec.pageid, revid=rec.revid,
                timestamp=rec.timestamp,
                archetype_tags=target["archetype_hints"],
                blp_sensitive=target["blp"],
                lead_paragraph_count=0, lead_first_sentence="",
                sections=[], section_count=0, subsection_count=0,
                infobox_names=[], navbox_names=[], other_templates=[],
                has_stats_table=False, has_awards_section=False,
                has_chronology_section=False, has_references_section=False,
                table_count=0, ref_count=0, image_count=0,
                chronology_type="unknown", lead_compression="unknown",
                source_density="unknown", template_families=[],
                policy_priority=target["policy_priority"],
                authorial_notes=[],
                fetch_error=rec.fetch_error,
            )

        sections_h2, sections_h3 = self._extract_section_headings(wt)
        all_sections = sections_h2 + sections_h3

        lead_text    = self._extract_lead(wt)
        lead_paras   = [p for p in lead_text.split("\n\n") if p.strip() and not p.startswith("{{") and not p.startswith("[[")]
        lead_first   = self._extract_first_sentence(lead_text)

        infoboxes    = self._find_templates_by_type(wt, "infobox")
        navboxes     = self._find_templates_by_type(wt, "navbox")
        others       = self._find_other_templates(wt, infoboxes + navboxes)

        table_count  = wt.count("{|")
        ref_count    = len(re.findall(r"<ref[^/]", wt, re.IGNORECASE))
        image_count  = len(re.findall(r"\[\[(?:File|Image):", wt, re.IGNORECASE))

        has_stats    = self._has_stats_table(wt, sections_h2)
        has_awards   = any(re.search(r"\baward|accolade|honor|honor", s, re.I) for s in all_sections)
        has_chron    = any(re.search(r"\bcareer|history|season|background|early life", s, re.I) for s in all_sections)
        has_refs     = any(re.search(r"\breference|source|note", s, re.I) for s in all_sections)

        chron_type   = self._classify_chronology(wt, sections_h2)
        compression  = self._classify_lead_compression(lead_paras, lead_first)
        src_density  = self._classify_source_density(ref_count, len(wt))
        tmpl_fams    = self._infer_template_families(infoboxes, navboxes, target)
        archetype    = self._refine_archetypes(target["archetype_hints"], wt, sections_h2, infoboxes)
        notes        = self._generate_authorial_notes(archetype, compression, chron_type, src_density,
                                                       has_stats, has_awards, table_count, target)

        return ArticleDossier(
            title=rec.title,
            pageid=rec.pageid,
            revid=rec.revid,
            timestamp=rec.timestamp,
            archetype_tags=archetype,
            blp_sensitive=target["blp"],
            lead_paragraph_count=len(lead_paras),
            lead_first_sentence=lead_first,
            sections=sections_h2,
            section_count=len(sections_h2),
            subsection_count=len(sections_h3),
            infobox_names=infoboxes,
            navbox_names=navboxes,
            other_templates=others[:15],
            has_stats_table=has_stats,
            has_awards_section=has_awards,
            has_chronology_section=has_chron,
            has_references_section=has_refs,
            table_count=table_count,
            ref_count=ref_count,
            image_count=image_count,
            chronology_type=chron_type,
            lead_compression=compression,
            source_density=src_density,
            template_families=tmpl_fams,
            policy_priority=target["policy_priority"],
            authorial_notes=notes,
        )

    # ------------------------------------------------------------------
    # Authorial pattern extraction
    # ------------------------------------------------------------------

    def _extract_authorial_patterns(self, dossiers: list[ArticleDossier]) -> list[dict]:
        """Cross-article pattern extraction."""
        patterns: list[dict] = []
        if not dossiers:
            return patterns

        live = [d for d in dossiers if not d.fetch_error]

        # Pattern 1: lead compression style
        compression_counts: dict[str, int] = {}
        for d in live:
            compression_counts[d.lead_compression] = compression_counts.get(d.lead_compression, 0) + 1
        dominant_compression = max(compression_counts, key=compression_counts.get) if compression_counts else "unknown"
        patterns.append({
            "id": "lead_compression_style",
            "name": "Lead compression style",
            "description": f"Dominant style across gold corpus: '{dominant_compression}'. "
                           f"Distribution: {compression_counts}.",
            "evidence_articles": [d.title for d in live if d.lead_compression == dominant_compression],
            "operator_tendency": dominant_compression,
        })

        # Pattern 2: chronology approach
        chron_counts: dict[str, int] = {}
        for d in live:
            chron_counts[d.chronology_type] = chron_counts.get(d.chronology_type, 0) + 1
        dominant_chron = max(chron_counts, key=chron_counts.get) if chron_counts else "unknown"
        patterns.append({
            "id": "chronology_sequencing",
            "name": "Chronology sequencing habit",
            "description": f"Dominant chronology type: '{dominant_chron}'. Distribution: {chron_counts}.",
            "evidence_articles": [d.title for d in live if d.chronology_type == dominant_chron],
            "operator_tendency": dominant_chron,
        })

        # Pattern 3: infobox usage
        articles_with_infobox = [d for d in live if d.infobox_names]
        patterns.append({
            "id": "infobox_integration",
            "name": "Infobox integration",
            "description": f"{len(articles_with_infobox)}/{len(live)} gold articles have infoboxes. "
                           f"All NFL biography and VG articles expected to have infoboxes.",
            "evidence_articles": [d.title for d in articles_with_infobox],
            "infobox_types_seen": list({ib for d in articles_with_infobox for ib in d.infobox_names}),
        })

        # Pattern 4: statistics table usage
        stats_articles = [d for d in live if d.has_stats_table]
        patterns.append({
            "id": "statistics_table_usage",
            "name": "Statistics table usage",
            "description": f"{len(stats_articles)}/{len(live)} gold articles contain statistics tables. "
                           f"Expected for NFL player biographies.",
            "evidence_articles": [d.title for d in stats_articles],
            "archetype_association": "athlete_biography_nfl",
        })

        # Pattern 5: source density
        src_counts: dict[str, int] = {}
        for d in live:
            src_counts[d.source_density] = src_counts.get(d.source_density, 0) + 1
        patterns.append({
            "id": "source_density_profile",
            "name": "Source density profile",
            "description": f"Distribution: {src_counts}. High-density articles suggest thoroughness.",
            "evidence_articles": [f"{d.title} ({d.source_density})" for d in live],
            "operator_tendency": max(src_counts, key=src_counts.get) if src_counts else "unknown",
        })

        # Pattern 6: section count norms per archetype
        for archetype in ["athlete_biography_nfl", "executive_biography", "video_game_article", "infrastructure_article"]:
            matching = [d for d in live if archetype in d.archetype_tags]
            if matching:
                avg_sections = sum(d.section_count for d in matching) / len(matching)
                patterns.append({
                    "id": f"section_depth_{archetype}",
                    "name": f"Section depth norm — {archetype}",
                    "description": f"Average H2 section count for {archetype}: {avg_sections:.1f}. "
                                   f"Typical sections: {matching[0].sections[:5] if matching else []}",
                    "evidence_articles": [d.title for d in matching],
                    "avg_section_count": round(avg_sections, 1),
                })

        # Pattern 7: BLP handling
        blp_articles = [d for d in live if d.blp_sensitive]
        if blp_articles:
            avg_refs = sum(d.ref_count for d in blp_articles) / len(blp_articles)
            patterns.append({
                "id": "blp_citation_density",
                "name": "BLP citation density",
                "description": f"Average ref count for BLP articles: {avg_refs:.0f}. "
                               f"High citation density consistent with WP:BLP compliance.",
                "evidence_articles": [d.title for d in blp_articles],
                "avg_ref_count": round(avg_refs, 1),
            })

        return patterns

    # ------------------------------------------------------------------
    # Crosswalk
    # ------------------------------------------------------------------

    def _build_crosswalk(self, dossiers: list[ArticleDossier]) -> dict[str, list[str]]:
        """Rule → list of gold articles where it is most applicable."""
        crosswalk: dict[str, list[str]] = {}
        for d in dossiers:
            for policy in d.policy_priority:
                if policy not in crosswalk:
                    crosswalk[policy] = []
                crosswalk[policy].append(d.title)
        return crosswalk

    # ------------------------------------------------------------------
    # Template-family prep
    # ------------------------------------------------------------------

    def _build_template_prep(self, dossiers: list[ArticleDossier]) -> dict[str, Any]:
        """Identify template families implied by the gold corpus."""
        infobox_inventory: dict[str, list[str]] = {}   # infobox → [articles]
        navbox_inventory:  dict[str, list[str]] = {}
        template_inventory: dict[str, list[str]] = {}

        for d in dossiers:
            for ib in d.infobox_names:
                infobox_inventory.setdefault(ib, []).append(d.title)
            for nb in d.navbox_names:
                navbox_inventory.setdefault(nb, []).append(d.title)
            for t in d.other_templates:
                template_inventory.setdefault(t, []).append(d.title)

        # Priority ingest queue — templates seen in 2+ gold articles
        priority_queue = sorted(
            {t: len(arts) for t, arts in {**infobox_inventory, **navbox_inventory}.items()}.items(),
            key=lambda x: -x[1]
        )

        return {
            "infobox_inventory":  infobox_inventory,
            "navbox_inventory":   navbox_inventory,
            "common_templates":   {t: arts for t, arts in template_inventory.items() if len(arts) >= 2},
            "priority_ingest_queue": [
                {"template": t, "seen_in": c, "articles": {**infobox_inventory, **navbox_inventory}[t]}
                for t, c in priority_queue
            ],
            "template_families_implied": list({f for d in dossiers for f in d.template_families}),
            "fragile_area_notes": [
                "NFL player infoboxes: |teams= format, |number= multi-value, birth_date template",
                "VG infoboxes: |image= no prefix, |released= use {{Video game release}}, |platforms= use {{unbulleted list}}",
                "Biography templates: {{birth date and age}}, {{death date and age}} — must be nested correctly",
            ],
        }

    # ------------------------------------------------------------------
    # Wikitext analysis helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_section_headings(wt: str) -> tuple[list[str], list[str]]:
        h2 = re.findall(r"^==\s*(.+?)\s*==\s*$", wt, re.MULTILINE)
        h3 = re.findall(r"^===\s*(.+?)\s*===\s*$", wt, re.MULTILINE)
        return h2, h3

    @staticmethod
    def _extract_lead(wt: str) -> str:
        """Everything before the first == heading."""
        m = re.search(r"^==", wt, re.MULTILINE)
        return wt[:m.start()].strip() if m else wt.strip()

    @staticmethod
    def _extract_first_sentence(text: str) -> str:
        """First sentence from lead (strips wikitext markup)."""
        clean = re.sub(r"\{\{[^{}]*\}\}", "", text)  # remove templates
        clean = re.sub(r"\[\[(?:[^|]*\|)?([^\]]+)\]\]", r"\1", clean)  # unwrap links
        clean = re.sub(r"'{2,3}", "", clean)  # remove bold/italic
        clean = clean.strip()
        m = re.search(r"(.+?[.!?])\s", clean)
        return m.group(1)[:200] if m else clean[:200]

    @staticmethod
    def _find_templates_by_type(wt: str, template_type: str) -> list[str]:
        """Find templates whose names start with the given type keyword."""
        pattern = re.compile(
            r"\{\{\s*(" + re.escape(template_type) + r"[^|{}\n]*?)(?:\||\}\})",
            re.IGNORECASE,
        )
        seen: dict[str, None] = {}
        for m in pattern.finditer(wt):
            name = m.group(1).strip()
            if name and name not in seen:
                seen[name] = None
        return list(seen.keys())

    @staticmethod
    def _find_other_templates(wt: str, exclude: list[str]) -> list[str]:
        """All template names not in exclude list."""
        exclude_set = {e.lower() for e in exclude}
        raw = re.findall(r"\{\{\s*([A-Za-z][^|{}\n]*?)(?:\||\}\})", wt)
        seen: dict[str, None] = {}
        for t in raw:
            t = t.strip()
            if t.lower() not in exclude_set and not t.startswith("#") and t not in seen:
                seen[t] = None
        return list(seen.keys())

    @staticmethod
    def _has_stats_table(wt: str, sections: list[str]) -> bool:
        section_signal = any(re.search(r"stat|career|record", s, re.I) for s in sections)
        table_signal = bool(re.search(r"\{\|[^\n]*wikitable", wt, re.IGNORECASE))
        return section_signal and table_signal

    @staticmethod
    def _classify_chronology(wt: str, sections: list[str]) -> str:
        """Infer the chronological organization of the article."""
        seasons = re.findall(r"\b(20\d\d)[\s-]+(20\d\d|\d\d)\b", wt[:5000])
        if len(seasons) >= 3:
            years = [int(s[0]) for s in seasons]
            if years == sorted(years):
                return "forward"
            if years == sorted(years, reverse=True):
                return "reverse"
            return "mixed"
        topical_signals = ["gameplay", "development", "reception", "legacy", "plot", "characters"]
        if any(s.lower() in topical_signals for s in sections):
            return "topical"
        return "mixed"

    @staticmethod
    def _classify_lead_compression(lead_paras: list[str], first_sentence: str) -> str:
        """Classify how dense/compressed the lead is."""
        if not lead_paras:
            return "sparse"
        word_count = sum(len(p.split()) for p in lead_paras)
        if word_count > 150 or len(lead_paras) >= 4:
            return "dense"
        if word_count > 60 or len(lead_paras) >= 2:
            return "moderate"
        return "sparse"

    @staticmethod
    def _classify_source_density(ref_count: int, wt_len: int) -> str:
        if wt_len == 0:
            return "unknown"
        ratio = ref_count / max(wt_len / 1000, 1)  # refs per 1000 chars
        if ratio > 3:
            return "high"
        if ratio > 1:
            return "medium"
        return "low"

    @staticmethod
    def _infer_template_families(
        infoboxes: list[str],
        navboxes: list[str],
        target: dict,
    ) -> list[str]:
        families: set[str] = set()
        combined = " ".join(infoboxes + navboxes).lower()
        if "nfl" in combined or "football" in combined:
            families.add("nfl")
        if "video game" in combined or "vg" in combined or target.get("domain_tags") and "vg" in target["domain_tags"]:
            families.add("vg")
        if "person" in combined or "biography" in combined or target.get("blp"):
            families.add("person")
        if "stadium" in combined or "arena" in combined or "venue" in combined:
            families.add("venue")
        if not families:
            families.add("general")
        return sorted(families)

    @staticmethod
    def _refine_archetypes(hints: list[str], wt: str, sections: list[str], infoboxes: list[str]) -> list[str]:
        """Refine initial archetype hints using wikitext evidence."""
        tags = list(hints)
        combined = (wt[:3000] + " ".join(sections) + " ".join(infoboxes)).lower()
        if "video game" in combined or "gameplay" in combined:
            if "video_game_article" not in tags:
                tags.append("video_game_article")
        if "nfl" in combined or "quarterback" in combined or "wide receiver" in combined:
            if "athlete_biography_nfl" not in tags:
                tags.append("athlete_biography_nfl")
        if re.search(r"\bstadium\b|\barena\b|\bvenue\b", combined):
            if "infrastructure_article" not in tags:
                tags.append("infrastructure_article")
        # Hybrid detection
        if len(tags) > 1:
            if "athlete_biography_nfl" in tags and "executive_biography" in tags:
                tags.append("hybrid_nfl_person")
        return list(dict.fromkeys(tags))  # preserve order, deduplicate

    @staticmethod
    def _generate_authorial_notes(
        archetypes: list[str],
        compression: str,
        chron_type: str,
        src_density: str,
        has_stats: bool,
        has_awards: bool,
        table_count: int,
        target: dict,
    ) -> list[str]:
        notes: list[str] = []
        if compression == "dense":
            notes.append("Dense lead — operator favors front-loaded identity establishment.")
        elif compression == "sparse":
            notes.append("Sparse lead — may reflect stub state or minimal coverage article.")

        if chron_type == "forward":
            notes.append("Forward chronology — career narrative sequences earliest to most recent.")
        elif chron_type == "topical":
            notes.append("Topical sequencing — structure organized by subject domain, not time.")

        if has_stats and "athlete_biography_nfl" in archetypes:
            notes.append("Statistics tables present — consistent with NFL biography MOS expectations.")

        if has_awards:
            notes.append("Awards/accolades section present — commonly uses {{div col}} or wikitable.")

        if src_density == "high":
            notes.append("High source density — operator applies tight inline sourcing.")
        elif src_density == "low" and target.get("blp"):
            notes.append("Low source density on a BLP article — potential citation gap.")

        if table_count > 3:
            notes.append(f"Multiple tables ({table_count}) — article relies on tabular data presentation.")

        return notes
