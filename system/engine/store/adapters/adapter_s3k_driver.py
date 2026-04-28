"""
adapter_s3k_driver.py — Helix adapter for Sonic 3 & Knuckles Z80 driver constants
====================================================================================
Source references:
    github.com/flamewing/flamedriver
      Z80.ASM — zTrack STRUCT, sound IDs, Z80 memory map, playback control,
                modulation envelope commands, DAC sample IDs, SSGEG flag

Purpose:
    Provide structural constants from the Sonic 3 & Knuckles (S3&K) Z80 SMPS
    driver implementation (flamedriver). This is the driver variant used in:
      - Sonic the Hedgehog 3 (1994) — 11 music tracks
      - Sonic & Knuckles (1994) — 49 music tracks (combined lock-on)

    These constants govern FM/PSG channel state layout, voice sourcing strategy,
    SSGEG activation, and sound ID routing — all fingerprinting signals for the
    S3K composer attribution testdive.

Input:
    query (str)  — one of:
        "ztrack"    — zTrack STRUCT field offsets and byte layout
        "sound_ids" — music, SFX, and DAC sample ID ranges
        "memory"    — Z80 memory map addresses
        "playback"  — playback control bits and modulation envelope commands
        "voices"    — voice sourcing strategy constants (inline vs UniBank)
        "all"       — everything

Adapter rules:
    • No Helix logic. Static constants only. Always available (Tier A).
"""
from __future__ import annotations

from typing import Any


class AdapterError(Exception):
    pass


# ---------------------------------------------------------------------------
# Z80 memory map  (flamedriver Z80.ASM zRAM/zROM/zHW constants)
# ---------------------------------------------------------------------------

# Z80 work RAM layout — key base addresses
Z80_WORK_RAM_START      = 0x0000   # Z80 RAM base
Z80_DRIVER_CODE_START   = 0x0000   # driver code loaded here at startup
Z80_SOUND_QUEUE         = 0x1B00   # inbound sound request queue (68k→Z80 mailbox)
Z80_TRACK_RAM_BASE      = 0x1C00   # zTrack array start (channel state blocks)
ZGEMS_PSG_FIFO          = 0x1B40   # PSG command FIFO base (same as GEMS; shared convention)

# Hardware register windows in Z80 address space
Z80_YM2612_A0           = 0x4000   # YM2612 part 1 address port
Z80_YM2612_A1           = 0x4001   # YM2612 part 1 data port
Z80_YM2612_B0           = 0x4002   # YM2612 part 2 address port
Z80_YM2612_B1           = 0x4003   # YM2612 part 2 data port
Z80_PSG                 = 0x7F11   # SN76489 data port
Z80_ROM_WINDOW          = 0x8000   # 68k ROM banked window (32KB, bank-switched)
Z80_BANK_REGISTER       = 0x6000   # serial bank register (bit 0 written 9× to set bank)
Z80_BANK_REGISTER_BITS  = 9        # number of bits written to set 512KB bank

# SonicDriverVer embedded constant (identifies this as S3&K driver)
SONIC_DRIVER_VER        = 5        # matches SMPS_VARIANTS["SK"]["sonic_driver_ver"]

# ---------------------------------------------------------------------------
# zTrack STRUCT — per-channel state block  (flamedriver Z80.ASM)
# ---------------------------------------------------------------------------

# Each active channel occupies one zTrack block. The struct is 48 bytes.
# FM channels: 6 blocks at TRACK_RAM_BASE + n×48
# PSG channels: 4 blocks following FM blocks
# Total: 10 channel blocks

ZTRACK_BYTE_LENGTH = 48   # bytes per channel state block

# Field offsets within zTrack (byte offset from block start)
ZTRACK_FIELDS: dict[str, dict] = {
    # Playback pointer and flow control
    "DataPointer":        {"offset": 0,  "size": 2, "desc": "Current read pointer into track data (16-bit)"},
    "ReturnAddress":      {"offset": 2,  "size": 2, "desc": "Call stack return address (one level deep)"},
    "LoopCounters":       {"offset": 4,  "size": 4, "desc": "4 × 8-bit loop counters (for CMREPT / nested loops)"},

    # Timing
    "DurationCounter":    {"offset": 8,  "size": 1, "desc": "Remaining ticks for current note/rest"},
    "SavedDuration":      {"offset": 9,  "size": 1, "desc": "Base duration before gate/tempo scaling"},
    "TempoScaler":        {"offset": 10, "size": 1, "desc": "Per-channel tempo divisor (copy of global cuntst)"},

    # Note / key state
    "NoteFlags":          {"offset": 11, "size": 1, "desc": "Bit flags: bit0=key-on pending, bit1=tie, bit2=rest"},
    "CurrentNote":        {"offset": 12, "size": 1, "desc": "Current SMPS note byte (0x00–0x7F)"},
    "TransposeSemitones": {"offset": 13, "size": 1, "desc": "Signed semitone transpose (cbase + bias sum)"},

    # Volume
    "VolumeSetting":      {"offset": 14, "size": 1, "desc": "Driver volume level (0–15 for FM, 0–15 for PSG)"},
    "VolumeSave":         {"offset": 15, "size": 1, "desc": "Saved volume for restore after SFX"},

    # FM-specific voice state
    "VoiceIndex":         {"offset": 16, "size": 1, "desc": "Index of current FM voice in voice table"},
    "VoicePointer":       {"offset": 17, "size": 2, "desc": "Pointer to current FM voice data (in ROM bank window)"},
    "VoiceBank":          {"offset": 19, "size": 1, "desc": "ROM bank number for voice data (UniBank or inline)"},

    # SSGEG flag — S3&K specific
    "HaveSSGEGFlag":      {"offset": 20, "size": 1, "desc": "0=no SSGEG in current voice; 1=SSGEG bytes present (4 bytes follow TL in patch)"},

    # LFO / modulation
    "LFOData":            {"offset": 21, "size": 3, "desc": "LFO slot mask, freq, AMS/PMS bytes (from $E9 LFO command)"},
    "VibratoDelay":       {"offset": 24, "size": 1, "desc": "FVR vibrato delay countdown"},
    "VibratoCount":       {"offset": 25, "size": 1, "desc": "FVR vibrato step counter"},
    "VibratoAdd":         {"offset": 26, "size": 1, "desc": "FVR signed frequency delta per step"},
    "VibratoLimit":       {"offset": 27, "size": 1, "desc": "FVR half-period steps (stored >>1)"},
    "VibratoFlags":       {"offset": 28, "size": 1, "desc": "Bit flags: bit7=vibrato active, bit6=direction"},

    # Modulation envelope (S3&K addition)
    "ModEnvPointer":      {"offset": 29, "size": 2, "desc": "Pointer to modulation envelope data (0=none)"},
    "ModEnvCounter":      {"offset": 31, "size": 1, "desc": "Modulation envelope step counter"},
    "ModEnvValue":        {"offset": 32, "size": 1, "desc": "Current modulation envelope output value"},

    # Pan
    "PanFlags":           {"offset": 33, "size": 1, "desc": "L/R pan byte (bits 6-7) + AMS/PMS (bits 0-5), written to YM2612 $B4+ch"},
    "AutoPanData":        {"offset": 34, "size": 5, "desc": "AUTOPAN state: active flag, table idx, current, limit, length"},

    # Channel hardware identity
    "ChannelID":          {"offset": 39, "size": 1, "desc": "Hardware channel ID: FM channel number (1-6) or PSG latch byte ($80/$A0/$C0/$E0)"},
    "ChannelType":        {"offset": 40, "size": 1, "desc": "Channel type: 0=FM, 1=PSG tone, 2=PSG noise, 3=DAC"},

    # Sound effect priority
    "SFXPriority":        {"offset": 41, "size": 1, "desc": "Current SFX priority level (0=none; higher=priority)"},

    # Padding / reserved to 48 bytes
    "_reserved":          {"offset": 42, "size": 6, "desc": "Reserved; align to 48-byte struct boundary"},
}

# Channel block base addresses in Z80 RAM
ZTRACK_FM_COUNT  = 6    # FM channels: blocks 0-5
ZTRACK_PSG_COUNT = 4    # PSG channels: blocks 6-9
ZTRACK_TOTAL     = 10   # total channel blocks

def ztrack_address(channel_index: int) -> int:
    """Return the Z80 RAM address of zTrack block for channel_index (0-based)."""
    return Z80_TRACK_RAM_BASE + channel_index * ZTRACK_BYTE_LENGTH

# ---------------------------------------------------------------------------
# Sound ID ranges  (flamedriver Z80.ASM sound request constants)
# ---------------------------------------------------------------------------

# Music track IDs — sent to Z80 via mailbox to start a BGM track
MUSIC_ID_MIN    = 0x00   # first music track ID
MUSIC_ID_MAX    = 0x7F   # last music track ID (128 possible slots)
MUSIC_STOP_ID   = 0x00   # ID 0 = stop all music

# Music ID range only — track IDs are ROM-layout-dependent and incomplete
# without a full flamedriver s3/ + sk/ directory audit.
# Use sound_id range constants below for classification; do not enumerate tracks here.

# Sound effect IDs
SFX_ID_MIN      = 0x80   # SFX range begins at $80
SFX_ID_MAX      = 0xFF   # SFX range ends at $FF

# DAC sample IDs — PCM instrument identifiers fed to GEMS-style DAC engine
# Source: flamedriver DAC sample table ($81–$D9 confirmed range)
DAC_SAMPLE_ID_MIN = 0x81
DAC_SAMPLE_ID_MAX = 0xD9
DAC_SAMPLE_COUNT  = DAC_SAMPLE_ID_MAX - DAC_SAMPLE_ID_MIN + 1  # 89 samples

# ---------------------------------------------------------------------------
# Playback control bits  (flamedriver Z80.ASM flag/mode constants)
# ---------------------------------------------------------------------------

# NoteFlags byte (zTrack offset 11) bit definitions
NOTE_FLAG_KEY_ON_PENDING = 0x01   # key-on requested for next tick
NOTE_FLAG_TIE            = 0x02   # note is tied (no key-on; continue previous)
NOTE_FLAG_REST           = 0x04   # channel is resting (no pitch output)
NOTE_FLAG_SFX_OVERRIDE   = 0x08   # SFX has locked this channel from BGM

# Global playback state flags (in Z80 work RAM, not per-channel)
GLOBAL_FLAG_MUSIC_PAUSED = 0x01   # set by S_PSE $FF 0x01 extended command
GLOBAL_FLAG_FADE_ACTIVE  = 0x02   # volume fade in progress

# Channel type values (zTrack.ChannelType, offset 40)
CHANNEL_TYPE_FM    = 0
CHANNEL_TYPE_PSG   = 1
CHANNEL_TYPE_NOISE = 2
CHANNEL_TYPE_DAC   = 3

# ---------------------------------------------------------------------------
# Modulation envelope commands  (flamedriver — S3&K addition to SMPS)
# ---------------------------------------------------------------------------

# Modulation envelopes are distinct from PSG volume envelopes.
# They apply a signed frequency delta to FM notes over time — creating
# pitch slides, vibrato-like curves, and instrument expression curves.
# ModEnvPointer in zTrack points to the modulation envelope data stream.

MOD_ENV_COMMANDS: dict[str, dict] = {
    "MOD_END":    {"byte": 0xFF, "desc": "End modulation envelope, clear pointer"},
    "MOD_HOLD":   {"byte": 0xFE, "desc": "Hold current modulation value indefinitely"},
    "MOD_LOOP":   {"byte": 0xFD, "desc": "Loop: next byte is byte-offset of loop point"},
    "MOD_RESET":  {"byte": 0xFC, "desc": "Reset envelope counter and restart from byte 0"},
}
# Bytes 0x00–0xFB are signed delta values applied to the frequency accumulator.
MOD_ENV_DATA_MIN = 0x00
MOD_ENV_DATA_MAX = 0xFB

# ---------------------------------------------------------------------------
# Voice sourcing strategies  (flamedriver — smpsHeaderVoice vs smpsHeaderVoiceUVB)
# ---------------------------------------------------------------------------

# Two distinct voice sourcing modes exist in S3&K music files.
# These are a direct composer/arranger fingerprint: the choice of mode
# reflects workflow and was set at authoring time, not overrideable by engine.

VOICE_SOURCE_INLINE = "inline"
# smpsHeaderVoice: FM voice data stored directly inside the music file,
# immediately following the channel headers.
# Use: all 4 voices defined per-track, self-contained.
# Files confirmed using inline: s3_title.bin (Sonic 3 Title Screen)
# Structural signal: voice data offset immediately follows header table.

VOICE_SOURCE_UNIBANK = "unibank"
# smpsHeaderVoiceUVB: FM voice data sourced from a shared voice bank (UniBank)
# loaded separately into ROM bank window. Music file contains only an index
# into the 35-patch UniBank rather than raw voice data.
# Files confirmed using UniBank: aiz1.bin (Angel Island Zone Act 1)
# Structural signal: header table followed by bank index bytes, not raw voices.

UNIBANK_PATCH_COUNT = 35   # number of FM voices in the shared UniBank
UNIBANK_INDEX_MIN   = 0    # first valid UniBank patch index
UNIBANK_INDEX_MAX   = 34   # last valid UniBank patch index (0-based)

VOICE_SOURCING_MODES: dict[str, dict] = {
    VOICE_SOURCE_INLINE: {
        "command":    "smpsHeaderVoice",
        "desc":       "Voice data embedded in music file immediately after channel headers",
        "patch_size": 25,   # bytes; 29 if HaveSSGEGFlag
        "fingerprint": "Voice data pointer is file-relative; data follows header table contiguously",
    },
    VOICE_SOURCE_UNIBANK: {
        "command":    "smpsHeaderVoiceUVB",
        "desc":       "Voice data sourced from shared 35-patch UniBank via index",
        "patch_size": 1,    # only the index byte is in the music file
        "fingerprint": "Header table followed by 1-byte index; voice data in separate bank",
    },
}

# S3 Title screen uses inline voices — extracted from flamedriverdir s3/title.bin analysis
# (4 voices, full inline layout; see S3K testdive dataset)
S3_TITLE_VOICE_COUNT = 4
S3_TITLE_VOICE_SOURCE = VOICE_SOURCE_INLINE


class Adapter:
    """
    Adapter exposing S3&K Z80 driver structural constants (flamedriver).

    Covers: zTrack STRUCT field layout, sound ID ranges, Z80 memory map,
    playback control flags, modulation envelope commands, voice sourcing
    strategy constants (inline vs UniBank).

    Primary use: S3K composer attribution analysis. Voice sourcing mode,
    SSGEG usage, and FM patch algorithm/feedback distributions are the
    core fingerprinting signals.

    Correct call path:
        HSL → ANALYZE_TRACK operator → Adapter → S3K driver constants
    """
    toolkit   = "s3k_driver"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query", "all")
        return self.query(query)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def query(self, what: str = "all") -> dict[str, Any]:
        """
        Return S3&K driver structural constants.

        Args:
            what: "ztrack" | "sound_ids" | "memory" | "playback" | "voices" | "all"
        """
        base: dict[str, Any] = {"driver": "S3K_flamedriver", "adapter": "s3k_driver",
                                 "sonic_driver_ver": SONIC_DRIVER_VER}

        if what in ("ztrack", "all"):
            base.update({
                "ztrack_byte_length": ZTRACK_BYTE_LENGTH,
                "ztrack_fields":      ZTRACK_FIELDS,
                "ztrack_fm_count":    ZTRACK_FM_COUNT,
                "ztrack_psg_count":   ZTRACK_PSG_COUNT,
                "ztrack_total":       ZTRACK_TOTAL,
                "z80_track_ram_base": Z80_TRACK_RAM_BASE,
            })

        if what in ("sound_ids", "all"):
            base.update({
                "music_id_min":       MUSIC_ID_MIN,
                "music_id_max":       MUSIC_ID_MAX,
                "music_stop_id":      MUSIC_STOP_ID,
                "sfx_id_min":         SFX_ID_MIN,
                "sfx_id_max":         SFX_ID_MAX,
                "dac_sample_id_min":  DAC_SAMPLE_ID_MIN,
                "dac_sample_id_max":  DAC_SAMPLE_ID_MAX,
                "dac_sample_count":   DAC_SAMPLE_COUNT,
            })

        if what in ("memory", "all"):
            base.update({
                "z80_work_ram_start":     Z80_WORK_RAM_START,
                "z80_driver_code_start":  Z80_DRIVER_CODE_START,
                "z80_sound_queue":        Z80_SOUND_QUEUE,
                "z80_track_ram_base":     Z80_TRACK_RAM_BASE,
                "z80_ym2612_a0":          Z80_YM2612_A0,
                "z80_ym2612_a1":          Z80_YM2612_A1,
                "z80_ym2612_b0":          Z80_YM2612_B0,
                "z80_ym2612_b1":          Z80_YM2612_B1,
                "z80_psg":                Z80_PSG,
                "z80_rom_window":         Z80_ROM_WINDOW,
                "z80_bank_register":      Z80_BANK_REGISTER,
                "z80_bank_register_bits": Z80_BANK_REGISTER_BITS,
            })

        if what in ("playback", "all"):
            base.update({
                "note_flag_key_on_pending": NOTE_FLAG_KEY_ON_PENDING,
                "note_flag_tie":            NOTE_FLAG_TIE,
                "note_flag_rest":           NOTE_FLAG_REST,
                "note_flag_sfx_override":   NOTE_FLAG_SFX_OVERRIDE,
                "global_flag_music_paused": GLOBAL_FLAG_MUSIC_PAUSED,
                "global_flag_fade_active":  GLOBAL_FLAG_FADE_ACTIVE,
                "channel_type_fm":          CHANNEL_TYPE_FM,
                "channel_type_psg":         CHANNEL_TYPE_PSG,
                "channel_type_noise":       CHANNEL_TYPE_NOISE,
                "channel_type_dac":         CHANNEL_TYPE_DAC,
                "mod_env_commands":         MOD_ENV_COMMANDS,
                "mod_env_data_min":         MOD_ENV_DATA_MIN,
                "mod_env_data_max":         MOD_ENV_DATA_MAX,
            })

        if what in ("voices", "all"):
            base.update({
                "voice_source_inline":   VOICE_SOURCE_INLINE,
                "voice_source_unibank":  VOICE_SOURCE_UNIBANK,
                "unibank_patch_count":   UNIBANK_PATCH_COUNT,
                "unibank_index_min":     UNIBANK_INDEX_MIN,
                "unibank_index_max":     UNIBANK_INDEX_MAX,
                "voice_sourcing_modes":  VOICE_SOURCING_MODES,
                "s3_title_voice_count":  S3_TITLE_VOICE_COUNT,
                "s3_title_voice_source": S3_TITLE_VOICE_SOURCE,
            })

        return base

    def ztrack_address(self, channel_index: int) -> int:
        """
        Return Z80 RAM address of zTrack block for given channel index (0-based).

        FM channels: indices 0-5
        PSG channels: indices 6-9
        """
        if not 0 <= channel_index < ZTRACK_TOTAL:
            raise AdapterError(
                f"channel_index must be 0–{ZTRACK_TOTAL - 1}, got {channel_index}"
            )
        return Z80_TRACK_RAM_BASE + channel_index * ZTRACK_BYTE_LENGTH

    def field_address(self, channel_index: int, field_name: str) -> int:
        """
        Return Z80 RAM address of a named zTrack field for a given channel.

        Args:
            channel_index: 0-based channel index (0-9)
            field_name: key from ZTRACK_FIELDS

        Returns:
            absolute Z80 address of the field
        """
        if field_name not in ZTRACK_FIELDS:
            raise AdapterError(f"Unknown zTrack field: {field_name!r}")
        block_base = self.ztrack_address(channel_index)
        return block_base + ZTRACK_FIELDS[field_name]["offset"]

    def classify_sound_id(self, sound_id: int) -> str:
        """
        Classify a sound request byte by its role.

        Returns: "music" | "sfx" | "dac_sample" | "stop" | "unknown"
        """
        if sound_id == MUSIC_STOP_ID:
            return "stop"
        if DAC_SAMPLE_ID_MIN <= sound_id <= DAC_SAMPLE_ID_MAX:
            return "dac_sample"
        if SFX_ID_MIN <= sound_id <= SFX_ID_MAX:
            return "sfx"
        if MUSIC_ID_MIN <= sound_id <= MUSIC_ID_MAX:
            return "music"
        return "unknown"

    def is_available(self) -> bool:
        """S3K driver adapter is always available — uses static constants."""
        return True
