"""
SMPS Voice Parser
=================
Parses FM voice/patch tables from SMPS assembly source files (Z80 and 68k variants).

The SMPS macro format (from m5mcr13.lib / mdeq11.lib) encodes YM2612 operator parameters
using 7 macros per voice patch:

    CNF ALG,FBK       → 1 byte: ALG (bits 0-2) | FBK (bits 3-5)
    MD  M1,D1,M2,D2,M3,D3,M4,D4  → 4 bytes: DT<<4|MUL per operator
    TL  T1,T2,T3,T4   → 4 bytes: TL per operator (bit7 set on carrier ops)
    RSAR K1,A1,...K4,A4 → 4 bytes: KS<<6|AR per operator
    D1R X1,X2,X3,X4   → 4 bytes: D1R per operator
    D2R X1,X2,X3,X4   → 4 bytes: D2R per operator
    RRL R1,DL1,...R4,DL4 → 4 bytes: DL<<4|RR per operator

Output: list of VoicePatch dataclasses, each with fully decoded YM2612 parameters.
Cross-reference against VGM register writes to identify instruments.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OperatorParams:
    """YM2612 operator parameters for one operator (1 of 4)."""
    dt: int = 0          # Detune (0-7)
    mul: int = 0         # Multiple (0-15)
    tl: int = 0          # Total Level (0-127; lower = louder)
    ks: int = 0          # Key Scale (0-3)
    ar: int = 0          # Attack Rate (0-31)
    ams_en: int = 0      # AMS Enable (0-1)
    d1r: int = 0         # First Decay Rate (0-31)
    d2r: int = 0         # Second Decay Rate / Sustain Rate (0-31)
    sl: int = 0          # Sustain Level (0-15)
    rr: int = 0          # Release Rate (0-15)
    is_carrier: bool = False  # True if this operator outputs to DAC (algorithm-dependent)


@dataclass
class VoicePatch:
    """One FM voice patch extracted from SMPS assembly source."""
    label: str               # ASM label (e.g. 'TIMB90', 'VOICE_00')
    source_file: str         # Source file name
    game: str                # Game/driver the patch belongs to
    patch_index: int         # Sequential index in this file (0-based)

    alg: int = 0             # Algorithm (0-7)
    fb: int = 0              # Feedback (0-7)
    lr: int = 3              # L/R output (3 = stereo; some variants encode this)

    operators: list[OperatorParams] = field(default_factory=lambda: [OperatorParams() for _ in range(4)])

    def to_ym2612_regs(self, channel: int = 0) -> dict[int, int]:
        """
        Convert patch to a dict of YM2612 register writes for channel 0-2 (port 0).
        Used for cross-referencing against VGM data.
        ch 0-2 → port 0 (0x52), ch 3-5 → port 1 (0x53).
        Operator order in YM2612 registers: OP1(0), OP3(1), OP2(2), OP4(3).
        """
        ch = channel % 3
        regs: dict[int, int] = {}
        # B0: FB/ALG
        regs[0xB0 + ch] = (self.fb << 3) | self.alg
        # B4: L/R/AMS/FMS
        regs[0xB4 + ch] = (self.lr << 6)

        # Operator register offsets: OP1=0, OP3=4, OP2=8, OP4=12
        op_reg_offs = [0, 4, 8, 12]
        for i, op in enumerate(self.operators):
            o = op_reg_offs[i]
            regs[0x30 + o + ch] = (op.dt << 4) | op.mul       # DT1/MUL
            regs[0x40 + o + ch] = op.tl & 0x7F                # TL
            regs[0x50 + o + ch] = (op.ks << 6) | op.ar        # KS/AR
            regs[0x60 + o + ch] = (op.ams_en << 7) | op.d1r   # AMS-EN/D1R
            regs[0x70 + o + ch] = op.d2r & 0x1F               # D2R
            regs[0x80 + o + ch] = (op.sl << 4) | op.rr        # SL/RR
        return regs

    def feature_vector(self) -> list[float]:
        """
        Compact 28-float representation of this patch for similarity matching.
        [alg/7, fb/7, op0.tl/127, op0.ar/31, op0.d1r/31, op0.d2r/31, op0.sl/15, op0.rr/15,
         op1..., op2..., op3...]
        """
        v: list[float] = [self.alg / 7.0, self.fb / 7.0]
        for op in self.operators:
            v += [
                op.tl / 127.0,
                op.ar / 31.0,
                op.d1r / 31.0,
                op.d2r / 31.0,
                op.sl / 15.0,
                op.rr / 15.0,
            ]
        return v  # 2 + 4*6 = 26 dims


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Regex for macro calls — handles spaces/tabs, hex literals (0xNN or NNH), decimals
_HEX_LITERAL = r'(?:0[xX][0-9a-fA-F]+|[0-9a-fA-F]+[hH]|[0-9]+)'
_INT = rf'({_HEX_LITERAL})'
_SEP = r'\s*,\s*'

def _parse_int(s: str) -> int:
    s = s.strip()
    if s.upper().endswith('H'):
        return int(s[:-1], 16)
    if s.startswith(('0x', '0X')):
        return int(s, 16)
    return int(s)


def _make_pattern(macro: str, n_args: int) -> re.Pattern:
    args = (_SEP).join([rf'\s*({_HEX_LITERAL})\s*' for _ in range(n_args)])
    return re.compile(
        rf'^\s*{re.escape(macro)}\s+{args}',
        re.IGNORECASE | re.MULTILINE
    )

_RE_CNF  = _make_pattern('CNF',  2)
_RE_MD   = _make_pattern('MD',   8)
_RE_TL   = _make_pattern('TL',   4)
_RE_RSAR = _make_pattern('RSAR', 8)
_RE_D1R  = _make_pattern('D1R',  4)
_RE_D2R  = _make_pattern('D2R',  4)
_RE_RRL  = _make_pattern('RRL',  8)
_RE_LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)::?\s*$', re.MULTILINE)


def _carriers_for_alg(alg: int) -> set[int]:
    """Return set of operator indices (0-3) that are carriers for a given algorithm."""
    carriers = {
        0: {3},
        1: {3},
        2: {3},
        3: {3},
        4: {1, 3},
        5: {1, 2, 3},
        6: {1, 2, 3},
        7: {0, 1, 2, 3},
    }
    return carriers.get(alg, {3})


def _parse_voice_block(block: str, label: str) -> Optional[VoicePatch]:
    """
    Parse a block of assembly text (the body of one voice patch) into a VoicePatch.
    Returns None if the block doesn't contain a complete patch.
    """
    def find(pat, text):
        m = pat.search(text)
        if m:
            return [_parse_int(g) for g in m.groups()]
        return None

    cnf_args  = find(_RE_CNF, block)
    md_args   = find(_RE_MD, block)
    tl_args   = find(_RE_TL, block)
    rsar_args = find(_RE_RSAR, block)
    d1r_args  = find(_RE_D1R, block)
    d2r_args  = find(_RE_D2R, block)
    rrl_args  = find(_RE_RRL, block)

    if not (cnf_args and md_args and tl_args and rsar_args and d1r_args and d2r_args and rrl_args):
        return None

    alg, fb = cnf_args[0] & 0x07, (cnf_args[0] >> 3) & 0x07 if len(cnf_args) == 1 else (cnf_args[0], cnf_args[1])
    if len(cnf_args) == 1:
        alg = cnf_args[0] & 0x07
        fb  = (cnf_args[0] >> 3) & 0x07
    else:
        alg, fb = cnf_args[0] & 0x07, cnf_args[1] & 0x07

    carriers = _carriers_for_alg(alg)
    ops = []
    for i in range(4):
        dt  = (md_args[i*2+1] >> 4) & 0x07
        mul = md_args[i*2+1] & 0x0F
        tl  = tl_args[i] & 0x7F
        ks  = (rsar_args[i*2] >> 6) & 0x03
        ar  = rsar_args[i*2+1] & 0x1F if len(rsar_args) == 8 else rsar_args[i] & 0x1F
        d1r = d1r_args[i] & 0x1F
        d2r = d2r_args[i] & 0x1F
        sl  = (rrl_args[i*2+1] >> 4) & 0x0F if len(rrl_args) == 8 else (rrl_args[i] >> 4) & 0x0F
        rr  = rrl_args[i*2] & 0x0F if len(rrl_args) == 8 else rrl_args[i] & 0x0F

        # Simpler RSAR: 4 args = KS<<6|AR each
        if len(rsar_args) == 4:
            ks = (rsar_args[i] >> 6) & 0x03
            ar = rsar_args[i] & 0x1F

        # Simpler RRL: 4 args = SL<<4|RR each
        if len(rrl_args) == 4:
            sl = (rrl_args[i] >> 4) & 0x0F
            rr = rrl_args[i] & 0x0F

        ops.append(OperatorParams(
            dt=dt, mul=mul, tl=tl, ks=ks, ar=ar, d1r=d1r, d2r=d2r, sl=sl, rr=rr,
            is_carrier=(i in carriers)
        ))

    return VoicePatch(label=label, source_file='', game='', patch_index=0,
                      alg=alg, fb=fb, operators=ops)


def parse_smps_asm_file(path: Path, game: str = '') -> list[VoicePatch]:
    """
    Parse all voice patches from a single SMPS assembly source file.
    Handles both Z80 (CNF/MD/TL/RSAR/D1R/D2R/RRL) and
    68k (M0/M1/M2/M3/M4/M5/M6) style macro sets.

    Returns list of VoicePatch objects.
    """
    text = path.read_text(encoding='ascii', errors='replace')
    patches: list[VoicePatch] = []

    # Split on label:: anchors that look like voice labels (TIMB*, VOICE_*, etc.)
    # Strategy: find all label:: or label: lines, then extract blocks between them
    label_pat = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)::?\s*$', re.MULTILINE)
    label_matches = list(label_pat.finditer(text))

    for i, lm in enumerate(label_matches):
        label = lm.group(1)
        # Only process labels that look like voice patches (TIMB, VOICE, etc.)
        if not any(label.upper().startswith(p) for p in (
            'TIMB', 'VOICE', 'INST', 'FM_', 'PATCH', 'VCE', 'SND_'
        )):
            continue

        start = lm.end()
        end = label_matches[i+1].start() if i+1 < len(label_matches) else len(text)
        block = text[start:end]

        patch = _parse_voice_block(block, label)
        if patch:
            patch.source_file = path.name
            patch.game = game or path.stem
            patch.patch_index = len(patches)
            patches.append(patch)

    return patches


def parse_smps_source_dir(source_dir: Path, game: str = '') -> list[VoicePatch]:
    """Parse all .s and .src assembly files in a directory recursively."""
    patches: list[VoicePatch] = []
    for ext in ('*.s', '*.src', '*.asm'):
        for fp in sorted(source_dir.rglob(ext)):
            patches.extend(parse_smps_asm_file(fp, game=game or fp.stem))
    return patches


# ---------------------------------------------------------------------------
# Reference library builder
# ---------------------------------------------------------------------------

def build_reference_library(
    source_dirs: dict[str, Path],
    output_path: Optional[Path] = None,
) -> list[dict]:
    """
    Build a cross-reference patch library from multiple SMPS source trees.

    Args:
        source_dirs: dict mapping game_name → source directory path
        output_path: if given, write the library as JSON

    Returns:
        list of patch dicts (one per voice patch found)
    """
    library: list[dict] = []

    for game_name, src_dir in source_dirs.items():
        if not src_dir.exists():
            continue
        patches = parse_smps_source_dir(src_dir, game=game_name)
        for p in patches:
            entry = asdict(p)
            entry['feature_vector'] = p.feature_vector()
            library.append(entry)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(library, indent=2))

    return library


# ---------------------------------------------------------------------------
# VGM patch matcher
# ---------------------------------------------------------------------------

def match_channel_to_patch(
    channel_regs: dict[int, int],
    library: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Given a dict of YM2612 register writes observed for a single channel,
    find the closest matching patches in the reference library.

    channel_regs: {reg_addr: value} — just the operator registers for one channel
    library: list of patch dicts from build_reference_library()
    Returns: list of top_k matches sorted by distance (ascending), each dict has
             {label, game, source_file, distance, feature_vector}
    """
    import math

    def _channel_to_vector(regs: dict[int, int]) -> list[float]:
        """Extract normalised feature vector from raw register dict."""
        # Find ALG/FB from 0xB0+ch
        b0 = next((v for k, v in regs.items() if 0xB0 <= k <= 0xB2), 0)
        alg = b0 & 0x07
        fb  = (b0 >> 3) & 0x07
        v = [alg / 7.0, fb / 7.0]

        op_offs = [0, 4, 8, 12]
        ch = 0
        for o in op_offs:
            tl  = (regs.get(0x40 + o + ch, 0) & 0x7F) / 127.0
            ar  = (regs.get(0x50 + o + ch, 0) & 0x1F) / 31.0
            d1r = (regs.get(0x60 + o + ch, 0) & 0x1F) / 31.0
            d2r = (regs.get(0x70 + o + ch, 0) & 0x1F) / 31.0
            slrr = regs.get(0x80 + o + ch, 0)
            sl  = ((slrr >> 4) & 0x0F) / 15.0
            rr  = (slrr & 0x0F) / 15.0
            v += [tl, ar, d1r, d2r, sl, rr]
        return v  # 26 dims

    query = _channel_to_vector(channel_regs)

    results = []
    for patch in library:
        ref = patch.get('feature_vector', [])
        if len(ref) != len(query):
            continue
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(query, ref)))
        results.append({
            'label':        patch.get('label', '?'),
            'game':         patch.get('game', '?'),
            'source_file':  patch.get('source_file', '?'),
            'alg':          patch.get('alg', 0),
            'fb':           patch.get('fb', 0),
            'distance':     dist,
        })

    results.sort(key=lambda r: r['distance'])
    return results[:top_k]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from substrates.music.ingestion.config import TEMP_DIR, DATA

    smps_dirs = {
        'SOUND-SORCE_Z80_v1.3':  TEMP_DIR / 'SMPS-Z80_source_code' / 'ver13',
        'SOUND-SORCE_68K_v1.1':  TEMP_DIR / 'SMPS-68000_source_code' / 'ver11',
    }

    out = DATA / 'smps_voice_library.json'
    library = build_reference_library(smps_dirs, output_path=out)
    print(f'Extracted {len(library)} voice patches → {out}')

    for p in library[:5]:
        print(f"  {p['game']} / {p['label']}  ALG={p['alg']} FB={p['fb']}")
