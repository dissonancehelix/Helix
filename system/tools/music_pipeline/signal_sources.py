"""
signal_sources.py — Per-source signal adapters for Phase 6 Part A.

Source model (Phase 6, revised 2026-03-29):
  PlaycountSource        Playcount 2003 JSON export
  LastFmSignalSource     Last.fm scrobble JSON history
  ListenBrainzSource     ListenBrainz history (JSON export or API)
  BeefwebSource          Beefweb live runtime state (interface only)

Enhanced Playback Statistics is NOT in scope.

Playcount 2003 JSON schema (export from Foobar plugin):
  {
    "2003_added":        int   (Unix seconds — when added to Foobar library)
    "2003_first_played": int   (Unix seconds — first play)
    "2003_last_played":  int   (Unix seconds — most recent play)
    "2003_loved":        int   (0 or 1)
    "2003_playcount":    int   (total play count)
    "id":                str   (file path + "|0" subsong index)
  }

Last.fm JSON schema (lastfm_dissident93.json):
  { "username": str, "scrobbles": [{"track", "artist", "album", "albumId", "date"}] }
  date is Unix milliseconds.

ListenBrainz schema (listenbrainz_dissident93.json — when available):
  {"username": str, "listens": [{"track_metadata": {...}, "listened_at": int}]}
  listened_at is Unix seconds.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]

_DATASETS = _REPO_ROOT / "domains" / "music" / "data" / "metadata"

_PC2003_PATH    = _DATASETS / "2003_playcount.json"
_LASTFM_PATH    = _DATASETS / "lastfm_dissident93.json"
_LB_PATH        = _DATASETS / "listenbrainz_dissident93.json"
_FIELD_INDEX    = _REPO_ROOT / "codex" / "library" / "music" / ".field_index.json"

# ── Normalization ─────────────────────────────────────────────────────────────

_ART_RE   = re.compile(r"^(the |a |an )", re.I)
_PUNCT_RE = re.compile(r"[^\w\s]")
_SPACE_RE = re.compile(r"\s+")


def _nk(s: str) -> str:
    """Normalize string for fuzzy key matching (same algorithm as staging.norm_key)."""
    if not s:
        return ""
    s = s.lower().strip()
    s = _ART_RE.sub("", s)
    s = _PUNCT_RE.sub(" ", s)
    s = _SPACE_RE.sub(" ", s).strip()
    return s


TrackKey = tuple[str, str, str]  # (artist_key, album_key, title_key)

_S_TO_MS = 1000  # convert Unix seconds → ms


# ── Playcount 2003 source ─────────────────────────────────────────────────────

class PlaycountSource:
    """
    Loads the Playcount 2003 JSON export.

    The export is keyed by file path (id field = path + "|0").
    We match against the field index source_map to resolve track_ids.

    Provides:
      local_playcount      — 2003_playcount
      local_loved          — 2003_loved (bool)
      local_first_played   — 2003_first_played (Unix ms)
      local_last_played    — 2003_last_played (Unix ms)
      local_added          — 2003_added (Unix ms)
    """

    def __init__(self, json_path: Path = _PC2003_PATH) -> None:
        self._json_path = json_path
        self._by_path: Optional[dict[str, dict]] = None

    def _load(self) -> dict[str, dict]:
        if self._by_path is not None:
            return self._by_path
        if not self._json_path.exists():
            self._by_path = {}
            return self._by_path

        raw = json.loads(self._json_path.read_text(encoding="utf-8"))
        index: dict[str, dict] = {}
        for entry in raw:
            raw_id = entry.get("id", "")
            # Strip the "|0" subsong suffix and normalize path separator
            path = raw_id.split("|")[0].replace("\\", "/").lower()
            index[path] = {
                "local_playcount":    entry.get("2003_playcount"),
                "local_loved":        bool(entry.get("2003_loved")),
                "local_first_played": (entry["2003_first_played"] * _S_TO_MS
                                       if entry.get("2003_first_played") else None),
                "local_last_played":  (entry["2003_last_played"] * _S_TO_MS
                                       if entry.get("2003_last_played") else None),
                "local_added":        (entry["2003_added"] * _S_TO_MS
                                       if entry.get("2003_added") else None),
            }
        self._by_path = index
        return self._by_path

    def get_by_path(self, file_path: str) -> Optional[dict]:
        """Look up signal data for a file path string."""
        norm = file_path.replace("\\", "/").lower()
        return self._load().get(norm)

    def total_entries(self) -> int:
        return len(self._load())

    def loved_count(self) -> int:
        return sum(1 for v in self._load().values() if v["local_loved"])

    def iter_all(self) -> Iterator[tuple[str, dict]]:
        """Yield (normalized_file_path, signal_dict) for all entries."""
        yield from self._load().items()


# ── Last.fm signal source ──────────────────────────────────────────────────────

class LastFmSignalSource:
    """
    Loads Last.fm scrobble JSON and indexes by (artist_key, album_key, track_key).

    Per-track output:
      lastfm_playcount      total scrobble count
      lastfm_first_played   first scrobble (Unix ms)
      lastfm_last_played    most recent scrobble (Unix ms)
    """

    def __init__(self, json_path: Path = _LASTFM_PATH) -> None:
        self._json_path = json_path
        self._index: Optional[dict[TrackKey, dict]] = None

    def _build(self) -> None:
        if self._index is not None:
            return
        if not self._json_path.exists():
            self._index = {}
            return

        raw = json.loads(self._json_path.read_text(encoding="utf-8"))
        scrobbles = raw.get("scrobbles", [])

        groups: dict[TrackKey, list[int]] = defaultdict(list)
        meta:   dict[TrackKey, dict]      = {}

        for s in scrobbles:
            ak  = _nk(s.get("artist", ""))
            alk = _nk(s.get("album",  ""))
            tk  = _nk(s.get("track",  ""))
            ts  = s.get("date", 0)
            if not ak and not tk:
                continue
            key = (ak, alk, tk)
            groups[key].append(ts)
            if key not in meta:
                meta[key] = {
                    "artist": s.get("artist", ""),
                    "album":  s.get("album", ""),
                    "track":  s.get("track", ""),
                }

        self._index = {}
        for key, timestamps in groups.items():
            timestamps.sort()
            self._index[key] = {
                **meta[key],
                "lastfm_playcount":    len(timestamps),
                "lastfm_first_played": timestamps[0]  if timestamps else None,
                "lastfm_last_played":  timestamps[-1] if timestamps else None,
            }

    def get(self, artist_key: str, album_key: str, title_key: str) -> Optional[dict]:
        self._build()
        return self._index.get((artist_key, album_key, title_key))

    def total_scrobbles(self) -> int:
        if not self._json_path.exists():
            return 0
        raw = json.loads(self._json_path.read_text(encoding="utf-8"))
        return len(raw.get("scrobbles", []))

    def unique_track_count(self) -> int:
        self._build()
        return len(self._index)

    def top_tracks(self, n: int = 100) -> list[dict]:
        self._build()
        return sorted(
            [{"key": k, **v} for k, v in self._index.items()],
            key=lambda x: -x["lastfm_playcount"],
        )[:n]


# ── ListenBrainz source ───────────────────────────────────────────────────────

class ListenBrainzSource:
    """
    ListenBrainz history adapter.

    Reads from:
    1. Local JSON export: model/domains/music/data/music/metadata/listenbrainz_dissident93.json
    2. ListenBrainz public API: https://api.listenbrainz.org/1/user/{username}/listens
       (no authentication required for public users)

    ListenBrainz JSON export schema:
      {
        "username": str,
        "listens": [
          {
            "listened_at": int,       # Unix seconds
            "track_metadata": {
              "track_name": str,
              "artist_name": str,
              "release_name": str,    # album
              "additional_info": {
                "recording_mbid": str,
                ...
              }
            }
          }
        ]
      }

    API response schema (paginated):
      GET /1/user/{username}/listens?count=100&max_ts={ts}
      → { "payload": { "listens": [...], "count": int, "latest_listen_ts": int } }

    Per-track output:
      listenbrainz_listen_count
      listenbrainz_first_listen    (Unix ms)
      listenbrainz_last_listen     (Unix ms)
    """

    _API_BASE = "https://api.listenbrainz.org"
    _API_TIMEOUT = 10

    def __init__(
        self,
        json_path: Path = _LB_PATH,
        username:  str  = "dissident93",
    ) -> None:
        self._json_path = json_path
        self._username  = username
        self._index: Optional[dict[TrackKey, dict]] = None

    def _build_from_listens(self, listens: list[dict]) -> None:
        groups: dict[TrackKey, list[int]] = defaultdict(list)
        meta:   dict[TrackKey, dict]      = {}

        for entry in listens:
            ts   = entry.get("listened_at", 0)
            meta_block = entry.get("track_metadata", {})
            ak   = _nk(meta_block.get("artist_name", ""))
            alk  = _nk(meta_block.get("release_name", ""))
            tk   = _nk(meta_block.get("track_name", ""))
            if not ak and not tk:
                continue
            key = (ak, alk, tk)
            groups[key].append(ts * _S_TO_MS)  # seconds → ms
            if key not in meta:
                meta[key] = {
                    "artist": meta_block.get("artist_name", ""),
                    "album":  meta_block.get("release_name", ""),
                    "track":  meta_block.get("track_name", ""),
                }

        self._index = {}
        for key, timestamps in groups.items():
            timestamps.sort()
            self._index[key] = {
                **meta[key],
                "listenbrainz_listen_count": len(timestamps),
                "listenbrainz_first_listen": timestamps[0]  if timestamps else None,
                "listenbrainz_last_listen":  timestamps[-1] if timestamps else None,
            }

    def _build(self) -> None:
        if self._index is not None:
            return

        # Try local JSON export first
        if self._json_path.exists():
            raw     = json.loads(self._json_path.read_text(encoding="utf-8"))
            listens = raw.get("listens", raw.get("payload", {}).get("listens", []))
            if listens:
                self._build_from_listens(listens)
                return

        # Try public API (requires network access)
        listens = self._fetch_from_api()
        if listens:
            self._build_from_listens(listens)
        else:
            self._index = {}

    def _fetch_from_api(self) -> list[dict]:
        """Fetch all listens from the ListenBrainz public API."""
        from urllib.request import urlopen, Request
        from urllib.error import URLError

        all_listens = []
        max_ts      = None
        url_base    = f"{self._API_BASE}/1/user/{self._username}/listens"

        for _ in range(1000):  # safety cap — each page = 100 listens
            params = "?count=100"
            if max_ts:
                params += f"&max_ts={max_ts}"
            url = url_base + params

            try:
                req  = Request(url, headers={"Accept": "application/json"})
                resp = urlopen(req, timeout=self._API_TIMEOUT)
                data = json.loads(resp.read().decode("utf-8"))
            except (URLError, OSError, json.JSONDecodeError):
                break

            payload = data.get("payload", {})
            page    = payload.get("listens", [])
            if not page:
                break

            all_listens.extend(page)

            # Advance cursor
            oldest_ts = min(e.get("listened_at", 0) for e in page)
            if oldest_ts >= (max_ts or oldest_ts + 1):
                break  # not making progress
            max_ts = oldest_ts - 1

            if len(page) < 100:
                break  # last page

        return all_listens

    def get(self, artist_key: str, album_key: str, title_key: str) -> Optional[dict]:
        self._build()
        return self._index.get((artist_key, album_key, title_key))

    def is_available(self) -> bool:
        """True if local export exists or API is reachable."""
        if self._json_path.exists():
            return True
        # Quick API check
        from urllib.request import urlopen, Request
        from urllib.error import URLError
        try:
            url = f"{self._API_BASE}/1/user/{self._username}/listen-count"
            req = Request(url, headers={"Accept": "application/json"})
            urlopen(req, timeout=3)
            return True
        except (URLError, OSError):
            return False

    def total_listens(self) -> int:
        self._build()
        return sum(v["listenbrainz_listen_count"] for v in self._index.values()) if self._index else 0

    def unique_track_count(self) -> int:
        self._build()
        return len(self._index) if self._index else 0

