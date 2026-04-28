"""
Template family ingestor — Phase 1.3.

Fetches template source, TemplateData, and /doc for each template in the
priority queue, then assembles per-family FamilyDossier objects with:

  - Live param inventory (from TemplateData)
  - Alias normalisation map
  - Fragile-param detection (cross-referenced against anti_patterns)
  - Per-family breakage patterns
  - Gold corpus article coverage

API surfaces used (MediaWiki official API only):
  action=query&prop=revisions     — template wikitext source
  action=templatedata             — parameter schema
  Template:/doc via revisions     — documentation text

No HTML scraping. No live edits. Read-only.

Artifacts written to domains/language/model/tools/wikimedia/:
  template_family_ingest_report.json      — full TemplateFamilyIngestReport
  template_family_dossier_report.json     — per-family dossiers only
  template_priority_queue.json            — ranked priority queue
  parameter_alias_analysis_report.json    — alias/param union per family
  template_fragility_report.json          — fragile params + breakage patterns
  family_to_article_crosswalk.json        — family_id → [article titles]
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from domains.language.tools.language_pipeline import ENWIKI_API
from domains.language.tools.language_pipeline.template_families.extractor import (
    build_priority_queue,
    load_prep_data,
    assign_family,
    policies_for_family,
    FAMILY_POLICIES,
    TIER_CORE,
    TIER_SUPPORTING,
    TIER_HELPER,
)
from domains.language.tools.language_pipeline.template_families.family_dossier import (
    FamilyDossier,
    TemplateFamilyMember,
    TemplateFamilyIngestReport,
)
from domains.language.tools.language_pipeline.template_families.crosswalk import (
    build_family_article_crosswalk,
    build_family_policy_crosswalk,
    build_article_family_crosswalk,
)

_USER_AGENT = "HelixWikiOperator/1.0 (Research; User:Dissident93)"
_ARTIFACTS = (
    Path(__file__).resolve().parents[5]
    / "domains" / "language" / "wikipedia" / "data"
)

# ---------------------------------------------------------------------------
# Static family metadata (descriptions, breakage patterns, sandbox notes)
# Used to seed FamilyDossier fields that are not derivable from TemplateData.
# ---------------------------------------------------------------------------

_FAMILY_META: dict[str, dict] = {
    "nfl_biography": {
        "name": "NFL Biography Family",
        "description": (
            "Infoboxes and navigation templates for NFL players, personnel, and team articles. "
            "Core member: {{Infobox NFL player}}. High BLP sensitivity — all living player "
            "articles require WP:BLP compliance on career, contract, and injury params."
        ),
        "breakage_patterns": [
            {
                "id":          "nfl_teams_wrong_format",
                "name":        "NFL teams wrong format",
                "description": "{{NFL team}} or similar should be used inside |teams=; "
                               "bare city/team names break infobox rendering.",
                "severity":    "medium",
                "templates_affected": ["Infobox NFL player"],
            },
            {
                "id":          "birth_date_bare",
                "name":        "Birth date bare value",
                "description": "|birth_date= must use {{birth date and age|YYYY|MM|DD}} "
                               "for living players; bare dates lose the age calculation.",
                "severity":    "medium",
                "templates_affected": ["Infobox NFL player", "Infobox person"],
            },
            {
                "id":          "contract_blp_violation",
                "name":        "Contract / salary BLP exposure",
                "description": "Contract terms or salary figures without reliable source "
                               "violate WP:BLP. Should be omitted or sourced.",
                "severity":    "high",
                "templates_affected": ["Infobox NFL player"],
            },
            {
                "id":          "number_multi_value",
                "name":        "|number= multi-value format",
                "description": "Multiple jersey numbers must follow the template's accepted "
                               "format (often a comma-separated list); free-text breaks sorting.",
                "severity":    "low",
                "templates_affected": ["Infobox NFL player"],
            },
        ],
        "sandbox_notes": [
            "Test |teams= with {{NFL team|Washington Commanders}} vs bare 'Washington Commanders'",
            "Test {{birth date and age}} vs bare date strings",
            "Validate empty |draft_round= / |draft_pick= don't leave blank rows",
        ],
    },
    "vg_infobox": {
        "name": "Video Game Infobox Family",
        "description": (
            "Infoboxes and release/reception helpers for video game articles. "
            "Core member: {{Infobox video game}}. "
            "MOS:VG governs title italics, genre taxonomy, and gameplay-before-plot structure."
        ),
        "breakage_patterns": [
            {
                "id":          "image_prefix_in_infobox",
                "name":        "Image prefix in VG infobox",
                "description": "{{Infobox video game}} |image= must not include the 'File:' prefix; "
                               "the template adds it internally.",
                "severity":    "medium",
                "templates_affected": ["Infobox video game"],
            },
            {
                "id":          "released_raw_date",
                "name":        "Raw date in |released=",
                "description": "|released= should use {{Video game release|NA|YYYY-MM-DD}}; "
                               "bare dates lose regional metadata and sort order.",
                "severity":    "medium",
                "templates_affected": ["Infobox video game"],
            },
            {
                "id":          "platforms_not_unbulleted",
                "name":        "|platforms= missing {{unbulleted list}}",
                "description": "Multiple platforms should be wrapped in {{unbulleted list}}; "
                               "inline comma-separated values render inconsistently.",
                "severity":    "low",
                "templates_affected": ["Infobox video game"],
            },
            {
                "id":          "genre_non_canonical",
                "name":        "Non-canonical genre in |genre=",
                "description": "MOS:VG requires genre terms from the MOS:VG genre list; "
                               "invented or overly specific genre names are flagged at FAC.",
                "severity":    "medium",
                "templates_affected": ["Infobox video game"],
            },
        ],
        "sandbox_notes": [
            "Test |image= with and without 'File:' prefix",
            "Test {{Video game release}} vs bare date in |released=",
            "Validate |platforms= with {{unbulleted list}} vs comma list",
        ],
    },
    "executive_bio": {
        "name": "Executive Biography Family",
        "description": (
            "Person, officeholder, and executive biography infoboxes plus "
            "birth/death date helpers. Applies to Josh Harris, Adam Peters, Brandon Sosna. "
            "WP:BLP governs all living subjects — unsourced negative claims must be omitted."
        ),
        "breakage_patterns": [
            {
                "id":          "birth_date_and_age_malformed",
                "name":        "{{birth date and age}} malformed nesting",
                "description": "Must be {{birth date and age|YYYY|MM|DD}} with pipe-separated "
                               "year/month/day; {{birth date and age|YYYY-MM-DD}} is incorrect.",
                "severity":    "medium",
                "templates_affected": ["Infobox person", "Infobox officeholder"],
            },
            {
                "id":          "blp_unsourced_negative",
                "name":        "BLP unsourced negative claim",
                "description": "Any contested or potentially negative claim about a living person "
                               "without an inline citation must be removed (WP:BLP).",
                "severity":    "high",
                "templates_affected": ["Infobox person", "Infobox officeholder"],
            },
            {
                "id":          "short_description_overly_long",
                "name":        "{{short description}} too long",
                "description": "Short descriptions should be under 40 characters and must not "
                               "start with an article ('A', 'An', 'The').",
                "severity":    "low",
                "templates_affected": ["Short description"],
            },
        ],
        "sandbox_notes": [
            "Validate {{birth date and age}} pipe vs hyphen separator",
            "Test {{short description}} length and capitalisation",
            "Check |alma_mater= / |education= don't expose unsourced claims",
        ],
    },
    "venue_project": {
        "name": "Venue / Project Family",
        "description": (
            "Stadium, arena, and infrastructure infoboxes plus project navigation. "
            "Core use: New Commanders Stadium article. "
            "NFL policy applies to stadium articles linked to NFL franchises."
        ),
        "breakage_patterns": [
            {
                "id":          "capacity_bare_number",
                "name":        "Bare capacity number",
                "description": "|capacity= should use {{formatnum:}} for large numbers; "
                               "bare integers don't localise for readers.",
                "severity":    "low",
                "templates_affected": ["Infobox stadium"],
            },
            {
                "id":          "coordinates_malformed",
                "name":        "Malformed coordinates",
                "description": "{{coord}} in |coordinates= must follow the deg/min/sec or "
                               "decimal-degree convention; mixed formats break geo-tagging.",
                "severity":    "medium",
                "templates_affected": ["Infobox stadium", "Infobox building"],
            },
        ],
        "sandbox_notes": [
            "Test {{coord}} decimal vs DMS format in |coordinates=",
            "Validate |opened= with and without {{start date}} wrapper",
        ],
    },
}


# ---------------------------------------------------------------------------
# Fragile param sets per family (name-based heuristics + anti-pattern cross-ref)
# ---------------------------------------------------------------------------

_FRAGILE_PARAMS: dict[str, list[str]] = {
    "nfl_biography":  ["teams", "birth_date", "draft_round", "draft_pick", "number", "position"],
    "vg_infobox":     ["image", "released", "platforms", "genre", "developer", "publisher"],
    "executive_bio":  ["birth_date", "birth_place", "death_date", "alma_mater", "net_worth"],
    "venue_project":  ["capacity", "coordinates", "opened", "surface", "tenants"],
}


# ---------------------------------------------------------------------------
# Ingestor
# ---------------------------------------------------------------------------

class TemplateFamilyIngestor:
    """
    Phase 1.3 ingestor: fetches templates by priority tier and builds
    FamilyDossier objects.

    Usage:
        ingestor = TemplateFamilyIngestor()
        report = ingestor.run()
        ingestor.save(report)
    """

    # Only fetch core + supporting + helper tiers by default (skip low_priority/deferred)
    _FETCH_TIERS = {TIER_CORE, TIER_SUPPORTING, TIER_HELPER}

    def __init__(self, api: str = ENWIKI_API, delay: float = 0.6):
        self.api     = api
        self.delay   = delay
        self.headers = {"User-Agent": _USER_AGENT}

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------

    def run(self) -> TemplateFamilyIngestReport:
        """
        Full Phase 1.3 pipeline:
        1. Load gold corpus prep data (or fall back to static metadata)
        2. Build priority queue
        3. Fetch templates in core/supporting/helper tiers
        4. Build family dossiers
        5. Build crosswalks
        6. Return TemplateFamilyIngestReport
        """
        prep_data = load_prep_data()
        priority_queue = build_priority_queue(prep_data)

        # Collect which templates to fetch
        to_fetch = [
            entry for entry in priority_queue
            if entry["tier"] in self._FETCH_TIERS
        ]

        # Fetch each template
        fetched: dict[str, dict] = {}     # template_name → raw fetch result
        ok_count = 0
        err_count = 0
        for entry in to_fetch:
            name = entry["template"]
            if name in fetched:
                continue
            result = self._fetch_template(name)
            fetched[name] = result
            if result.get("fetch_error"):
                err_count += 1
            else:
                ok_count += 1
            time.sleep(self.delay)

        # Build family member objects
        family_members: dict[str, list[TemplateFamilyMember]] = {
            fid: [] for fid in _FAMILY_META
        }

        for entry in priority_queue:
            name = entry["template"]
            family_id = entry["family"]
            if family_id not in family_members:
                continue  # skip unrecognised families

            raw = fetched.get(name)
            if raw is None:
                # Not fetched (low_priority / deferred tier) — create a minimal member
                member = TemplateFamilyMember(
                    name=name,
                    full_title=f"Template:{name}",
                    family_id=family_id,
                    priority_tier=entry["tier"],
                    fetch_ok=False,
                    fetch_error="not fetched (below fetch threshold)",
                    param_names=[],
                    alias_map={},
                    required_params=[],
                    suggested_params=[],
                    param_descriptions={},
                    fragile_params=[p for p in _FRAGILE_PARAMS.get(family_id, [])],
                    fragility_notes=[],
                    has_source=False,
                    has_doc=False,
                    has_templatedata=False,
                    seen_in_articles=entry["articles"],
                )
            else:
                member = self._build_member(name, family_id, entry, raw)

            family_members[family_id].append(member)

        # Build FamilyDossier per family
        families: dict[str, FamilyDossier] = {}
        for family_id, members in family_members.items():
            if not members:
                continue
            families[family_id] = self._build_family_dossier(family_id, members)

        # Article coverage: derive from priority queue
        articles_by_family: dict[str, set[str]] = {fid: set() for fid in _FAMILY_META}
        for entry in priority_queue:
            fid = entry["family"]
            if fid in articles_by_family:
                for art in entry["articles"]:
                    articles_by_family[fid].add(art)

        # Update family articles_using_family
        for fid, d in families.items():
            d.articles_using_family = sorted(articles_by_family.get(fid, set()))

        # Crosswalks
        fam_article_xwalk = build_family_article_crosswalk(families)
        fam_policy_xwalk  = build_family_policy_crosswalk(families)
        art_family_xwalk  = build_article_family_crosswalk(families)

        fetch_summary = {
            "total_templates_in_queue": len(priority_queue),
            "templates_fetched": len(to_fetch),
            "ok": ok_count,
            "errors": err_count,
            "families_built": len(families),
        }

        return TemplateFamilyIngestReport(
            families=families,
            priority_queue=priority_queue,
            family_article_crosswalk=fam_article_xwalk,
            family_policy_crosswalk=fam_policy_xwalk,
            article_family_crosswalk=art_family_xwalk,
            fetch_summary=fetch_summary,
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, report: TemplateFamilyIngestReport, out_dir: Path | None = None) -> dict[str, Path]:
        target = out_dir or _ARTIFACTS
        target.mkdir(parents=True, exist_ok=True)
        written: dict[str, Path] = {}

        def _w(name: str, data: Any) -> Path:
            p = target / name
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            written[name] = p
            return p

        _w("template_family_ingest_report.json",
           report.to_dict())
        _w("template_family_dossier_report.json",
           {fid: d.to_dict() for fid, d in report.families.items()})
        _w("template_priority_queue.json",
           report.priority_queue)
        _w("parameter_alias_analysis_report.json",
           self._build_alias_report(report))
        _w("template_fragility_report.json",
           self._build_fragility_report(report))
        _w("family_to_article_crosswalk.json",
           report.family_article_crosswalk)

        return written

    # ------------------------------------------------------------------
    # Fetch helpers
    # ------------------------------------------------------------------

    def _fetch_template(self, name: str) -> dict:
        """Fetch source wikitext + TemplateData for one template."""
        full_title = f"Template:{name}"
        result: dict = {
            "name": name,
            "full_title": full_title,
            "source_wikitext": None,
            "doc_wikitext": None,
            "templatedata": {},
            "fetch_error": None,
        }

        # 1. Source wikitext
        source, source_err = self._fetch_wikitext(full_title)
        if source_err:
            result["fetch_error"] = f"source: {source_err}"
            return result
        result["source_wikitext"] = source
        time.sleep(self.delay)

        # 2. TemplateData
        td, td_err = self._fetch_templatedata(full_title)
        if not td_err:
            result["templatedata"] = td
        time.sleep(self.delay)

        # 3. /doc page
        doc, _ = self._fetch_wikitext(f"{full_title}/doc")
        result["doc_wikitext"] = doc

        return result

    def _fetch_wikitext(self, title: str) -> tuple[str | None, str | None]:
        params = {
            "action":      "query",
            "prop":        "revisions",
            "titles":      title,
            "rvprop":      "content",
            "rvslots":     "main",
            "redirects":   "1",
            "formatversion": "2",
            "format":      "json",
        }
        url = f"{self.api}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return None, str(e)

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return None, "no pages in response"
        page = pages[0]
        if page.get("missing"):
            return None, "page missing"
        revisions = page.get("revisions", [])
        if not revisions:
            return None, "no revisions"
        rev = revisions[0]
        wikitext = rev.get("slots", {}).get("main", {}).get("content") or rev.get("content")
        return wikitext, None

    def _fetch_templatedata(self, title: str) -> tuple[dict, str | None]:
        params = {
            "action":  "templatedata",
            "titles":  title,
            "format":  "json",
        }
        url = f"{self.api}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {}, str(e)

        pages = data.get("pages", {})
        if not pages:
            return {}, "no templatedata pages"
        # TemplateData returns a dict keyed by page ID (as string)
        td = next(iter(pages.values()), {})
        return td, None

    # ------------------------------------------------------------------
    # Member builder
    # ------------------------------------------------------------------

    def _build_member(
        self,
        name: str,
        family_id: str,
        queue_entry: dict,
        raw: dict,
    ) -> TemplateFamilyMember:
        """Build a TemplateFamilyMember from a raw fetch result."""
        td = raw.get("templatedata", {})
        td_params: dict[str, Any] = td.get("params", {})

        param_names: list[str] = list(td_params.keys())
        alias_map: dict[str, str] = {}
        required_params: list[str] = []
        suggested_params: list[str] = []
        param_descriptions: dict[str, str] = {}

        for pname, pdata in td_params.items():
            aliases: list[str] = pdata.get("aliases", [])
            for alias in aliases:
                alias_map[str(alias)] = pname
            if pdata.get("required"):
                required_params.append(pname)
            if pdata.get("suggested"):
                suggested_params.append(pname)
            # TemplateData descriptions can be strings or {"en": "..."} objects
            desc = pdata.get("description", "")
            if isinstance(desc, dict):
                desc = desc.get("en", "")
            param_descriptions[pname] = desc or ""

        # Fragile param detection: intersect known fragile params with actual params
        known_fragile = _FRAGILE_PARAMS.get(family_id, [])
        fragile_hit = [p for p in known_fragile if p in param_names]
        # Also flag params with names containing fragile keywords
        fragile_keywords = ["birth", "death", "image", "date", "coord", "number"]
        for pname in param_names:
            for kw in fragile_keywords:
                if kw in pname.lower() and pname not in fragile_hit:
                    fragile_hit.append(pname)
                    break

        fragility_notes: list[str] = []
        if "birth_date" in fragile_hit:
            fragility_notes.append("birth_date: use {{birth date and age|YYYY|MM|DD}}")
        if "image" in fragile_hit:
            fragility_notes.append("image: omit 'File:' prefix")
        if "released" in fragile_hit:
            fragility_notes.append("released: use {{Video game release}} not bare date")
        if "teams" in fragile_hit:
            fragility_notes.append("teams: use {{NFL team}} not bare name")

        return TemplateFamilyMember(
            name=name,
            full_title=f"Template:{name}",
            family_id=family_id,
            priority_tier=queue_entry["tier"],
            fetch_ok=raw.get("fetch_error") is None,
            fetch_error=raw.get("fetch_error"),
            param_names=param_names,
            alias_map=alias_map,
            required_params=required_params,
            suggested_params=suggested_params,
            param_descriptions=param_descriptions,
            fragile_params=fragile_hit,
            fragility_notes=fragility_notes,
            has_source=raw.get("source_wikitext") is not None,
            has_doc=raw.get("doc_wikitext") is not None,
            has_templatedata=bool(td_params),
            seen_in_articles=queue_entry["articles"],
        )

    # ------------------------------------------------------------------
    # Family dossier builder
    # ------------------------------------------------------------------

    def _build_family_dossier(
        self,
        family_id: str,
        members: list[TemplateFamilyMember],
    ) -> FamilyDossier:
        meta = _FAMILY_META.get(family_id, {})

        # Union of all param names across members
        param_union_set: set[str] = set()
        alias_union: dict[str, str] = {}
        for m in members:
            param_union_set.update(m.param_names)
            alias_union.update(m.alias_map)

        # Shared fragile params: appear in 2+ members OR are in the static list
        fragile_counter: dict[str, int] = {}
        for m in members:
            for fp in m.fragile_params:
                fragile_counter[fp] = fragile_counter.get(fp, 0) + 1
        shared_fragile = [p for p, c in fragile_counter.items() if c >= 1]
        # Always include the static list for the family
        for p in _FRAGILE_PARAMS.get(family_id, []):
            if p not in shared_fragile:
                shared_fragile.append(p)

        return FamilyDossier(
            family_id=family_id,
            family_name=meta.get("name", family_id),
            description=meta.get("description", ""),
            member_templates=members,
            param_union=sorted(param_union_set),
            alias_union=alias_union,
            shared_fragile_params=shared_fragile,
            breakage_patterns=meta.get("breakage_patterns", []),
            policy_codes=policies_for_family(family_id),
            articles_using_family=[],   # filled in by run() after the loop
            sandbox_notes=meta.get("sandbox_notes", []),
        )

    # ------------------------------------------------------------------
    # Report helpers
    # ------------------------------------------------------------------

    def _build_alias_report(self, report: TemplateFamilyIngestReport) -> dict:
        out: dict = {}
        for fid, d in report.families.items():
            out[fid] = {
                "family_name":  d.family_name,
                "param_union":  d.param_union,
                "alias_union":  d.alias_union,
                "member_params": {
                    m.name: m.param_names for m in d.member_templates
                },
            }
        return out

    def _build_fragility_report(self, report: TemplateFamilyIngestReport) -> dict:
        out: dict = {}
        for fid, d in report.families.items():
            out[fid] = {
                "family_name":         d.family_name,
                "shared_fragile_params": d.shared_fragile_params,
                "breakage_patterns":   d.breakage_patterns,
                "per_template": {
                    m.name: {
                        "fragile_params":    m.fragile_params,
                        "fragility_notes":   m.fragility_notes,
                    }
                    for m in d.member_templates
                },
            }
        return out

