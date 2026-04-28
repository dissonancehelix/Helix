"""
substrates.music.analysis — Per-stage analysis modules.

Stages:
  3  chip         — synthesis architecture extraction (YM2612 / PSG / DAC profiles)
  4  symbolic     — note event reconstruction from chip register streams
  5  mir          — MIR audio features (or chip-proxy MIR for emulated formats)
  6  musicology   — key estimation, tempo, motif detection, harmonic density
"""
from .chip       import run as chip
from .symbolic   import run as symbolic
from .mir        import run as mir
from .musicology import run as musicology

__all__ = ["chip", "symbolic", "mir", "musicology"]
