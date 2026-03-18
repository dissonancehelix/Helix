"""
adapter_smps.py — Helix adapter for SMPS driver constants
==========================================================
Source references:
    data/music/source/code/SMPS/SMPS-68000_source_code/ver11/
      mdcmd11.asm  — command dispatch table (all $E0–$FE opcodes)
      mdpsg11.asm  — PSG frequency scale table, envelope system, channel control
      mdcnt11.asm  — main control loop, vibrato engine, gate system
      mdbse11.s    — back sound-effect data, FM patch macro format
      mdtb11.asm   — address tables, envelope table entries

Purpose:
    Provide ALL structural constants from the Sega Music Processor System (SMPS)
    driver source code. SMPS is the primary sound driver for Sega Genesis
    (Mega Drive) first-party titles (Sonic 1-3&K, Streets of Rage, etc.).

    These constants are used to interpret VGM register-write streams in
    the context of driver-level behaviour, separating hardware capability
    (YM2612/SN76489) from software orchestration (SMPS).

Input:
    query (str)  — one of:
        "timing"     — tick rates, channel counts
        "opcodes"    — full command opcode table
        "volume"     — FM volume attenuation table, carrier flags
        "psg"        — PSG frequency scale, channel encoding, envelope system
        "fm_format"  — FM patch format, register write order, vibrato/LFO params
        "all"        — everything

Adapter rules:
    • No Helix logic. Static constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

_TICK_RATE_NTSC    = 60   # Hz — NTSC vertical interrupt (60.098 Hz, rounded)
_TICK_RATE_PAL     = 50   # Hz — PAL vertical interrupt (50.000 Hz)
_TEMPO1TICK_JITTER = 1    # ±1 tick variance from Z80 mailbox polling latency

# ---------------------------------------------------------------------------
# Channel allocation
# ---------------------------------------------------------------------------

_FM_CHANNELS  = 6   # YM2612 channels 1-6 (channel 6 doubles as DAC)
_PSG_CHANNELS = 4   # SN76489: 3 tone + 1 noise
_DAC_CHANNEL  = 6   # YM2612 channel 6, DAC mode for PCM sample stream

# ---------------------------------------------------------------------------
# Opcode structure
# ---------------------------------------------------------------------------

_NOTE_MIN    = 0x00   # 128 note values (0x00–0x7F)
_NOTE_MAX    = 0x7F
_COMMAND_MIN = 0x80   # driver command range
_COMMAND_MAX = 0xFF

# Full command opcode table from mdcmd11.asm command_tbl + excommand_tbl
# Format: opcode -> (name, arg_bytes, description)
COMMAND_TABLE: dict[int, dict] = {
    0xE0: {"name": "LRPAN",     "arg_bytes": 1, "desc": "L/R pan: 1-byte bitfield (bits 6-7=LR, bits 0-5=AMS/PMS)"},
    0xE1: {"name": "FDT",       "arg_bytes": 1, "desc": "Fine detune: signed 8-bit frequency offset added per tick"},
    0xE2: {"name": "SET_TFLG",  "arg_bytes": 1, "desc": "Set T-flag global byte in sound RAM"},
    0xE3: {"name": "CMTREND",   "arg_bytes": 0, "desc": "Channel trend: ramp TL/RR to silence, then CMEND"},
    0xE4: {"name": "AUTOPAN",   "arg_bytes": 5, "desc": "Automated LR pan: no, table_idx, start, limit, length — 0=off (restores pan)"},
    0xE5: {"name": "PFVADD",    "arg_bytes": 2, "desc": "PSG volume add / FM volume add (dispatches by channel type)"},
    0xE6: {"name": "CMVADD",    "arg_bytes": 1, "desc": "FM volume add: signed delta added to volm, triggers vol_set"},
    0xE7: {"name": "CMTAB",     "arg_bytes": 0, "desc": "Tie flag set (next note is tied to this one, no key-on)"},
    0xE8: {"name": "CMGATE",    "arg_bytes": 1, "desc": "Gate: 1-byte count; decremented per tick; at 0 key-off then null"},
    0xE9: {"name": "LFO",       "arg_bytes": 3, "desc": "LFO: slot_byte (bit mask), lfo_freq_byte, ams_pms_byte"},
    0xEA: {"name": "TEMPO_CHG", "arg_bytes": 1, "desc": "Tempo change: writes to cuntst and rcunt (tempo divisor)"},
    0xEB: {"name": "KEYSET",    "arg_bytes": 1, "desc": "Key set: stores to kyflag in sound RAM"},
    0xEC: {"name": "PVADD",     "arg_bytes": 1, "desc": "PSG volume add: signed delta added to volm (PSG-only, no vol_set)"},
    0xED: {"name": "REGSET",    "arg_bytes": 2, "desc": "Register set (channel-locked): reg, data → opn_wrt_chk"},
    0xEE: {"name": "FMWRITE",   "arg_bytes": 2, "desc": "FM write (channel-unlocked): reg, data → opn1_wrt_chk"},
    0xEF: {"name": "FEV",       "arg_bytes": 1, "desc": "FM envelope/voice: select voice index; triggers full FM patch write"},
    0xF0: {"name": "FVR",       "arg_bytes": 4, "desc": "FM vibrato: delay, count, add (signed), limit — sets fvr_str"},
    0xF1: {"name": "VRON",      "arg_bytes": 0, "desc": "Vibrato on: sets fvr bit without resetting parameters"},
    0xF2: {"name": "CMEND",     "arg_bytes": 0, "desc": "Channel end: key-off, clear enable flag, restore song voice"},
    0xF3: {"name": "CMNOIS",    "arg_bytes": 1, "desc": "PSG noise mode: sets channel to $E0 (noise), writes noise control byte"},
    0xF4: {"name": "VROFF",     "arg_bytes": 0, "desc": "Vibrato off: clears fvr bit"},
    0xF5: {"name": "EV",        "arg_bytes": 1, "desc": "PSG envelope select: 1-byte envelope table index"},
    0xF6: {"name": "CMJUMP",    "arg_bytes": 2, "desc": "Jump: 2-byte signed offset added to table pointer"},
    0xF7: {"name": "CMREPT",    "arg_bytes": 4, "desc": "Repeat: reg_no, count, 2-byte jump offset — decrements counter, jumps if nonzero"},
    0xF8: {"name": "CMCALL",    "arg_bytes": 2, "desc": "Call subroutine: push return addr to 4-byte stack, jump"},
    0xF9: {"name": "CMRET",     "arg_bytes": 0, "desc": "Return: pop 4-byte longword from call stack, +2 adjust"},
    0xFA: {"name": "CMBASE",    "arg_bytes": 1, "desc": "Set cbase: note base offset for this channel"},
    0xFB: {"name": "CMBIAS",    "arg_bytes": 1, "desc": "Bias add: signed delta added to bias (transpose/pitch shift)"},
    0xFC: {"name": "SNG_BASE",  "arg_bytes": 1, "desc": "Song base: set cbase for ALL active song channels simultaneously"},
    0xFD: {"name": "TVR",       "arg_bytes": 1, "desc": "Table vibrato: 1-byte index into tvr table, loads fvr parameters"},
    0xFE: {"name": "DT",        "arg_bytes": 8, "desc": "DT (detune): 8-byte detune data, enables ch2 se_mode for frequency-split"},
}

# Extended commands (via $FF dispatch, excommand_tbl in mdcmd11.asm)
EXTENDED_COMMAND_TABLE: dict[int, dict] = {
    0x00: {"name": "S_PSE", "arg_bytes": 1, "desc": "Song pause on/off: 1=pause all channels (key-off, LR off), 0=resume"},
    0x01: {"name": "SSG",   "arg_bytes": 4, "desc": "SSG-EG mode: writes 4 operator SSG registers with bit3 set, AR=0x1F"},
}

# Backward-compatible flat map (name -> opcode)
COMMAND_OPCODES: dict[str, int] = {v["name"]: k for k, v in COMMAND_TABLE.items()}

# ---------------------------------------------------------------------------
# FM volume attenuation table  (mdcnt11.asm vol_flg_tbl + general design)
# ---------------------------------------------------------------------------

# Driver-level volume attenuation: 16 steps, each is a TL offset added to
# carrier operator TL values. Step 0 = loudest, step 15 = effectively silent.
# Source: general SMPS design (TL offset per voice volume level)
_VOLUME_STEPS = 16
_VOLUME_TL_OFFSETS: list[int] = [
    0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 96, 127
]

# Carrier operator volume flag table — which operators receive volume attenuation
# Source: mdcmd11.asm vol_flg_tbl (bit per operator: bit0=OP1, bit1=OP2, bit2=OP3, bit3=OP4)
# 1 = carrier (gets TL offset), 0 = modulator (TL unchanged)
# Mirrors nuked_opn2 carrier slot logic but as SMPS bitmask form
CARRIER_VOLUME_FLAGS: dict[int, int] = {
    0: 0x08,  # ALG0: OP4 only
    1: 0x08,  # ALG1: OP4 only
    2: 0x08,  # ALG2: OP4 only
    3: 0x08,  # ALG3: OP4 only
    4: 0x0A,  # ALG4: OP2 + OP4 (bits 1,3)
    5: 0x0E,  # ALG5: OP2 + OP3 + OP4 (bits 1,2,3)
    6: 0x0E,  # ALG6: OP2 + OP3 + OP4 (bits 1,2,3)
    7: 0x0F,  # ALG7: all 4 operators (bits 0,1,2,3)
}

# ---------------------------------------------------------------------------
# FM parameter register write order  (mdcmd11.asm fm_reg_tbl / tl_reg_tbl)
# ---------------------------------------------------------------------------

# When SMPS writes a full FM voice (FEV / voice_set), it writes registers in
# this exact order: MUL/DT1 × 4, then AR/KS × 4, then D1R × 4, then D2R × 4,
# then RR/D1L × 4 — then separately TL × 4 (volume-adjusted).
FM_REGISTER_WRITE_ORDER: list[str] = [
    "MU1", "MU2", "MU3", "MU4",   # MULT + DT1 per operator
    "AR1", "AR2", "AR3", "AR4",   # Attack Rate + KS
    "DR1", "DR2", "DR3", "DR4",   # Decay 1 Rate
    "SR1", "SR2", "SR3", "SR4",   # Decay 2 Rate (Sustain Rate)
    "RR1", "RR2", "RR3", "RR4",   # Release Rate + D1L
    "TL1", "TL2", "TL3", "TL4",   # Total Level (written separately after volume-adjust)
]

# SMPS FM patch binary layout (from mdbse11.s CNF/MD/RSAR/D1R/D2R/RRL/TL macros)
# Byte layout of one FM voice in the SMPS voice table:
#   Byte  0:   ALG | (FB << 3)              — CNF macro
#   Bytes 1–4: MUL[1–4] | (DT1[1-4] << 4)  — MD macro (one byte per operator)
#   Bytes 5–8: AR[1–4] | (KS[1-4] << 6)    — RSAR macro
#   Bytes 9–12:  D1R[1–4]                   — D1R macro
#   Bytes 13–16: D2R[1–4]                   — D2R macro
#   Bytes 17–20: RR[1–4] | (D1L[1-4] << 4) — RRL macro
#   Bytes 21–24: TL[1–4]                    — TL macro (raw, before driver volume)
FM_PATCH_BYTE_LENGTH = 25   # 1 + 4×6 = 25 bytes per FM voice in SMPS voice table

# ---------------------------------------------------------------------------
# PSG frequency scale table  (mdpsg11.asm psg_scale)
# ---------------------------------------------------------------------------

# 10-bit SN76489 tone period register values for SMPS note indices 0x81–0xC9
# (73 entries; index 72 = 0 marks noise-mode hihat boundary)
# Note index maps: SMPS note byte 0x81+n uses psg_scale[n+bias]
# Frequency formula: f_hz = 3579545 / (32 × period)
PSG_FREQUENCY_TABLE: list[int] = [
    854, 806, 761, 718, 677, 640,
    604, 570, 538, 507, 479, 452,
    427, 403, 381, 359, 339, 320,
    302, 285, 269, 254, 239, 226,
    214, 201, 190, 180, 169, 160,
    151, 143, 135, 127, 120, 113,
    107, 101,  95,  90,  85,  80,
     75,  71,  67,  64,  60,  57,
     54,  51,  48,  45,  43,  40,
     38,  36,  34,  32,  31,  29,
     27,  26,  24,  23,  22,  21,
     19,  18,  17,   0,  # 0 = noise hihat boundary
]

# PSG channel latch bytes for SN76489 clear (mute all channels)
# Sent in sequence to psg68k to silence the PSG completely
PSG_CLEAR_SEQUENCE: list[int] = [0x9F, 0xBF, 0xDF, 0xFF]
# Format: channel_select (bits 5-4) | register_type (bits 4-3) | volume=15

# PSG channel identifier bytes (high nibble of latch byte for channel select)
# Tone channels: 0x80=Ch0, 0xA0=Ch1, 0xC0=Ch2; Noise: 0xE0
# When channel RAM value chian = $E0 → re-mapped to $C0 for volume writes
PSG_CHANNEL_LATCH_BITS: dict[str, int] = {
    "tone0_freq":   0x80,  # latch | low 4 bits of 10-bit period
    "tone1_freq":   0xA0,
    "tone2_freq":   0xC0,
    "noise":        0xE0,
    "tone0_volume": 0x90,  # channel | 0x10 (volume register bit)
    "tone1_volume": 0xB0,
    "tone2_volume": 0xD0,
    "noise_volume": 0xF0,
}

# PSG off value: channel_byte | 0x1F = set volume to max attenuation (silent)
PSG_SILENCE_MASK = 0x1F

# PSG envelope system (mdpsg11.asm etbend/etbbak/etbrept + mdtb11.asm envetb)
# Envelopes are sequences of 0–127 volume delta values (summed with base volm).
# Special terminal bytes:
PSG_ENVELOPE_COMMANDS: dict[str, int] = {
    "TBEND":  0x80,  # end: hold current value
    "TBBAK":  0x81,  # jump: next byte is index to jump to within envelope
    "TBREPT": 0x82,  # restart: reset envelope counter to 0
}
# 8 predefined envelope shapes defined in mdtb11.asm envetb table (EV1–EV8)
PSG_ENVELOPE_COUNT = 8
PSG_ENVELOPE_MAX_VALUE = 15  # PSG volume register is 4 bits (0=loud, 15=silent)

# ---------------------------------------------------------------------------
# Vibrato / FVR system  (mdcnt11.asm vibr_chk + mdcmd11.asm FVR $F0 + TVR $FD)
# ---------------------------------------------------------------------------

# FVR ($F0) parameter layout — 4 bytes in sequence table:
#   Byte 0: v_delay  — ticks before vibrato starts
#   Byte 1: v_count  — ticks per vibrato step
#   Byte 2: v_add    — signed frequency delta applied per step
#   Byte 3: v_limit  — half-period in steps (0 = symmetric oscillation)
# Note: v_limit stored as (raw >> 1) — the driver halves it for ± symmetry

FVR_PARAM_LAYOUT: dict[str, dict] = {
    "byte_0": {"field": "v_delay",  "type": "uint8",  "desc": "Ticks before vibrato begins"},
    "byte_1": {"field": "v_count",  "type": "uint8",  "desc": "Ticks per vibrato step (sub-cycle)"},
    "byte_2": {"field": "v_add",    "type": "int8",   "desc": "Signed frequency delta per step (in F-Number units)"},
    "byte_3": {"field": "v_limit",  "type": "uint8",  "desc": "Half-period steps; 0=continuous oscillation. Stored >>1."},
}

# LFO ($E9) parameter layout — 3 bytes:
#   Byte 0: slot_mask — bit per operator (bit7=OP1, bit6=OP2, bit5=OP3, bit4=OP4)
#                       matching bit enables AMON (amplitude modulation) for that operator
#   Byte 1: lfo_freq  — YM2612 LFO frequency byte written to reg 0x22 (bits 0-2)
#   Byte 2: ams_pms   — AMS+PMS byte merged with LR pan bits; written to reg 0xB4+ch

LFO_PARAM_LAYOUT: dict[str, dict] = {
    "byte_0": {"field": "slot_mask", "desc": "Operator AM enable: bit7=OP1 … bit4=OP4; matching ops get D1R bit7 set"},
    "byte_1": {"field": "lfo_freq",  "desc": "YM2612 LFO frequency (0-7, reg 0x22 bits 0-2)"},
    "byte_2": {"field": "ams_pms",   "desc": "AMS (bits 5-4) + PMS (bits 2-0); merged with LR from panstr"},
}

# LFO register table (mdcmd11.asm lfo_reg_tbl): DR1, DR2, DR3, DR4
LFO_OPERATOR_DR_REGISTERS: list[str] = ["DR1", "DR2", "DR3", "DR4"]

# ---------------------------------------------------------------------------
# Gate system  (mdcnt11.asm gate_chk)
# ---------------------------------------------------------------------------

# CMGATE ($E8) sets a countdown counter. Each tick the counter decrements.
# When counter reaches 0: null flag set → key-off on next tick.
# 0 in the gate byte disables gating (note holds full duration).
GATE_DISABLED_VALUE = 0
GATE_NOTE: str = (
    "Gate is a per-tick countdown. gate=0x80 means ~half the note length "
    "before key-off (depends on tempo). gate=1 = key-off on next tick."
)

# ---------------------------------------------------------------------------
# SSG-EG operator mode  (mdcmd11.asm jssg, ssg_reg_tbl)
# ---------------------------------------------------------------------------

# SSG mode ($FF 0x01): writes 4 operator SSG registers with bit 3 set,
# then writes AR=0x1F for each operator.
# ssg_reg_tbl: SSG1, AR1, SSG2, AR2, SSG3, AR3, SSG4, AR4
SSG_REGISTER_SEQUENCE: list[str] = ["SSG1", "AR1", "SSG2", "AR2", "SSG3", "AR3", "SSG4", "AR4"]
SSG_BIT_MASK = 0x08  # bit 3 set in SSG register data
SSG_AR_VALUE = 0x1F  # attack rate forced to maximum when SSG mode active


class Adapter:
    """
    Adapter exposing complete SMPS driver structural constants.

    Covers: timing, full opcode table, PSG frequency scale & envelope system,
    FM patch format, vibrato engine, LFO control, gate system, SSG-EG mode.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → SMPS constants
    """
    toolkit  = "smps"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return SMPS structural constants.

        Args:
            what: "timing" | "opcodes" | "volume" | "psg" | "fm_format" | "all"
        """
        base: dict[str, Any] = {"driver": "SMPS", "adapter": "smps"}

        if what in ("timing", "all"):
            base.update({
                "tick_rate_ntsc":      _TICK_RATE_NTSC,
                "tick_rate_pal":       _TICK_RATE_PAL,
                "tempo_jitter_ticks":  _TEMPO1TICK_JITTER,
                "fm_channels":         _FM_CHANNELS,
                "psg_channels":        _PSG_CHANNELS,
                "dac_channel":         _DAC_CHANNEL,
            })

        if what in ("opcodes", "all"):
            base.update({
                "note_range":            [_NOTE_MIN, _NOTE_MAX],
                "command_range":         [_COMMAND_MIN, _COMMAND_MAX],
                "command_table":         COMMAND_TABLE,
                "extended_command_table": EXTENDED_COMMAND_TABLE,
                "command_opcodes":       COMMAND_OPCODES,
            })

        if what in ("volume", "all"):
            base.update({
                "volume_steps":          _VOLUME_STEPS,
                "volume_tl_offsets":     _VOLUME_TL_OFFSETS,
                "carrier_volume_flags":  CARRIER_VOLUME_FLAGS,
            })

        if what in ("psg", "all"):
            base.update({
                "psg_frequency_table":    PSG_FREQUENCY_TABLE,
                "psg_clear_sequence":     PSG_CLEAR_SEQUENCE,
                "psg_channel_latch_bits": PSG_CHANNEL_LATCH_BITS,
                "psg_silence_mask":       PSG_SILENCE_MASK,
                "psg_envelope_commands":  PSG_ENVELOPE_COMMANDS,
                "psg_envelope_count":     PSG_ENVELOPE_COUNT,
                "psg_envelope_max_value": PSG_ENVELOPE_MAX_VALUE,
            })

        if what in ("fm_format", "all"):
            base.update({
                "fm_register_write_order": FM_REGISTER_WRITE_ORDER,
                "fm_patch_byte_length":    FM_PATCH_BYTE_LENGTH,
                "fvr_param_layout":        FVR_PARAM_LAYOUT,
                "lfo_param_layout":        LFO_PARAM_LAYOUT,
                "lfo_operator_dr_regs":    LFO_OPERATOR_DR_REGISTERS,
                "gate_disabled_value":     GATE_DISABLED_VALUE,
                "gate_note":               GATE_NOTE,
                "ssg_register_sequence":   SSG_REGISTER_SEQUENCE,
                "ssg_bit_mask":            SSG_BIT_MASK,
                "ssg_ar_value":            SSG_AR_VALUE,
            })

        return base

    def classify_opcode(self, opcode: int) -> dict[str, Any]:
        """
        Classify a single SMPS byte.

        Returns:
            {"type": "note" | "command", "opcode": int, "name": str | None,
             "arg_bytes": int | None, "desc": str | None}
        """
        if _NOTE_MIN <= opcode <= _NOTE_MAX:
            return {"type": "note", "opcode": opcode, "name": None,
                    "arg_bytes": 0, "desc": "Note value (maps to FM keycode or PSG period table)"}
        entry = COMMAND_TABLE.get(opcode)
        if entry:
            return {"type": "command", "opcode": opcode, **entry}
        return {"type": "command", "opcode": opcode, "name": None,
                "arg_bytes": None, "desc": "Unknown command"}

    def psg_period_to_hz(self, period: int, clock_hz: float = 3_579_545.0) -> float:
        """Convert SN76489 tone period register to output frequency in Hz."""
        if period <= 0:
            return 0.0
        return clock_hz / (32.0 * period)

    def ticks_to_seconds(self, ticks: int, region: str = "ntsc") -> float:
        """Convert SMPS tick count to seconds. region: 'ntsc' or 'pal'."""
        rate = _TICK_RATE_NTSC if region == "ntsc" else _TICK_RATE_PAL
        return ticks / rate

    def is_available(self) -> bool:
        """SMPS adapter is always available — uses static constants."""
        return True
