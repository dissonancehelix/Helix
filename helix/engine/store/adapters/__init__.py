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

Available adapters and their tiers:

  Tier A — Static constants, always available (no compilation):
    adapter_nuked_opn2  — YM2612 (OPN2) FM carrier topology
    adapter_nuked_opm   — YM2151 (OPM) FM carrier topology
    adapter_nuked_opl3  — YMF262 (OPL3) FM carrier topology (2-op and 4-op)
    adapter_nuked_opll  — YM2413/OPLL FM carrier topology + patch ROM names
    adapter_nuked_opl2  — YM3812 (OPL2) FM carrier topology (2-op)
    adapter_nuked_psg   — YM7101/SN76489 PSG channel constants + volume table
    adapter_rf5c68a     — RF5C68A/RF5C164 PCM channel constants (Sega CD)
    adapter_smps        — SMPS driver timing + opcode constants
    adapter_gems        — GEMS driver patch format + MIDI conversion bridge
    adapter_vgmfile     — VGMFile.h: VGM header parser, GD3 reader, tag priority
    adapter_chiptext    — chiptext.c: NES APU, GB DMG, Pokey, OPN/OPL flags, waveforms
    adapter_vgm_system  — vgm_tag.c: 70+ gaming platform taxonomy (code → name)

  Tier B — Compiled C libraries (requires cmake build):
    adapter_libvgm      — libvgm ctypes bridge (VGM/VGZ emulation)
    adapter_gme         — Game_Music_Emu bridge (SPC, NSF, GBS, HES, KSS, AY)
    adapter_vgmstream   — vgmstream CLI bridge (broad format decoding)

  Tier B (subprocess) — vgmtools binaries (requires compile from vgmtools/):
    adapter_vgm2txt     — vgm2txt: full register timeline → causal.temporal_trajectories
    adapter_vgm_cnt     — vgm_cnt: per-chip command frequency → channel_usage stats
    adapter_vgm_stat    — vgm_stat: duration/loop statistics + GD3 metadata
    adapter_gems        — gems_to_midi() via gems2mid binary

  Tier C — Symbolic analysis (requires Python packages):
    adapter_music21     — music21 symbolic score analysis
    adapter_pretty_midi — pretty_midi MIDI parsing and feature extraction

  Tier D — MIR / signal analysis (requires Python packages):
    adapter_librosa     — librosa MIR feature extraction
    adapter_essentia    — Essentia audio descriptors

  Tag Priority (VGM metadata):
    External .tag file (foobar2000 dialect) > GD3 embedded in VGM binary.
    adapter_vgmfile enforces this. External tags are canon; GD3 is fallback.
"""
from __future__ import annotations

from core.engine.adapters.adapter_libvgm      import Adapter as LibvgmAdapter
from core.engine.adapters.adapter_gme         import Adapter as GmeAdapter
from core.engine.adapters.adapter_vgmstream   import Adapter as VgmstreamAdapter
from core.engine.adapters.adapter_nuked_opn2  import Adapter as NukedOpn2Adapter
from core.engine.adapters.adapter_nuked_opm   import Adapter as NukedOpmAdapter
from core.engine.adapters.adapter_nuked_opl3  import Adapter as NukedOpl3Adapter
from core.engine.adapters.adapter_nuked_opll  import Adapter as NukedOpllAdapter
from core.engine.adapters.adapter_nuked_opl2  import Adapter as NukedOpl2Adapter
from core.engine.adapters.adapter_nuked_psg   import Adapter as NukedPsgAdapter
from core.engine.adapters.adapter_rf5c68a     import Adapter as Rf5c68aAdapter
from core.engine.adapters.adapter_smps        import Adapter as SmpsAdapter
from core.engine.adapters.adapter_gems        import Adapter as GemsAdapter
from core.engine.adapters.adapter_vgmfile     import Adapter as VgmfileAdapter
from core.engine.adapters.adapter_chiptext    import Adapter as ChiptextAdapter
from core.engine.adapters.adapter_vgm_system  import Adapter as VgmSystemAdapter
from core.engine.adapters.adapter_vgm2txt     import Adapter as Vgm2txtAdapter
from core.engine.adapters.adapter_vgm_cnt     import Adapter as VgmCntAdapter
from core.engine.adapters.adapter_vgm_stat    import Adapter as VgmStatAdapter
from core.engine.adapters.adapter_librosa     import Adapter as LibrosaAdapter
from core.engine.adapters.adapter_essentia    import Adapter as EssentiaAdapter
from core.engine.adapters.adapter_music21     import Adapter as Music21Adapter
from core.engine.adapters.adapter_pretty_midi import Adapter as PrettyMidiAdapter

__all__ = [
    # Tier A — Nuked FM/PSG chip topology
    "NukedOpn2Adapter",
    "NukedOpmAdapter",
    "NukedOpl3Adapter",
    "NukedOpllAdapter",
    "NukedOpl2Adapter",
    "NukedPsgAdapter",
    "Rf5c68aAdapter",
    "SmpsAdapter",
    "GemsAdapter",
    # Tier A — vgmtools static knowledge
    "VgmfileAdapter",
    "ChiptextAdapter",
    "VgmSystemAdapter",
    # Tier B — compiled libraries
    "LibvgmAdapter",
    "GmeAdapter",
    "VgmstreamAdapter",
    # Tier B — vgmtools binaries
    "Vgm2txtAdapter",
    "VgmCntAdapter",
    "VgmStatAdapter",
    # Tier C
    "Music21Adapter",
    "PrettyMidiAdapter",
    # Tier D
    "LibrosaAdapter",
    "EssentiaAdapter",
]
