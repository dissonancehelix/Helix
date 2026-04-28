"""
TrackAnalysis Schema — domains/music/model/analysis/track_analysis.py
===============================================================
Unified, schema-consistent output record for all music formats.

Every codec — VGM, SPC, NSF, SID, MP3, Opus, USF, PSF — is translated
into a TrackAnalysis by the codec_pipeline. Think of this as a "translator":
  - Input: any supported codec (native chip data, waveform, or both)
  - Output: one TrackAnalysis dict, schema-consistent regardless of source

Tiers of analysis depth:
  Tier A (native chip):   VGM, SPC, NSF, SID
  Tier B (emulation):     GME-rendered chip state trace
  Tier C (waveform):      essentia/librosa descriptors (MP3, Opus, rendered)
  Tier D (MIDI/symbolic): Sheet-music-level analysis from MIDI reconstruction

Metadata:
  NEVER sourced from embedded tags (ID666, GD3, ID3, Vorbis).
  Always joined from codex/library/music/ by file path/title lookup.

DCP and substrate:
  Five DCP proxy fields are computed for every track (where data permits).
  A substrate vector is attached from the primary chip's capability profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json


SCHEMA_VERSION = "track_analysis_v1"


@dataclass
class ChipVoiceSnapshot:
    """Per-voice register state at file/snapshot time. Used for SPC, SID, NSF."""
    voice_index:   int
    active:        bool
    pitch_raw:     int           # raw pitch/frequency register
    pitch_hz:      float         # converted to Hz
    pitch_midi:    int           # approximate MIDI note (-1 if unknown)
    vol_l:         float         # left volume (normalised 0-1)
    vol_r:         float         # right volume (normalised 0-1)
    # Envelope state (ADSR)
    adsr_enabled:  bool = False
    attack:        int  = 0      # raw attack rate
    decay:         int  = 0
    sustain:       int  = 0
    release:       int  = 0
    waveform:      str  = ""     # SID waveform name, or "" for sample-based
    srcn:          int  = 0      # SPC700: sample source number


@dataclass
class NoteEvent:
    """A single note-on event reconstructed from register data (VGM / MIDI)."""
    time_s:        float         # absolute time in seconds
    channel:       int           # logical channel index
    pitch_midi:    int           # MIDI note number (0-127, -1 if pitch-modulated)
    pitch_hz:      float         # frequency in Hz
    velocity:      float         # normalised 0-1 (from volume register)
    is_loop:       bool = False  # True if at/after the loop point


@dataclass
class StructuralSection:
    """A detected structural boundary (section start, loop point, fade, etc.)."""
    time_s:        float
    label:         str           # 'intro', 'loop_start', 'loop_end', 'outro', 'section'
    confidence:    float = 1.0


@dataclass
class DCPProxies:
    """Five DCP component proxies and the composite score."""
    possibility_space:  Optional[float] = None   # pitch entropy / policy entropy
    constraint:         Optional[float] = None   # register saturation / chip utilisation
    tension:            Optional[float] = None   # pre-seam variance elevation
    collapse:           Optional[float] = None   # sharpness of loop seam / section boundary
    post_narrowing:     Optional[float] = None   # post-seam trajectory narrowing
    composite:          float = 0.0
    qualification:      str   = "INSUFFICIENT"  # FULL / UNCONFIRMED / INCOMPLETE / INSUFFICIENT


@dataclass
class SubstrateVector:
    """
    Substrate capability vector — the DCP profile of the primary chip.
    Static upper bound on generative capacity; derived from chip spec,
    NOT from the specific track's content.
    Values are 0-1 normalised (1 = maximum capability on that axis).
    """
    possibility_space:    float = 0.0  # max expressible pitch/timbre entropy
    constraint:           float = 0.0  # how tightly hardware limits output
    attractor_stability:  float = 0.0  # loop support + hardware repeat
    basin_permeability:   float = 0.0  # key-on delay + release floor
    recurrence_depth:     float = 0.0  # polyphony x available timbres
    chip_id:              str   = ""   # which chip this vector is for


@dataclass
class WaveformFeatures:
    """Essentia / librosa waveform-level features (waveform analysis path)."""
    bpm:                  Optional[float] = None
    key:                  Optional[str]   = None
    key_strength:         Optional[float] = None
    spectral_centroid:    float = 0.0
    spectral_complexity:  float = 0.0
    dissonance:           float = 0.0
    dynamic_complexity:   float = 0.0
    hfc:                  float = 0.0
    tonal_centroid:       list[float] = field(default_factory=lambda: [0.0] * 6)
    chord_histogram:      list[float] = field(default_factory=lambda: [0.0] * 24)
    # Timbral fingerprint — 13 MFCC coefficients (librosa)
    mfcc_means:           list[float] = field(default_factory=lambda: [0.0] * 13)
    # Harmonic fingerprint — 12-bin pitch-class chroma (librosa chroma_cqt)
    chroma_means:         list[float] = field(default_factory=lambda: [0.0] * 12)
    # Spectral contrast — 7-band peaks-vs-valleys (librosa)
    spectral_contrast:    list[float] = field(default_factory=lambda: [0.0] * 7)
    # Tonal network — 6-dim tonnetz (librosa)
    tonnetz_means:        list[float] = field(default_factory=lambda: [0.0] * 6)
    # Dynamics
    onset_density:        float = 0.0   # onsets/sec — rhythmic activity proxy
    dynamic_range:        float = 0.0   # peak_rms - mean_rms
    adapter:              str = ""   # 'essentia' or 'librosa'


@dataclass
class SymbolicFeatures:
    """
    Sheet-music-level features from MIDI reconstruction.

    For emulated formats (VGM, SPC via SPC2MID/VGMTrans, NSF):
    this is the 'reading sheet music' view — what a musicologist would see.
    Much richer than waveform for emulated formats.
    """
    note_count:        int   = 0
    unique_pitches:    int   = 0
    pitch_range:       int   = 0      # semitones from lowest to highest note
    pitch_center:      float = 0.0    # mean MIDI note
    pitch_entropy:     float = 0.0    # Shannon entropy of pitch histogram
    avg_note_duration: float = 0.0    # seconds
    rhythmic_entropy:  float = 0.0    # entropy of inter-note interval distribution
    note_density:      float = 0.0    # notes per second
    active_channels:   int   = 0
    # Key estimation from note histogram
    estimated_key:     str   = ""
    # Structural
    loop_start_beat:   Optional[float] = None
    loop_end_beat:     Optional[float] = None
    # Per-channel breakdown
    channel_note_counts: dict[int, int] = field(default_factory=dict)
    channel_pitch_ranges: dict[int, int] = field(default_factory=dict)
    # MIDI source
    midi_source:       str   = ""     # 'vgm_reconstructor', 'spc2mid', 'vgmtrans', 'nsf2vgm', etc.


@dataclass
class TrackAnalysis:
    """
    Unified analysis record for any music codec.

    Schema-consistent output regardless of input format.
    Metadata comes from the library, not embedded tags.
    """

    # --- Identity ---
    file_path:          str
    format:             str         # 'VGM', 'SPC', 'NSF', 'SID', 'MP3', 'OPUS', etc.
    schema_version:     str = SCHEMA_VERSION
    extraction_ts:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # --- Library metadata (populated by library join, NOT embedded tags) ---
    library_title:      str   = ""
    library_artist:     str   = ""
    library_game:       str   = ""
    library_platform:   str   = ""
    library_year:       str   = ""
    library_is_loved:   bool  = False
    library_meta:       dict  = field(default_factory=dict)  # full library record

    # --- Chip info (Tier A/B: native chip formats only) ---
    chips:              list[str] = field(default_factory=list)   # e.g. ['YM2612', 'SN76489']
    voice_count:        int   = 0
    active_voices:      int   = 0

    # --- Voice snapshots (Tier A: static snapshot from file header/DSP state) ---
    voices:             list[ChipVoiceSnapshot] = field(default_factory=list)

    # --- Note events (Tier A+: register trace / MIDI reconstruction) ---
    note_events:        list[NoteEvent] = field(default_factory=list)

    # --- Structural sections ---
    sections:           list[StructuralSection] = field(default_factory=list)
    has_loop:           bool  = False
    loop_start_s:       Optional[float] = None
    loop_end_s:         Optional[float] = None
    duration_s:         Optional[float] = None

    # --- Waveform features (Tier C) ---
    waveform:           Optional[WaveformFeatures] = None

    # --- Symbolic/MIDI features (Tier D) ---
    symbolic:           Optional[SymbolicFeatures] = None

    # --- DCP analysis ---
    dcp:                Optional[DCPProxies] = None

    # --- Substrate capability vector (DCP profile of the chip) ---
    substrate:          Optional[SubstrateVector] = None

    # --- Provenance ---
    analysis_tier:      str   = ""   # 'A'=hardware+notes, 'B'=symbolic, 'C'=waveform, 'AB'=both
    confidence:         float = 0.0  # overall confidence (0-1)
    error:              str   = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def error_record(cls, path: Path, error: str) -> "TrackAnalysis":
        return cls(
            file_path=str(path),
            format=path.suffix.lstrip(".").upper(),
            error=error,
            analysis_tier="error",
        )

