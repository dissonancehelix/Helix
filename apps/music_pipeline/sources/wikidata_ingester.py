"""
wikidata_ingester.py — Wikidata SPARQL Ingester
================================================
Queries the Wikidata SPARQL endpoint for VGM composer biographical data.
No authentication required — Wikidata is a free open knowledge base.

Queries:
  - fetch_composer(wikidata_id)     — biography, aliases, nationality, instruments
  - search_composer(name)           — search by name, returns list of candidates
  - fetch_vgm_composers()           — bulk query for video game music composers

API
---
enrich_composer(node: ComposerNode) -> ComposerNode   (adds bio data in-place)
search(name: str) -> list[dict]
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Any

from domains.music.atlas_integration.composer_schema import ComposerNode

log = logging.getLogger(__name__)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
_USER_AGENT     = "HelixMusicLab/1.0 (helix-vgm-research; research-use)"

_RATE_LIMIT_SEC = 1.0   # polite delay between requests
_TIMEOUT_SEC    = 15


# ---------------------------------------------------------------------------
# SPARQL query helpers
# ---------------------------------------------------------------------------

def _sparql_query(query: str) -> list[dict[str, Any]]:
    """Execute a SPARQL query and return result bindings."""
    url = f"{SPARQL_ENDPOINT}?query={urllib.parse.quote(query)}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", {}).get("bindings", [])
    except Exception as exc:
        log.warning("wikidata_ingester: SPARQL query failed: %s", exc)
        return []


def _val(binding: dict, key: str) -> str | None:
    item = binding.get(key)
    return item["value"] if item else None


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_COMPOSER_QUERY = """
SELECT DISTINCT
  ?person ?personLabel ?birthYear ?deathYear
  ?nationalityLabel ?genderLabel
  ?sitelinks
WHERE {{
  BIND(wd:{wikidata_id} AS ?person)
  OPTIONAL {{ ?person wdt:P569 ?birthDate. BIND(YEAR(?birthDate) AS ?birthYear) }}
  OPTIONAL {{ ?person wdt:P570 ?deathDate. BIND(YEAR(?deathDate) AS ?deathYear) }}
  OPTIONAL {{ ?person wdt:P27 ?nationality. }}
  OPTIONAL {{ ?person wdt:P21 ?gender. }}
  OPTIONAL {{ ?person wikibase:sitelinks ?sitelinks. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ja". }}
}}
LIMIT 1
"""

_ALIASES_QUERY = """
SELECT ?altLabel
WHERE {{
  BIND(wd:{wikidata_id} AS ?person)
  ?person skos:altLabel ?altLabel.
  FILTER(LANG(?altLabel) IN ("en", "ja"))
}}
LIMIT 20
"""

_INSTRUMENTS_QUERY = """
SELECT DISTINCT ?instrumentLabel
WHERE {{
  BIND(wd:{wikidata_id} AS ?person)
  ?person wdt:P1303 ?instrument.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 10
"""

_EMPLOYER_QUERY = """
SELECT DISTINCT ?employerLabel
WHERE {{
  BIND(wd:{wikidata_id} AS ?person)
  ?person wdt:P108 ?employer.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 10
"""

_SEARCH_QUERY = """
SELECT DISTINCT ?person ?personLabel ?description
WHERE {{
  ?person wdt:P31 wd:Q5.                          # is a human
  ?person wdt:P106 ?occupation.                   # has occupation
  VALUES ?occupation {{ wd:Q36834 wd:Q753110 wd:Q177220 }}  # composer, musician, songwriter
  ?person rdfs:label "{name}"@en.
  OPTIONAL {{ ?person schema:description ?description. FILTER(LANG(?description)="en") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 10
"""


def fetch_composer_data(wikidata_id: str) -> dict[str, Any]:
    """
    Fetch biographical data for a composer by Wikidata QID (e.g. "Q14934873").
    Returns a dict with keys: full_name, birth_year, death_year, nationality,
    aliases, instruments, studios.
    """
    result: dict[str, Any] = {"wikidata_id": wikidata_id}

    # Main query
    rows = _sparql_query(_COMPOSER_QUERY.format(wikidata_id=wikidata_id))
    if rows:
        r = rows[0]
        result["full_name"]   = _val(r, "personLabel")
        result["birth_year"]  = int(_val(r, "birthYear")) if _val(r, "birthYear") else None
        result["death_year"]  = int(_val(r, "deathYear")) if _val(r, "deathYear") else None
        result["nationality"] = _val(r, "nationalityLabel")
        result["bio_url"]     = f"https://www.wikidata.org/wiki/{wikidata_id}"
    else:
        return result

    time.sleep(_RATE_LIMIT_SEC)

    # Aliases
    alias_rows = _sparql_query(_ALIASES_QUERY.format(wikidata_id=wikidata_id))
    result["aliases"] = list({_val(r, "altLabel") for r in alias_rows if _val(r, "altLabel")})
    time.sleep(_RATE_LIMIT_SEC)

    # Instruments
    instr_rows = _sparql_query(_INSTRUMENTS_QUERY.format(wikidata_id=wikidata_id))
    result["instruments"] = [_val(r, "instrumentLabel") for r in instr_rows
                             if _val(r, "instrumentLabel")]
    time.sleep(_RATE_LIMIT_SEC)

    # Employers / studios
    emp_rows = _sparql_query(_EMPLOYER_QUERY.format(wikidata_id=wikidata_id))
    result["studios"] = [_val(r, "employerLabel") for r in emp_rows
                         if _val(r, "employerLabel")]

    return result


def enrich_composer(node: ComposerNode) -> ComposerNode:
    """
    Fetch Wikidata data for a composer node and merge it in-place.
    Only runs if the node has a "wikidata" external_id.
    """
    wikidata_id = node.external_ids.get("wikidata")
    if not wikidata_id:
        log.debug("wikidata_ingester: no wikidata ID for %s", node.full_name)
        return node

    log.info("wikidata_ingester: fetching %s (%s)", node.full_name, wikidata_id)
    data = fetch_composer_data(wikidata_id)

    if data.get("full_name") and not node.full_name:
        node.full_name = data["full_name"]
    if data.get("birth_year") and not node.birth_year:
        node.birth_year = data["birth_year"]
    if data.get("death_year") and not node.death_year:
        node.death_year = data["death_year"]
    if data.get("nationality") and not node.nationality:
        node.nationality = data["nationality"]
    if data.get("bio_url") and not node.bio_url:
        node.bio_url = data["bio_url"]
    if data.get("aliases"):
        node.aliases = list(dict.fromkeys(node.aliases + data["aliases"]))
    if data.get("instruments"):
        node.instruments = list(dict.fromkeys(node.instruments + data["instruments"]))
    if data.get("studios"):
        node.studios = list(dict.fromkeys(node.studios + data["studios"]))

    return node


def search(name: str) -> list[dict[str, Any]]:
    """Search Wikidata for a composer by name. Returns list of candidate dicts."""
    rows = _sparql_query(_SEARCH_QUERY.format(name=name.replace('"', '\\"')))
    return [
        {
            "wikidata_id":  _val(r, "person", "").split("/")[-1] if _val(r, "person") else "",
            "name":         _val(r, "personLabel"),
            "description":  _val(r, "description"),
        }
        for r in rows
    ]
