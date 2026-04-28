"""
SteamSpy API client with local file cache.
Fetches tag metadata for games — no API key required.
Rate limit: ~1 req/sec per SteamSpy guidelines.
"""
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT / "data" / "derived" / "games_pipeline" / "steamspy_cache"
STEAMSPY_BASE = "https://steamspy.com/api.php"


def _get(params: dict, retries: int = 3) -> dict:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{STEAMSPY_BASE}?{query}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HelixGamesIngest/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"[steamspy] Failed {url}: {e}")
                return {}
        except Exception as e:
            print(f"[steamspy] Unexpected error: {e}")
            return {}
    return {}


def get_app_details(appid: str | int, use_cache: bool = True) -> dict:
    """Fetch tag and metadata for a single appid. Caches to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{appid}.json"

    if use_cache and cache_file.exists():
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    data = _get({"request": "appdetails", "appid": str(appid)})
    if data:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    time.sleep(1.0)  # respect rate limit
    return data


def get_all_games(page: int = 0) -> dict:
    """Fetch a page of all Steam games from SteamSpy (~1000 per page)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"_all_page_{page}.json"

    if cache_file.exists():
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    data = _get({"request": "all", "page": str(page)})
    if data:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    time.sleep(1.0)
    return data


def enrich_library(
    library: list[dict],
    overrides: dict | None = None,
    verbose: bool = True,
) -> list[dict]:
    """
    Adds SteamSpy tags to each game in the library.
    library: list of dicts with at least 'appid' and 'playtime_forever_min'.
    overrides: dict with 'substitute' {appid -> appid} and 'skip' [appid, ...]
    Returns enriched list — skips games with 0 playtime.
    """
    substitute = {str(k): str(v) for k, v in (overrides or {}).get("substitute", {}).items()}
    skip = {str(a) for a in (overrides or {}).get("skip", [])}

    played = [g for g in library if g.get("playtime_forever_min", 0) > 0]
    total = len(played)
    enriched = []

    for i, game in enumerate(played):
        appid = str(game["appid"])

        if appid in skip:
            if verbose:
                print(f"  [{i+1}/{total}] SKIP {game.get('name', appid)}")
            continue

        lookup_appid = substitute.get(appid, appid)
        label = game.get("name", appid)
        if lookup_appid != appid:
            label += f" [tags from appid {lookup_appid}]"

        if verbose:
            print(f"  [{i+1}/{total}] {label}", end="\r", flush=True)

        details = get_app_details(lookup_appid)
        tags = details.get("tags", {})
        positive = details.get("positive", 0)
        negative = details.get("negative", 0)
        total_reviews = positive + negative
        review_ratio = positive / total_reviews if total_reviews > 0 else None

        enriched.append({
            **game,
            "tags": tags,
            "tags_source_appid": lookup_appid,
            "review_ratio": review_ratio,
            "total_reviews": total_reviews,
            "genre": details.get("genre", ""),
            "developer": details.get("developer", ""),
            "publisher": details.get("publisher", ""),
            "price": details.get("price", ""),
            "initialprice": details.get("initialprice", ""),
        })

    if verbose:
        print(f"\n  Done. Enriched {len(enriched)} games.")
    return enriched
