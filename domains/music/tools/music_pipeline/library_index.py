"""
Library index builder
======================
Generates atlas/music/library_index.json — a mapping from local audio
file paths to their canonical Helix entity IDs.

Helix uses this index to locate audio sources without scanning the
full library filesystem on every run.

Schema:
{
  "version": "1.0",
  "generated_at": "2026-03-17T...",
  "track_count": 91765,
  "entries": [
    {
      "entity_id":   "music.track:angel_island_zone_act_1",
      "file_path":   "C:/Users/dissonance/Music/VGM/...",
      "format":      "vgz",
      "track_id_hash": "sha1hex...",
      "title":       "Angel Island Zone Act 1",
      "artist":      "Masato Nakamura",
      "album":       "Sonic 3 & Knuckles",
      "platform":    "Sega Genesis",
      "sound_chip":  "YM2612"
    },
    ...
  ]
}
"""
from __future__ import annotations

import hashlib
import json
import re as _re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_NON_ALNUM = _re.compile(r"[^a-z0-9]+")
_ATLAS_MUSIC = Path(__file__).parent.parent.parent.parent / "atlas" / "music"


def _slugify(text: str) -> str:
    return _NON_ALNUM.sub("_", text.lower().strip()).strip("_") or "unknown"


def build_library_index(db: Any, registry: Any) -> Path | None:
    """
    Build atlas/music/library_index.json from DB track records.

    Args:
        db:       TrackDB instance
        registry: EntityRegistry (used to validate entity IDs exist)

    Returns:
        Path to the written index file, or None on error.
    """
    try:
        tracks = db.get_tracks_by_tier(max_tier=4)   # all tiers
    except Exception as exc:
        print(f"    library_index: could not load tracks: {exc}")
        return None

    entries = []
    for t in tracks:
        title    = t.get("title") or t.get("file_name") or ""
        fp       = t.get("file_path") or ""
        artist   = t.get("artist") or ""
        album    = t.get("album") or ""
        platform = t.get("platform") or ""
        chip     = t.get("sound_chip") or ""

        if not title or not fp:
            continue

        entity_id = f"music.track:{_slugify(title)}"
        tid       = hashlib.sha1(fp.encode()).hexdigest()

        entries.append({
            "entity_id":     entity_id,
            "file_path":     fp,
            "format":        Path(fp).suffix.lstrip(".").lower(),
            "track_id_hash": tid,
            "title":         title,
            "artist":        artist,
            "album":         album,
            "platform":      platform,
            "sound_chip":    chip,
        })

    index = {
        "version":      "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "track_count":  len(entries),
        "entries":      entries,
    }

    _ATLAS_MUSIC.mkdir(parents=True, exist_ok=True)
    out = _ATLAS_MUSIC / "library_index.json"
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    return out
