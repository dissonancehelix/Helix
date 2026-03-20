"""
Stage 2 — Metadata normalization
==================================
Reads chip-format files (VGM/SPC/NSF/etc.) at the static parse level.
Combines internal header data with external APEv2 .tag sidecars to
produce a canonical metadata record per track.

Sidecar fields take priority over internal metadata for chip formats:
  Sound chip, Platform, Franchise, Sound Team, Featuring

Delegates to MasterPipeline stage:
  3 (tier_a_parse) — static parse of chip register headers
"""
import json
from pathlib import Path
from typing import Any

def normalize_foobar_metadata(tags: dict[str, Any]) -> dict[str, Any]:
    """Phase 13 — Metadata Normalization"""
    normalized = {
        "track": {
            "title": tags.get("Title", ""),
            "featuring_artist": tags.get("Featuring", ""),
            "number": tags.get("Track Number", ""),
            "notes": tags.get("Comment", "")
        },
        "artist": {
            "name": tags.get("Artist", ""),
            "associated_genres": [tags.get("Genre", "")] if tags.get("Genre") else [],
            "alias": tags.get("Sound Team", "")
        },
        "album": {
            "title": tags.get("Album", ""),
            "release_year": tags.get("Date", ""),
            "artist": tags.get("Album Artist", ""),
            "disc_number": tags.get("Disc Number", "")
        },
        "game": {
            "franchise": tags.get("Franchise", "")
        },
        "platform": {
            "name": tags.get("Platform", "")
        },
        "sound_chip": {
            "name": tags.get("Sound Chip", "")
        }
    }
    return normalized

def parse_chip_header(header_data: dict[str, Any]) -> dict[str, Any]:
    """Phase 14 — Chip Header Metadata Ingestion"""
    parsed = {
        "sound_chip": {
            "name": header_data.get("ACCURATE_CHIP_NAME") or header_data.get("CHIP_NAME", ""),
            "clock_rate": header_data.get("YM2612_CLOCK_RATE") or header_data.get("SEGA_PSG_CLOCK_RATE", 0)
        },
        "track_playback": {
            "loop_samples": header_data.get("VGM_LOOP_SAMPLES", 0),
            "song_samples": header_data.get("VGM_SONG_SAMPLES", 0),
            "recorded_rate": header_data.get("VGM_RECORDED_RATE", 44100),
            "vgm_version": header_data.get("VGM_VERSION", "")
        }
    }
    return parsed

def process_file_metadata(file_path: Path, raw_tags: dict, raw_header: dict) -> dict:
    """Combines normalized foobar tags and chip header metadata."""
    metadata = normalize_foobar_metadata(raw_tags)
    chip_data = parse_chip_header(raw_header)
    
    # Merge chip data into metadata
    if chip_data["sound_chip"].get("name"):
        metadata["sound_chip"]["name"] = chip_data["sound_chip"]["name"]
    if chip_data["sound_chip"].get("clock_rate"):
        metadata["sound_chip"]["clock_rate"] = chip_data["sound_chip"]["clock_rate"]
        
    metadata["track"].update(chip_data["track_playback"])
    
    return metadata

