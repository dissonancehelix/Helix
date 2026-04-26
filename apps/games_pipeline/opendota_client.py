"""
Games Domain — OpenDota API Client
domains/games/ingestion/opendota_client.py

Thin wrapper around the OpenDota REST API for fetching match data.
No auth required. Free tier has ~2000 req/day.

Endpoints used:
    /players/{account_id}/heroes     — per-hero stats (games, wins)
    /players/{account_id}/matches    — match history (basic stats per match)
    /matches/{match_id}              — full match data (requires replay parse)

Parse status:
    OpenDota stores basic match stats for all games.
    Full replay data (ability_uses, teamfights, kills_log) requires the match
    to have been parsed. Parsed matches have a non-null `version` field.
    Unparsed matches can be submitted for parsing via POST /request/{match_id},
    but processing takes time and is not guaranteed for old matches.

Account IDs:
    Steam uses 64-bit IDs (steamcommunity.com profile). OpenDota uses 32-bit.
    Conversion: account_id_32 = steam64 - 76561197960265728
    STEAM_0:W:Z → account_id = Z * 2 + W
    dissonance: STEAM_0:0:45789161 → 91578322
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

_BASE = "https://api.opendota.com/api"
_RATE_DELAY = 0.5  # seconds between requests — stay well within free tier


def _get(path: str, timeout: int = 15) -> dict | list:
    """Simple blocking GET against the OpenDota API."""
    url = f"{_BASE}{path}"
    time.sleep(_RATE_DELAY)
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "curl/8.16.0",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ---------------------------------------------------------------------------
# Public fetch functions
# ---------------------------------------------------------------------------

def fetch_player_heroes(account_id: int) -> list[dict]:
    """
    Return all hero stats for a player.
    Each entry: {hero_id, games, win, with_games, with_win, against_games, against_win}
    Sorted by games descending.
    """
    heroes = _get(f"/players/{account_id}/heroes")
    return sorted(heroes, key=lambda h: h.get("games", 0), reverse=True)


def fetch_player_matches(
    account_id: int,
    hero_id: Optional[int] = None,
    limit: int = 100,
    significant: int = 0,
) -> list[dict]:
    """
    Return match history for a player.

    Args:
        account_id: 32-bit OpenDota account ID
        hero_id:    filter to specific hero (None = all heroes)
        limit:      max matches to return (max 500 per request)
        significant: 0 = include all matches; 1 = ranked/competitive only

    Each entry contains basic match stats (match_id, start_time, duration,
    radiant_win, player_slot, kills, deaths, assists, hero_id).
    Does NOT include ability logs or teamfight data — use fetch_match() for that.
    """
    params = f"?limit={limit}&significant={significant}"
    if hero_id is not None:
        params += f"&hero_id={hero_id}"
    return _get(f"/players/{account_id}/matches{params}")


def fetch_match(match_id: int) -> dict:
    """
    Return full match data for a single match.

    Includes per-player ability_uses, kills_log, gold_t, xp_t, and
    match-level teamfights array — but ONLY if the match has been parsed.
    Parsed status: match['version'] is not None.

    Raises urllib.error.HTTPError on non-200 responses.
    """
    return _get(f"/matches/{match_id}")


def is_parsed(match_data: dict) -> bool:
    """Return True if a match has full replay parse data."""
    return match_data.get("version") is not None


def get_player_slot(match_data: dict, account_id: int) -> Optional[int]:
    """Return the player_slot (0-4 Radiant, 128-132 Dire) for account_id."""
    for p in match_data.get("players", []):
        if p.get("account_id") == account_id:
            return p.get("player_slot")
    return None


def is_radiant(player_slot: int) -> bool:
    """Return True if player_slot is on the Radiant team."""
    return player_slot < 128


def teamfight_player_index(player_slot: int) -> int:
    """
    Map player_slot to index in a teamfight's players array.
    Radiant slots 0-4 → indices 0-4
    Dire slots 128-132 → indices 5-9
    """
    if player_slot < 128:
        return player_slot
    return 5 + (player_slot - 128)


def fetch_and_cache(
    match_ids: list[int],
    cache_dir: Path,
    verbose: bool = True,
) -> dict[int, dict]:
    """
    Fetch and locally cache match data.

    Cached matches are stored as {match_id}.json in cache_dir.
    Already-cached matches are loaded from disk without API calls.

    Returns:
        Dict mapping match_id → match_data (only successfully fetched matches).
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: dict[int, dict] = {}

    for match_id in match_ids:
        cache_path = cache_dir / f"{match_id}.json"
        if cache_path.exists():
            with cache_path.open() as f:
                results[match_id] = json.load(f)
            if verbose:
                print(f"  [cache] {match_id}")
            continue

        try:
            data = fetch_match(match_id)
            with cache_path.open("w") as f:
                json.dump(data, f)
            results[match_id] = data
            status = "parsed" if is_parsed(data) else "unscored"
            if verbose:
                print(f"  [fetch] {match_id} — {status}")
        except Exception as e:
            if verbose:
                print(f"  [error] {match_id} — {e}")

    return results
