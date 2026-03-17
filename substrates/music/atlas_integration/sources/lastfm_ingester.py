"""
lastfm_ingester.py — Last.fm Data Ingester
===========================================
Fetches biography summaries, top tags (genre), and similar artists from Last.fm.

Last.fm requires an API key (free registration at https://www.last.fm/api/account/create).
Set environment variable LASTFM_API_KEY or pass api_key explicitly.

Endpoints used
--------------
artist.getInfo:      biography, tags, similar artists, mbid
artist.search:       name → candidates

Rate limiting: Last.fm allows 5 req/sec; we use 0.25s delay to be polite.

API
---
fetch_artist_info(name, mbid=None) -> dict
search_artist(name) -> list[dict]
enrich_composer(node, api_key=None) -> bool
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from substrates.music.atlas_integration.composer_schema import ComposerNode

log = logging.getLogger(__name__)

_BASE_URL   = "https://ws.audioscrobbler.com/2.0/"
_RATE_DELAY = 0.25
_TIMEOUT    = 10

_last_request: float = 0.0


def _get_api_key(api_key: str | None = None) -> str | None:
    return api_key or os.environ.get("LASTFM_API_KEY")


def _call(method: str, params: dict[str, str], api_key: str) -> dict[str, Any]:
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < _RATE_DELAY:
        time.sleep(_RATE_DELAY - elapsed)

    full_params = {
        **params,
        "method":  method,
        "api_key": api_key,
        "format":  "json",
    }
    url = f"{_BASE_URL}?{urllib.parse.urlencode(full_params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "HelixMusicLab/1.0 (helix-research)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            _last_request = time.monotonic()
            data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                log.debug("lastfm: API error %s: %s", data["error"], data.get("message"))
                return {}
            return data
    except Exception as exc:
        log.warning("lastfm: request failed (%s): %s", method, exc)
        return {}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_artist_info(
    name:    str,
    mbid:    str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Fetch artist biography, tags, and similar artists from Last.fm.
    Returns normalized dict ready to merge into ComposerNode.
    """
    key = _get_api_key(api_key)
    if not key:
        log.warning("lastfm: no API key — set LASTFM_API_KEY env var")
        return {}

    params: dict[str, str] = {"autocorrect": "1"}
    if mbid:
        params["mbid"] = mbid
    else:
        params["artist"] = name

    data = _call("artist.getInfo", params, key)
    artist = data.get("artist", {})
    if not artist:
        return {}

    # Biography
    bio_raw  = artist.get("bio", {}) or {}
    bio_text = bio_raw.get("summary", "") or ""
    # Strip Last.fm HTML boilerplate  (<a href=...> links)
    bio_text = _strip_html(bio_text).strip()
    # Truncate to 500 chars
    if len(bio_text) > 500:
        bio_text = bio_text[:497] + "…"

    # Tags → genre hints
    tags_raw = artist.get("tags", {}).get("tag", []) or []
    if isinstance(tags_raw, dict):
        tags_raw = [tags_raw]
    tags = [t["name"] for t in tags_raw if isinstance(t, dict) and t.get("name")][:8]

    # Similar artists
    similar_raw = artist.get("similar", {}).get("artist", []) or []
    if isinstance(similar_raw, dict):
        similar_raw = [similar_raw]
    similar = [s["name"] for s in similar_raw[:5] if isinstance(s, dict)]

    # External IDs
    external_ids: dict[str, str] = {}
    mb = artist.get("mbid")
    if mb:
        external_ids["musicbrainz"] = mb
    lfm_url = artist.get("url")
    if lfm_url:
        external_ids["lastfm_url"] = lfm_url

    return {
        "bio_summary":  bio_text or None,
        "external_ids": external_ids,
        "style_traits": {
            "lastfm_tags":    tags,
            "similar_artists": similar,
        },
    }


def search_artist(name: str, api_key: str | None = None) -> list[dict[str, Any]]:
    """Search Last.fm for an artist by name. Returns candidate list."""
    key = _get_api_key(api_key)
    if not key:
        return []

    data = _call("artist.search", {"artist": name, "limit": "5"}, key)
    matches = (
        data.get("results", {})
        .get("artistmatches", {})
        .get("artist", []) or []
    )
    if isinstance(matches, dict):
        matches = [matches]

    return [
        {
            "name":       m.get("name"),
            "mbid":       m.get("mbid"),
            "listeners":  m.get("listeners"),
            "url":        m.get("url"),
        }
        for m in matches
        if isinstance(m, dict)
    ]


# ---------------------------------------------------------------------------
# ComposerNode enrichment
# ---------------------------------------------------------------------------

def enrich_composer(node: ComposerNode, api_key: str | None = None) -> bool:
    """
    Fetch Last.fm data for node and merge into node in-place.
    Returns True if any data was added.
    """
    key = _get_api_key(api_key)
    if not key:
        return False

    mbid = node.external_ids.get("musicbrainz")
    data = fetch_artist_info(node.full_name, mbid=mbid, api_key=key)
    if not data:
        return False

    if not node.bio_summary and data.get("bio_summary"):
        node.bio_summary = data["bio_summary"]

    node.external_ids.update(
        {k: v for k, v in data.get("external_ids", {}).items()
         if k not in node.external_ids}
    )

    lfm_traits = data.get("style_traits", {})
    if lfm_traits.get("lastfm_tags"):
        node.style_traits["lastfm_tags"] = lfm_traits["lastfm_tags"]
    if lfm_traits.get("similar_artists"):
        node.style_traits["similar_artists"] = lfm_traits["similar_artists"]

    log.debug("lastfm: enriched '%s'", node.full_name)
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re as _re

_HTML_TAG_RE = _re.compile(r"<[^>]+>")
_WHITESPACE_RE = _re.compile(r"\s+")


def _strip_html(text: str) -> str:
    text = _HTML_TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()
