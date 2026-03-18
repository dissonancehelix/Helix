"""
adapter_gems.py — Helix adapter for GEMS driver constants
==========================================================
Source references:
    data/music/source/code/GEMS/GEMS.DOC    — authoritative v2.0 documentation
    data/music/source/code/GEMS/GEMS/GEMS.H — C API header (Recreational Brainware)
    data/music/source/code/GEMS/GEMS/Z80.ASM — Z80 driver implementation
    data/music/source/code/MidiConverters/gems2mid.c — GEMS→MIDI converter

Purpose:
    Provide ALL structural constants from the Genesis Editor for Music and Sound
    (GEMS) driver v2.0. GEMS is Sega of America's interactive audio driver,
    used by Comix Zone, Sonic Spinball, Sonic 3D Blast (SoA), and many other
    licensed Genesis titles.

    Also bridges the gems2mid converter (via tool_bridge) for GEMS sequence →
    MIDI conversion, enabling the chip→symbolic translation path.

GEMS vs SMPS structural differences:
    - GEMS is event-driven (tempo in BPM), SMPS is tick-quantized (60/50Hz)
    - GEMS has dynamic voice allocation (no fixed channel assignment)
    - GEMS exposes a 30-mailbox shared-memory system for game integration
    - GEMS channel model maps 1:1 to MIDI channels (16 max)
    - GEMS FM patch bank: separate patch bank + modulator (pitch env) bank

Input:
    query (str)  — one of:
        "patch_format"  — FM patch byte layout
        "channels"      — hardware voice counts
        "sequencer"     — timing, resolution, loop, conditional opcodes
        "audio"         — digital sample playback constants
        "midi_map"      — MIDI controller mappings used by GEMS
        "allocation"    — voice allocation and priority system
        "all"
    OR for MIDI conversion:
    gems_seq_path (str)  — path to GEMS sequence file
    output_midi_path (str | None)  — output MIDI path (optional)

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

# ---------------------------------------------------------------------------
# Hardware voice allocation
# ---------------------------------------------------------------------------

_FM_CHANNELS  = 6   # YM2612 FM channels (GEMS uses all 6 dynamically)
_PSG_CHANNELS = 4   # SN76489: 3 tone + 1 noise

# FM channel special modes (from GEMS.DOC hardware_voices)
FM_CHANNEL_SPECIAL_MODES: dict[str, str] = {
    "channel_3": (
        "Ch3 operator-frequency mode — assigns arbitrary frequency to each of "
        "4 operators independently. Used for drum/percussion. "
        "GEMS voice allocator avoids this channel for normal FM patches."
    ),
    "channel_6": (
        "DAC mode — digital PCM sample playback at 5200–10400 Hz. "
        "GEMS voice allocator avoids this channel for normal FM patches. "
        "Z80 runs sample playback; 68000 halts Z80 for MIDI reads."
    ),
}

# PSG special mode
PSG_CHANNEL_3_NOTE = (
    "PSG voice 3 (noise) can be driven by PSG tone channel 2 frequency — "
    "enables frequency-swept noise (explosion effects, etc.)"
)

# ---------------------------------------------------------------------------
# Sequencer / timing
# ---------------------------------------------------------------------------

# Sequencer resolution (from GEMS.DOC sequencer section)
SEQUENCER_RESOLUTION_DIVISIONS = 24      # 1/24 of a beat (quarter note)
SEQUENCER_NOTE_DIVISIONS = {
    "quarter":   1,    # 24 ticks
    "eighth":    2,    # 12 ticks
    "sixteenth":  4,   #  6 ticks
    "64th_triplet": 1, #  1 tick minimum resolution (1/64 note triplet)
}

TEMPO_RANGE_BPM_MIN  = 40
TEMPO_RANGE_BPM_MAX  = 167
SFX_TEMPO_BPM        = 150    # fixed timebase for all sound effects

LOOP_DEPTH_MAX       = 4      # max nested loop depth per sequence
CHANNELS_PER_SEQUENCE_MAX = 16  # 16 MIDI channels per sequence

# Conditional sequencer opcodes (from GEMS.DOC)
CONDITIONAL_OPCODES: list[str] = ["Label", "Goto", "If", "Store"]

# ---------------------------------------------------------------------------
# Mailbox system (from GEMS.DOC + GEMS.H)
# ---------------------------------------------------------------------------

MAILBOX_COUNT   = 30    # shared 68000↔GEMS communication variables (indices 0–29)
MAILBOX_VALUE_MIN = 0
MAILBOX_VALUE_MAX = 127
MAILBOX_NOTE = (
    "30 shared variables readable and writable by both 68000 game code "
    "(via gemsreadmbox/gemsstorembox) and GEMS sequence 'Store' opcodes. "
    "Used for game-state-driven music events and conditional branching."
)

# ---------------------------------------------------------------------------
# Digital audio / sample playback (from GEMS.DOC digital_audio + GEMS.H)
# ---------------------------------------------------------------------------

DIGITAL_AUDIO_BIT_DEPTH   = 8          # 8-bit signed PCM samples
DIGITAL_AUDIO_RATE_MIN_HZ = 5200       # lowest supported playback rate
DIGITAL_AUDIO_RATE_MAX_HZ = 10400      # highest supported playback rate

# gemssamprate() rate constants (from GEMS.H comments)
SAMPLE_RATE_CONSTANTS: dict[int, str] = {
    4: "Don't override rate — use rate stored in sample bank",
    5: "Play at 10.4 kHz (GEMS-standard high-quality rate)",
}

SAMPLE_CPU = "Z80"  # Z80 runs sample playback loop
SAMPLE_LATENCY_NOTE = (
    "68000 must halt Z80 to read MIDI data (gemsholdz80/gemsreleasez80). "
    "This causes audio quality degradation in MIDI authoring mode. "
    "Not an issue during in-game playback."
)

# ---------------------------------------------------------------------------
# MIDI controller mappings (from GEMS.DOC + GEMS.H API)
# ---------------------------------------------------------------------------

MIDI_CONTROLLER_MAP: dict[int, str] = {
    19:  "Channel priority (0–127; higher steals voices from lower)",
    68:  "Pitch modulator trigger/retrigger mode (0x80=on, 0=off)",
    80:  "Pitch modulator select (envelope index for pitch envelope)",
}

# gemssustain mode (from GEMS.H)
SUSTAIN_MODES: dict[int, str] = {
    0x80: "Sustain on — rotate through free voices (polyphonic)",
    0x00: "Sustain off — stay on one voice (monophonic per channel)",
}

# ---------------------------------------------------------------------------
# Voice allocation / priority system (from GEMS.DOC voice_allocation)
# ---------------------------------------------------------------------------

PRIORITY_RANGE_MIN = 0
PRIORITY_RANGE_MAX = 127
PRIORITY_NOTE = (
    "GEMS dynamically allocates hardware voices based on priority. "
    "When all voices are busy, higher-priority notes steal from lower. "
    "Default priority = 0. Typical assignments: "
    "music channels 1–10 (priority 0–30), SFX 99–103, digital samples 110."
)

TYPICAL_PRIORITY_ASSIGNMENTS: dict[str, dict] = {
    "music_channels":  {"channel_range": "1–10",  "typical_priority": "0–30"},
    "sfx_channels":    {"channel_range": "99–103", "typical_priority": "50–80"},
    "digital_samples": {"channel_range": "110",    "typical_priority": "110"},
}

# ---------------------------------------------------------------------------
# Pitch modulation envelope (from GEMS.DOC pitch_modulation)
# ---------------------------------------------------------------------------

PITCH_MOD_SIMULTANEOUS_MAX = 4   # max simultaneously active pitch modulators
PITCH_MOD_TYPE = "Piecewise linear ramp curve over time"
PITCH_MOD_NOTE = (
    "Pitch modulation is applied via separate Modulator Bank (not to be "
    "confused with FM operators). Each modulator is a piecewise linear "
    "pitch envelope triggered by MIDI Controller #68."
)

# ---------------------------------------------------------------------------
# Known game usage (from GEMS.DOC + atlas entity)
# ---------------------------------------------------------------------------

KNOWN_GAMES: list[str] = [
    "Comix Zone",
    "Sonic Spinball",
    "Garfield: Caught in the Act",
    "Sonic 3D Blast (Sega of America version)",
    "Various Sega of America published Genesis titles",
]


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
        base: dict[str, Any] = {"driver": "GEMS", "adapter": "gems"}

        if what in ("patch_format", "all"):
            base.update({
                "patch_byte_length":    _PATCH_BYTE_LENGTH,
                "patch_operator_count": _PATCH_OPERATOR_COUNT,
                "patch_offsets":        PATCH_OFFSETS,
            })

        if what in ("channels", "all"):
            base.update({
                "fm_channels":             _FM_CHANNELS,
                "psg_channels":            _PSG_CHANNELS,
                "fm_channel_special_modes": FM_CHANNEL_SPECIAL_MODES,
                "psg_channel_3_note":      PSG_CHANNEL_3_NOTE,
            })

        if what in ("sequencer", "all"):
            base.update({
                "sequencer_resolution_divisions": SEQUENCER_RESOLUTION_DIVISIONS,
                "tempo_range_bpm_min":            TEMPO_RANGE_BPM_MIN,
                "tempo_range_bpm_max":            TEMPO_RANGE_BPM_MAX,
                "sfx_tempo_bpm":                  SFX_TEMPO_BPM,
                "loop_depth_max":                 LOOP_DEPTH_MAX,
                "channels_per_sequence_max":      CHANNELS_PER_SEQUENCE_MAX,
                "conditional_opcodes":            CONDITIONAL_OPCODES,
            })

        if what in ("audio", "all"):
            base.update({
                "digital_audio_bit_depth":   DIGITAL_AUDIO_BIT_DEPTH,
                "digital_audio_rate_min_hz": DIGITAL_AUDIO_RATE_MIN_HZ,
                "digital_audio_rate_max_hz": DIGITAL_AUDIO_RATE_MAX_HZ,
                "sample_rate_constants":     SAMPLE_RATE_CONSTANTS,
                "sample_cpu":                SAMPLE_CPU,
                "sample_latency_note":       SAMPLE_LATENCY_NOTE,
            })

        if what in ("midi_map", "all"):
            base.update({
                "midi_controller_map": MIDI_CONTROLLER_MAP,
                "sustain_modes":       SUSTAIN_MODES,
            })

        if what in ("allocation", "all"):
            base.update({
                "priority_range_min":            PRIORITY_RANGE_MIN,
                "priority_range_max":            PRIORITY_RANGE_MAX,
                "priority_note":                 PRIORITY_NOTE,
                "typical_priority_assignments":  TYPICAL_PRIORITY_ASSIGNMENTS,
                "mailbox_count":                 MAILBOX_COUNT,
                "mailbox_value_range":           [MAILBOX_VALUE_MIN, MAILBOX_VALUE_MAX],
                "mailbox_note":                  MAILBOX_NOTE,
                "pitch_mod_simultaneous_max":    PITCH_MOD_SIMULTANEOUS_MAX,
                "pitch_mod_type":                PITCH_MOD_TYPE,
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
