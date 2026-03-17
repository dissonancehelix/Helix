"""
musicbrainz_ingester.py — MusicBrainz Data Ingester
=====================================================
Fetches composer/artist data from the MusicBrainz JSON API.

MusicBrainz is a canonical, fully open music encyclopedia.
We use it for: artist MBIDs, recording credits, release groups (soundtracks),
and label/studio information.

Endpoints used
--------------
https://musicbrainz.org/ws/2/artist/<mbid>?inc=aliases+tags+url-rels&fmt=json
https://musicbrainz.org/ws/2/release-group?artist=<mbid>&type=soundtrack&fmt=json
https://musicbrainz.org/ws/2/artist?query=<name>&fmt=json   (search)

Rate limiting: MusicBrainz allows 1 req/sec without auth; 5/sec with auth.
We respect 1 req/sec unconditionally.

API
---
fetch_artist(mbid) -> dict
fetch_release_groups(mbid, rg_type="soundtrack") -> list[dict]
search_artist(name) -> list[dict]
enrich_composer(node) -> None   (modifies node in-place)
"""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import json
from typing import Any

from substrates.music.atlas_integration.composer_schema import ComposerNode

log = logging.getLogger(__name__)

_BASE_URL  = "https://musicbrainz.org/ws/2"
_USER_AGENT = "HelixMusicLab/1.0 (helix-research; contact@helix.local)"
_RATE_DELAY = 1.1   # seconds between requests
_TIMEOUT    = 15

_last_request: float = 0.0


def _get(path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < _RATE_DELAY:
        time.sleep(_RATE_DELAY - elapsed)

    if params:
        path = f"{path}?{urllib.parse.urlencode({**params, 'fmt': 'json'})}"
    else:
        path = f"{path}?fmt=json"

    url = f"{_BASE_URL}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            _last_request = time.monotonic()
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise
    except Exception as exc:
        log.warning("musicbrainz: request failed (%s): %s", url, exc)
        return {}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_artist(mbid: str) -> dict[str, Any]:
    """
    Fetch full artist record from MusicBrainz.
    Returns normalized dict ready to merge into ComposerNode.
    """
    data = _get(f"artist/{mbid}", {"inc": "aliases+tags+url-rels+genres"})
    if not data:
        return {}

    aliases = [a["name"] for a in data.get("aliases", []) if a.get("name")]
    tags    = [t["name"] for t in data.get("tags", []) if t.get("count", 0) > 0]
    genres  = [g["name"] for g in data.get("genres", []) if g.get("count", 0) > 0]

    # External URLs from url-rels
    external_ids: dict[str, str] = {"musicbrainz": mbid}
    for rel in data.get("relations", []):
        url_info = rel.get("url", {})
        resource = url_info.get("resource", "")
        rel_type = rel.get("type", "")
        if "wikidata" in resource:
            qid = resource.split("/")[-1]
            external_ids["wikidata"] = qid
        elif "wikipedia" in resource:
            title = resource.split("/wiki/")[-1]
            external_ids["wikipedia"] = title
        elif "last.fm" in resource or "lastfm" in resource:
            external_ids["lastfm_url"] = resource
        elif "spotify" in resource:
            external_ids["spotify"] = resource.split("/")[-1]
        elif "discogs" in resource:
            external_ids["discogs"] = resource

    area = data.get("area", {}) or {}
    life = data.get("life-span", {}) or {}

    return {
        "full_name":     data.get("name"),
        "sort_name":     data.get("sort-name"),
        "aliases":       aliases,
        "nationality":   area.get("name"),
        "birth_year":    _year_from_date(life.get("begin")),
        "death_year":    _year_from_date(life.get("end")),
        "bio_url":       external_ids.get("wikipedia"),
        "external_ids":  external_ids,
        "style_traits":  {
            "mb_tags":   tags[:10],
            "mb_genres": genres[:5],
            "mb_type":   data.get("type"),
        },
    }


def fetch_release_groups(
    mbid:    str,
    rg_type: str = "soundtrack",
    limit:   int = 25,
) -> list[dict[str, Any]]:
    """
    Fetch release groups (soundtracks/albums) for an artist MBID.
    Returns list of normalized release group dicts.
    """
    data = _get(
        "release-group",
        {
            "artist": mbid,
            "type":   rg_type,
            "limit":  str(limit),
        },
    )
    groups = data.get("release-groups", [])
    results = []
    for rg in groups:
        results.append({
            "mbid":       rg.get("id"),
            "title":      rg.get("title"),
            "type":       rg.get("primary-type"),
            "first_year": _year_from_date(rg.get("first-release-date")),
        })
    return results


def search_artist(name: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search MusicBrainz for an artist by name.
    Returns list of candidate dicts with mbid, name, score.
    """
    data = _get("artist", {"query": name, "limit": str(limit)})
    artists = data.get("artists", [])
    results = []
    for a in artists:
        results.append({
            "mbid":    a.get("id"),
            "name":    a.get("name"),
            "score":   a.get("score", 0),
            "country": a.get("country"),
            "type":    a.get("type"),
            "disambiguation": a.get("disambiguation", ""),
        })
    return results


# ---------------------------------------------------------------------------
# ComposerNode enrichment
# ---------------------------------------------------------------------------

def enrich_composer(node: ComposerNode) -> bool:
    """
    Fetch MusicBrainz data for node and merge into node in-place.
    Uses node.external_ids["musicbrainz"] if present, else searches by name.

    Returns True if any data was added.
    """
    mbid = node.external_ids.get("musicbrainz")

    if not mbid:
        # Attempt search
        candidates = search_artist(node.full_name, limit=3)
        if candidates:
            best = max(candidates, key=lambda c: c.get("score", 0))
            if best.get("score", 0) >= 80:
                mbid = best["mbid"]
                log.info(
                    "musicbrainz: resolved '%s' → %s (score=%s)",
                    node.full_name, mbid, best.get("score"),
                )

    if not mbid:
        return False

    data = fetch_artist(mbid)
    if not data:
        return False

    # Merge non-destructively
    if not node.nationality and data.get("nationality"):
        node.nationality = data["nationality"]
    if not node.birth_year and data.get("birth_year"):
        node.birth_year = data["birth_year"]
    if not node.death_year and data.get("death_year"):
        node.death_year = data["death_year"]
    if not node.bio_url and data.get("bio_url"):
        node.bio_url = data["bio_url"]

    # Merge aliases
    existing_aliases = set(node.aliases)
    for a in data.get("aliases", []):
        if a and a not in existing_aliases and a != node.full_name:
            node.aliases.append(a)
            existing_aliases.add(a)

    # Merge external IDs
    node.external_ids.update(
        {k: v for k, v in data.get("external_ids", {}).items()
         if k not in node.external_ids}
    )

    # Merge style traits (MB-specific)
    node.style_traits.update(
        {k: v for k, v in data.get("style_traits", {}).items()
         if k not in node.style_traits}
    )

    log.debug("musicbrainz: enriched '%s' (mbid=%s)", node.full_name, mbid)
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _year_from_date(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        return int(str(date_str)[:4])
    except (ValueError, TypeError):
        return None
