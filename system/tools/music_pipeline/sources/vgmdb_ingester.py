"""
vgmdb_ingester.py — VGMDB Ingester
====================================
Uses the unofficial vgmdb.info JSON API to fetch composer/artist and
album/soundtrack data.

vgmdb.info is a community-maintained JSON frontend for vgmdb.net.
Base URL: https://vgmdb.info/

Endpoints used:
  /artist/{id}   — artist profile (name, aliases, units, discography)
  /album/{id}    — album metadata (titles, tracks, performers, composers)
  /search/artists/{name} — search by name

Rate limiting: polite 1s delay between requests.
All calls fail gracefully and return empty results on error.

API
---
fetch_artist(vgmdb_id) -> dict
fetch_album(vgmdb_id)  -> dict
search_artist(name)    -> list[dict]
enrich_composer(node)  -> ComposerNode
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Any

# from model.domains.music.atlas_integration.composer_schema import ComposerNode, TrackNode, GameNode

log = logging.getLogger(__name__)

_BASE_URL     = "https://vgmdb.info"
_USER_AGENT   = "HelixMusicLab/1.0 (helix-vgm-research)"
_RATE_LIMIT   = 1.0
_TIMEOUT      = 15


def _get(path: str) -> dict[str, Any] | None:
    url = f"{_BASE_URL}/{path.lstrip('/')}?format=json"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        log.debug("vgmdb_ingester: GET %s failed: %s", url, exc)
        return None


def fetch_artist(vgmdb_id: str) -> dict[str, Any]:
    """
    Fetch artist profile from vgmdb.info.
    Returns normalized dict: name, aliases, units, websites, discography.
    """
    data = _get(f"/artist/{vgmdb_id}")
    if not data:
        return {}

    time.sleep(_RATE_LIMIT)

    # Normalize name: prefer English
    names = data.get("names", {})
    name = names.get("en") or names.get("ja-latn") or names.get("ja") or ""

    # Aliases: other name entries
    aliases = [v for k, v in names.items() if k != "en" and v != name]

    # Units (groups/companies)
    units = [u.get("names", {}).get("en") or "" for u in data.get("units", [])]

    # Websites
    websites: dict[str, str] = {}
    for site in data.get("websites", []):
        link_name = site.get("name", "").lower()
        link_url  = site.get("link", "")
        if link_url:
            websites[link_name] = link_url

    return {
        "vgmdb_id":      vgmdb_id,
        "full_name":     name,
        "aliases":       [a for a in aliases if a],
        "units":         [u for u in units if u],
        "websites":      websites,
        "notes":         data.get("notes", ""),
    }


def fetch_album(vgmdb_id: str) -> dict[str, Any]:
    """
    Fetch album/soundtrack from vgmdb.info.
    Returns normalized dict: title, year, composers, performers, track_list.
    """
    data = _get(f"/album/{vgmdb_id}")
    if not data:
        return {}

    time.sleep(_RATE_LIMIT)

    names = data.get("names", {})
    title = names.get("en") or names.get("ja-latn") or names.get("ja") or ""

    year = None
    date_str = data.get("release_date", "")
    if date_str and len(date_str) >= 4:
        try:
            year = int(date_str[:4])
        except ValueError:
            pass

    # Composers / performers
    composers  = [p.get("names", {}).get("en", "") for p in data.get("composers", [])]
    performers = [p.get("names", {}).get("en", "") for p in data.get("performers", [])]
    arrangers  = [p.get("names", {}).get("en", "") for p in data.get("arrangers", [])]

    # Track list (flattened from disc structure)
    track_list: list[dict[str, Any]] = []
    for disc in data.get("discs", []):
        for track in disc.get("tracks", []):
            tnames = track.get("names", {})
            track_list.append({
                "number": track.get("track_position"),
                "title":  tnames.get("en") or tnames.get("ja") or "",
            })

    return {
        "vgmdb_id":   vgmdb_id,
        "title":      title,
        "year":       year,
        "composers":  [c for c in composers if c],
        "performers": [p for p in performers if p],
        "arrangers":  [a for a in arrangers if a],
        "track_list": track_list,
        "notes":      data.get("notes", ""),
    }


def search_artist(name: str) -> list[dict[str, Any]]:
    """Search VGMDB for an artist by name."""
    data = _get(f"/search/artists/{urllib.parse.quote(name)}")
    if not data:
        return []
    results = []
    for item in data.get("results", {}).get("artists", [])[:10]:
        item_names = item.get("names", {})
        results.append({
            "vgmdb_id": str(item.get("link", "").replace("artist/", "")),
            "name":     item_names.get("en") or item_names.get("ja") or "",
            "aliases":  list(item_names.values()),
        })
    return results


def enrich_composer(node: Any) -> Any:
    """Fetch VGMDB data and merge into an existing Composer object."""
    vgmdb_id = getattr(node, "external_ids", {}).get("vgmdb")
    if not vgmdb_id:
        return node

    log.info("vgmdb_ingester: fetching artist %s (%s)", getattr(node, "full_name", "Unknown"), vgmdb_id)
    data = fetch_artist(vgmdb_id)

    if not data:
        return node

    if data.get("full_name") and not getattr(node, "full_name", None):
        node.full_name = data["full_name"]
    if data.get("aliases"):
        node.aliases = list(dict.fromkeys(getattr(node, "aliases", []) + data["aliases"]))
    
    return node


def build_track_nodes_from_album(
    vgmdb_album_id: str,
    game_id: str,
) -> tuple[dict | None, list[dict]]:
    """
    Fetch a VGMDB album and build Track nodes + optional Game node as dicts.
    Returns (game_dict, track_dicts).
    """
    data = fetch_album(vgmdb_album_id)
    if not data:
        return None, []

    composers_slugs = [
        name.lower().replace(" ", "_").replace(".", "")
        for name in data.get("composers", [])
    ]

    game = {
        "game_id": game_id,
        "title": data["title"],
        "year": data.get("year"),
        "composers": composers_slugs,
        "external_ids": {"vgmdb": vgmdb_album_id},
    }

    tracks = [
        {
            "track_id": f"{game_id}_{str(t['number']).zfill(2)}",
            "title": t["title"],
            "game_id": game_id,
            "track_number": t["number"],
            "composers": composers_slugs,
        }
        for t in data.get("track_list", [])
        if t.get("title")
    ]

    return game, tracks


# Avoid circular import in SPARQL helper
try:
    import urllib.parse
except ImportError:
    pass

