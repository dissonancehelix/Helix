"""
glossary.py — Controlled vocabulary for music domain semantic layer.

Provides:
  - Platform canonical names and aliases
  - Sound chip canonical names and aliases
  - Format category labels
  - Credit role vocabulary
  - Franchise / series groupings

These are used by credit_resolver and entity_layer to normalize
raw tag strings into stable semantic identifiers.

NOT a complete hardware database. Only covers what appears in the
Helix library. New platforms/chips are added as the corpus grows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PlatformEntry:
    id: str                       # music.platform:<slug>
    canonical_name: str
    aliases: frozenset[str]       # raw tag strings that map here
    primary_chip: Optional[str]   # primary sound chip id, if unambiguous


@dataclass(frozen=True)
class ChipEntry:
    id: str                       # music.chip:<slug>
    canonical_name: str
    aliases: frozenset[str]
    manufacturer: str
    chip_type: str                # FM | PSG | PCM | ADPCM | Wavetable | Mixed


@dataclass(frozen=True)
class RoleEntry:
    id: str
    label: str
    description: str


# ── Platforms ─────────────────────────────────────────────────────────────────

PLATFORMS: list[PlatformEntry] = [
    PlatformEntry(
        id="music.platform:mega_drive",
        canonical_name="Mega Drive",
        aliases=frozenset({
            "Mega Drive", "Genesis", "Sega Genesis", "Sega Mega Drive",
            "MD", "SMD",
        }),
        primary_chip="music.chip:ym2612",
    ),
    PlatformEntry(
        id="music.platform:master_system",
        canonical_name="Master System",
        aliases=frozenset({
            "Master System", "SMS", "Sega Master System",
            "Mark III", "Mark 3",
        }),
        primary_chip="music.chip:sn76489",
    ),
    PlatformEntry(
        id="music.platform:game_gear",
        canonical_name="Game Gear",
        aliases=frozenset({
            "Game Gear", "GG", "Sega Game Gear",
        }),
        primary_chip="music.chip:sn76489",
    ),
    PlatformEntry(
        id="music.platform:snes",
        canonical_name="SNES",
        aliases=frozenset({
            "SNES", "Super Nintendo", "Super NES", "Super Famicom", "SFC",
        }),
        primary_chip="music.chip:spc700",
    ),
    PlatformEntry(
        id="music.platform:nes",
        canonical_name="NES",
        aliases=frozenset({
            "NES", "Famicom", "FC", "Nintendo Entertainment System",
        }),
        primary_chip="music.chip:2a03",
    ),
    PlatformEntry(
        id="music.platform:game_boy",
        canonical_name="Game Boy",
        aliases=frozenset({
            "Game Boy", "GB", "DMG", "Game Boy Color", "GBC",
        }),
        primary_chip="music.chip:lr35902",
    ),
    PlatformEntry(
        id="music.platform:game_boy_advance",
        canonical_name="Game Boy Advance",
        aliases=frozenset({"Game Boy Advance", "GBA"}),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:saturn",
        canonical_name="Saturn",
        aliases=frozenset({
            "Saturn", "Sega Saturn", "SS",
        }),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:dreamcast",
        canonical_name="Dreamcast",
        aliases=frozenset({
            "Dreamcast", "DC", "Sega Dreamcast",
        }),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:playstation",
        canonical_name="PlayStation",
        aliases=frozenset({
            "PlayStation", "PS1", "PSX", "PSF",
        }),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:playstation_2",
        canonical_name="PlayStation 2",
        aliases=frozenset({"PlayStation 2", "PS2", "PS2F"}),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:nintendo_64",
        canonical_name="Nintendo 64",
        aliases=frozenset({
            "Nintendo 64", "N64", "Ultra 64",
        }),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:pc",
        canonical_name="PC",
        aliases=frozenset({
            "PC", "DOS", "Windows", "MS-DOS",
        }),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:arcade",
        canonical_name="Arcade",
        aliases=frozenset({
            "Arcade", "MAME", "CPS", "CPS2", "Neo Geo", "MVS", "AES",
        }),
        primary_chip=None,
    ),
    PlatformEntry(
        id="music.platform:pc_engine",
        canonical_name="PC Engine",
        aliases=frozenset({
            "PC Engine", "TurboGrafx-16", "TurboGrafx", "PCE",
        }),
        primary_chip="music.chip:huc6280",
    ),
    PlatformEntry(
        id="music.platform:x68000",
        canonical_name="X68000",
        aliases=frozenset({
            "X68000", "Sharp X68000", "X68k",
        }),
        primary_chip="music.chip:ym2151",
    ),
]

# ── Sound Chips ───────────────────────────────────────────────────────────────

CHIPS: list[ChipEntry] = [
    ChipEntry(
        id="music.chip:ym2612",
        canonical_name="YM2612",
        aliases=frozenset({"YM2612", "OPN2", "YM 2612"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
    ChipEntry(
        id="music.chip:sn76489",
        canonical_name="SN76489",
        aliases=frozenset({"SN76489", "PSG", "SN 76489"}),
        manufacturer="Texas Instruments",
        chip_type="PSG",
    ),
    ChipEntry(
        id="music.chip:spc700",
        canonical_name="SPC700",
        aliases=frozenset({"SPC700", "SPC", "Sony SPC700"}),
        manufacturer="Sony",
        chip_type="PCM",
    ),
    ChipEntry(
        id="music.chip:2a03",
        canonical_name="2A03",
        aliases=frozenset({"2A03", "RP2A03", "NES APU"}),
        manufacturer="Ricoh",
        chip_type="PSG",
    ),
    ChipEntry(
        id="music.chip:lr35902",
        canonical_name="LR35902",
        aliases=frozenset({"LR35902", "DMG-CPU", "Game Boy APU"}),
        manufacturer="Sharp",
        chip_type="PSG",
    ),
    ChipEntry(
        id="music.chip:ym2151",
        canonical_name="YM2151",
        aliases=frozenset({"YM2151", "OPM"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
    ChipEntry(
        id="music.chip:ym2413",
        canonical_name="YM2413",
        aliases=frozenset({"YM2413", "OPLL"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
    ChipEntry(
        id="music.chip:ym3812",
        canonical_name="YM3812",
        aliases=frozenset({"YM3812", "OPL2"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
    ChipEntry(
        id="music.chip:ymf262",
        canonical_name="YMF262",
        aliases=frozenset({"YMF262", "OPL3"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
    ChipEntry(
        id="music.chip:huc6280",
        canonical_name="HuC6280",
        aliases=frozenset({"HuC6280", "PC Engine APU"}),
        manufacturer="Hudson Soft",
        chip_type="Wavetable",
    ),
    ChipEntry(
        id="music.chip:ym2203",
        canonical_name="YM2203",
        aliases=frozenset({"YM2203", "OPN"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
    ChipEntry(
        id="music.chip:ym2608",
        canonical_name="YM2608",
        aliases=frozenset({"YM2608", "OPNA"}),
        manufacturer="Yamaha",
        chip_type="FM",
    ),
]

# ── Credit roles ──────────────────────────────────────────────────────────────

ROLES: list[RoleEntry] = [
    RoleEntry("role:composer",       "Composer",    "Original music composition"),
    RoleEntry("role:arranger",       "Arranger",    "Arrangement of existing composition"),
    RoleEntry("role:programmer",     "Programmer",  "Sound driver or sequencer programmer"),
    RoleEntry("role:sound_designer", "Sound Designer", "Patch/instrument design"),
    RoleEntry("role:performer",      "Performer",   "Vocal or live instrument performance"),
    RoleEntry("role:featured",       "Featured",    "Featured guest credit (FEATURING tag)"),
    RoleEntry("role:producer",       "Producer",    "Music production credit"),
    RoleEntry("role:unknown",        "Unknown",     "Role not determined"),
]


# ── Lookup helpers ─────────────────────────────────────────────────────────────

def _build_alias_map(entries: list) -> dict[str, object]:
    m: dict[str, object] = {}
    for e in entries:
        m[e.canonical_name.lower()] = e
        for alias in e.aliases:
            m[alias.lower()] = e
    return m


_PLATFORM_MAP: dict[str, PlatformEntry] = _build_alias_map(PLATFORMS)
_CHIP_MAP:     dict[str, ChipEntry]     = _build_alias_map(CHIPS)
_ROLE_MAP:     dict[str, RoleEntry]     = {r.id: r for r in ROLES}


def resolve_platform(raw: str) -> Optional[PlatformEntry]:
    """Resolve a raw platform string to its canonical PlatformEntry."""
    return _PLATFORM_MAP.get(raw.strip().lower())


def resolve_chip(raw: str) -> Optional[ChipEntry]:
    """Resolve a raw chip string to its canonical ChipEntry."""
    return _CHIP_MAP.get(raw.strip().lower())


def resolve_role(role_id: str) -> Optional[RoleEntry]:
    """Return a RoleEntry by id (e.g. 'role:featured')."""
    return _ROLE_MAP.get(role_id)


def platform_id(raw: str) -> Optional[str]:
    """Return platform entity id for a raw string, or None."""
    entry = resolve_platform(raw)
    return entry.id if entry else None


def chip_id(raw: str) -> Optional[str]:
    """Return chip entity id for a raw string, or None."""
    entry = resolve_chip(raw)
    return entry.id if entry else None
