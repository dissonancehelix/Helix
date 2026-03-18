"""
adapter_gems.py — Helix adapter for GEMS driver constants
==========================================================
Source references:
    data/music/source/code/GEMS/
    data/music/source/code/GEMSPlay/
    data/music/source/code/MidiConverters/gems2mid.c

Purpose:
    Provide structural constants from the Genesis Editor for Music and Sound
    (GEMS) driver. GEMS is Sega's mid-90s interactive audio driver, used by
    many licensed Genesis/Mega Drive third-party titles.

    Also bridges the gems2mid converter (via tool_bridge) for GEMS sequence →
    MIDI conversion, enabling the chip→symbolic translation path.

GEMS structural constants (from GEMS.DOC and GEMSPlay source):
    - FM patch format: 26 bytes per instrument (4 operators × 6 params + header)
    - Sequence format: event-driven, not tick-quantized like SMPS
    - Tempo: fixed at driver init, stored as BPM not tick-rate
    - Up to 8 FM channels and 4 PSG channels

Input:
    query (str)  — one of: "patch_format", "channels", "all"
    OR for MIDI conversion:
    gems_seq_path (str)  — path to GEMS sequence file
    output_midi_path (str | None)  — output MIDI path (optional)

Output (dict):
    {
        "driver":               "GEMS",
        "fm_channels":          int,
        "psg_channels":         int,
        "patch_byte_length":    int,
        "patch_operator_count": int,
        "patch_offsets":        dict,   # register → byte offset mapping
        "adapter":              "gems",
    }

Adapter rules:
    • Static constants are always Tier A (no compilation needed).
    • MIDI conversion (gems_to_midi) is Tier B — requires gems2mid compiled.
    • No Helix logic. Translation only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


# GEMS FM patch format constants (from GEMS.DOC and MidiConverters/gems2mid.c)
# Each GEMS FM instrument is 26 bytes:
#   Byte 0:    Algorithm (bits 0-2) + Feedback (bits 3-5)
#   Byte 1:    Output mask / stereo flags
#   Bytes 2-7: Operator 1 (M1) parameters
#   Bytes 8-13: Operator 2 (C1) parameters
#   Bytes 14-19: Operator 3 (M2) parameters
#   Bytes 20-25: Operator 4 (C2) parameters
#
# Each operator block (6 bytes):
#   [0] MULT + DT1
#   [1] TL (Total Level, 0-127)
#   [2] AR + KS (Attack Rate + Key Scale)
#   [3] D1R + AM-Enable (Decay 1 Rate)
#   [4] D2R (Decay 2 Rate / Sustain Rate)
#   [5] RR + D1L (Release Rate + Decay 1 Level)

_PATCH_BYTE_LENGTH    = 26
_PATCH_OPERATOR_COUNT = 4

PATCH_OFFSETS: dict[str, Any] = {
    "algorithm_feedback": 0,   # byte 0: bits[2:0]=ALG, bits[5:3]=FB
    "stereo_flags":       1,   # byte 1: output routing
    "operators": {
        0: {"base": 2,  "name": "OP1/M1"},  # modulator 1
        1: {"base": 8,  "name": "OP2/C1"},  # carrier 1
        2: {"base": 14, "name": "OP3/M2"},  # modulator 2
        3: {"base": 20, "name": "OP4/C2"},  # carrier 2
    },
    "operator_field_offsets": {
        "MULT_DT1": 0,   # multiply + detune
        "TL":       1,   # total level (volume, inverted: 0=loud, 127=silent)
        "AR_KS":    2,   # attack rate + key scale
        "D1R_AM":   3,   # decay 1 rate + AM enable
        "D2R":      4,   # decay 2 rate (sustain rate)
        "RR_D1L":   5,   # release rate + decay 1 level
    },
}

# GEMS channel allocation
_FM_CHANNELS  = 8   # up to 8 FM channels (GEMS allocates dynamically)
_PSG_CHANNELS = 4   # SN76489: 3 tone + 1 noise


class Adapter:
    """
    Adapter exposing GEMS driver structural constants and MIDI bridge.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → GEMS constants
        HIL → ANALYZE_TRACK operator → Adapter → tool_bridge.gems_to_midi
    """
    toolkit = "gems"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # MIDI conversion path
        if "gems_seq_path" in payload:
            seq_path = Path(payload["gems_seq_path"])
            out_path = payload.get("output_midi_path")
            return self.convert_to_midi(seq_path, Path(out_path) if out_path else None)
        # Constants query path
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """Return GEMS structural constants."""
        base: dict[str, Any] = {
            "driver":  "GEMS",
            "adapter": "gems",
        }
        if what in ("patch_format", "all"):
            base.update({
                "patch_byte_length":    _PATCH_BYTE_LENGTH,
                "patch_operator_count": _PATCH_OPERATOR_COUNT,
                "patch_offsets":        PATCH_OFFSETS,
            })
        if what in ("channels", "all"):
            base.update({
                "fm_channels":  _FM_CHANNELS,
                "psg_channels": _PSG_CHANNELS,
            })
        return base

    def parse_patch_bytes(self, patch_bytes: bytes) -> dict[str, Any]:
        """
        Parse a raw 26-byte GEMS FM patch into structured fields.

        Args:
            patch_bytes: 26 bytes of raw GEMS patch data.

        Returns:
            Structured dict with algorithm, feedback, and per-operator params.
        """
        if len(patch_bytes) < _PATCH_BYTE_LENGTH:
            raise AdapterError(
                f"GEMS patch requires {_PATCH_BYTE_LENGTH} bytes, "
                f"got {len(patch_bytes)}."
            )
        header  = patch_bytes[0]
        algorithm = header & 0x07
        feedback  = (header >> 3) & 0x07

        operators = []
        for op_idx, op_info in PATCH_OFFSETS["operators"].items():
            base = op_info["base"]
            raw  = patch_bytes[base : base + 6]
            operators.append({
                "index":  op_idx,
                "name":   op_info["name"],
                "MULT":   raw[0] & 0x0F,
                "DT1":    (raw[0] >> 4) & 0x07,
                "TL":     raw[1] & 0x7F,
                "AR":     raw[2] & 0x1F,
                "KS":     (raw[2] >> 6) & 0x03,
                "D1R":    raw[3] & 0x1F,
                "AM_EN":  (raw[3] >> 7) & 0x01,
                "D2R":    raw[4] & 0x1F,
                "RR":     raw[5] & 0x0F,
                "D1L":    (raw[5] >> 4) & 0x0F,
            })
        return {
            "algorithm": algorithm,
            "feedback":  feedback,
            "operators": operators,
            "adapter":   "gems",
        }

    def convert_to_midi(
        self,
        gems_seq_path: Path,
        output_midi_path: Path | None = None,
    ) -> dict[str, Any]:
        """
        Convert a GEMS sequence file to MIDI via gems2mid (Tier B).

        Returns:
            {"success": bool, "midi_path": str | None, "available": bool}
        """
        try:
            from substrates.music.domain_analysis.tool_bridge import gems_to_midi
            result_path = gems_to_midi(gems_seq_path, output_midi_path)
            return {
                "success":    result_path is not None,
                "midi_path":  str(result_path) if result_path else None,
                "available":  True,
                "adapter":    "gems",
            }
        except ImportError:
            return {
                "success":   False,
                "midi_path": None,
                "available": False,
                "adapter":   "gems",
                "error":     "tool_bridge not importable",
            }

    def is_available(self) -> bool:
        """Static constants always available. gems_to_midi requires gcc build."""
        return True

    def is_midi_conversion_available(self) -> bool:
        """Return True if gems2mid binary has been compiled."""
        try:
            from substrates.music.domain_analysis.tool_bridge import available_tools
            return available_tools().get("gems2mid", False)
        except ImportError:
            return False
