"""
adapter_vgm_system.py — Helix adapter for VGM platform/system taxonomy
=======================================================================
Tier A: Pure Python — no compilation required.
Source reference: domains/music/toolkits/vgmtools/vgm_tag.c (SYSTEM_NAMES table)

Purpose:
    Expose the complete gaming platform taxonomy from vgm_tag.c.
    Maps short system codes (used in GD3 tags and community conventions)
    to canonical English platform names.

    Used to normalize the 'platform' field in UMO metadata.recorded
    and to populate Platform entities in the atlas.

Input (payload dict):
    code (str)  — short system code (e.g. "SMD", "NES", "TG16")
                  Case-insensitive. Returns None if not found.

Output (dict):
    {
        "code":    str,
        "name":    str | None,   # canonical English name
        "found":   bool,
        "adapter": "vgm_system",
    }

Additional calls:
    all_systems()       -> list of all (code, name) pairs
    normalize_platform(raw) -> best-match name for a raw platform string
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ── Platform taxonomy (from vgm_tag.c SYSTEM_NAMES[]) ───────────────────────
# Format: code -> canonical English name
# Extracted verbatim from vgm_tag.c; Japanese NCR strings omitted.

SYSTEM_TABLE: dict[str, str] = {
    "SMS":    "Sega Master System",
    "SGG":    "Sega Game Gear",
    "SMSGG":  "Sega Master System / Game Gear",
    "SMD":    "Sega Mega Drive / Genesis",
    "SG1k":   "Sega Game 1000",
    "SC3k":   "Sega Computer 3000",
    "SS*":    "Sega System *",
    "CPS":    "CP System",
    "CPS2":   "CP System II",
    "CPS3":   "CP System III",
    "Ccv":    "Colecovision",
    "BMM*":   "BBC Micro Model *",
    "BM128":  "BBC Master 128",
    "Arc":    "Arcade Machine",
    "NGP":    "Neo Geo Pocket",
    "NGPC":   "Neo Geo Pocket Color",
    "SCD":    "Sega MegaCD / SegaCD",
    "32X":    "Sega 32X / Mega 32X",
    "SCD32":  "Sega MegaCD 32X / SegaCD 32X",
    "Nmc*":   "Namco System *",
    "SX":     "Sega X",
    "SY":     "Sega Y",
    "SGX":    "System GX",
    "AS?":    "Atari System ?",
    "BS":     "Bubble System",
    "IM*":    "Irem M*",
    "TW16":   "Twin 16",
    "NG":     "Neo Geo",
    "NG*":    "Neo Geo *",
    "NES":    "Nintendo Entertainment System",
    "FDS":    "Famicom Disk System",
    "NESFDS": "Nintendo Entertainment System / Famicom Disk System",
    "GB":     "Game Boy",
    "GBC":    "Game Boy Color",
    "GBGBC":  "Game Boy / Game Boy Color",
    "GBA":    "Game Boy Advance",
    "TG16":   "TurboGrafx-16",
    "TGCD":   "TurboGrafx-CD",
    "Tp?":    "Toaplan ?",
    "VB":     "Virtual Boy",
    # Additional common codes not in the vgm_tag.c table but widely used
    "SNES":   "Super Nintendo Entertainment System",
    "SFC":    "Super Famicom",
    "N64":    "Nintendo 64",
    "GCN":    "Nintendo GameCube",
    "Wii":    "Nintendo Wii",
    "NDS":    "Nintendo DS",
    "3DS":    "Nintendo 3DS",
    "PS1":    "PlayStation",
    "PS2":    "PlayStation 2",
    "PS3":    "PlayStation 3",
    "PSP":    "PlayStation Portable",
    "SAT":    "Sega Saturn",
    "DC":     "Sega Dreamcast",
    "PCE":    "PC Engine",
    "X68":    "Sharp X68000",
    "PC88":   "NEC PC-8801",
    "PC98":   "NEC PC-9801",
    "MSX":    "MSX",
    "MSX2":   "MSX2",
    "Atari":  "Atari",
    "2600":   "Atari 2600",
    "5200":   "Atari 5200",
    "7800":   "Atari 7800",
    "Lynx":   "Atari Lynx",
    "Jag":    "Atari Jaguar",
    "WS":     "WonderSwan",
    "WSC":    "WonderSwan Color",
    "NGCD":   "Neo Geo CD",
    "3DO":    "3DO",
    "CD32":   "Amiga CD32",
    "Amiga":  "Amiga",
    "C64":    "Commodore 64",
    "ZX":     "ZX Spectrum",
    "CPC":    "Amstrad CPC",
    "ApII":   "Apple II",
    "Dos":    "DOS / IBM PC",
    "Win":    "Windows",
}

# Build a case-insensitive lookup index
_CODE_INDEX: dict[str, str] = {k.lower(): k for k in SYSTEM_TABLE}

# Common freeform aliases found in real metadata → canonical code
_ALIAS_MAP: dict[str, str] = {
    "genesis":             "SMD",
    "mega drive":          "SMD",
    "megadrive":           "SMD",
    "sega genesis":        "SMD",
    "sega mega drive":     "SMD",
    "master system":       "SMS",
    "sega master system":  "SMS",
    "game gear":           "SGG",
    "sega game gear":      "SGG",
    "nintendo":            "NES",
    "famicom":             "NES",
    "super nintendo":      "SNES",
    "super famicom":       "SFC",
    "super nes":           "SNES",
    "gameboy":             "GB",
    "game boy":            "GB",
    "game boy color":      "GBC",
    "game boy advance":    "GBA",
    "turbo grafx":         "TG16",
    "turbografx":          "TG16",
    "turbografx-16":       "TG16",
    "pc engine":           "PCE",
    "neo geo":             "NG",
    "neo-geo":             "NG",
    "playstation":         "PS1",
    "psx":                 "PS1",
    "playstation 2":       "PS2",
    "playstation 3":       "PS3",
    "saturn":              "SAT",
    "sega saturn":         "SAT",
    "dreamcast":           "DC",
    "sega dreamcast":      "DC",
    "32x":                 "32X",
    "sega 32x":            "32X",
    "segacd":              "SCD",
    "sega cd":             "SCD",
    "mega cd":             "SCD",
    "nintendo 64":         "N64",
    "n64":                 "N64",
    "gamecube":            "GCN",
    "nintendo ds":         "NDS",
    "nds":                 "NDS",
    "wonderswan":          "WS",
    "wonder swan":         "WS",
    "arcade":              "Arc",
    "x68000":              "X68",
    "sharp x68000":        "X68",
    "pc-88":               "PC88",
    "pc-98":               "PC98",
    "commodore 64":        "C64",
    "zx spectrum":         "ZX",
    "amstrad":             "CPC",
}


class Adapter:
    """
    Adapter exposing vgm_tag.c gaming platform taxonomy.

    Tier A — no build required.
    """
    toolkit  = "vgm_system"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        code = payload.get("code", "")
        result = self.lookup(code)
        return self.normalize(result)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def is_available(self) -> bool:
        return True

    def lookup(self, code: str) -> dict[str, Any]:
        """Look up a system code. Case-insensitive."""
        canonical_code = _CODE_INDEX.get(code.lower())
        if canonical_code:
            return {
                "code":    canonical_code,
                "name":    SYSTEM_TABLE[canonical_code],
                "found":   True,
                "adapter": "vgm_system",
            }
        return {
            "code":    code,
            "name":    None,
            "found":   False,
            "adapter": "vgm_system",
        }

    def normalize_platform(self, raw: str) -> dict[str, Any]:
        """
        Normalize a freeform platform string to a canonical system entry.
        Checks the code index first, then the alias map.
        Returns the lookup result with matched_via provenance.
        """
        raw_lower = raw.strip().lower()

        # Direct code match
        canonical_code = _CODE_INDEX.get(raw_lower)
        if canonical_code:
            return {**self.lookup(canonical_code), "matched_via": "code"}

        # Alias match
        alias_code = _ALIAS_MAP.get(raw_lower)
        if alias_code:
            result = self.lookup(alias_code)
            return {**result, "matched_via": "alias", "alias_input": raw}

        return {
            "code":        raw,
            "name":        None,
            "found":       False,
            "matched_via": None,
            "adapter":     "vgm_system",
        }

    def all_systems(self) -> list[dict[str, str]]:
        """Return all (code, name) pairs in table order."""
        return [{"code": k, "name": v} for k, v in SYSTEM_TABLE.items()]
