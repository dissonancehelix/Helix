"""
tool_bridge.py — Subprocess wrappers for compiled C analysis tools
===================================================================
Wraps external C tools as Python calls.  All functions fail gracefully
and return empty results if the tool isn't compiled.  Only tools that
add real analytical value not achievable in pure Python are included.

Tools integrated:
  vgm2txt     (vgmtools)       — precise VGM command-level text decode with
                                 chip register annotations; validates our
                                 Python parser and catches edge cases.
  gems2mid    (MidiConverters) — GEMS sequence → MIDI; direct MIDI export
                                 for tracks using the GEMS driver, bypassing
                                 our YM2612 register reconstruction entirely.
  s98tovgm    (S98toVGM)       — S98 → VGM format conversion; feeds S98
                                 arcade recordings into the libvgm pipeline.
  nsf2vgm     (nsf2vgm)        — NSF → VGM conversion; converts NES NSF
                                 files to VGM for register-level analysis.
  Nuked-OPN2  (ym3438.h)       — register constants / carrier mask per algorithm;
                                 authoritative YM2612 operator topology table.

NOT included (no unique value over existing Python pipeline):
  SMPSPlay    — playback only, no analysis output
  vgmstream   — decodes audio formats; we don't need rendered audio here
  vgm_stat    — redundant with our header parser

Source location: domains/music/data/output/library/source/code/
Build:          run compile_tools() once to produce binaries in toolkits/bin/
"""

from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_TOOLKITS_DIR  = Path(__file__).parent.parent / "toolkits"
_BIN_DIR       = _TOOLKITS_DIR / "bin"

# Root of Helix repo (substrates/music/domain_analysis → up 4 levels)
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_CODE_DIR  = _REPO_ROOT / "data" / "music" / "source" / "code"

_VGM2TXT_SRC   = _TOOLKITS_DIR / "vgmtools" / "vgm2txt.c"
_VGM2TXT_BIN   = _BIN_DIR / "vgm2txt.exe"

_GEMS2MID_SRC  = _CODE_DIR / "MidiConverters" / "gems2mid.c"
_GEMS2MID_BIN  = _BIN_DIR / "gems2mid.exe"

_S98TOVGM_SRC  = _CODE_DIR / "S98toVGM" / "S98toVGM" / "S982VGM.c"
_S98TOVGM_BIN  = _BIN_DIR / "s98tovgm.exe"

_NSF2VGM_SRC   = _CODE_DIR / "nsf2vgm" / "v1.0" / "src" / "main.c"
_NSF2VGM_BIN   = _BIN_DIR / "nsf2vgm.exe"

# ---------------------------------------------------------------------------
# Nuked-OPN2 carrier masks (from ym3438.h — static lookup, no compilation needed)
# ---------------------------------------------------------------------------
# YM2612 operator connection depends on algorithm.
# Operators that output to the DAC (carriers) per algorithm (0–7):
# These are hardware-validated from Nuked-OPN2 ym3438.c op_connect[] tables.
#
# Operator numbering in hardware register space:
#   Slot 0 (reg offset +0) = OP1/M1
#   Slot 1 (reg offset +4) = OP3/C1 (confusingly labeled)
#   Slot 2 (reg offset +8) = OP2/M2
#   Slot 3 (reg offset +C) = OP4/C2 (final carrier in most algorithms)
#
# carrier_slots[alg] = set of slot indices (0–3) that are carriers

CARRIER_SLOTS: dict[int, frozenset[int]] = {
    0: frozenset({3}),            # OP4 only
    1: frozenset({3}),            # OP4 only
    2: frozenset({3}),            # OP4 only
    3: frozenset({3}),            # OP4 only
    4: frozenset({1, 3}),         # OP3 + OP4
    5: frozenset({1, 2, 3}),      # OP2 + OP3 + OP4
    6: frozenset({1, 2, 3}),      # OP2 + OP3 + OP4
    7: frozenset({0, 1, 2, 3}),   # all 4 operators are carriers
}

# Brightness proxy: for each algorithm, mean TL of carrier slots
# Lower TL = louder/brighter carrier output
def carrier_tl_mean(tl_list: list[int], alg: int) -> float:
    """
    Given a list of 4 TL values (one per slot 0–3) and algorithm,
    return mean TL of the carrier operators.

    tl_list: [TL_slot0, TL_slot1, TL_slot2, TL_slot3]
    """
    slots = CARRIER_SLOTS.get(alg, frozenset({3}))
    values = [tl_list[s] for s in slots if s < len(tl_list)]
    return sum(values) / len(values) if values else 127.0


def operator_brightness(tl_list: list[int], alg: int) -> float:
    """
    Normalized carrier brightness: 0 = silent, 1 = maximum output.
    Uses mean TL of carrier operators (TL=0 → loudest, TL=127 → silent).
    """
    mean_tl = carrier_tl_mean(tl_list, alg)
    return 1.0 - (mean_tl / 127.0)


# ---------------------------------------------------------------------------
# Build helper
# ---------------------------------------------------------------------------

def compile_tools(force: bool = False) -> dict[str, bool]:
    """
    Compile C tools to toolkits/bin/.
    Requires gcc in PATH.  Returns {tool: success}.

    Tools compiled:
        vgm2txt   — VGM register dump (from vgmtools)
        gems2mid  — GEMS sequence → MIDI (from MidiConverters)
        s98tovgm  — S98 → VGM format converter (from S98toVGM)
        nsf2vgm   — NSF → VGM format converter (from nsf2vgm)
    """
    _BIN_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, bool] = {}

    tools = [
        ("vgm2txt",
         _VGM2TXT_SRC,
         _VGM2TXT_BIN,
         ["-I", str(_TOOLKITS_DIR / "vgmtools"), "-lz", "-lm"]),
        ("gems2mid",
         _GEMS2MID_SRC,
         _GEMS2MID_BIN,
         ["-I", str(_CODE_DIR / "MidiConverters")]),
        ("s98tovgm",
         _S98TOVGM_SRC,
         _S98TOVGM_BIN,
         ["-I", str(_CODE_DIR / "S98toVGM" / "S98toVGM")]),
        ("nsf2vgm",
         _NSF2VGM_SRC,
         _NSF2VGM_BIN,
         ["-I", str(_CODE_DIR / "nsf2vgm" / "v1.0" / "src"), "-lm"]),
    ]

    for name, src, out, extra_flags in tools:
        if out.exists() and not force:
            log.debug("tool_bridge: %s already compiled at %s", name, out)
            results[name] = True
            continue
        if not src.exists():
            log.warning("tool_bridge: %s source not found at %s", name, src)
            results[name] = False
            continue
        cmd = ["gcc", str(src)] + extra_flags + ["-o", str(out)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                log.info("tool_bridge: compiled %s → %s", name, out)
                results[name] = True
            else:
                log.warning("tool_bridge: compile failed for %s: %s", name, r.stderr[:300])
                results[name] = False
        except Exception as exc:
            log.warning("tool_bridge: compile error for %s: %s", name, exc)
            results[name] = False

    return results


# ---------------------------------------------------------------------------
# vgm2txt: VGM → annotated text dump
# ---------------------------------------------------------------------------

def vgm2txt(vgm_path: Path, no_waits: bool = True) -> list[dict[str, Any]]:
    """
    Run vgm2txt on a VGM/VGZ file and parse the output into structured events.

    Returns a list of event dicts:
      {"t": int, "chip": str, "port": int, "reg": int, "val": int,
       "annotation": str}

    Returns [] if vgm2txt is not compiled or fails.
    """
    if not _VGM2TXT_BIN.exists():
        return []

    try:
        args = [str(_VGM2TXT_BIN)]
        if no_waits:
            args.append("-NoWait")
        args.append(str(vgm_path))

        result = subprocess.run(
            args, capture_output=True, text=True, timeout=30, errors="replace"
        )
        if result.returncode != 0:
            log.debug("vgm2txt failed for %s: %s", vgm_path.name, result.stderr[:200])
            return []

        return _parse_vgm2txt_output(result.stdout)

    except Exception as exc:
        log.debug("vgm2txt error: %s", exc)
        return []


def _parse_vgm2txt_output(text: str) -> list[dict[str, Any]]:
    """Parse vgm2txt text output into structured event dicts."""
    events: list[dict[str, Any]] = []
    # Pattern: optional time, chip name, register hex, value hex, optional annotation
    # e.g.  "00:01.234  YM2612/0  B0 = 34  (alg=4, fb=2)"
    line_re = re.compile(
        r"(?:(\d+:\d+\.\d+)\s+)?"       # optional timestamp
        r"(YM2612|YM2151|PSG|SN76489)"  # chip name
        r"(?:/(\d+))?"                   # optional port
        r"\s+([0-9A-Fa-f]{2})\s*=\s*([0-9A-Fa-f]{2})"  # reg = val
        r"(?:\s+\(([^)]*)\))?",          # optional annotation
        re.IGNORECASE,
    )
    for line in text.splitlines():
        m = line_re.search(line)
        if m:
            ts_str, chip, port, reg_h, val_h, annotation = m.groups()
            events.append({
                "t":          ts_str or "",
                "chip":       chip.upper(),
                "port":       int(port) if port else 0,
                "reg":        int(reg_h, 16),
                "val":        int(val_h, 16),
                "annotation": annotation or "",
            })
    return events


# ---------------------------------------------------------------------------
# gems2mid: GEMS sequence → MIDI
# ---------------------------------------------------------------------------

def gems_to_midi(gems_seq_path: Path, output_midi_path: Path | None = None) -> Path | None:
    """
    Convert a GEMS sequence file to MIDI using gems2mid.
    Returns the output MIDI path if successful, None otherwise.

    If output_midi_path is None, writes to a temp file (caller must clean up).
    """
    if not _GEMS2MID_BIN.exists():
        return None

    if output_midi_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
        tmp.close()
        output_midi_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [str(_GEMS2MID_BIN), str(gems_seq_path), str(output_midi_path)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and output_midi_path.exists():
            return output_midi_path
        log.debug("gems2mid failed for %s: %s", gems_seq_path.name, result.stderr[:200])
        return None
    except Exception as exc:
        log.debug("gems2mid error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# s98tovgm: S98 → VGM format conversion
# ---------------------------------------------------------------------------

def s98_to_vgm(s98_path: Path, output_vgm_path: Path | None = None) -> Path | None:
    """
    Convert an S98 arcade recording to VGM format via s98tovgm.

    S98 files contain FM register dumps from Japanese arcade hardware.
    Converting to VGM enables them to be processed by the libvgm pipeline.

    Returns the output VGM path if successful, None otherwise.
    """
    if not _S98TOVGM_BIN.exists():
        return None

    if output_vgm_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".vgm", delete=False)
        tmp.close()
        output_vgm_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [str(_S98TOVGM_BIN), str(s98_path), str(output_vgm_path)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and output_vgm_path.exists():
            return output_vgm_path
        log.debug("s98tovgm failed for %s: %s", s98_path.name, result.stderr[:200])
        return None
    except Exception as exc:
        log.debug("s98tovgm error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# nsf2vgm: NSF → VGM format conversion
# ---------------------------------------------------------------------------

def nsf_to_vgm(nsf_path: Path, output_vgm_path: Path | None = None) -> Path | None:
    """
    Convert an NSF (NES Sound Format) file to VGM via nsf2vgm.

    NSF files contain NES 2A03 music data. Converting to VGM enables
    register-level analysis via the libvgm pipeline, giving causal timeline
    data not available from the raw NSF format alone.

    Returns the output VGM path if successful, None otherwise.
    """
    if not _NSF2VGM_BIN.exists():
        return None

    if output_vgm_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".vgm", delete=False)
        tmp.close()
        output_vgm_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [str(_NSF2VGM_BIN), str(nsf_path), str(output_vgm_path)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0 and output_vgm_path.exists():
            return output_vgm_path
        log.debug("nsf2vgm failed for %s: %s", nsf_path.name, result.stderr[:200])
        return None
    except Exception as exc:
        log.debug("nsf2vgm error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Tool availability check
# ---------------------------------------------------------------------------

def available_tools() -> dict[str, bool]:
    return {
        "vgm2txt":  _VGM2TXT_BIN.exists(),
        "gems2mid": _GEMS2MID_BIN.exists(),
        "s98tovgm": _S98TOVGM_BIN.exists(),
        "nsf2vgm":  _NSF2VGM_BIN.exists(),
        # Static references — always available (no compilation needed)
        "nuked_opn2_constants": True,
        "nuked_opm_constants":  True,
        "nuked_opl3_constants": True,
        "smps_constants":       True,
        "gems_constants":       True,
    }
