"""
Template index — fetches and caches template source, TemplateData, and /doc pages
from the MediaWiki API.

Uses official surfaces only:
  - action=query&prop=revisions  →  template wikitext source
  - action=templatedata           →  parameter schema (names, aliases, types, required)
  - Template:/doc page source     →  documentation text

No HTML scraping. No guessed parameter behavior.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from system.tools.language_pipeline import ENWIKI_API

_USER_AGENT = "HelixWikiOperator/1.0 (Research; User:Dissident93)"

_INDEX_CACHE = (
    Path(__file__).resolve().parents[1]
    / "data" / "template_index"
)


@dataclass
class TemplateParam:
    name: str
    aliases: list[str]
    description: str
    type_: str           # "string", "number", "boolean", "content", "wiki-page-name", etc.
    required: bool
    suggested: bool
    default: str | None


@dataclass
class TemplateRecord:
    name: str                              # e.g. "Infobox NFL player"
    full_title: str                        # e.g. "Template:Infobox NFL player"
    source_wikitext: str | None            # raw template source
    doc_wikitext: str | None               # /doc page source
    templatedata: dict[str, Any]           # raw TemplateData JSON
    params: list[TemplateParam]            # parsed parameter list
    description: str                       # from TemplateData description
    dependencies: list[str]               # templates transcluded inside this one (heuristic)
    fetch_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "full_title": self.full_title,
            "description": self.description,
            "params": [
                {
                    "name": p.name,
                    "aliases": p.aliases,
                    "description": p.description,
                    "type": p.type_,
                    "required": p.required,
                    "suggested": p.suggested,
                    "default": p.default,
                }
                for p in self.params
            ],
            "dependencies": self.dependencies,
            "has_source": self.source_wikitext is not None,
            "has_doc": self.doc_wikitext is not None,
            "has_templatedata": bool(self.templatedata),
            "fetch_error": self.fetch_error,
        }


class TemplateIndexer:
    """
    Fetches and indexes Wikipedia templates.

    Usage:
        ix = TemplateIndexer()
        record = ix.fetch("Infobox NFL player")
        ix.save(record)                      # writes to template_index cache
        records = ix.fetch_many(names)
        ix.save_index(records)               # writes full index JSON
    """

    def __init__(self, api_endpoint: str = ENWIKI_API):
        self.api = api_endpoint
        self.headers = {"User-Agent": _USER_AGENT}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, title: str) -> TemplateRecord:
        """Fetch a single page's source, TemplateData, and /doc."""
        if title.startswith(":"):
            full_title = title[1:]
            name = full_title
        elif ":" in title:
            full_title = title
            name = title.split(":", 1)[1]
        else:
            name = title
            full_title = f"Template:{name}"

        doc_title  = f"{full_title}/doc"

        source  = self._get_page_source(full_title)
        doc     = self._get_page_source(doc_title)
        tddata  = self._get_templatedata(full_title)
        params  = self._parse_templatedata_params(tddata)
        desc    = self._extract_description(tddata)
        deps    = self._extract_dependencies(source or "")

        return TemplateRecord(
            name=name,
            full_title=full_title,
            source_wikitext=source,
            doc_wikitext=doc,
            templatedata=tddata,
            params=params,
            description=desc,
            dependencies=deps,
        )

    def fetch_many(self, template_names: list[str], delay: float = 0.5) -> list[TemplateRecord]:
        """Fetch multiple templates. Polite delay between requests."""
        records = []
        for name in template_names:
            try:
                records.append(self.fetch(name))
            except Exception as e:
                records.append(TemplateRecord(
                    name=name,
                    full_title=f"Template:{name}",
                    source_wikitext=None,
                    doc_wikitext=None,
                    templatedata={},
                    params=[],
                    description="",
                    dependencies=[],
                    fetch_error=str(e),
                ))
            time.sleep(delay)
        return records

    def save(self, record: TemplateRecord) -> Path:
        """Write a single record to the cache."""
        _INDEX_CACHE.mkdir(parents=True, exist_ok=True)
        safe_name = record.name.replace(" ", "_").replace("/", "__").replace(":", "__")
        path = _INDEX_CACHE / f"{safe_name}.json"
        data: dict[str, Any] = {**record.to_dict()}
        if record.source_wikitext is not None:
            data["source_wikitext"] = record.source_wikitext
        if record.doc_wikitext is not None:
            data["doc_wikitext"] = record.doc_wikitext
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def save_index(self, records: list[TemplateRecord]) -> Path:
        """Write a master index JSON (no source/doc text — just metadata)."""
        _INDEX_CACHE.mkdir(parents=True, exist_ok=True)
        index_path = _INDEX_CACHE / "template_index.json"
        index_data = {
            "total": len(records),
            "templates": [r.to_dict() for r in records],
        }
        index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return index_path

    def load_cached(self, template_name: str) -> TemplateRecord | None:
        """Load a previously cached record without hitting the API."""
        name = template_name.removeprefix("Template:")
        safe_name = name.replace(" ", "_").replace("/", "__")
        path = _INDEX_CACHE / f"{safe_name}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        params = [
            TemplateParam(
                name=p["name"], aliases=p["aliases"], description=p["description"],
                type_=p["type"], required=p["required"], suggested=p["suggested"],
                default=p["default"],
            )
            for p in data.get("params", [])
        ]
        return TemplateRecord(
            name=data["name"],
            full_title=data["full_title"],
            source_wikitext=data.get("source_wikitext"),
            doc_wikitext=data.get("doc_wikitext"),
            templatedata=data.get("templatedata", {}),
            params=params,
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            fetch_error=data.get("fetch_error"),
        )

    # ------------------------------------------------------------------
    # MediaWiki API calls
    # ------------------------------------------------------------------

    def _api_get(self, params: dict) -> dict:
        params["format"] = "json"
        url = f"{self.api}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))

    def _get_page_source(self, title: str) -> str | None:
        """Fetch wikitext source of a page via action=query&prop=revisions."""
        try:
            data = self._api_get({
                "action": "query",
                "prop": "revisions",
                "titles": title,
                "rvprop": "content",
                "rvslots": "main",
            })
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if "missing" in page:
                    return None
                slots = page.get("revisions", [{}])[0].get("slots", {})
                return slots.get("main", {}).get("*") or slots.get("main", {}).get("content")
        except Exception:
            return None

    def _get_templatedata(self, title: str) -> dict:
        """Fetch TemplateData for a template."""
        try:
            data = self._api_get({
                "action": "templatedata",
                "titles": title,
                "includeMissingTitles": "1",
            })
            pages = data.get("pages", {})
            for page in pages.values():
                return page
        except Exception:
            pass
        return {}

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_templatedata_params(self, tddata: dict) -> list[TemplateParam]:
        raw_params = tddata.get("params", {})
        result = []
        for pname, pdata in raw_params.items():
            desc = pdata.get("description", {})
            if isinstance(desc, dict):
                desc = desc.get("en", "") or next(iter(desc.values()), "")
            result.append(TemplateParam(
                name=pname,
                aliases=pdata.get("aliases", []),
                description=str(desc),
                type_=pdata.get("type", "string"),
                required=pdata.get("required", False),
                suggested=pdata.get("suggested", False),
                default=pdata.get("default"),
            ))
        return result

    def _extract_description(self, tddata: dict) -> str:
        desc = tddata.get("description", {})
        if isinstance(desc, dict):
            return desc.get("en", "") or next(iter(desc.values()), "")
        return str(desc) if desc else ""

    def _extract_dependencies(self, source: str) -> list[str]:
        """
        Heuristic: extract template names transcluded inside the source.
        Matches {{Template name}} patterns that don't start with # (parser functions).
        """
        import re
        raw = re.findall(r"\{\{([^#|{}\n][^|{}\n]*?)(?:\||\}\})", source)
        seen: dict[str, None] = {}
        for t in raw:
            t = t.strip()
            if t and not t.startswith("#") and t not in seen:
                seen[t] = None
        return list(seen.keys())[:30]

