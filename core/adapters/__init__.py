"""
core/adapters/ — Helix Toolkit Adapter Layer
=============================================
Adapters wrap external toolkits and normalize their input/output into
structured, JSON-compatible Helix artifacts.

ADAPTER CONTRACT:
  • Adapters contain NO Helix business logic.
  • They are pure translation layers between toolkit APIs and Helix schemas.
  • All inputs are normalized before the toolkit call.
  • All outputs are structured as dicts matching Atlas entity schemas.
  • Adapters must never import from core/operators/, core/semantics/, or
    core/compiler/. They know nothing about Atlas.

Available adapters:
    adapter_libvgm    — libvgm ctypes bridge (VGM emulation, YM2612 etc.)
    adapter_gme       — Game_Music_Emu bridge (SPC, NSF, GBS, etc.)
    adapter_vgmstream — vgmstream CLI bridge (broad format decoding)
    adapter_nuked_opn2 — Nuked-OPN2 topology reference (YM2612 carrier slots)
    adapter_librosa   — librosa MIR feature extraction
    adapter_essentia  — Essentia audio descriptors
    adapter_music21   — music21 symbolic score analysis
    adapter_pretty_midi — pretty_midi MIDI parsing and feature extraction
"""
from __future__ import annotations

from core.adapters.adapter_libvgm    import Adapter as LibvgmAdapter
from core.adapters.adapter_gme       import Adapter as GmeAdapter
from core.adapters.adapter_vgmstream import Adapter as VgmstreamAdapter
from core.adapters.adapter_nuked_opn2 import Adapter as NukedOpn2Adapter
from core.adapters.adapter_librosa   import Adapter as LibrosaAdapter
from core.adapters.adapter_essentia  import Adapter as EssentiaAdapter
from core.adapters.adapter_music21   import Adapter as Music21Adapter
from core.adapters.adapter_pretty_midi import Adapter as PrettyMidiAdapter

__all__ = [
    "LibvgmAdapter",
    "GmeAdapter",
    "VgmstreamAdapter",
    "NukedOpn2Adapter",
    "LibrosaAdapter",
    "EssentiaAdapter",
    "Music21Adapter",
    "PrettyMidiAdapter",
]
