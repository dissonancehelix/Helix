"""
YM2612 Synthesis Profiler
==========================
Extracts FM synthesis architecture from a parsed VGMTrack event stream.

Captures per-channel:
  - Algorithm (0-7) and Feedback (0-7) from regs 0xB0-0xB5
  - Operator envelope parameters (ADSR) from regs 0x50-0x8F
  - Total Level per operator from regs 0x40-0x4F
  - LFO enable/rate from reg 0x22
  - DAC enable/usage from regs 0x2A/0x2B
  - Key-on activity from reg 0x28

Returns a SynthesisProfile dataclass serialisable via .to_dict().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from substrates.music.vgm_parser import VGMTrack


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OperatorParams:
    total_level:  int = 127   # 0 = loudest, 127 = silent
    attack_rate:  int = 0     # 0-31
    decay_rate1:  int = 0     # 0-31
    decay_rate2:  int = 0     # 0-31
    sustain_level: int = 0    # 0-15
    release_rate: int = 0     # 0-15
    detune:       int = 0     # 0-7
    multiple:     int = 0     # 0-15

    def to_dict(self) -> dict:
        return {
            "total_level":   self.total_level,
            "attack_rate":   self.attack_rate,
            "decay_rate1":   self.decay_rate1,
            "decay_rate2":   self.decay_rate2,
            "sustain_level": self.sustain_level,
            "release_rate":  self.release_rate,
            "detune":        self.detune,
            "multiple":      self.multiple,
        }


@dataclass
class FMPatch:
    """Snapshot of a single FM channel's synthesis settings."""
    channel:   int
    algorithm: int                                         # 0-7
    feedback:  int                                         # 0-7
    operators: list[OperatorParams] = field(default_factory=lambda: [OperatorParams() for _ in range(4)])

    def to_dict(self) -> dict:
        return {
            "channel":   self.channel,
            "algorithm": self.algorithm,
            "feedback":  self.feedback,
            "operators": [op.to_dict() for op in self.operators],
        }


@dataclass
class SynthesisProfile:
    """Full synthesis architecture profile extracted from a VGM track."""
    has_ym2612: bool = False
    has_psg:    bool = False
    has_dac:    bool = False
    has_lfo:    bool = False
    lfo_rate:   int  = 0

    algorithms_used:  list[int] = field(default_factory=list)
    feedback_levels:  list[int] = field(default_factory=list)
    fm_channels_active: int = 0
    keyon_count:        int = 0
    dac_writes:         int = 0

    patches: list[FMPatch] = field(default_factory=list)

    def to_dict(self) -> dict:
        alg_counts: dict[int, int] = {}
        for a in self.algorithms_used:
            alg_counts[a] = alg_counts.get(a, 0) + 1

        return {
            "chips": {
                "ym2612":      self.has_ym2612,
                "psg_sn76489": self.has_psg,
            },
            "ym2612": {
                "dac_enabled":         self.has_dac,
                "lfo_enabled":         self.has_lfo,
                "lfo_rate":            self.lfo_rate,
                "fm_channels_active":  self.fm_channels_active,
                "keyon_events":        self.keyon_count,
                "dac_writes":          self.dac_writes,
                "algorithm_histogram": alg_counts,
                "algorithms_used":     sorted(set(self.algorithms_used)),
                "feedback_levels":     sorted(set(self.feedback_levels)),
                "patches":             [p.to_dict() for p in self.patches[:24]],
            },
        }


# ---------------------------------------------------------------------------
# Channel state tracker
# ---------------------------------------------------------------------------

class _ChannelState:
    """Mutable per-channel FM register state."""
    def __init__(self) -> None:
        self.algorithm  = 0
        self.feedback   = 0
        self.active     = False
        self.ops        = [OperatorParams() for _ in range(4)]

    def snapshot(self, ch: int) -> FMPatch:
        import copy
        p = FMPatch(channel=ch, algorithm=self.algorithm, feedback=self.feedback)
        p.operators = copy.deepcopy(self.ops)
        return p


# ---------------------------------------------------------------------------
# Main profiler
# ---------------------------------------------------------------------------

def profile_vgm_track(track: "VGMTrack") -> SynthesisProfile:
    """
    Walk the VGM event list and extract synthesis architecture.

    Returns a SynthesisProfile suitable for serialisation.
    """
    prof = SynthesisProfile(
        has_ym2612 = track.header.has_ym2612,
        has_psg    = track.header.has_psg,
    )

    channels    = [_ChannelState() for _ in range(6)]
    seen_patches: set[tuple] = set()

    for ev in track.events:
        if ev.kind == "ym2612_port0":
            _handle_write(ev.reg, ev.val, 0, channels, prof, seen_patches)
        elif ev.kind == "ym2612_port1":
            _handle_write(ev.reg, ev.val, 3, channels, prof, seen_patches)
        elif ev.kind == "psg":
            prof.has_psg = True

    prof.fm_channels_active = sum(1 for ch in channels if ch.active)
    return prof


# ---------------------------------------------------------------------------
# Register dispatch
# ---------------------------------------------------------------------------

def _handle_write(
    reg: int, val: int, ch_offset: int,
    channels: list[_ChannelState],
    prof: SynthesisProfile,
    seen: set[tuple],
) -> None:

    # --- Global registers (port 0 only, ch_offset==0) -------------------------
    if ch_offset == 0:
        if reg == 0x22:                              # LFO
            if val & 0x08:
                prof.has_lfo = True
                prof.lfo_rate = val & 0x07
            return
        if reg == 0x2B:                              # DAC enable
            if val & 0x80:
                prof.has_dac = True
            return
        if reg == 0x2A:                              # DAC data write
            prof.dac_writes += 1
            return

    # --- Key-on (reg 0x28, port 0 only) --------------------------------------
    if ch_offset == 0 and reg == 0x28:
        ch_raw  = val & 0x03
        port    = (val >> 2) & 0x01
        op_mask = (val >> 4) & 0x0F
        if ch_raw < 3:
            ch_idx = ch_raw + port * 3
            if 0 <= ch_idx < 6 and op_mask:
                channels[ch_idx].active = True
                prof.keyon_count += 1
        return

    # --- Per-channel registers ------------------------------------------------
    ch_lane = reg & 0x03
    if ch_lane == 0x03:
        return                                       # reserved
    ch_idx = ch_offset + ch_lane
    if not (0 <= ch_idx < 6):
        return
    op_lane = (reg >> 2) & 0x03
    ch      = channels[ch_idx]

    # Algorithm + Feedback
    if 0xB0 <= reg <= 0xB2:
        ch.algorithm = val & 0x07
        ch.feedback  = (val >> 3) & 0x07
        prof.algorithms_used.append(ch.algorithm)
        prof.feedback_levels.append(ch.feedback)
        _try_snapshot(ch_idx, ch, prof, seen)
        return

    # L/R / AMS / PMS — snapshot opportunity
    if 0xB4 <= reg <= 0xB6:
        _try_snapshot(ch_idx, ch, prof, seen)
        return

    op = ch.ops[op_lane]

    # Total Level
    if 0x40 <= reg <= 0x4F:
        op.total_level = val & 0x7F
    # Rate Scaling + Attack Rate
    elif 0x50 <= reg <= 0x5F:
        op.attack_rate = val & 0x1F
    # AM + Decay Rate 1
    elif 0x60 <= reg <= 0x6F:
        op.decay_rate1 = val & 0x1F
    # Decay Rate 2
    elif 0x70 <= reg <= 0x7F:
        op.decay_rate2 = val & 0x1F
    # Sustain Level + Release Rate
    elif 0x80 <= reg <= 0x8F:
        op.sustain_level = (val >> 4) & 0x0F
        op.release_rate  = val & 0x0F
    # Detune + Multiple
    elif 0x30 <= reg <= 0x3F:
        op.detune   = (val >> 4) & 0x07
        op.multiple = val & 0x0F


def _try_snapshot(
    ch_idx: int,
    ch: _ChannelState,
    prof: SynthesisProfile,
    seen: set[tuple],
) -> None:
    """Record a patch if this algorithm+feedback+operator combo is novel."""
    key = (
        ch.algorithm,
        ch.feedback,
        tuple((op.total_level, op.attack_rate, op.multiple) for op in ch.ops),
    )
    if key not in seen:
        seen.add(key)
        prof.patches.append(ch.snapshot(ch_idx))
