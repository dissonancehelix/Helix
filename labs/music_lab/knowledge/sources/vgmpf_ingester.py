"""
vgmpf_ingester.py — VGMPF (Video Game Music Preservation Foundation) Ingester
===============================================================================
VGMPF (vgmpf.com) documents sound drivers, chips, and composer technical
practices. This ingester reads:

  1. Pre-baked VGMPF knowledge (canonical driver/chip facts) — always available
  2. Optional HTML scraping of vgmpf.com composer/driver pages — requires network

The pre-baked data covers the Sega Genesis / SMPS ecosystem used by S3K.

API
---
get_driver_info(driver_name) -> dict      (from built-in registry)
get_chip_info(chip_name) -> dict          (from built-in registry)
enrich_composer_technical(node) -> None   (attach technical style traits)
enrich_driver_node(node) -> None          (populate SoundDriverNode fields)
"""

from __future__ import annotations

import logging
from typing import Any

from labs.music_lab.knowledge.composer_schema import ComposerNode, SoundDriverNode

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in VGMPF knowledge base
# ---------------------------------------------------------------------------

CHIP_REGISTRY: dict[str, dict[str, Any]] = {
    "YM2612": {
        "full_name":   "Yamaha YM2612 (OPN2)",
        "type":        "FM synthesizer",
        "channels":    6,
        "operators":   4,
        "algorithms":  8,
        "voices_per_ch": 1,
        "special":     "Channel 6 can be used for 8-bit DAC (PCM samples)",
        "vgmpf_url":   "https://www.vgmpf.com/Wiki/index.php?title=YM2612",
        "wikidata":    "Q2432091",
        "notes": (
            "Core FM chip in Sega Genesis/Mega Drive. "
            "Supports LFO, AM/FM modulation. "
            "DAC mode on Ch6 used for drum samples in SMPS."
        ),
    },
    "SN76489": {
        "full_name":   "Texas Instruments SN76489 (PSG)",
        "type":        "Programmable Sound Generator",
        "channels":    4,
        "operators":   None,
        "voices_per_ch": 1,
        "special":     "3 square wave + 1 noise channel",
        "vgmpf_url":   "https://www.vgmpf.com/Wiki/index.php?title=SN76489",
        "wikidata":    "Q2421900",
        "notes": (
            "Secondary chip in Sega Genesis. "
            "Used for high-hat, bass drone, and simple melodic lines in SMPS."
        ),
    },
    "SPC700": {
        "full_name":   "Sony SPC700",
        "type":        "Sample-based DSP",
        "channels":    8,
        "operators":   None,
        "voices_per_ch": 1,
        "special":     "BRR sample playback with ADSR envelopes, echo/reverb DSP",
        "vgmpf_url":   "https://www.vgmpf.com/Wiki/index.php?title=SPC700",
        "wikidata":    "Q3467975",
        "notes": "Super Nintendo audio processor. All sound is sample-based (BRR format).",
    },
    "2A03": {
        "full_name":   "Ricoh 2A03 (NES APU)",
        "type":        "APU (Audio Processing Unit)",
        "channels":    5,
        "operators":   None,
        "voices_per_ch": 1,
        "special":     "2 pulse + 1 triangle + 1 noise + 1 DPCM",
        "vgmpf_url":   "https://www.vgmpf.com/Wiki/index.php?title=2A03",
        "notes":       "NES/Famicom sound chip.",
    },
    "SID": {
        "full_name":   "MOS Technology 6581/8580 SID",
        "type":        "SID chip (analog synth)",
        "channels":    3,
        "operators":   None,
        "special":     "Ring modulation, filter, oscillator sync",
        "vgmpf_url":   "https://www.vgmpf.com/Wiki/index.php?title=SID",
        "notes":       "Commodore 64 sound chip. Distinctive analog character.",
    },
}

DRIVER_REGISTRY: dict[str, dict[str, Any]] = {
    "SMPS": {
        "full_name":    "Sega Master/Mega Drive Player System (SMPS)",
        "platform":     "Sega Genesis / Mega Drive",
        "developer":    "Sega Sound Team",
        "chips":        ["YM2612", "SN76489"],
        "format":       "Binary bytecode; interpreted by Z80 co-processor",
        "loop_support": True,
        "features": [
            "FM voice programming via operator TL/DT/MUL parameters",
            "PSG square wave + noise control",
            "PCM drum samples via YM2612 DAC (Ch6)",
            "Loop with offset (VGM loop_offset maps to this)",
            "Frequency via hardware period registers",
            "Multiple SMPS variants: Z80, 68k, T6W28",
        ],
        "vgmpf_url":  "https://www.vgmpf.com/Wiki/index.php?title=SMPS",
        "sega_retro": "https://segaretro.org/SMPS",
        "notes": (
            "SMPS is the dominant sound driver used across Sega Genesis games. "
            "The S3K variant was written by Yoshiaki 'Milpo' Kashima and features "
            "extended DAC sample tables and custom envelope handling."
        ),
    },
    "SPC700_SPC": {
        "full_name":    "SPC700 (SNES native)",
        "platform":     "Super Nintendo Entertainment System",
        "chips":        ["SPC700"],
        "loop_support": True,
        "features": [
            "BRR sample compression/playback",
            "8 independent voices with ADSR",
            "Hardware echo/reverb DSP",
            "Pitch modulation between voices",
        ],
        "vgmpf_url": "https://www.vgmpf.com/Wiki/index.php?title=SPC700",
    },
}

# Composer → technical style traits from VGMPF knowledge
# (manually curated from VGMPF composer pages + Sonic Retro research)
COMPOSER_TECHNICAL_TRAITS: dict[str, dict[str, Any]] = {
    "masayuki_nagao": {
        "primary_chip":     "YM2612",
        "technique":        "Arranging over pre-existing compositions; modal bass lines",
        "vgmpf_notes":      "Specialises in FM voice programming and arrangement for Genesis",
        "driver":           "SMPS",
    },
    "tatsuyuki_maeda": {
        "primary_chip":     "YM2612",
        "technique":        "Rock-influenced FM programming; aggressive TL envelopes",
        "driver":           "SMPS",
    },
    "jun_senoue": {
        "primary_chip":     "YM2612",
        "technique":        "Guitar-style FM lead voices; driving rock arrangements",
        "driver":           "SMPS",
        "vgmpf_url":        "https://www.vgmpf.com/Wiki/index.php?title=Jun_Senoue",
    },
    "yoshiaki_kashima": {
        "primary_chip":     "YM2612+SN76489",
        "technique":        "Sound driver programming; Special Stage loop architecture",
        "driver":           "SMPS",
        "role_technical":   "Sound driver author for S3K",
        "vgmpf_notes":      "Author of the S3K SMPS variant; recycled Special Stage from SegaSonic Bros.",
    },
    "brad_buxer": {
        "primary_chip":     "YM2612",
        "technique":        "Pop/R&B arrangement; beatboxing sample integration",
        "driver":           "SMPS",
        "vgmpf_notes":      "IceCap Zone based on The Jetzons 'Hard Times' (1982)",
    },
    "cirocco_jones": {
        "primary_chip":     "YM2612",
        "technique":        "Electronic/pop arrangement; sample programming",
        "driver":           "SMPS",
    },
    "miyoko_takaoka": {
        "primary_chip":     "YM2612+SN76489",
        "technique":        "Melodic composition; Cube Corp contracted work",
        "driver":           "SMPS",
    },
    "masanori_hikichi": {
        "primary_chip":     "YM2612",
        "technique":        "Boss music composition; percussive FM programming",
        "driver":           "SMPS",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_chip_info(chip_name: str) -> dict[str, Any]:
    """Return built-in chip metadata dict (empty dict if unknown)."""
    return CHIP_REGISTRY.get(chip_name, {})


def get_driver_info(driver_name: str) -> dict[str, Any]:
    """Return built-in sound driver metadata dict (empty dict if unknown)."""
    return DRIVER_REGISTRY.get(driver_name, {})


def enrich_composer_technical(node: ComposerNode) -> bool:
    """
    Attach VGMPF-sourced technical style traits to a ComposerNode.
    Returns True if any data was added.
    """
    traits = COMPOSER_TECHNICAL_TRAITS.get(node.composer_id)
    if not traits:
        return False

    for key, val in traits.items():
        if key not in node.style_traits:
            node.style_traits[key] = val

    vgmpf_url = traits.get("vgmpf_url")
    if vgmpf_url and "vgmpf" not in node.external_ids:
        node.external_ids["vgmpf"] = vgmpf_url

    log.debug("vgmpf: enriched technical traits for '%s'", node.composer_id)
    return True


def enrich_driver_node(node: SoundDriverNode) -> bool:
    """
    Populate a SoundDriverNode with built-in VGMPF registry data.
    Matches by driver_id against DRIVER_REGISTRY keys (case-insensitive prefix).
    Returns True if any data was added.
    """
    key = None
    for k in DRIVER_REGISTRY:
        if node.driver_id.upper().startswith(k.upper()) or k.upper() in node.driver_id.upper():
            key = k
            break

    if not key:
        return False

    info = DRIVER_REGISTRY[key]
    if not node.chips:
        node.chips = info.get("chips", [])
    if not node.features:
        node.features = info.get("features", [])
    if not node.notes:
        node.notes = info.get("notes")

    ext = {}
    if info.get("vgmpf_url"):
        ext["vgmpf"] = info["vgmpf_url"]
    if info.get("sega_retro"):
        ext["sega_retro"] = info["sega_retro"]
    node.external_ids.update({k: v for k, v in ext.items() if k not in node.external_ids})

    log.debug("vgmpf: enriched driver node '%s'", node.driver_id)
    return True


def enrich_all_composers(composers: list[ComposerNode]) -> int:
    """Bulk-enrich a list of ComposerNodes. Returns count enriched."""
    count = 0
    for node in composers:
        if enrich_composer_technical(node):
            count += 1
    return count
