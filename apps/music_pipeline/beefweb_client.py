"""
beefweb_client.py — Beefweb Remote Control REST API client.

Beefweb is installed as a Foobar2000 plugin that exposes a REST API
for external control and state inspection.

Default address: http://localhost:8880

Role in Helix:
  - External runtime/API/control layer
  - Current playback state: what is playing NOW
  - Playlist/queue inspection
  - Future: Helix runtime dashboards, session-aware signal enrichment
  - NOT a metadata authority — never overrides canonical tags

Endpoints used:
  GET /api/player                  — current playback state
  GET /api/playlists               — list of playlists
  GET /api/playlist/{id}/items/{range}?columns={cols}
                                   — playlist items with metadata columns
  GET /api/query                   — combined state query

All calls have a configurable timeout (default 2s).
If Foobar is not running or Beefweb is not active, all methods
return None/empty gracefully without raising.

Beefweb column IDs (Foobar title formatting expressions):
  %title%       track title
  %artist%      artist
  %album%       album
  %tracknumber% track number
  %length%      duration string
  %play_count%  Playcount 2003 counter (if plugin active)
  %2003_loved%  Playcount 2003 loved state
  %first_played%  EPS first play timestamp
  %last_played%   EPS last play timestamp
  %play_counter%  EPS play counter
  $meta(PLAYED_TIMES,0)  EPS played times (multi-value — first value only)
"""
from __future__ import annotations

import base64
import json
from typing import Any, Optional
from urllib.error import URLError
from urllib.request import urlopen, Request

_DEFAULT_BASE = "http://localhost:8880"

_DEFAULT_TIMEOUT = 2   # seconds — short; Foobar may not be running

# Beefweb column expressions for signal-relevant fields
SIGNAL_COLUMNS = [
    "%title%",
    "%artist%",
    "%album%",
    "%tracknumber%",
    "%length%",
    "%play_count%",      # Playcount 2003
    "%2003_loved%",      # Playcount 2003 loved
    "%first_played%",    # Enhanced Playback Statistics
    "%last_played%",     # Enhanced Playback Statistics
    "%play_counter%",    # Enhanced Playback Statistics
    "$meta(PLAYED_TIMES,0)",  # EPS first timestamp (multi-value)
]


class BeefwebClient:
    """
    Thin REST client for Beefweb Remote Control.

    All methods degrade gracefully when Foobar is not running.
    Never raises on connection failure — returns None/empty instead.
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE,
        timeout:  float = _DEFAULT_TIMEOUT,
        username: str = None,
        password: str = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout
        self._auth_header: Optional[str] = None
        if username and password:
            credentials = base64.b64encode(
                f"{username}:{password}".encode("utf-8")
            ).decode("ascii")
            self._auth_header = f"Basic {credentials}"

    def _get(self, path: str, params: dict = None) -> Optional[Any]:
        """Make a GET request. Returns parsed JSON or None on failure."""
        return self._request("GET", path, params=params)

    def _post(self, path: str, body: dict = None, params: dict = None) -> Optional[Any]:
        """Make a POST request. Returns parsed JSON or None on failure."""
        return self._request("POST", path, body=body, params=params)

    def _delete(self, path: str, params: dict = None) -> Optional[Any]:
        """Make a DELETE request. Returns parsed JSON or None on failure."""
        return self._request("DELETE", path, params=params)

    def _request(self, method: str, path: str, body: dict = None, params: dict = None) -> Optional[Any]:
        """Generic request handler."""
        url = f"{self.base_url}{path}"
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"
        try:
            headers = {"Accept": "application/json"}
            if self._auth_header:
                headers["Authorization"] = self._auth_header
            
            data = None
            if body is not None:
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"
                
            req = Request(url, data=data, headers=headers, method=method)
            # Use urlopen to perform the request
            with urlopen(req, timeout=self.timeout) as resp:
                status = resp.getcode()
                if 200 <= status < 300:
                    content = resp.read().decode("utf-8")
                    return json.loads(content) if content else {}
                return None
        except (URLError, OSError, json.JSONDecodeError):
            return None

    def is_reachable(self) -> bool:
        """Return True if Beefweb is running and reachable."""
        return self._get("/api/player") is not None

    def player_state(self) -> Optional[dict]:
        """
        Return current player state.

        Result shape (when Foobar is running):
        {
          "player": {
            "playbackState": "playing" | "paused" | "stopped",
            "activeItem": {
              "playlistId": str,
              "playlistIndex": int,
              "index": int,
              "position": float,   # seconds
              "duration": float,   # seconds
              "columns": [...],    # parallel to requested columns
            },
            "volume": {...},
          }
        }
        """
        return self._get("/api/player")

    def now_playing(self) -> Optional[dict]:
        """
        Return enriched now-playing record with signal columns.

        Requests signal-relevant columns so the response includes
        Playcount 2003 and EPS fields for the currently-playing track.
        """
        cols = ",".join(SIGNAL_COLUMNS)
        result = self._get("/api/player", params={"columns": cols})
        if not result:
            return None

        player = result.get("player", {})
        state  = player.get("playbackState", "stopped")
        if state == "stopped":
            return {"state": "stopped"}

        active = player.get("activeItem", {})
        columns = active.get("columns", [])

        # Map column values to names
        col_map = {}
        for i, col_expr in enumerate(SIGNAL_COLUMNS):
            if i < len(columns):
                col_map[col_expr] = columns[i]

        return {
            "state":          state,
            "position_s":     active.get("position"),
            "duration_s":     active.get("duration"),
            "title":          col_map.get("%title%"),
            "artist":         col_map.get("%artist%"),
            "album":          col_map.get("%album%"),
            "track_number":   col_map.get("%tracknumber%"),
            # Playcount 2003
            "local_playcount": _parse_int(col_map.get("%play_count%")),
            "local_loved":     _parse_bool(col_map.get("%2003_loved%")),
            # Enhanced Playback Statistics
            "first_played":    col_map.get("%first_played%"),
            "last_played":     col_map.get("%last_played%"),
            "play_counter":    _parse_int(col_map.get("%play_counter%")),
            "played_times_first": col_map.get("$meta(PLAYED_TIMES,0)"),
        }

    def playlists(self) -> list[dict]:
        """Return list of playlists with id, title, track count."""
        result = self._get("/api/playlists")
        if not result:
            return []
        return result.get("playlists", [])

    def playlist_items(
        self,
        playlist_id: str,
        offset: int = 0,
        count: int = 100,
        columns: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Return items from a playlist with requested columns.
        Returns list of {columns: [...], index: int}.
        """
        cols = ",".join(columns or SIGNAL_COLUMNS)
        path = f"/api/playlist/{playlist_id}/items/{offset}:{count}"
        result = self._get(path, params={"columns": cols})
        if not result:
            return []

        items = result.get("playlistItems", {}).get("items", [])
        col_names = columns or SIGNAL_COLUMNS
        out = []
        for item in items:
            vals = item.get("columns", [])
            col_map = {col_names[i]: vals[i] for i in range(min(len(col_names), len(vals)))}
            out.append({"index": item.get("index"), **col_map})
        return out

    def active_playlist_signals(self, max_items: int = 1000) -> list[dict]:
        """
        Return signal columns for all items in the active playlist.
        Useful for building a session-level signal snapshot.
        """
        pls = self.playlists()
        if not pls:
            return []

        # Find the active playlist (isCurrent=True)
        active = next((p for p in pls if p.get("isCurrent")), pls[0] if pls else None)
        if not active:
            return []

        return self.playlist_items(
            playlist_id=active["id"],
            count=min(max_items, active.get("itemCount", max_items)),
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_int(s: Any) -> Optional[int]:
    if s is None:
        return None
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return None


def _parse_bool(s: Any) -> Optional[bool]:
    if s is None:
        return None
    sv = str(s).strip().lower()
    if sv in ("1", "true", "yes", "loved"):
        return True
    if sv in ("0", "false", "no", ""):
        return False
    return None
