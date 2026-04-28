"""
model/domains/music/attribution/fm_patch_extractor.py
================================================
Extracts YM2612 FM patches from a VGM register write stream.

YM2612 full patch write sequence (per channel):
  0xB0+ch  → ALG (bits 0-2), FB (bits 3-5)        ← algorithm / feedback
  0x30+op*4+ch → DTMUL: DT (bits 4-6), MUL (0-3)  ← detune / frequency multiple
  0x40+op*4+ch → TL (bits 0-6)                     ← total level
  0x50+op*4+ch → KSAR: KS (bits 6-7), AR (0-4)    ← key scale / attack rate
  0x60+op*4+ch → AMDR: AM (bit 7), D1R (0-4)      ← AM enable / first decay
  0x70+op*4+ch → D2R (bits 0-4)                    ← second decay (sustain rate)
  0x80+op*4+ch → SLD1: SL (bits 4-7), RR (0-3)   ← sustain level / release rate
  0x90+op*4+ch → SSG: SSG-EG (bit 3 enable, bits 0-2 shape)

ch offsets: ch1=0, ch2=1, ch3=2; ch4-6 are in Part 2 (base+0x100).
op offsets: op1=0x00, op2=0x08, op3=0x04, op4=0x0C (YM2612 operator interleave).

Usage:
    from model.domains.music.attribution.fm_patch_extractor import extract_patches_from_events
    patches = extract_patches_from_events(vgm_event_list)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any


# YM2612 operator slot offset interleave (not sequential!)
# Slot 1=0x00, Slot 2=0x08, Slot 3=0x04, Slot 4=0x0C
OP_OFFSETS = [0x00, 0x08, 0x04, 0x0C]  # indices → OP1, OP2, OP3, OP4

# Registers: base address per register type
REG_DTMUL  = 0x30  # + op_offset + ch: DT<<4 | MUL
REG_TL     = 0x40  # + op_offset + ch: TL
REG_KSAR   = 0x50  # + op_offset + ch: KS<<6 | AR
REG_AMDR   = 0x60  # + op_offset + ch: AM<<7 | D1R
REG_D2R    = 0x70  # + op_offset + ch: D2R
REG_SLRR   = 0x80  # + op_offset + ch: SL<<4 | RR
REG_SSGEG  = 0x90  # + op_offset + ch: SSG-EG
REG_ALGFB  = 0xB0  # + ch: ALG | FB<<3
REG_LRPAN  = 0xB4  # + ch: L/R pan + AMS/PMS

# Channel index from register low nibble (ch4-6 come from Part 2)
_CH_FROM_NIBBLE = {0: 0, 1: 1, 2: 2, 4: 3, 5: 4, 6: 5}


@dataclass
class FMOperator:
    dt:   int = 0
    mul:  int = 0
    tl:   int = 0
    ks:   int = 0
    ar:   int = 0
    am:   int = 0
    d1r:  int = 0
    d2r:  int = 0
    sl:   int = 0
    rr:   int = 0
    ssgeg_enabled: bool = False
    ssgeg_shape:   int  = 0


@dataclass
class FMPatch:
    """A fully decoded YM2612 FM patch as observed from register writes."""
    channel:    int               # 0-5 (0=ch1, 5=ch6)
    alg:        int = 0           # algorithm 0-7
    fb:         int = 0           # feedback 0-7
    lr:         int = 3           # L/R pan bits (3=stereo)
    operators:  list[FMOperator] = field(default_factory=lambda: [FMOperator() for _ in range(4)])
    patch_hash: str = ""          # SHA1 of canonical params (excluding TL — volume-varying)

    def compute_hash(self) -> str:
        """Structural hash: ALG+FB+per-op params excluding TL (volume-dependent)."""
        parts = [str(self.alg), str(self.fb)]
        for op in self.operators:
            parts += [str(op.dt), str(op.mul), str(op.ks), str(op.ar),
                      str(op.am), str(op.d1r), str(op.d2r), str(op.sl),
                      str(op.rr), str(int(op.ssgeg_enabled)), str(op.ssgeg_shape)]
        raw = "|".join(parts).encode()
        self.patch_hash = hashlib.sha1(raw).hexdigest()[:12]
        return self.patch_hash

    def to_dict(self) -> dict:
        d = asdict(self)
        d["patch_hash"] = self.patch_hash or self.compute_hash()
        return d


def _part_and_ch(reg: int, is_part2: bool) -> tuple[int, int] | None:
    """Return (part, ch_index) or None if reg is not an FM channel register."""
    ch_nibble = reg & 0x03
    if ch_nibble == 3:
        return None
    ch = _CH_FROM_NIBBLE.get(ch_nibble if not is_part2 else ch_nibble + 4)
    if ch is None:
        return None
    return (2 if is_part2 else 1), ch


def _op_from_reg(reg: int) -> int | None:
    """Return operator index (0-3) from register address."""
    op_nibble = (reg >> 2) & 0x03
    # Operator interleave: offset 0x00→op0, 0x04→op2, 0x08→op1, 0x0C→op3
    interleave = {0: 0, 1: 2, 2: 1, 3: 3}
    return interleave.get(op_nibble)


def extract_patches_from_events(events: list[dict[str, Any]]) -> list[FMPatch]:
    """
    Scan a VGM event list for YM2612 register writes and reconstruct
    FM patches as they are loaded.

    Each time ALG/FB (0xB0) is written, snapshot the current register
    state for that channel as a new patch observation.

    events: list of {type, reg, val, ts, part} dicts from vgm_parser
    Returns: list of FMPatch (may have duplicates — same patch reloaded)
    """
    # Per-channel register state
    state: dict[int, dict] = {ch: {} for ch in range(6)}

    def _ch(reg: int, part: int) -> int | None:
        nibble = reg & 0x03
        if nibble == 3:
            return None
        base = 0 if part == 1 else 3
        return _CH_FROM_NIBBLE.get(nibble + (4 if part == 2 else 0))

    patches: list[FMPatch] = []

    for ev in events:
        ev_type = str(ev.get("type", ""))
        if "YM2612" not in ev_type and "ym2612" not in ev_type.lower():
            continue

        reg = ev.get("reg", -1)
        val = ev.get("val", 0)
        part = 2 if ev.get("part", 1) == 2 else 1

        if not (0x00 <= reg <= 0xFF):
            continue

        ch = _ch(reg, part)
        if ch is None:
            continue

        base = reg & 0xFC   # strip ch offset
        op_idx = None

        if 0x30 <= base <= 0x9C:
            # Operator register — determine which op
            op_sub = (reg - 0x30) >> 2
            interleave = {0: 0, 1: 2, 2: 1, 3: 3}
            op_idx = interleave.get((reg >> 2) & 0x03)

        s = state[ch]
        s.setdefault("ops", [{} for _ in range(4)])

        if base == REG_ALGFB:
            s["alg"] = val & 0x07
            s["fb"]  = (val >> 3) & 0x07
            # Snapshot this channel as a patch
            patch = _snapshot(ch, s)
            patches.append(patch)
        elif base == REG_LRPAN:
            s["lr"] = (val >> 6) & 0x03
        elif op_idx is not None:
            op = s["ops"][op_idx] if op_idx < 4 else {}
            if   0x30 <= base <= 0x3C: op["dt"] = (val >> 4) & 0x07; op["mul"] = val & 0x0F
            elif 0x40 <= base <= 0x4C: op["tl"]  = val & 0x7F
            elif 0x50 <= base <= 0x5C: op["ks"]  = (val >> 6) & 0x03; op["ar"]  = val & 0x1F
            elif 0x60 <= base <= 0x6C: op["am"]  = (val >> 7) & 0x01; op["d1r"] = val & 0x1F
            elif 0x70 <= base <= 0x7C: op["d2r"] = val & 0x1F
            elif 0x80 <= base <= 0x8C: op["sl"]  = (val >> 4) & 0x0F; op["rr"]  = val & 0x0F
            elif 0x90 <= base <= 0x9C:
                op["ssgeg_enabled"] = bool(val & 0x08)
                op["ssgeg_shape"]   = val & 0x07
            if op_idx < 4:
                s["ops"][op_idx] = op

    return patches


def _snapshot(ch: int, state: dict) -> FMPatch:
    patch = FMPatch(channel=ch)
    patch.alg = state.get("alg", 0)
    patch.fb  = state.get("fb",  0)
    patch.lr  = state.get("lr",  3)
    for i, op_state in enumerate(state.get("ops", [{} for _ in range(4)])):
        if i >= 4:
            break
        op = patch.operators[i]
        op.dt            = op_state.get("dt", 0)
        op.mul           = op_state.get("mul", 0)
        op.tl            = op_state.get("tl", 0)
        op.ks            = op_state.get("ks", 0)
        op.ar            = op_state.get("ar", 0)
        op.am            = op_state.get("am", 0)
        op.d1r           = op_state.get("d1r", 0)
        op.d2r           = op_state.get("d2r", 0)
        op.sl            = op_state.get("sl", 0)
        op.rr            = op_state.get("rr", 0)
        op.ssgeg_enabled = op_state.get("ssgeg_enabled", False)
        op.ssgeg_shape   = op_state.get("ssgeg_shape", 0)
    patch.compute_hash()
    return patch


def patch_set_from_events(events: list[dict]) -> set[str]:
    """Return the set of unique patch hashes observed in a VGM event stream."""
    return {p.patch_hash for p in extract_patches_from_events(events)}


def patch_overlap(set_a: set[str], set_b: set[str]) -> float:
    """
    Jaccard-like overlap between two patch sets.
    1.0 = all patches in A also appear in B (composer reused instruments).
    0.0 = no shared instruments.
    """
    if not set_a:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

