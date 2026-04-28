"""
adapter_snes_spc.py — Helix adapter for SNES SPC700 CPU + S-DSP
================================================================
Source references:
    SNESAPU documentation (Caitsith2 / Nall)
    furnace src/engine/platform/snes.cpp/.h
    MAME src/devices/sound/s_dsp.cpp/.h
    anomie's SNES DSP document (anomie's registers)
    SPC file format specification v0.30 (Deflemask, various)

Purpose:
    Complete structural constants for the Super Nintendo Entertainment
    System audio subsystem:

        SPC700   — 8-bit CPU running at 1.024 MHz; hosts the sound program
                   (driver) in 64KB of dedicated RAM; generates note/patch
                   data as DSP register writes
        S-DSP    — Digital Signal Processor; 8 independent voices,
                   BRR-format sample playback, ADSR/GAIN envelope, echo
                   with 8-tap FIR filter, pitch modulation

    The SPC700 is inaccessible during normal gameplay — the main CPU
    communicates via four bidirectional I/O ports. Audio programs are
    completely self-contained in SPC RAM. SPC files capture the full
    64KB RAM + 128-byte DSP register snapshot.

Input:
    query (str) — one of:
        "clock"      — SPC700 clock, DSP sample rate, pitch formula
        "registers"  — complete S-DSP register map (all 128 bytes, $00–$7F)
        "voice"      — per-voice register layout (offsets $V0–$V9)
        "adsr"       — ADSR envelope encoding, rate table, sustain levels
        "gain"       — GAIN register modes (fixed, linear, exponential, bent)
        "brr"        — BRR sample format: block layout, filters, shift range
        "echo"       — echo buffer, FIR coefficients, delay parameters
        "spc_file"   — SPC file format layout
        "all"        — everything

Adapter rules:
    • No Helix logic. Static constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Clock constants
# ---------------------------------------------------------------------------

SPC700_CLOCK_HZ  = 1_024_000    # Hz — SPC700 CPU master clock
APU_RAM_BYTES    = 65_536       # bytes — total SPC700 address space (64KB)
DSP_SAMPLE_RATE  = 32_000       # Hz — S-DSP output sample rate (approximate)
                                # True value: 32040.5 Hz (SPC700_CLOCK / 31.97...)
                                # 32000 Hz is the standard approximation used by players

# DSP clocks at the same 1.024 MHz as SPC700
# It produces one output sample every 32 master clocks → 1024000/32 = 32000 Hz
DSP_CLOCKS_PER_SAMPLE = 32

# Pitch (PITCH register, 14-bit) to frequency conversion:
#   output_freq = PITCH × DSP_SAMPLE_RATE / 0x1000
# So PITCH = 0x1000 → plays sample at its natural rate (32000 Hz reference)
#    PITCH = 0x0800 → one octave down
#    PITCH = 0x2000 → one octave up (max usable before artifacts)
PITCH_UNITY          = 0x1000   # natural rate (1× speed)
PITCH_MAX            = 0x3FFF   # 14-bit maximum
PITCH_FREQ_FORMULA   = "f_hz = PITCH × 32000 / 0x1000"
PITCH_SEMITONE_STEP  = 0x0080   # approximate semitone step at unity pitch
                                # exact: 0x1000 × (2^(1/12) - 1) ≈ 0x0080

# Key-on delay: S-DSP suppresses voice output for 8 samples after KON write.
# Source: MAME s_dsp.cpp `on_cnt = 8`. Some documents cite 5 — 8 is hardware-accurate.
KEY_ON_DELAY_SAMPLES = 8

# SPC700 I/O ports (communication with main 65816 CPU)
SPC_IO_PORT_COUNT    = 4        # ports $00F4–$00F7 (CPU side: $2140–$2143)

# ---------------------------------------------------------------------------
# S-DSP register map — 128 bytes ($00–$7F)
# ---------------------------------------------------------------------------

# Per-voice registers: voice V uses addresses V×0x10 + offset
# Offset within each voice block (0-9):
VOICE_REGISTER_OFFSETS: dict[str, dict] = {
    "VOL_L":  {"offset": 0x0, "size": 1, "type": "signed",
               "desc": "Voice left output volume (signed 8-bit, -128 to +127)"},
    "VOL_R":  {"offset": 0x1, "size": 1, "type": "signed",
               "desc": "Voice right output volume (signed 8-bit)"},
    "PITCH_L":{"offset": 0x2, "size": 1, "type": "uint8",
               "desc": "Pitch low byte (bits 7-0 of 14-bit pitch)"},
    "PITCH_H":{"offset": 0x3, "size": 1, "type": "uint8",
               "desc": "Pitch high byte (bits 13-8 of 14-bit pitch; only bits 5-0 used)"},
    "SCRN":   {"offset": 0x4, "size": 1, "type": "uint8",
               "desc": "Source number — index into sample directory table (0-255)"},
    "ADSR1":  {"offset": 0x5, "size": 1, "type": "bitfield",
               "desc": "ADSR1: bit7=ADSR_enable, bits6-4=DR(0-7), bits3-0=AR(0-15)"},
    "ADSR2":  {"offset": 0x6, "size": 1, "type": "bitfield",
               "desc": "ADSR2: bits7-5=SL(0-7), bits4-0=SR(0-31)"},
    "GAIN":   {"offset": 0x7, "size": 1, "type": "bitfield",
               "desc": "GAIN: bit7=0→fixed(bits6-0), bit7=1→mode in bits6-5, rate in bits4-0"},
    "ENVX":   {"offset": 0x8, "size": 1, "type": "read_only",
               "desc": "Current envelope level (read-only, 0-127, top 7 bits of internal 11-bit envelope)"},
    "OUTX":   {"offset": 0x9, "size": 1, "type": "read_only",
               "desc": "Current voice output (read-only, signed 8-bit, top byte of 16-bit output)"},
}

VOICE_BLOCK_SIZE = 0x10   # 16 bytes per voice block; only first 10 used
VOICE_COUNT      = 8      # 8 independent voices

# Global DSP registers (fixed addresses, not per-voice)
GLOBAL_REGISTERS: dict[int, dict] = {
    0x0C: {"name": "MVOL_L",  "desc": "Master volume left (signed 8-bit)"},
    0x1C: {"name": "MVOL_R",  "desc": "Master volume right (signed 8-bit)"},
    0x2C: {"name": "EVOL_L",  "desc": "Echo volume left (signed 8-bit)"},
    0x3C: {"name": "EVOL_R",  "desc": "Echo volume right (signed 8-bit)"},
    0x4C: {"name": "KON",
           "desc": "Key-on: one bit per voice (bit N = voice N). Write 1 to start voice. "
                   "Must write 0 before next KON to the same voice."},
    0x5C: {"name": "KOFF",
           "desc": "Key-off: one bit per voice. Write 1 to begin release phase."},
    0x6C: {"name": "FLG",
           "desc": "Flags: bit7=RESET(mute all+env→0), bit6=MUTE, bit5=ECHO_DISABLE, "
                   "bits4-0=NOISE_CLK(noise rate index 0-31)"},
    0x7C: {"name": "ENDX",
           "desc": "End flags (read-only): bit set when voice reaches BRR end block. "
                   "Cleared by writing any value."},
    0x0D: {"name": "EFB",
           "desc": "Echo feedback volume (signed 8-bit; added to echo buffer each sample)"},
    0x2D: {"name": "PMON",
           "desc": "Pitch modulation enable: one bit per voice. Voice 0 cannot use PMON. "
                   "PMON voice N: pitch modulated by OUTX of voice N-1."},
    0x3D: {"name": "NON",
           "desc": "Noise enable: one bit per voice. Replaces BRR sample with LFSR noise output."},
    0x4D: {"name": "EON",
           "desc": "Echo enable: one bit per voice. Voice output is summed into echo buffer."},
    0x5D: {"name": "DIR",
           "desc": "Sample directory page: start address of 4-byte directory entries = DIR × $100"},
    0x6D: {"name": "ESA",
           "desc": "Echo buffer start address page: start = ESA × $100"},
    0x7D: {"name": "EDL",
           "desc": "Echo delay: buffer length = EDL × 2048 samples. "
                   "EDL=0 → 1 sample (effectively off). Max useful = 15 (960ms at 32kHz)"},
    # FIR coefficients — 8 signed 8-bit values
    0x0F: {"name": "FIR_C0", "desc": "FIR coefficient 0 (signed 8-bit, earliest tap)"},
    0x1F: {"name": "FIR_C1", "desc": "FIR coefficient 1"},
    0x2F: {"name": "FIR_C2", "desc": "FIR coefficient 2"},
    0x3F: {"name": "FIR_C3", "desc": "FIR coefficient 3"},
    0x4F: {"name": "FIR_C4", "desc": "FIR coefficient 4"},
    0x5F: {"name": "FIR_C5", "desc": "FIR coefficient 5"},
    0x6F: {"name": "FIR_C6", "desc": "FIR coefficient 6"},
    0x7F: {"name": "FIR_C7", "desc": "FIR coefficient 7 (most recent tap)"},
}

FIR_COEFFICIENT_ADDRS = [0x0F, 0x1F, 0x2F, 0x3F, 0x4F, 0x5F, 0x6F, 0x7F]
FIR_COEFFICIENT_COUNT = 8
FIR_DEFAULT_ALL_PASS  = [127, 0, 0, 0, 0, 0, 0, 0]  # C0=127, C1-C7=0 → flat response

# ---------------------------------------------------------------------------
# ADSR envelope
# ---------------------------------------------------------------------------

# ADSR1 ($V5) bit fields:
ADSR1_ENABLE_BIT    = 7           # bit 7: 1=ADSR mode, 0=GAIN mode
ADSR1_DR_BITS       = (6, 4)      # bits 6-4: decay rate (0-7)
ADSR1_AR_BITS       = (3, 0)      # bits 3-0: attack rate (0-15)

# ADSR2 ($V6) bit fields:
ADSR2_SL_BITS       = (7, 5)      # bits 7-5: sustain level (0-7)
ADSR2_SR_BITS       = (4, 0)      # bits 4-0: sustain rate (0-31)

# Sustain level threshold: envelope drops to release when ENVX crosses this
# SL value 0-7 → actual threshold = (SL + 1) × 0x100  (i.e. 1/8 to 8/8 of max)
# ENVX is 7-bit (0-127); sustain threshold = (SL + 1) × 16
SUSTAIN_LEVEL_THRESHOLDS: list[int] = [0x100, 0x200, 0x300, 0x400, 0x500, 0x600, 0x700, 0x800]
# Index = SL value; threshold in internal 11-bit envelope units (range 0-0x7FF)

# ADSR/GAIN rate table — 32 entries
# Each entry is the number of DSP samples (at 32kHz) between envelope steps.
# Rate 0 = never fires. Rates 1-31 decrease geometrically.
# Source: ares-emulator/ares counter.cpp (countdown form); verified against
#         MAME s_dsp.cpp ENVCNT[] which is the count-up form (period = 30720/ENVCNT[n]).
DSP_RATE_TABLE: list[int] = [
       0,                                               # rate  0 = never
    2048, 1536, 1280, 1024,  768,  640,  512,  384,    # rates  1– 8
     320,  256,  192,  160,  128,   96,   80,   64,    # rates  9–16
      48,   40,   32,   24,   20,   16,   12,   10,    # rates 17–24
       8,    6,    5,    4,    3,    2,    1,           # rates 25–31
]
DSP_RATE_ENTRIES    = 32

# MAME ENVCNT[] (count-up form, for reference):
# Envelope counter increments each sample; step fires when it reaches ENVCNT_INIT (30720).
# Period in samples = 30720 / ENVCNT[n]  (matches DSP_RATE_TABLE above).
DSP_ENVCNT_MAME: list[int] = [
        0,                                               # never
       15,   20,   24,   30,   40,   48,   60,   80,   # rates  1– 8
       96,  120,  160,  192,  240,  320,  384,  480,   # rates  9–16
      640,  768,  960, 1280, 1536, 1920, 2560, 3072,   # rates 17–24
     3840, 5120, 6144, 7680,10240,15360,30720,          # rates 25–31
]
DSP_ENVCNT_INIT     = 30720   # counter ceiling

# Attack rate encoding: AR 0-14 → rate_table index = AR × 2 + 1; AR 15 → index 31 (fastest)
# Decay  rate encoding: DR 0-7  → rate_table index = DR × 2 + 16
# Sustain rate: SR 0-31 → rate_table index = SR directly (SR=0 = never fires)
# Release: fixed step of 0x08 per DSP tick (no rate table)

# Envelope step values (internal 11-bit accumulator range 0x000–0x7FF):
ENVELOPE_ATTACK_STEP_NORMAL = 0x020   # +32 per rate period during attack
ENVELOPE_ATTACK_STEP_FINAL  = 0x400   # +1024 on final step to ceiling (overshoots, clamped)
ENVELOPE_DECAY_STEP         = 0x008   # −8 per DSP tick during decay phase (decay rate table selects period)
ENVELOPE_RELEASE_STEP       = 0x008   # −8 per DSP tick during release (key-off)
ENVELOPE_CEILING            = 0x7FF   # maximum envelope value (11-bit)

# Noise clock source: FLG bits 4-0 index directly into DSP_RATE_TABLE.
# There is no separate noise table — noise reuses the ADSR rate ladder.
NOISE_RATE_TABLE_SOURCE = "DSP_RATE_TABLE"   # same table, same indices

# ---------------------------------------------------------------------------
# GAIN register encoding
# ---------------------------------------------------------------------------

# GAIN ($V7) when ADSR1 bit7 = 0 (GAIN mode active):
GAIN_FIXED_BIT      = 7    # bit 7 = 0: fixed gain; 1: dynamic mode
GAIN_FIXED_MAX      = 127  # bits 6-0 = direct gain value (0-127)

# When GAIN bit 7 = 1, bits 6-5 select the mode:
GAIN_MODES: dict[int, dict] = {
    0b00: {
        "name": "linear_decrease",
        "rate_bits": "4-0",
        "desc": "Decrease by 32 per rate period, clamp at 0",
        "step": 32,
    },
    0b01: {
        "name": "exponential_decrease",
        "rate_bits": "4-0",
        "desc": "Decrease by ENVX×255/2048 per rate period (faster from high levels)",
    },
    0b10: {
        "name": "linear_increase",
        "rate_bits": "4-0",
        "desc": "Increase by 32 per rate period, clamp at 0x7FF",
        "step": 32,
    },
    0b11: {
        "name": "bent_line_increase",
        "rate_bits": "4-0",
        "desc": "Increase by 32 per period until ENVX ≥ 0x600 (75%), then increase by 8",
        "step_low": 32,
        "step_high": 8,
        "bend_point": 0x600,  # switch from fast to slow at 75% of max
    },
}
GAIN_MODE_BITS      = (6, 5)   # bits 6-5 select mode when bit 7=1
GAIN_RATE_BITS      = (4, 0)   # bits 4-0 = rate index into DSP_RATE_TABLE

# ---------------------------------------------------------------------------
# BRR (Bit Rate Reduction) sample format
# ---------------------------------------------------------------------------

# BRR is the SNES proprietary lossy audio compression format.
# Samples are stored as 9-byte blocks: 1 header byte + 8 data bytes.
BRR_BLOCK_BYTES      = 9      # bytes per BRR block
BRR_HEADER_BYTES     = 1      # 1 header byte per block
BRR_DATA_BYTES       = 8      # 8 data bytes per block = 16 nibbles = 16 samples
BRR_SAMPLES_PER_BLOCK = 16    # four 4-bit samples per data byte, high nibble first

# Header byte bit layout:
BRR_HEADER_SHIFT_BITS  = (7, 4)  # bits 7-4: right-shift amount (0-12 valid; 13-15 = same as 13)
BRR_HEADER_FILTER_BITS = (3, 2)  # bits 3-2: filter mode (0-3)
BRR_HEADER_LOOP_BIT    = 1       # bit 1: loop flag (1=loop from loop point on end)
BRR_HEADER_END_BIT     = 0       # bit 0: end flag (1=this is the last block)
BRR_SHIFT_MAX_EFFECTIVE = 12     # shifts 13-15 clip all samples to 0

# BRR filter formulas:
# s = decoded nibble (signed 4-bit, scaled by shift)
# p1 = previous decoded sample, p2 = sample before that
# All arithmetic in fixed-point (15-bit precision); results clamped to 16-bit signed
BRR_FILTERS: dict[int, dict] = {
    0: {
        "name": "no_filter",
        "formula": "out = s",
        "p1_coeff": 0.0, "p2_coeff": 0.0,
        "int_ops": "out = s",
        "desc": "No previous sample history used",
    },
    1: {
        "name": "filter_1",
        "formula": "out = s + p1 × 0.46875",
        "p1_coeff": 0.46875, "p2_coeff": 0.0,
        # Integer operations on 15-bit samples (ares/MAME hardware-accurate form):
        "int_ops": "out = s + (p1 >> 1) + ((-p1) >> 5)",
        "desc": "Single-pole IIR: 0.5 - 0.03125 = 0.46875 × p1",
    },
    2: {
        "name": "filter_2",
        "formula": "out = s + p1 × 0.953125 − p2 × 0.46875",
        "p1_coeff":  0.953125, "p2_coeff": -0.46875,
        "int_ops": "out = s + p1 + ((-p1 * 3) >> 6) - (p2 >> 1) + (p2 >> 4)",
        "desc": "Two-pole IIR: stronger resonance (p1 ≈ 1×, p2 ≈ -0.5×)",
    },
    3: {
        "name": "filter_3",
        "formula": "out = s + p1 × 0.8984375 − p2 × 0.40625",
        "p1_coeff":  0.8984375, "p2_coeff": -0.40625,
        "int_ops": "out = s + p1 + ((-p1 * 13) >> 7) - (p2 >> 1) + ((p2 * 3) >> 4)",
        "desc": "Two-pole IIR: maximum resonance / highest BRR compression ratio",
    },
}
# Source for filter coefficients: ares-emulator/ares brr.cpp + MAME s_dsp.cpp (verified)
# Note: some older documents (anomie's SNES DSP doc) give different values such as
# 15/16, 61/32, 115/64, 13/16. These describe the same hardware using a different
# precision convention (16-bit vs 15-bit sample representation). The ares/MAME values
# above are the hardware-accurate integer-arithmetic form.

BRR_SAMPLE_BITS      = 4       # 4-bit signed samples in data bytes
BRR_SAMPLE_MIN       = -8      # 4-bit signed minimum
BRR_SAMPLE_MAX       = 7       # 4-bit signed maximum
BRR_OUTPUT_RANGE     = (-32768, 32767)   # 16-bit signed output after decoding

# Sample directory entry structure (at DIR × $100):
DIR_ENTRY_BYTES     = 4       # 4 bytes per sample directory entry
DIR_START_OFFSET    = 0       # bytes 0-1: start address of sample data (little-endian)
DIR_LOOP_OFFSET     = 2       # bytes 2-3: loop point address (used when BRR end+loop flags set)

# ---------------------------------------------------------------------------
# Echo system
# ---------------------------------------------------------------------------

# Echo buffer: stores stereo 16-bit samples for convolution with FIR filter
ECHO_SAMPLE_BYTES       = 4    # 4 bytes per stereo sample (2 bytes L + 2 bytes R)
ECHO_DELAY_SAMPLES_PER_UNIT = 2048   # EDL × 2048 samples of delay
ECHO_DELAY_MS_PER_UNIT  = 2048 * 1000.0 / DSP_SAMPLE_RATE  # ~64ms per EDL unit
ECHO_DELAY_MIN_MS       = 0    # EDL=0: 1 sample (essentially no delay)
ECHO_DELAY_MAX_MS       = 240  # EDL=15: ~240ms
ECHO_EDL_MAX            = 15   # maximum useful EDL value
ECHO_BUFFER_MAX_BYTES   = ECHO_DELAY_MAX_MS * DSP_SAMPLE_RATE // 1000 * ECHO_SAMPLE_BYTES  # ~30720

# FIR filter: 8 taps, each an 8-bit signed coefficient (-128 to +127)
# Applied to the last 8 echo buffer stereo samples before output
# Internal computation uses 15-bit fixed point; right-shifted by 6 (×64 prescale)
FIR_TAP_COUNT           = 8
FIR_COEFF_RANGE         = (-128, 127)

# ---------------------------------------------------------------------------
# SPC file format (for parsing SPC snapshots)
# ---------------------------------------------------------------------------

SPC_HEADER_SIGNATURE    = b"SNES-SPC700 Sound File Data v0.30\x1a\x1a"
SPC_HEADER_BYTES        = 66    # fixed header length
SPC_RAM_BYTES           = 65536 # SPC700 RAM dump
SPC_DSP_REG_BYTES       = 128   # DSP register dump
SPC_EXTRA_RAM_BYTES     = 64    # extra RAM (IPL ROM shadow)
SPC_TOTAL_BYTES         = SPC_HEADER_BYTES + SPC_RAM_BYTES + SPC_DSP_REG_BYTES + SPC_EXTRA_RAM_BYTES

# SPC header field offsets:
SPC_OFFSET_PC           = 0x25  # 2 bytes: SPC700 program counter
SPC_OFFSET_A            = 0x27  # 1 byte:  accumulator
SPC_OFFSET_X            = 0x28  # 1 byte:  X register
SPC_OFFSET_Y            = 0x29  # 1 byte:  Y register
SPC_OFFSET_PSW          = 0x2A  # 1 byte:  processor status
SPC_OFFSET_SP           = 0x2B  # 1 byte:  stack pointer
SPC_OFFSET_TITLE        = 0x2E  # 32 bytes: song title (null-terminated)
SPC_OFFSET_GAME         = 0x4E  # 32 bytes: game title
SPC_OFFSET_DUMPER       = 0x6E  # 16 bytes: dumper name
SPC_OFFSET_COMMENTS     = 0x7E  # 32 bytes: comments
SPC_OFFSET_DATE         = 0x9E  # 11 bytes: dump date
SPC_OFFSET_PLAY_SECS    = 0xA9  # 3 bytes:  play time in seconds (ASCII)
SPC_OFFSET_FADEOUT_MS   = 0xAC  # 5 bytes:  fadeout time in ms (ASCII)
SPC_OFFSET_ARTIST       = 0xB1  # 32 bytes: artist name
SPC_OFFSET_CHANNEL_DISABLE = 0xD3  # 1 byte: default channel disables (bitmask)
SPC_OFFSET_EMULATOR     = 0xD4  # 1 byte:  emulator used to dump
SPC_OFFSET_RAM_START    = SPC_HEADER_BYTES                  # 0x100 — RAM dump start
SPC_OFFSET_DSP_REG_START = SPC_OFFSET_RAM_START + SPC_RAM_BYTES  # DSP regs
SPC_OFFSET_EXTRA_RAM    = SPC_OFFSET_DSP_REG_START + SPC_DSP_REG_BYTES  # extra RAM


class Adapter:
    """
    Adapter exposing complete SNES SPC700 + S-DSP structural constants.

    Covers: SPC700 clock and DSP sample rate, 14-bit pitch formula, full
    128-byte DSP register map (per-voice offsets + global registers), FIR
    coefficient addresses, ADSR rate table (32 entries), ADSR bit field
    encoding, GAIN register modes (fixed/linear/exponential/bent-line),
    BRR sample format (9-byte blocks, 4 filter formulas, shift encoding),
    echo buffer delay calculation, FIR tap count and coefficient range,
    SPC file format field offsets.

    Correct call path:
        HSL → ANALYZE_TRACK operator → Adapter → SNES SPC constants
    """
    toolkit   = "snes_spc"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.query(payload.get("query", "all"))

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return SNES SPC700 + S-DSP structural constants.

        Args:
            what: "clock" | "registers" | "voice" | "adsr" | "gain" |
                  "brr" | "echo" | "spc_file" | "all"
        """
        base: dict[str, Any] = {"chip": "SNES_SPC700_SDSP", "adapter": "snes_spc"}

        if what in ("clock", "all"):
            base.update({
                "spc700_clock_hz":      SPC700_CLOCK_HZ,
                "apu_ram_bytes":        APU_RAM_BYTES,
                "dsp_sample_rate":      DSP_SAMPLE_RATE,
                "dsp_clocks_per_sample": DSP_CLOCKS_PER_SAMPLE,
                "pitch_unity":          PITCH_UNITY,
                "pitch_max":            PITCH_MAX,
                "pitch_freq_formula":   PITCH_FREQ_FORMULA,
                "pitch_semitone_step":  PITCH_SEMITONE_STEP,
                "key_on_delay_samples": KEY_ON_DELAY_SAMPLES,
            })

        if what in ("registers", "all"):
            base.update({
                "voice_register_offsets": VOICE_REGISTER_OFFSETS,
                "voice_block_size":       VOICE_BLOCK_SIZE,
                "voice_count":            VOICE_COUNT,
                "global_registers":       GLOBAL_REGISTERS,
                "fir_coefficient_addrs":  FIR_COEFFICIENT_ADDRS,
                "fir_default_all_pass":   FIR_DEFAULT_ALL_PASS,
            })

        if what in ("voice", "all"):
            base.update({
                "voice_register_offsets": VOICE_REGISTER_OFFSETS,
                "voice_block_size":       VOICE_BLOCK_SIZE,
                "voice_count":            VOICE_COUNT,
                "pitch_unity":            PITCH_UNITY,
                "pitch_freq_formula":     PITCH_FREQ_FORMULA,
                "key_on_delay_samples":   KEY_ON_DELAY_SAMPLES,
            })

        if what in ("adsr", "all"):
            base.update({
                "adsr1_enable_bit":              ADSR1_ENABLE_BIT,
                "adsr1_dr_bits":                 ADSR1_DR_BITS,
                "adsr1_ar_bits":                 ADSR1_AR_BITS,
                "adsr2_sl_bits":                 ADSR2_SL_BITS,
                "adsr2_sr_bits":                 ADSR2_SR_BITS,
                "sustain_level_thresholds":      SUSTAIN_LEVEL_THRESHOLDS,
                "dsp_rate_table":                DSP_RATE_TABLE,
                "dsp_envcnt_mame":               DSP_ENVCNT_MAME,
                "dsp_envcnt_init":               DSP_ENVCNT_INIT,
                "dsp_rate_entries":              DSP_RATE_ENTRIES,
                "envelope_attack_step_normal":   ENVELOPE_ATTACK_STEP_NORMAL,
                "envelope_attack_step_final":    ENVELOPE_ATTACK_STEP_FINAL,
                "envelope_decay_step":           ENVELOPE_DECAY_STEP,
                "envelope_release_step":         ENVELOPE_RELEASE_STEP,
                "envelope_ceiling":              ENVELOPE_CEILING,
                "noise_rate_table_source":       NOISE_RATE_TABLE_SOURCE,
            })

        if what in ("gain", "all"):
            base.update({
                "gain_fixed_bit":  GAIN_FIXED_BIT,
                "gain_fixed_max":  GAIN_FIXED_MAX,
                "gain_modes":      GAIN_MODES,
                "gain_mode_bits":  GAIN_MODE_BITS,
                "gain_rate_bits":  GAIN_RATE_BITS,
                "dsp_rate_table":  DSP_RATE_TABLE,
            })

        if what in ("brr", "all"):
            base.update({
                "brr_block_bytes":          BRR_BLOCK_BYTES,
                "brr_header_bytes":         BRR_HEADER_BYTES,
                "brr_data_bytes":           BRR_DATA_BYTES,
                "brr_samples_per_block":    BRR_SAMPLES_PER_BLOCK,
                "brr_header_shift_bits":    BRR_HEADER_SHIFT_BITS,
                "brr_header_filter_bits":   BRR_HEADER_FILTER_BITS,
                "brr_header_loop_bit":      BRR_HEADER_LOOP_BIT,
                "brr_header_end_bit":       BRR_HEADER_END_BIT,
                "brr_shift_max_effective":  BRR_SHIFT_MAX_EFFECTIVE,
                "brr_filters":              BRR_FILTERS,
                "brr_sample_bits":          BRR_SAMPLE_BITS,
                "brr_sample_range":         (BRR_SAMPLE_MIN, BRR_SAMPLE_MAX),
                "brr_output_range":         BRR_OUTPUT_RANGE,
                "dir_entry_bytes":          DIR_ENTRY_BYTES,
                "dir_start_offset":         DIR_START_OFFSET,
                "dir_loop_offset":          DIR_LOOP_OFFSET,
            })

        if what in ("echo", "all"):
            base.update({
                "echo_sample_bytes":              ECHO_SAMPLE_BYTES,
                "echo_delay_samples_per_unit":    ECHO_DELAY_SAMPLES_PER_UNIT,
                "echo_delay_ms_per_unit":         round(ECHO_DELAY_MS_PER_UNIT, 2),
                "echo_delay_min_ms":              ECHO_DELAY_MIN_MS,
                "echo_delay_max_ms":              ECHO_DELAY_MAX_MS,
                "echo_edl_max":                   ECHO_EDL_MAX,
                "fir_tap_count":                  FIR_TAP_COUNT,
                "fir_coeff_range":                FIR_COEFF_RANGE,
                "fir_coefficient_addrs":          FIR_COEFFICIENT_ADDRS,
                "fir_default_all_pass":           FIR_DEFAULT_ALL_PASS,
            })

        if what in ("spc_file", "all"):
            base.update({
                "spc_header_bytes":     SPC_HEADER_BYTES,
                "spc_ram_bytes":        SPC_RAM_BYTES,
                "spc_dsp_reg_bytes":    SPC_DSP_REG_BYTES,
                "spc_extra_ram_bytes":  SPC_EXTRA_RAM_BYTES,
                "spc_total_bytes":      SPC_TOTAL_BYTES,
                "spc_offset_title":     SPC_OFFSET_TITLE,
                "spc_offset_game":      SPC_OFFSET_GAME,
                "spc_offset_artist":    SPC_OFFSET_ARTIST,
                "spc_offset_ram_start": SPC_OFFSET_RAM_START,
                "spc_offset_dsp_regs":  SPC_OFFSET_DSP_REG_START,
            })

        return base

    def voice_register_address(self, voice: int, register_name: str) -> int:
        """
        Return DSP register address for a named register on the given voice (0-7).

        Args:
            voice: voice index 0-7
            register_name: key from VOICE_REGISTER_OFFSETS

        Returns:
            DSP register address (0x00-0x7F)
        """
        if not 0 <= voice < VOICE_COUNT:
            raise AdapterError(f"voice must be 0-7, got {voice}")
        if register_name not in VOICE_REGISTER_OFFSETS:
            raise AdapterError(f"Unknown voice register: {register_name!r}")
        return voice * VOICE_BLOCK_SIZE + VOICE_REGISTER_OFFSETS[register_name]["offset"]

    def pitch_to_frequency(self, pitch: int) -> float:
        """Convert 14-bit pitch register to output frequency in Hz."""
        return (pitch / PITCH_UNITY) * DSP_SAMPLE_RATE

    def frequency_to_pitch(self, freq_hz: float) -> int:
        """Convert target frequency to 14-bit pitch register value."""
        raw = round(freq_hz * PITCH_UNITY / DSP_SAMPLE_RATE)
        return max(0, min(PITCH_MAX, raw))

    def echo_delay_ms(self, edl: int) -> float:
        """Return echo delay in milliseconds for a given EDL register value."""
        if not 0 <= edl <= ECHO_EDL_MAX:
            raise AdapterError(f"EDL must be 0-{ECHO_EDL_MAX}, got {edl}")
        samples = max(1, edl) * ECHO_DELAY_SAMPLES_PER_UNIT
        return samples * 1000.0 / DSP_SAMPLE_RATE

    def brr_parse_header(self, header_byte: int) -> dict[str, Any]:
        """Decompose a BRR block header byte into its fields."""
        return {
            "shift":      (header_byte >> 4) & 0xF,
            "filter":     (header_byte >> 2) & 0x3,
            "loop":       bool(header_byte & 0x2),
            "end":        bool(header_byte & 0x1),
            "filter_desc": BRR_FILTERS[(header_byte >> 2) & 0x3]["name"],
        }

    def adsr_rate_period(self, rate_index: int) -> int:
        """Return DSP sample period between envelope steps for a given rate index (0-31)."""
        if not 0 <= rate_index < DSP_RATE_ENTRIES:
            raise AdapterError(f"rate_index must be 0-31, got {rate_index}")
        return DSP_RATE_TABLE[rate_index]

    def is_available(self) -> bool:
        return True
