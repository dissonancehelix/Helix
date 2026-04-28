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

    github.com/flamewing/flamedriver (S3&K-specific constants)
      flamedriver Z80 ASM: SonicDriverVer, zTrack STRUCT, SSGEG fields
    github.com/sonicretro/s1_music_gen (S1 variant operator ordering)
      smps_voice.h: operator layout 1,3,2,4 for S1 FM voices
    github.com/sonicretro/vgm2smps (SN76489 multi-octave period table)
      sn76489_tone_table[6][12]: 6-octave period reference

Purpose:
    Provide ALL structural constants from the Sega Music Processor System (SMPS)
    driver source code. SMPS is the primary sound driver for Sega Genesis
    (Mega Drive) first-party titles (Sonic 1-3&K, Streets of Rage, etc.).

    These constants are used to interpret VGM register-write streams in
    the context of driver-level behaviour, separating hardware capability
    (YM2612/SN76489) from software orchestration (SMPS).

Input:
    query (str)  — one of:
        "timing"      — tick rates, channel counts
        "opcodes"     — full command opcode table
        "volume"      — FM volume attenuation table, carrier flags
        "psg"         — PSG frequency scale, channel encoding, envelope system
        "fm_format"   — FM patch format, register write order, vibrato/LFO params
        "variants"    — multi-variant type codes (S1/S2/S3/SK/S3D), operator ordering, psg shift
        "s3k"         — S3&K SSGEG constants, extended FM patch format
        "ym2612_clock" — YM2612 clock derivation from master oscillator
        "all"         — everything

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
# YM2612 F-Number scale table  (mdcnt11.asm fm_scale)
# ---------------------------------------------------------------------------

# 12-tone equal temperament F-Number values for one octave.
# SMPS stores frequency as (block << 11 | f_number); this table gives the
# f_number component for notes C through B at the reference octave.
# Frequency formula: f_hz = (clock / 144) × (F_Number / 2^(21 - Block))
# Source: mdcnt11.asm frq_c through frq_b constants
FM_FREQUENCY_TABLE: dict[str, int] = {
    "C":   606,   # 0x25E
    "C#":  644,   # 0x284
    "D":   683,   # 0x2AB
    "D#":  723,   # 0x2D3
    "E":   766,   # 0x2FE
    "F":   813,   # 0x32D
    "F#":  860,   # 0x35C
    "G":   911,   # 0x38F
    "G#":  965,   # 0x3C5
    "A":   1023,  # 0x3FF
    "A#":  542,   # 0x21E (stored halved; ×2 = 1084 = 0x43C)
    "B":   574,   # 0x23E (stored halved; ×2 = 1148 = 0x47C)
}
# Note: A# and B are stored as half-values in the SMPS source (lsr #1 applied
# before use). Multiply by 2 to get the actual F-Number register value.

# ---------------------------------------------------------------------------
# Channel allocation constants  (mdcnt11.asm song channel tables)
# ---------------------------------------------------------------------------

# Channel count constants from mdcnt11.asm symbol definitions
FM_CHANNEL_COUNT     = 6   # fm_no: YM2612 channels available to song engine
PSG_CHANNEL_COUNT    = 3   # psg_no: SN76489 tone channels (not noise)
PCM_CHANNEL_COUNT    = 1   # pcm_no: rhythm/PCM channel
SONG_CHANNEL_TOTAL   = 10  # song_no = fm_no + psg_no + pcm_no
FM_SE_CHANNEL_COUNT  = 3   # fm_se_no: FM sound effect channels (ch 2, 4, 5)
PSG_SE_CHANNEL_COUNT = 3   # psg_se_no: PSG sound effect channels

# FM channel hardware IDs used in se_song_tb (channel work index → YM2612 channel)
FM_CHANNEL_ID_TABLE: list[int] = [6, 0, 1, 2, 4, 5, 6]
# Index 0 = rhythm (ch6), indices 1–3 = FM1–3 (OPN1), indices 4–5 = FM4–5 (OPN2)
# ch6 duplicated at end for DAC overlap handling

# PSG channel latch byte identifiers (se_song_tb PSG entries)
PSG_CHANNEL_IDS: list[int] = [0x80, 0xA0, 0xC0]
# 0x80 = Tone0, 0xA0 = Tone1, 0xC0 = Tone2; 0xE0 = Noise (special case)

# Song channel assignment: song channels 1–6 are FM, 7–9 are PSG, 10 is PCM
# Sound effects use: FM channels 2, 4, 5; PSG channels $80, $A0, $C0, $E0
SONG_CHANNEL_TYPES: dict[str, dict] = {
    "song_fm":   {"channels": [1, 2, 3, 4, 5, 6], "hw_channels": [1, 2, 3, 4, 5, 6]},
    "song_psg":  {"channels": [7, 8, 9],           "hw_ids":      [0x80, 0xA0, 0xC0]},
    "song_pcm":  {"channels": [10],                "hw_channel":  6},  # DAC via ch6
    "se_fm":     {"channels": [2, 4, 5],           "hw_channels": [2, 4, 5]},
    "se_psg":    {"channels": [7, 8, 9],           "hw_ids":      [0x80, 0xA0, 0xC0]},
}

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


# ---------------------------------------------------------------------------
# YM2612 clock derivation  (NTSC master oscillator chain)
# ---------------------------------------------------------------------------

# NTSC Genesis master oscillator: 53.693100 MHz
# Derived from: OSC → ÷14 → YM2612 chip clock → ÷72 → sample rate
# Source: general Genesis hardware reference; confirmed by nukedopn2 source
YM2612_OSC_HZ_NTSC       = 53_693_100       # Hz — NTSC master oscillator
YM2612_OSC_HZ_PAL        = 53_203_424       # Hz — PAL master oscillator
YM2612_MASTER_DIVIDER    = 14               # master → chip clock divisor
YM2612_SAMPLE_DIVIDER    = 72               # chip clock → sample rate divisor
YM2612_CHIP_CLOCK_NTSC   = YM2612_OSC_HZ_NTSC // YM2612_MASTER_DIVIDER  # 3,835,221 Hz
YM2612_SAMPLE_RATE_NTSC  = YM2612_OSC_HZ_NTSC // YM2612_MASTER_DIVIDER // YM2612_SAMPLE_DIVIDER  # 53,267 Hz

# F-Number frequency formula: f_hz = chip_clock / 144 × F_Number / 2^(21 − Block)
# (144 = 2 × 72; the ×2 comes from halving in the YM2612 frequency accumulator)
YM2612_FNUMBER_FORMULA = "f_hz = (chip_clock / 144) × (F_Number / 2^(21 − Block))"

# ---------------------------------------------------------------------------
# SMPS multi-variant type codes
# ---------------------------------------------------------------------------

# SonicDriverVer constant embeds the variant into the Z80 driver binary.
# Source: flamedriver (S3&K = 5), general SMPS source tree conventions.
SMPS_VARIANTS: dict[str, dict] = {
    "S1": {
        "game":           "Sonic the Hedgehog (1991)",
        "sonic_driver_ver": 1,
        "fm_patch_bytes": 25,
        "operator_order": [1, 3, 2, 4],   # S1 ONLY: patches stored OP1,OP3,OP2,OP4
        "ssgeg_support":  False,
        "psg_note_base":  0,              # no inter-variant shift applied
    },
    "S2": {
        "game":           "Sonic the Hedgehog 2 (1992)",
        "sonic_driver_ver": 2,
        "fm_patch_bytes": 25,
        "operator_order": [1, 2, 3, 4],
        "ssgeg_support":  False,
        "psg_note_base":  0,
    },
    "S3": {
        "game":           "Sonic the Hedgehog 3 (1994)",
        "sonic_driver_ver": 3,
        "fm_patch_bytes": 25,
        "operator_order": [1, 2, 3, 4],
        "ssgeg_support":  False,
        "psg_note_base":  0,
    },
    "SK": {
        "game":           "Sonic & Knuckles / Sonic 3 & Knuckles (1994)",
        "sonic_driver_ver": 5,
        "fm_patch_bytes": 29,             # 25 base + 4 SSGEG bytes (one per operator)
        "operator_order": [1, 2, 3, 4],
        "ssgeg_support":  True,
        "psg_note_base":  0,
    },
    "S3D": {
        "game":           "Sonic 3D Blast (1996)",
        "sonic_driver_ver": 6,
        "fm_patch_bytes": 25,
        "operator_order": [1, 2, 3, 4],
        "ssgeg_support":  False,
        "psg_note_base":  0,
    },
}

# S1 operator ordering — OP1, OP3, OP2, OP4 (not sequential)
# Source: s1_music_gen smps_voice.h — confirmed non-standard layout.
# When parsing S1 FM patches, byte positions [1–4] map to OP1, OP3, OP2, OP4
# for MUL/DT1, AR/KS, D1R, D2R, RR/D1L, and TL fields.
# Standard (S2/S3/SK/S3D): OP1, OP2, OP3, OP4.
S1_OPERATOR_ORDER = [1, 3, 2, 4]     # S1 only
STANDARD_OPERATOR_ORDER = [1, 2, 3, 4]  # S2, S3, SK, S3D

# PSG inter-variant semitone shift
# When converting PSG sequences between S1/S2 and S3/SK formats, note indices
# shift by 12 semitones (one octave). Source: vgm2smps psgdelta = 12.
PSG_INTER_VARIANT_SEMITONE_SHIFT = 12  # semitones; S3/SK PSG tuned one octave lower

# ---------------------------------------------------------------------------
# S3&K SSGEG constants  (flamedriver Z80 ASM)
# ---------------------------------------------------------------------------

# YM2612 SSG-EG register addresses (per operator, part 1 and part 2 banks)
# Part 1 (channels 1-3): $90=OP1, $94=OP2, $98=OP3, $9C=OP4
# Part 2 (channels 4-6): same offsets in the $100+ bank
SSGEG_REGISTER_ADDRS: list[int] = [0x90, 0x94, 0x98, 0x9C]

# SSG-EG byte field layout:
#   bit 3:  enable SSG-EG mode (0 = normal envelope, 1 = SSG-EG active)
#   bits 2-0: envelope shape (0-7, only shapes 8-15 are actually effective on hardware)
SSGEG_BIT_ENABLE   = 0x08   # bit 3: set to activate SSG-EG
SSGEG_MASK_SHAPE   = 0x07   # bits 0-2: envelope shape selector
SSGEG_SHAPE_COUNT  = 8      # 8 shapes (0-7), mapped to YM2612 shapes 8-15

# S3&K FM patch format — extended 29-byte layout (SK variant only)
# Base 25 bytes identical to standard SMPS format (see FM_PATCH_BYTE_LENGTH above)
# Bytes 25-28: SSGEG per operator [OP1, OP2, OP3, OP4]
#   Each byte: bit3=enable | bits0-2=shape
# HaveSSGEGFlag: tracked per-channel in zTrack STRUCT (see adapter_s3k_driver.py)
SK_FM_PATCH_BYTE_LENGTH      = 29   # S3&K only: 25 base + 4 SSGEG
SK_FM_PATCH_SSGEG_OFFSET     = 25   # byte index where SSGEG data begins
SK_FM_PATCH_SSGEG_BYTE_COUNT = 4    # one per operator

# SSG-EG envelope shape semantics (YM2612 hardware shapes 8-15)
# SMPS stores shape-8 (0x08) as SSGEG byte shape=0, shape-9 as shape=1, etc.
SSGEG_SHAPE_TABLE: dict[int, str] = {
    0: "attack only (hard reset after peak)",         # YM2612 shape 8
    1: "attack–decay cycle, sustain low",             # shape 9
    2: "attack–decay–attack–decay (saw up)",          # shape 10
    3: "single attack, sustain at peak",              # shape 11
    4: "decay only (hard reset after floor)",         # shape 12
    5: "decay–attack cycle, sustain high",            # shape 13
    6: "decay–attack–decay–attack (saw down)",        # shape 14
    7: "single decay, sustain at floor",              # shape 15
}

# ---------------------------------------------------------------------------
# SN76489 6-octave period table  (vgm2smps sn76489_tone_table[6][12])
# ---------------------------------------------------------------------------

# Period values for SN76489 tone registers across 6 octaves.
# Frequency formula: f_hz = 3,579,545 / (32 × period)
# Octave numbering: octave 0 = lowest (C1 range), octave 5 = highest (C6 range).
# Each row is 12 semitones: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
# Source: vgm2smps sn76489_tone_table — integer period values (rounded).
SN76489_TONE_TABLE: list[list[int]] = [
    # Octave 0 — C1 to B1 (C1 ≈ 32.70 Hz)
    [3414, 3224, 3043, 2873, 2711, 2560, 2416, 2281, 2153, 2033, 1919, 1812],
    # Octave 1 — C2 to B2 (C2 ≈ 65.41 Hz)
    [1707, 1612, 1522, 1436, 1356, 1280, 1208, 1140, 1077, 1016,  960,  906],
    # Octave 2 — C3 to B3 (C3 ≈ 130.81 Hz)
    [ 854,  806,  761,  718,  678,  640,  604,  570,  538,  508,  480,  453],
    # Octave 3 — C4 to B4 (C4 ≈ 261.63 Hz)
    [ 427,  403,  381,  359,  339,  320,  302,  285,  269,  254,  240,  226],
    # Octave 4 — C5 to B5 (C5 ≈ 523.25 Hz)
    [ 214,  202,  190,  180,  170,  160,  151,  143,  135,  127,  120,  113],
    # Octave 5 — C6 to B6 (C6 ≈ 1046.50 Hz)
    [ 107,  101,   95,   90,   85,   80,   76,   71,   67,   64,   60,   57],
]
SN76489_TONE_TABLE_OCTAVES     = 6
SN76489_TONE_TABLE_NOTES       = 12
SN76489_CLOCK_HZ               = 3_579_545  # NTSC Genesis SN76489 clock
SN76489_PERIOD_FORMULA         = "f_hz = 3579545 / (32 × period)"


class Adapter:
    """
    Adapter exposing complete SMPS driver structural constants.

    Covers: timing, full opcode table, PSG frequency scale & envelope system,
    FM patch format, vibrato engine, LFO control, gate system, SSG-EG mode,
    multi-variant type codes, S3&K SSGEG extended patch format, YM2612 clock
    derivation, SN76489 6-octave period table.

    Correct call path:
        HSL → ANALYZE_TRACK operator → Adapter → SMPS constants
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
            what: "timing" | "opcodes" | "volume" | "psg" | "fm_format" |
                  "variants" | "s3k" | "ym2612_clock" | "all"
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

        if what in ("variants", "all"):
            base.update({
                "smps_variants":                    SMPS_VARIANTS,
                "s1_operator_order":                S1_OPERATOR_ORDER,
                "standard_operator_order":          STANDARD_OPERATOR_ORDER,
                "psg_inter_variant_semitone_shift": PSG_INTER_VARIANT_SEMITONE_SHIFT,
            })

        if what in ("s3k", "all"):
            base.update({
                "ssgeg_register_addrs":         SSGEG_REGISTER_ADDRS,
                "ssgeg_bit_enable":             SSGEG_BIT_ENABLE,
                "ssgeg_mask_shape":             SSGEG_MASK_SHAPE,
                "ssgeg_shape_count":            SSGEG_SHAPE_COUNT,
                "ssgeg_shape_table":            SSGEG_SHAPE_TABLE,
                "sk_fm_patch_byte_length":      SK_FM_PATCH_BYTE_LENGTH,
                "sk_fm_patch_ssgeg_offset":     SK_FM_PATCH_SSGEG_OFFSET,
                "sk_fm_patch_ssgeg_byte_count": SK_FM_PATCH_SSGEG_BYTE_COUNT,
            })

        if what in ("ym2612_clock", "all"):
            base.update({
                "ym2612_osc_hz_ntsc":      YM2612_OSC_HZ_NTSC,
                "ym2612_osc_hz_pal":       YM2612_OSC_HZ_PAL,
                "ym2612_master_divider":   YM2612_MASTER_DIVIDER,
                "ym2612_sample_divider":   YM2612_SAMPLE_DIVIDER,
                "ym2612_chip_clock_ntsc":  YM2612_CHIP_CLOCK_NTSC,
                "ym2612_sample_rate_ntsc": YM2612_SAMPLE_RATE_NTSC,
                "ym2612_fnumber_formula":  YM2612_FNUMBER_FORMULA,
                "sn76489_tone_table":      SN76489_TONE_TABLE,
                "sn76489_tone_octaves":    SN76489_TONE_TABLE_OCTAVES,
                "sn76489_tone_notes":      SN76489_TONE_TABLE_NOTES,
                "sn76489_clock_hz":        SN76489_CLOCK_HZ,
                "sn76489_period_formula":  SN76489_PERIOD_FORMULA,
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

    def parse_ssgeg_byte(self, byte: int) -> dict[str, Any]:
        """
        Decompose an SSG-EG byte (S3&K FM patch bytes 25-28) into fields.

        Args:
            byte: raw byte from SK FM patch SSGEG field

        Returns:
            {"enabled": bool, "shape": int (0-7), "shape_desc": str}
        """
        enabled = bool(byte & SSGEG_BIT_ENABLE)
        shape   = byte & SSGEG_MASK_SHAPE
        return {
            "enabled":    enabled,
            "shape":      shape,
            "shape_desc": SSGEG_SHAPE_TABLE.get(shape, "unknown") if enabled else "inactive",
        }

    def parse_sk_fm_patch(self, data: bytes) -> dict[str, Any]:
        """
        Parse a 29-byte S3&K FM patch (SK variant with SSGEG).

        Args:
            data: exactly 29 bytes from smpsHeaderVoice in SK format

        Returns:
            dict with all FM patch fields + ssgeg list of 4 operator dicts
        """
        if len(data) < SK_FM_PATCH_BYTE_LENGTH:
            raise AdapterError(
                f"SK FM patch requires {SK_FM_PATCH_BYTE_LENGTH} bytes, got {len(data)}"
            )
        base = {
            "alg":      data[0] & 0x07,
            "fb":       (data[0] >> 3) & 0x07,
            "operators": [],
        }
        for op_idx in range(4):
            b = 1 + op_idx
            base["operators"].append({
                "op":   STANDARD_OPERATOR_ORDER[op_idx],
                "mult": data[b]        & 0x0F,
                "dt1":  (data[b] >> 4) & 0x07,
                "ar":   data[b + 4]    & 0x1F,
                "ks":   (data[b + 4] >> 6) & 0x03,
                "d1r":  data[b + 8]    & 0x1F,
                "d2r":  data[b + 12]   & 0x1F,
                "rr":   data[b + 16]   & 0x0F,
                "d1l":  (data[b + 16] >> 4) & 0x0F,
                "tl":   data[b + 20]   & 0x7F,
                "ssgeg": self.parse_ssgeg_byte(data[SK_FM_PATCH_SSGEG_OFFSET + op_idx]),
            })
        return base

    def variant_for_driver_ver(self, ver: int) -> str | None:
        """
        Look up SMPS variant key from SonicDriverVer integer.

        Returns the variant key string (e.g. "SK") or None if unknown.
        """
        for key, info in SMPS_VARIANTS.items():
            if info["sonic_driver_ver"] == ver:
                return key
        return None

    def is_available(self) -> bool:
        """SMPS adapter is always available — uses static constants."""
        return True
