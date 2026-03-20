"""
domains/music/style_vector/ — Composer Style Vector System
==============================================================
Computes ArtistStyleVector entities from accumulated track analysis artifacts.

The style vector encodes a composer's MUSICAL IDENTITY, not their hardware.

Musical cognition features dominate. Hardware context (chips, platforms) is
stored as metadata to explain differences but never override the fingerprint.

This enables cross-era composer reasoning:
    Motoi Sakuraba on YM2612 (El Viento, 1991)
    vs. Motoi Sakuraba on orchestral samples (Dark Souls, 2011)
    → same composer entity; differences explained by platform constraints

Exported from this package:
    StyleVectorComputer — main computation class
    CrossEraAnalyzer    — cross-platform style comparison
"""
from domains.music.style_vector.style_vector import StyleVectorComputer
from domains.music.style_vector.cross_era import CrossEraAnalyzer

__all__ = ["StyleVectorComputer", "CrossEraAnalyzer"]
