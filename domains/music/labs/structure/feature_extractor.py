"""
VGM Feature Extractor — Helix Music Lab
=========================================
Extracts chip-level structural features from parsed VGMTrack objects.

Features extracted:
  YM2612 (FM):
    - per-channel note event density
    - key-on/key-off ratios per channel (ch 0–5)
    - frequency register distributions (pitch/scale)
    - operator TL (total level) distributions per algorithm slot
    - algorithm (ALG) distribution across channels
    - feedback (FB) distribution
    - modulation (AMS/FMS) usage
    - operator attack/decay/release shapes

  SN76489 (PSG):
    - channel 0-2 (tone) activity ratio
    - channel 3 (noise) activity ratio
    - PSG-to-FM ratio (relative activity)

  Timing:
    - note density (key-ons per second)
    - rhythmic entropy (entropy of inter-note intervals)
    - silence ratio (wait samples / total samples)
    - avg phrase length (samples between long silences)
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from model.domains.music.parsing.vgm_parser import VGMTrack, VGMEvent

# Symbolic reconstruction (optional — imported lazily to avoid circular deps)
try:
    from model.domains.music.parsing.vgm_note_reconstructor import reconstruct as _symbolic_reconstruct
    from model.domains.music.parsing.score_representation import SymbolicScore
    _SYMBOLIC_AVAILABLE = True
except ImportError:
    _SYMBOLIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# YM2612 register map constants
# ---------------------------------------------------------------------------

# Key-on register: port 0, reg 0x28
# bits 2:0 = channel (0-2 = ch1-3, 4-6 = ch4-6)
# bits 7:4 = operator slots

REG_KEY_ON      = 0x28
REG_ALG_FB      = 0xB0   # algo + feedback (per channel, +0/+1/+2)
REG_FREQ_LO_CH  = 0xA0   # freq low (ch1-3 = 0xA0/A1/A2, port1 = A0/A1/A2)
REG_FREQ_HI_CH  = 0xA4   # freq high + block
REG_TL_BASE     = 0x40   # Total Level operators: 0x40-0x4E (op1), 0x48 (op2), etc.
REG_AR_BASE     = 0x50
REG_DR_BASE     = 0x60
REG_RR_BASE     = 0x80
REG_AMS_FMS     = 0xB4   # AMS/FMS stereo panning


# Frequency to nearest MIDI note (rough, Genesis YM2612 clock ~7.67 MHz)
# f_note = (clock / 144) * (F_num * 2^(block-1)) / 2^20
# We use F_num directly as a proxy for pitch
def _fnumber_to_semitone(fnum: int, block: int) -> int:
    """Map YM2612 F-number + block to approximate MIDI semitone (0-127)."""
    if fnum == 0:
        return -1
    try:
        # Genesis YM2612: f = clock/(144 * 2^20) * fnum * 2^block
        # Reference A4 (440 Hz) ≈ fnum=653, block=4 for ~7.67MHz clock
        ratio = fnum * (2 ** block) / (653.0 * 16)  # relative to A4
        if ratio <= 0:
            return -1
        semitone = round(69 + 12 * math.log2(ratio))
        return max(0, min(127, semitone))
    except (ValueError, ZeroDivisionError):
        return -1


# ---------------------------------------------------------------------------
# Feature dataclass
# ---------------------------------------------------------------------------

@dataclass
class TrackFeatures:
    track_name:     str
    total_samples:  int
    duration_sec:   float

    # FM features
    keyon_count:            int   = 0
    keyon_density:          float = 0.0   # key-ons per second
    channel_activity:       dict  = field(default_factory=dict)   # ch -> count
    algorithm_dist:         dict  = field(default_factory=dict)   # alg -> count
    feedback_dist:          dict  = field(default_factory=dict)   # fb -> count
    pitch_histogram:        list  = field(default_factory=list)   # 128 bins
    pitch_entropy:          float = 0.0
    pitch_range:            int   = 0
    pitch_center:           float = 0.0   # mean semitone
    tl_mean_op1:            float = 0.0
    tl_mean_op2:            float = 0.0
    ams_fms_usage:          float = 0.0   # fraction of channels using LFO mod
    dac_count:              int   = 0     # DAC (PCM) writes
    dac_density:            float = 0.0
    active_channels_count:  int   = 0     # Number of channels that ever keyed-on

    # PSG features
    psg_tone_count:         int   = 0
    psg_noise_count:        int   = 0
    psg_to_fm_ratio:        float = 0.0

    # Timing features
    silence_ratio:          float = 0.0
    rhythmic_entropy:       float = 0.0
    note_interval_mean:     float = 0.0
    burst_density:          float = 0.0   # density of rapid note clusters

    # Chip config
    has_ym2612:             bool  = False
    has_psg:                bool  = False
    ym2612_clock:           int   = 0
    psg_clock:              int   = 0

    # Symbolic features (populated by extract() when symbolic=True)
    symbolic_note_count:    int   = 0
    symbolic_unique_pitches: int  = 0
    symbolic_pitch_range:   int   = 0
    symbolic_avg_duration:  float = 0.0
    symbolic_score:         object = None   # SymbolicScore | None

    # Loop point features
    loop_event_index:       int   = -1    # index in events list where is_loop first becomes True
    loop_point_s:           float = 0.0   # loop point in seconds (from header)
    has_loop:               bool  = False


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

def _entropy(counter: dict | Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total)
        for c in counter.values()
        if c > 0
    )


def extract(track: VGMTrack, symbolic: bool = False) -> TrackFeatures:
    h = track.header
    sample_rate = 44100

    duration_sec = track.header.total_samples / sample_rate if track.header.total_samples > 0 else 1.0

    feat = TrackFeatures(
        track_name=track.path.stem,
        total_samples=h.total_samples,
        duration_sec=duration_sec,
        has_ym2612=h.has_ym2612,
        has_psg=h.has_psg,
        ym2612_clock=h.ym2612_clock,
        psg_clock=h.sn76489_clock,
    )

    if track.error:
        return feat

    # --- Pass 1: YM2612 register state tracking ---
    # We track: current fnum+block per channel (for pitch), algo/fb, TL
    ch_fnum  = [0] * 6    # last F-num per channel
    ch_block = [0] * 6   # last block per channel
    ch_algo  = [0] * 6
    ch_fb    = [0] * 6
    ch_tl    = [[127] * 4 for _ in range(6)]   # TL per operator per channel
    ch_ams_fms = [False] * 6

    ch_keyon_count = Counter()
    pitches_all: list[int] = []
    alg_counter = Counter()
    fb_counter  = Counter()

    psg_tone_count  = 0
    psg_noise_count = 0
    dac_count       = 0

    wait_samples_total = 0
    keyon_times: list[int] = []
    current_sample = 0

    for ev in track.events:
        if ev.kind == "wait":
            wait_samples_total += ev.samples
            current_sample += ev.samples
            continue
        if ev.kind == "end":
            break

        # --- YM2612 port 0 ---
        if ev.kind in ("ym2612_p0", "ym2612_p1"):
            port = 0 if ev.kind == "ym2612_p0" else 1
            ch_offset = port * 3  # channels 0-2 on port0, 3-5 on port1
            r, v = ev.reg, ev.val

            # Key-on
            if r == REG_KEY_ON and port == 0:
                ch_raw = v & 0x07
                ch_idx = ch_raw if ch_raw < 3 else (ch_raw - 1)  # map 0,1,2,4,5,6 -> 0..5
                if ch_idx < 6:
                    slots = (v >> 4) & 0x0F
                    if slots:  # any operator keyed on
                        ch_keyon_count[ch_idx] += 1
                        semi = _fnumber_to_semitone(ch_fnum[ch_idx], ch_block[ch_idx])
                        if semi >= 0:
                            pitches_all.append(semi)
                        keyon_times.append(current_sample)

            # F-number low (A0-A2 on each port)
            elif 0xA0 <= r <= 0xA2:
                ch_idx = ch_offset + (r - 0xA0)
                if ch_idx < 6:
                    ch_fnum[ch_idx] = (ch_fnum[ch_idx] & ~0xFF) | v

            # F-number high + block (A4-A6 on each port)
            elif 0xA4 <= r <= 0xA6:
                ch_idx = ch_offset + (r - 0xA4)
                if ch_idx < 6:
                    ch_fnum[ch_idx]  = (ch_fnum[ch_idx] & 0xFF) | ((v & 0x07) << 8)
                    ch_block[ch_idx] = (v >> 3) & 0x07

            # Algorithm + Feedback (B0-B2)
            elif 0xB0 <= r <= 0xB2:
                ch_idx = ch_offset + (r - 0xB0)
                if ch_idx < 6:
                    ch_algo[ch_idx] = v & 0x07
                    ch_fb[ch_idx]   = (v >> 3) & 0x07
                    alg_counter[v & 0x07] += 1
                    fb_counter[(v >> 3) & 0x07] += 1

            # AMS/FMS (B4-B6)
            elif 0xB4 <= r <= 0xB6:
                ch_idx = ch_offset + (r - 0xB4)
                if ch_idx < 6:
                    ams = (v >> 4) & 0x03
                    fms = v & 0x07
                    ch_ams_fms[ch_idx] = bool(ams or fms)

            # Total Level — operators 1-4 per channel
            # Regs: 0x40-0x4E (op1 ch0-2), 0x44-0x4E step4, etc.
            # Layout: op1=0x40+ch, op3=0x44+ch, op2=0x48+ch, op4=0x4C+ch
            elif 0x40 <= r <= 0x4F:
                ch_idx  = ch_offset + (r & 0x03)
                op_slot = (r >> 2) & 0x03
                if ch_idx < 6:
                    ch_tl[ch_idx][op_slot] = v & 0x7F
            
            # DAC data (Port 0, Reg 0x2A)
            elif r == 0x2A and port == 0:
                dac_count += 1

        # --- PSG ---
        elif ev.kind == "psg":
            v = ev.val
            if v & 0x80:  # LATCH byte
                ch = (v >> 5) & 0x03
                kind_bit = (v >> 4) & 0x01   # 0=freq, 1=volume
                if ch == 3:
                    psg_noise_count += 1
                else:
                    psg_tone_count += 1

    # --- Compile features ---
    feat.keyon_count      = sum(ch_keyon_count.values())
    feat.keyon_density    = feat.keyon_count / max(duration_sec, 0.001)
    feat.channel_activity = dict(ch_keyon_count)
    feat.algorithm_dist   = dict(alg_counter)
    feat.feedback_dist    = dict(fb_counter)
    feat.psg_tone_count   = psg_tone_count
    feat.psg_noise_count  = psg_noise_count

    fm_total  = feat.keyon_count + 1
    psg_total = psg_tone_count + psg_noise_count
    feat.psg_to_fm_ratio  = psg_total / fm_total
    feat.dac_count        = dac_count
    feat.dac_density      = dac_count / max(duration_sec, 0.001)
    feat.active_channels_count = len([c for c in ch_keyon_count.values() if c > 0])

    feat.silence_ratio = wait_samples_total / max(h.total_samples, 1)

    # Pitch histogram (128 bins)
    pitch_hist = [0] * 128
    for s in pitches_all:
        if 0 <= s < 128:
            pitch_hist[s] += 1
    feat.pitch_histogram = pitch_hist
    pitch_counter = Counter(pitches_all)
    feat.pitch_entropy = _entropy(pitch_counter)
    if pitches_all:
        feat.pitch_range  = max(pitches_all) - min(pitches_all)
        feat.pitch_center = sum(pitches_all) / len(pitches_all)

    # TL analysis: mean TL for op1 (carrier in many algorithms)
    op1_tls = [ch_tl[c][0] for c in range(6)]
    op2_tls = [ch_tl[c][2] for c in range(6)]
    feat.tl_mean_op1 = sum(op1_tls) / 6
    feat.tl_mean_op2 = sum(op2_tls) / 6

    feat.ams_fms_usage = sum(ch_ams_fms) / 6

    # Rhythmic entropy: entropy of quantized inter-event intervals
    if len(keyon_times) > 1:
        intervals = [
            keyon_times[i+1] - keyon_times[i]
            for i in range(len(keyon_times) - 1)
            if keyon_times[i+1] > keyon_times[i]
        ]
        if intervals:
            # Quantize to nearest 50-sample bucket (~1.1ms)
            buckets = Counter(round(iv / 50) * 50 for iv in intervals)
            feat.rhythmic_entropy  = _entropy(buckets)
            feat.note_interval_mean = sum(intervals) / len(intervals)

    # --- Optional symbolic reconstruction pass ---
    if symbolic and _SYMBOLIC_AVAILABLE and not track.error:
        score = _symbolic_reconstruct(track)
        feat.symbolic_note_count     = score.note_count
        feat.symbolic_unique_pitches = len(score.unique_pitches)
        feat.symbolic_pitch_range    = score.pitch_range
        feat.symbolic_avg_duration   = round(score.avg_duration(), 4)
        feat.symbolic_score          = score

    return feat

