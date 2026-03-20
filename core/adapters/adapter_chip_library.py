"""
adapter_chip_library.py — Helix adapter for the Sound Chip JSON Library
======================================================================
Tier A: Pure Python — no compilation required.

Purpose:
    Provide a unified programmatic interface to the Sound Chip JSON library.
    Allows other adapters (vgmfile, chiptext, etc.) to fetch hardware
    specifications, analysis notes, and invariant links.

Output:
    Structured dict of chip properties derived from codex/library/audio/chips/*.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Global base path for the library
CHIPS_BASE_PATH = Path(r"c:\Users\dissonance\Desktop\Helix\core\library\audio\chips")

class ChipLibrary:
    """Singleton-style interface to the chip library."""
    _cache: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_chip(cls, chip_id: str) -> dict[str, Any] | None:
        """
        Fetch chip data by ID or filename.
        Example: get_chip("ym2612") or get_chip("music.chip.ym2612")
        """
        # Clean ID (strip prefix if present)
        clean_id = chip_id.replace("music.chip.", "")
        
        if clean_id in cls._cache:
            return cls._cache[clean_id]
            
        json_path = CHIPS_BASE_PATH / f"{clean_id}.json"
        
        if not json_path.exists():
            # Try case-insensitive or common variants (sn76489 vs sn76489a)
            # For now, stick to exact match
            return None
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls._cache[clean_id] = data
                return data
        except Exception:
            return None

    @classmethod
    def list_all_ids(cls) -> list[str]:
        """Returns all available chip IDs in the library."""
        if not CHIPS_BASE_PATH.exists():
            return []
        return [f.stem for f in CHIPS_BASE_PATH.glob("*.json")]

class Adapter:
    """
    Helix Adapter wrapper for the Chip Library.
    Can be used standalone to query the library.
    """
    toolkit  = "chip_library"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        chip_id = payload.get("chip_id")
        if not chip_id:
            # If no ID, return summary of library
            return {
                "available_chips": ChipLibrary.list_all_ids(),
                "adapter": "chip_library"
            }
            
        chip_data = ChipLibrary.get_chip(chip_id)
        if not chip_data:
            return {"error": f"Chip '{chip_id}' not found in library.", "adapter": "chip_library"}
            
        return {
            "chip": chip_data,
            "adapter": "chip_library"
        }

    def is_available(self) -> bool:
        return CHIPS_BASE_PATH.exists()
