"""
runtime_adapter.py — Runtime plane contract over Beefweb.

Beefweb is a Foobar2000 component that exposes a REST API on localhost:8880.
This adapter wraps the raw BeefwebClient and produces typed RuntimeTrack
records with a stable contract for the bridge.

Critical addition over raw BeefwebClient:
  %path% column is always requested so the bridge can perform identity
  resolution against external-tags.db using the file URI.

Contract rules:
  - Read-only observation layer. Never controls playback.
  - Degrades gracefully when Foobar is not running.
  - NOT a metadata authority — runtime state never overrides canonical tags.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from system.tools.music_pipeline.beefweb_client import BeefwebClient, SIGNAL_COLUMNS

# Add %path% to the column set so identity resolution is possible
_BRIDGE_COLUMNS = ["%path%"] + SIGNAL_COLUMNS


@dataclass
class RuntimeTrack:
    """
    A track as observed in the Foobar runtime via Beefweb.

    file_uri is the key used for identity resolution against external-tags.db.
    All other fields are live runtime values — not canonical metadata.
    """
    playback_state: str         # "playing" | "paused" | "stopped"
    file_uri: str               # foobar file:// URI — identity resolution key
    file_path: str              # Windows path form of the URI
    title: str
    artist: str
    album: str
    track_number: str
    position_s: Optional[float]
    duration_s: Optional[float]
    # Playlist context
    playlist_id: Optional[str] = None
    playlist_index: Optional[int] = None
    index: Optional[int] = None
    # Signal fields (from active plugins — may be empty strings if plugins absent)
    local_playcount: Optional[int] = None
    local_loved: Optional[bool] = None
    first_played: Optional[str] = None
    last_played: Optional[str] = None
    play_counter: Optional[int] = None

    @property
    def is_playing(self) -> bool:
        return self.playback_state == "playing"

    @property
    def is_paused(self) -> bool:
        return self.playback_state == "paused"

    @property
    def progress_pct(self) -> Optional[float]:
        if self.position_s and self.duration_s and self.duration_s > 0:
            return round(self.position_s / self.duration_s * 100, 1)
        return None


@dataclass
class RuntimeState:
    """Top-level runtime state. Track is None when stopped."""
    is_live: bool               # True if Beefweb is reachable
    playback_state: str         # "playing" | "paused" | "stopped" | "offline"
    track: Optional[RuntimeTrack]
    active_playlist_id: Optional[str] = None
    active_playlist_name: Optional[str] = None


class RuntimeAdapter:
    """
    Read-only interface to the Foobar2000 runtime via Beefweb.

    Usage:
        adapter = RuntimeAdapter()
        state = adapter.state()
        if state.track:
            print(state.track.file_uri)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8880",
        timeout: float = 2.0,
        username: str = None,
        password: str = None,
    ) -> None:
        self._client = BeefwebClient(base_url=base_url, timeout=timeout,
                                     username=username, password=password)

    def is_live(self) -> bool:
        """Return True if Beefweb is reachable (Foobar is running)."""
        return self._client.is_reachable()

    def state(self) -> RuntimeState:
        """
        Return the current runtime state.
        Always returns a valid RuntimeState — never raises.
        """
        cols = ",".join(_BRIDGE_COLUMNS)
        result = self._client._get("/api/player", params={"columns": cols})

        if result is None:
            return RuntimeState(is_live=False, playback_state="offline", track=None)

        player = result.get("player", {})
        pb_state = player.get("playbackState", "stopped")

        playlists = self.playlists()
        active_playlist_id = None
        active_playlist_name = None
        active_playlist_is_playing = False
        
        for pl in playlists:
            if pl.get("isCurrent", False):
                active_playlist_id = pl.get("id")
                active_playlist_name = pl.get("title")
            if pl.get("isPlayback", False):
                active_playlist_is_playing = True

        active = player.get("activeItem", {})
        if not active_playlist_id:
            active_playlist_id = active.get("playlistId")

        if pb_state == "stopped":
            return RuntimeState(
                is_live=True, 
                playback_state="stopped", 
                track=None,
                active_playlist_id=active_playlist_id,
                active_playlist_name=active_playlist_name
            )

        columns = active.get("columns", [])
        col_map = {_BRIDGE_COLUMNS[i]: columns[i]
                   for i in range(min(len(_BRIDGE_COLUMNS), len(columns)))}

        raw_path = col_map.get("%path%", "")
        file_uri = _path_to_uri(raw_path)

        track = RuntimeTrack(
            playback_state=pb_state,
            file_uri=file_uri,
            file_path=raw_path,
            title=col_map.get("%title%", ""),
            artist=col_map.get("%artist%", ""),
            album=col_map.get("%album%", ""),
            track_number=col_map.get("%tracknumber%", ""),
            position_s=active.get("position"),
            duration_s=active.get("duration"),
            playlist_id=active_playlist_id,
            playlist_index=active.get("playlistIndex"),
            index=active.get("index"),
            local_playcount=_parse_int(col_map.get("%play_count%")),
            local_loved=_parse_bool(col_map.get("%2003_loved%")),
            first_played=col_map.get("%first_played%") or None,
            last_played=col_map.get("%last_played%") or None,
            play_counter=_parse_int(col_map.get("%play_counter%")),
        )
        return RuntimeState(
            is_live=True, 
            playback_state=pb_state, 
            track=track,
            active_playlist_id=active_playlist_id,
            active_playlist_name=active_playlist_name
        )

    def now_playing(self) -> Optional[RuntimeTrack]:
        """Return the currently playing track, or None if stopped/offline."""
        s = self.state()
        return s.track if s.track and s.playback_state in ("playing", "paused") else None

    def get_selection(self) -> Optional[RuntimeTrack]:
        """Return the first selected track in the active (browsed) playlist."""
        playlists = self.playlists()
        current_pl_id = next((p["id"] for p in playlists if p.get("isCurrent")), None)
        if not current_pl_id:
             return None
             
        cols = ",".join(_BRIDGE_COLUMNS)
        items = self._client._get(f"/api/playlists/{current_pl_id}/items/0:100", params={"columns": cols})
        if not items or "playlistItems" not in items:
            return None
            
        for item in items["playlistItems"].get("items", []):
            if item.get("selected"):
                cols_data = item.get("columns", [])
                col_map = {_BRIDGE_COLUMNS[i]: cols_data[i]
                           for i in range(min(len(_BRIDGE_COLUMNS), len(cols_data)))}
                
                raw_path = col_map.get("%path%", "")
                return RuntimeTrack(
                    playback_state="stopped", # Selection context is static
                    file_uri=_path_to_uri(raw_path),
                    file_path=raw_path,
                    title=col_map.get("%title%", ""),
                    artist=col_map.get("%artist%", ""),
                    album=col_map.get("%album%", ""),
                    track_number=col_map.get("%tracknumber%", ""),
                    position_s=None,
                    duration_s=None,
                    playlist_id=current_pl_id,
                    playlist_index=item.get("playlistIndex"),
                    index=item.get("index"),
                    local_playcount=_parse_int(col_map.get("%play_count%")),
                    local_loved=_parse_bool(col_map.get("%2003_loved%")),
                )
        return None

    def get_active_playlist_tracks(self) -> list[RuntimeTrack]:
        """Return all tracks in the currently browsed playlist."""
        playlists = self.playlists()
        current_pl_id = next((p["id"] for p in playlists if p.get("isCurrent")), None)
        if not current_pl_id:
             return []
             
        cols = ",".join(_BRIDGE_COLUMNS)
        items = self._client._get(f"/api/playlists/{current_pl_id}/items/0:1000", params={"columns": cols})
        if not items or "playlistItems" not in items:
            return []
            
        tracks = []
        for item in items["playlistItems"].get("items", []):
            cols_data = item.get("columns", [])
            col_map = {_BRIDGE_COLUMNS[i]: cols_data[i]
                       for i in range(min(len(_BRIDGE_COLUMNS), len(cols_data)))}
            tracks.append(RuntimeTrack(
                playback_state="stopped",
                file_uri=_path_to_uri(col_map.get("%path%", "")),
                file_path=col_map.get("%path%", ""),
                title=col_map.get("%title%", ""),
                artist=col_map.get("%artist%", ""),
                album=col_map.get("%album%", ""),
                track_number=col_map.get("%tracknumber%", ""),
                position_s=None,
                duration_s=None,
                playlist_id=current_pl_id,
                playlist_index=item.get("playlistIndex"),
                index=item.get("index")
            ))
        return tracks

    def playlists(self) -> list[dict]:
        """Return raw playlist list from Beefweb."""
        return self._client.playlists()

    def create_playlist(self, title: str) -> Optional[str]:
        """Create a new playlist and return its ID."""
        result = self._client._post("/api/playlists/add", body={"title": title, "index": 100})
        if result:
            # We might need to find its ID as Beefweb sometimes returns empty or partial
            pls = self.playlists()
            for p in pls:
                if p["title"] == title:
                    return p["id"]
        return None

    def add_playlist_items(self, playlist_id: str, file_uris: list[str]) -> bool:
        """Add multiple tracks to a playlist by URI."""
        if not file_uris:
            return True
        # Beefweb expects paths in the add request
        paths = [_uri_to_path(u) for u in file_uris]
        result = self._client._post(f"/api/playlists/{playlist_id}/items/add", body={"items": paths})
        return result is not None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _path_to_uri(path: str) -> str:
    if path.startswith("file://"):
        return path.replace("\\", "/")
    p = path.replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    return f"file://{p}"


def _uri_to_path(uri: str) -> str:
    if not uri.startswith("file://"):
        return uri
    # file:///C:/path -> C:\path
    p = uri.replace("file://", "")
    if p.startswith("/"):
        p = p[1:]
    return p.replace("/", "\\")


def _parse_int(s) -> Optional[int]:
    if s is None:
        return None
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return None


def _parse_bool(s) -> Optional[bool]:
    if s is None:
        return None
    sv = str(s).strip().lower()
    if sv in ("1", "true", "yes", "loved"):
        return True
    if sv in ("0", "false", "no", ""):
        return False
    return None

