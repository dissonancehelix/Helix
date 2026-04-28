"""
Spotify Audio Analysis Fetcher
domains/music/model/ingestion/adapters/spotify_audio_analysis.py
===========================================================
Fetches Spotify's /audio-analysis endpoint for a list of track URIs.
Uses only Python stdlib — no spotipy required.

The audio-analysis response contains:
  sections  — structural divisions (start, duration, loudness, tempo, key, mode)
  segments  — fine-grained acoustic events (start, duration, pitches, timbre)
  beats     — beat timestamps
  bars      — bar timestamps

This is the data needed to:
  - Fill collapse_proxy for loop-seam DCP events
  - Measure section boundary sharpness
  - Detect pre-seam tension accumulation

Auth: Client Credentials flow (no user login needed for audio-analysis).

Credentials: set environment variables before running:
  SPOTIFY_CLIENT_ID=<your client id>
  SPOTIFY_CLIENT_SECRET=<your client secret>

Get credentials at: https://developer.spotify.com/dashboard
  → Create an app → copy Client ID and Client Secret

Usage:
  python -m domains.music.ingestion.adapters.spotify_audio_analysis
  (will run against top loop-seam candidates by default)

Rate limits: Spotify allows ~180 req/min on client credentials.
  We add a small delay between requests.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists()
)

CACHE_DIR = ROOT / "domains/music/data/output/library/processed/audio_analysis"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_DELAY = 0.35   # seconds between API calls — safe under rate limit
TOKEN_URL     = "https://accounts.spotify.com/api/token"
ANALYSIS_URL  = "https://api.spotify.com/v1/audio-analysis/{track_id}"


# ─── Auth ─────────────────────────────────────────────────────────────────────

def get_client_token(client_id: str, client_secret: str) -> str:
    """Client Credentials flow — no user login needed."""
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


# ─── Fetch single track analysis ─────────────────────────────────────────────

def fetch_audio_analysis(
    track_uri: str,
    token: str,
    use_cache: bool = True,
) -> Optional[dict]:
    """
    Fetch audio analysis for a single Spotify track URI.
    Caches result to disk so re-runs don't re-fetch.

    Returns the full audio-analysis dict, or None on failure.
    """
    track_id = track_uri.split(":")[-1]
    cache_path = CACHE_DIR / f"{track_id}.json"

    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    url = ANALYSIS_URL.format(track_id=track_id)
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        cache_path.write_text(json.dumps(data), encoding="utf-8")
        return data
    except urllib.error.HTTPError as e:
        if e.code == 429:
            retry_after = int(e.headers.get("Retry-After", 5))
            print(f"    Rate limited — sleeping {retry_after}s")
            time.sleep(retry_after)
            return fetch_audio_analysis(track_uri, token, use_cache)
        print(f"    HTTP {e.code} for {track_id}")
        return None
    except Exception as ex:
        print(f"    Error fetching {track_id}: {ex}")
        return None


# ─── Batch fetch ─────────────────────────────────────────────────────────────

def fetch_batch(
    track_records: list[dict],
    client_id: str,
    client_secret: str,
    use_cache: bool = True,
) -> dict[str, dict]:
    """
    Fetch audio analysis for a list of track records.
    Each record must have a 'track_uri' field.

    Returns: {track_uri: audio_analysis_dict}
    """
    print("Authenticating with Spotify…")
    token = get_client_token(client_id, client_secret)
    print(f"  Token obtained. Fetching {len(track_records)} tracks…")

    results: dict[str, dict] = {}
    for i, rec in enumerate(track_records):
        uri = rec.get("track_uri", "")
        if not uri:
            continue
        track_id = uri.split(":")[-1]
        cache_path = CACHE_DIR / f"{track_id}.json"
        cached = cache_path.exists() and use_cache
        print(f"  [{i+1}/{len(track_records)}] {rec.get('track_name','?')[:40]}"
              f"{'  [cached]' if cached else ''}")
        analysis = fetch_audio_analysis(uri, token, use_cache)
        if analysis:
            results[uri] = analysis
        if not cached:
            time.sleep(REQUEST_DELAY)

    print(f"  Fetched: {len(results)}/{len(track_records)}")
    return results


if __name__ == "__main__":
    client_id     = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.")
        print("Get them at: https://developer.spotify.com/dashboard")
        sys.exit(1)

    # Load top candidates from loop-seam probe
    candidates_path = (
        ROOT / "domains/music/model/outputs/loop_seam_probe/loop_seam_candidates.csv"
    )
    if not candidates_path.exists():
        print(f"Run loop_seam probe first: python -m domains.music.analysis.loop_seam")
        sys.exit(1)

    import csv
    with open(candidates_path, encoding="utf-8") as f:
        top = list(csv.DictReader(f))[:50]  # top 50 by default

    results = fetch_batch(top, client_id, client_secret)
    print(f"\nAudio analysis cached to: {CACHE_DIR}")
    print(f"Next: python -m domains.music.analysis.loop_seam_audio")


