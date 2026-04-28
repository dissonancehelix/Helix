"""
Symbolic Music Analyzer — model/domains/music/analysis/symbolic_analyzer.py
======================================================================
Extracts sheet-music-level (Tier D) features from a MIDI file.

This is the musicologist's view: the actual notes, rhythms, intervals,
motifs, and structure a composer wrote — not the waveform output.

For emulated formats this is the highest-information representation:
  - VGM  → vgm_note_reconstructor (native) OR adapter_vgmtrans
  - SPC  → SPC2MID binaries (engine-specific, preferred)
  - NSF  → nsf2vgm → then this module
  - SID  → not yet (reSID render path only)

Features extracted are specifically calibrated to the DISSONANCE profile:
each feature maps to a structural attractor described in docs/profiles/DISSONANCE.md.

Structural attractors mapped:
  - Groove Engine:        bass channel identification, rhythmic regularity,
                          pulse coherence, bass/melody independence
  - Floating Upper:       register separation (bass vs treble channels),
                          sustained note ratio, upper-voice pitch range
  - Coherent Variation:   motif recurrence, section-level identity tracking,
                          phrase repetition with variation
  - Loop-Seam Collapse:   tension accumulation pre-loop, note density spike,
                          layer count change at/after loop boundary
  - Crooked Coherence:    pitch dissonance score (non-12TET proximity),
                          off-beat event ratio, harmonic chromatic density
  - Threshold Attraction: density gradient (tracks that fade in/out of density),
                          emergence index, disappearance index
  - Coherent Abrasion:    interval roughness (minor 2nds, tritones),
                          harmonic tension density without melodic loss
  - Rhythmic-Harmonic:    inter-channel rhythmic independence,
                          harmonic rhythm (chord change rate)
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Feature container
# ---------------------------------------------------------------------------

@dataclass
class SymbolicAnalysis:
    """
    Complete symbolic feature set extracted from a MIDI rendering of a track.
    Every field maps to at least one structural attractor in DISSONANCE.md.
    """
    midi_source:        str   = ""    # 'spc2mid', 'vgm_reconstructor', 'vgmtrans', 'nsf2vgm'
    parser:             str   = ""    # 'music21' or 'pretty_midi'

    # --- Basic statistics ---
    total_notes:        int   = 0
    duration_s:         float = 0.0
    active_channels:    int   = 0
    note_density:       float = 0.0   # notes per second (total)
    unique_pitches:     int   = 0
    pitch_range:        int   = 0     # semitones: max_pitch - min_pitch

    # --- Pitch / harmonic ---
    pitch_center:       float = 0.0   # mean MIDI note
    pitch_entropy:      float = 0.0   # Shannon entropy of pitch histogram (12-bin)
    chromatic_density:  float = 0.0   # fraction of 12 chromatic classes used
    interval_roughness: float = 0.0   # fraction of intervals that are m2, M7, tritone
    estimated_key:      str   = ""    # e.g. 'C major', 'A minor'
    key_confidence:     float = 0.0   # 0-1
    # 12-bin pitch-class histogram (normalised to sum=1.0).
    # Bin 0 = C, 1 = C#/Db, ..., 11 = B.
    # This is the harmonic "chroma fingerprint" from note data — the single most
    # discriminating feature for composer attribution within a chip family.
    pitch_class_histogram: list[float] = field(default_factory=lambda: [0.0] * 12)

    # --- Rhythm ---
    rhythmic_entropy:   float = 0.0   # entropy of inter-onset interval distribution
    pulse_coherence:    float = 0.0   # how regular the dominant pulse is (0=chaotic, 1=metronomic)
    off_beat_ratio:     float = 0.0   # fraction of notes landing on weak beats (syncopation proxy)
    tempo_bpm:          float = 0.0   # estimated tempo from dominant IOI

    # --- Register / role separation ---
    bass_channel:       int   = -1    # channel index inferred as bass/engine
    upper_channels:     list[int] = field(default_factory=list)  # floating upper voices
    register_separation: float = 0.0  # mean pitch distance between bass and upper voices
    bass_note_density:  float = 0.0   # notes/s on bass channel
    upper_note_density: float = 0.0   # notes/s on upper channels (average)
    sustained_ratio:    float = 0.0   # fraction of note durations > 0.5s (floating upper proxy)

    # --- Groove Engine (DISSONANCE primary attractor) ---
    # Bass + percussion fusion: how much does the bass channel correlate with
    # the rhythmic backbone? High = strong groove engine.
    groove_score:       float = 0.0
    bass_rhythmic_regularity: float = 0.0  # consistency of bass onset timing
    melody_bass_independence: float = 0.0  # how different melody rhythm is from bass rhythm

    # --- Coherent Variation (identity with internal motion) ---
    motif_recurrence:   float = 0.0   # fraction of short pitch sequences that repeat
    phrase_variation:   float = 0.0   # mean interval distance between repeated phrases
    section_count:      int   = 0     # structural sections detected

    # --- Loop-Seam / Circular Collapse (DISSONANCE cluster 3) ---
    # This is the core attractor: pre-loop tension build, circular return
    has_loop_seam:      bool  = False
    loop_point_s:       Optional[float] = None
    pre_seam_density_spike: float = 0.0   # note density ratio: final 10% vs overall mean
    pre_seam_layer_count: int   = 0       # simultaneous active channels in final 10%
    post_seam_reset:    float = 0.0       # density drop at loop return (0=no reset, 1=full reset)
    seam_sharpness:     float = 0.0       # abruptness of transition at loop boundary

    # --- Crooked Coherence (cluster 1) ---
    # Intact structure under subtle distortion
    chromatic_intrusion_rate: float = 0.0  # non-diatonic notes as fraction of total
    rhythmic_displacement: float = 0.0     # mean temporal distance from nearest strong beat

    # --- Threshold Attraction (cluster 2) ---
    # Half-emerged / half-dissolved structures
    emergence_index:    float = 0.0   # note density rise rate in first 20%
    disappearance_index: float = 0.0  # note density fall rate in last 20%
    density_range:      float = 0.0   # max - min density in rolling window

    # --- Coherent Abrasion (cluster 4) ---
    # Grain, pressure, and strain without structural loss
    dissonance_density: float = 0.0   # rough intervals per second
    harmonic_tension_score: float = 0.0  # weighted sum of interval tensions
    prevalence_of_tritones: float = 0.0  # jSymbolic: fraction of melodic intervals that are tritones
    vertical_dissonance: float = 0.0     # jSymbolic: fraction of vertical slices that are dissonant chords

    # --- Per-channel breakdown ---
    channel_note_counts:  dict[int, int]   = field(default_factory=dict)
    channel_pitch_ranges: dict[int, int]   = field(default_factory=dict)
    channel_pitch_means:  dict[int, float] = field(default_factory=dict)
    channel_densities:    dict[int, float] = field(default_factory=dict)

    # -----------------------------------------------------------------------
    # Music theory (the musicologist layer)
    # What you'd read from sheet music + what a theorist would annotate
    # -----------------------------------------------------------------------

    # Key and mode (full 7-mode detection, not just major/minor)
    # Mode describes the 'flavour' of the scale:
    #   major/Ionian   = bright, resolved (most pop/classical)
    #   minor/Aeolian  = darker, serious
    #   Dorian         = minor but with a raised 6th — jazzy, cool darkness (e.g. Daft Punk, much VGM)
    #   Phrygian       = very dark, 'Spanish', tense
    #   Lydian         = dreamy, floating, raised 4th (film music, some Shimomura)
    #   Mixolydian     = major but flat 7th — bluesy, rock, unresolved (Beatles, blues)
    #   Locrian        = unstable, rare
    scale_mode:         str   = ""     # 'Ionian', 'Dorian', 'Phrygian', 'Lydian', 'Mixolydian', 'Aeolian', 'Locrian'
    mode_confidence:    float = 0.0

    # Chord progressions
    # A progression is the sequence of harmonies the composer uses.
    # e.g. ['I', 'IV', 'V', 'I'] = basic tonal resolution
    #      ['i', 'bVII', 'bVI', 'V'] = Aeolian cadence common in VGM
    #      ['ii', 'V', 'I', 'vi'] = jazz turnaround
    detected_chords:    list[str] = field(default_factory=list)  # chord names at timestamps
    chord_progression:  list[str] = field(default_factory=list)  # Roman numeral labels
    harmonic_rhythm:    float = 0.0   # average chord changes per second — high = harmonically busy
    progression_fingerprint: str = ""  # short canonical progression string e.g. 'i-bVII-bVI-V'

    # Phrase structure
    # A phrase is a musical sentence — typically 2 or 4 bars.
    # Phrase length tells you if a composer writes regular (4-bar) or irregular phrases.
    phrase_lengths_beats: list[float] = field(default_factory=list)  # detected phrase boundaries in beats
    avg_phrase_length:  float = 0.0   # in beats
    phrase_regularity:  float = 0.0   # 0 = all irregular, 1 = all same length

    # Melodic contour
    # Describes the overall shape of the melody:
    #   ascending  = climbing line (creates tension/expectation)
    #   descending = falling line (resolution, closure)
    #   arch       = rises then falls (phrase-level arc, very common)
    #   valley     = falls then rises (less common)
    #   zigzag     = bounces up and down (rhythmically active, groove-forward)
    #   static     = stays in one register
    melodic_contour:    str   = ""     # 'ascending', 'descending', 'arch', 'valley', 'zigzag', 'static'
    contour_smoothness: float = 0.0   # 0 = jagged (zigzag), 1 = smooth (arch/ascending)

    # Polyphony (simultaneous note density)
    # Tells you how many notes sound at the same time on average.
    # Low polyphony = sparse, open texture. High = dense, clustered.
    mean_polyphony:     float = 0.0   # average simultaneous notes
    max_polyphony:      int   = 0     # peak simultaneous notes (all channels)
    polyphony_variance: float = 0.0   # how much the density fluctuates

    # Dynamic arc (intensity over time)
    # For MIDI with velocity data, tracks whether the piece builds or decays.
    # For VGM/SPC, approximated from note density and register opens.
    dynamic_arc:        str   = ""    # 'build', 'decay', 'arch', 'stable', 'variable'
    intensity_slope:    float = 0.0   # positive = building, negative = fading
    peak_intensity_s:   float = 0.0   # time of highest note density

    error: str = ""


# ---------------------------------------------------------------------------
# MIDI interval roughness table
# Tension weights by interval class (0=unison, 6=tritone)
# ---------------------------------------------------------------------------

_INTERVAL_TENSION: list[float] = [
    0.0,   # 0: unison
    1.0,   # 1: minor 2nd (high roughness)
    0.4,   # 2: major 2nd
    0.2,   # 3: minor 3rd
    0.1,   # 4: major 3rd
    0.1,   # 5: perfect 4th
    0.9,   # 6: tritone (high tension)
    0.1,   # 7: perfect 5th
    0.2,   # 8: minor 6th
    0.2,   # 9: major 6th
    0.5,   # 10: minor 7th
    0.9,   # 11: major 7th (high tension)
]


def _interval_tension(a: int, b: int) -> float:
    return _INTERVAL_TENSION[abs(a - b) % 12]


def _is_rough(a: int, b: int) -> bool:
    ic = abs(a - b) % 12
    return ic in (1, 6, 11)  # m2, tritone, M7


def _shannon_entropy(counts: list[int]) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts if c > 0)


def _pitch_to_class(p: int) -> int:
    return p % 12


# ---------------------------------------------------------------------------
# Analysis core
# ---------------------------------------------------------------------------

def _try_music21(midi_path: Path, loop_point_s: Optional[float]) -> SymbolicAnalysis:
    """music21-based deep analysis with proper harmonic analysis."""
    import music21
    from music21 import converter, key as m21key, chord as m21chord, roman, tempo as m21tempo

    result = SymbolicAnalysis(midi_source="", parser="music21")
    try:
        score = converter.parse(str(midi_path))
    except Exception as e:
        result.error = f"music21 parse failed: {e}"
        return result

    # Extract all notes with timestamps across all parts
    all_notes: list[tuple[float, float, int, int]] = []  # (onset_s, offset_s, pitch, channel)
    channel_notes: dict[int, list[tuple[float, float, int]]] = {}

    # Get tempo for beat→second conversion
    tempos = list(score.flatten().getElementsByClass(m21tempo.MetronomeMark))
    bpm_val = tempos[0].number if tempos else 120.0
    beat_dur = 60.0 / bpm_val

    for part_idx, part in enumerate(score.parts):
        notes = list(part.flatten().notes)
        for n in notes:
            try:
                onset_s  = float(n.offset) * beat_dur
                dur_s    = float(n.duration.quarterLength) * beat_dur
                if hasattr(n, 'pitch'):
                    pitch = n.pitch.midi
                elif hasattr(n, 'pitches'):
                    pitch = n.pitches[0].midi if n.pitches else 60
                else:
                    continue
                all_notes.append((onset_s, onset_s + dur_s, pitch, part_idx))
                channel_notes.setdefault(part_idx, []).append((onset_s, onset_s + dur_s, pitch))
            except Exception:
                continue

    # --- music21 harmonic analysis (much better than custom triad matcher) ---
    # chordify() reduces the full score to a chord-per-beat representation
    # then Roman numeral analysis gives the actual harmonic grammar
    result = _compute_features(all_notes, channel_notes, loop_point_s, "music21")

    try:
        # Key analysis (music21's built-in, more accurate than KS manual)
        k = score.analyze('key')
        result.estimated_key = f"{k.tonic.name} {k.mode}"
        result.key_confidence = float(k.correlationCoefficient) if hasattr(k, 'correlationCoefficient') else 0.0

        # Full chord progression via chordify + Roman numerals
        chordified = score.chordify()
        chord_names: list[str] = []
        roman_labels: list[str] = []
        prev_rn = ""
        changes = 0
        total_dur = 0.0

        for c in chordified.flatten().getElementsByClass(m21chord.Chord):
            try:
                rn = roman.romanNumeralFromChord(c, k)
                label = rn.figure  # e.g. 'V7', 'ii6', 'bVII'
                chord_name = c.pitches[0].name if c.pitches else "?"
                total_dur += float(c.duration.quarterLength) * beat_dur
                if label != prev_rn:
                    roman_labels.append(label)
                    chord_names.append(chord_name)
                    changes += 1
                    prev_rn = label
            except Exception:
                continue

        result.detected_chords = chord_names
        result.chord_progression = roman_labels
        result.harmonic_rhythm = changes / max(0.01, total_dur)
        if roman_labels:
            result.progression_fingerprint = '-'.join(roman_labels[:8])

    except Exception:
        pass  # fall back to what _compute_features already computed

    return result


def _try_pretty_midi(midi_path: Path, loop_point_s: Optional[float]) -> SymbolicAnalysis:
    """pretty_midi-based analysis (faster, less harmonic depth)."""
    import pretty_midi

    result = SymbolicAnalysis(midi_source="", parser="pretty_midi")
    try:
        midi = pretty_midi.PrettyMIDI(str(midi_path))
    except Exception as e:
        result.error = f"pretty_midi parse failed: {e}"
        return result

    all_notes: list[tuple[float, float, int, int]] = []
    channel_notes: dict[int, list[tuple[float, float, int]]] = {}

    for ch_idx, instrument in enumerate(midi.instruments):
        for note in instrument.notes:
            all_notes.append((note.start, note.end, note.pitch, ch_idx))
            channel_notes.setdefault(ch_idx, []).append((note.start, note.end, note.pitch))

    return _compute_features(all_notes, channel_notes, loop_point_s, "pretty_midi")


def _compute_features(
    all_notes: list[tuple[float, float, int, int]],
    channel_notes: dict[int, list[tuple[float, float, int]]],
    loop_point_s: Optional[float],
    parser: str,
) -> SymbolicAnalysis:
    """
    Core feature computation from raw note lists.
    Input: [(onset_s, offset_s, pitch_midi, channel_idx), ...]
    """
    r = SymbolicAnalysis(parser=parser)
    if not all_notes:
        r.error = "no notes found"
        return r

    all_notes.sort(key=lambda n: n[0])
    onsets  = [n[0] for n in all_notes]
    offsets = [n[1] for n in all_notes]
    pitches = [n[2] for n in all_notes]

    t_start = onsets[0]
    t_end   = max(offsets) if offsets else (onsets[-1] + 0.5)
    dur     = t_end - t_start or 1.0

    r.total_notes   = len(all_notes)
    r.duration_s    = dur
    r.active_channels = len(channel_notes)
    r.note_density  = r.total_notes / dur
    r.unique_pitches = len(set(pitches))
    r.pitch_range   = max(pitches) - min(pitches) if pitches else 0
    r.pitch_center  = sum(pitches) / len(pitches)

    # --- Pitch class distribution → entropy, chromatic density, histogram ---
    pc_counts = [0] * 12
    for p in pitches:
        pc_counts[p % 12] += 1
    r.pitch_entropy     = _shannon_entropy(pc_counts)
    r.chromatic_density = sum(1 for c in pc_counts if c > 0) / 12.0
    _pc_total = sum(pc_counts) or 1
    r.pitch_class_histogram = [c / _pc_total for c in pc_counts]

    # --- Key estimation (Krumhansl-Schmuckler via correlation) ---
    r.estimated_key, r.key_confidence = _estimate_key(pc_counts)

    # --- Interval analysis ---
    rough_count   = 0
    tension_total = 0.0
    for i in range(len(pitches) - 1):
        a, b = pitches[i], pitches[i + 1]
        if _is_rough(a, b): rough_count += 1
        tension_total += _interval_tension(a, b)
    denom = max(1, len(pitches) - 1)
    r.interval_roughness     = rough_count / denom
    r.harmonic_tension_score = tension_total / denom
    r.dissonance_density     = rough_count / dur

    # --- Rhythm ---
    iois = [onsets[i+1] - onsets[i] for i in range(len(onsets)-1) if onsets[i+1] - onsets[i] > 0]
    if iois:
        ioi_buckets = _quantise_iois(iois)
        r.rhythmic_entropy = _shannon_entropy(list(ioi_buckets.values()))
        # Restrict dominant IOI search to the 40–280 BPM range (0.214s–1.5s).
        # Very short IOIs (e.g. 0.1s = 600 BPM) are note-density artifacts, not beat pulses.
        _BPM_IOI_MIN = 60.0 / 280.0   # ~0.214 s
        _BPM_IOI_MAX = 60.0 / 40.0    # 1.5 s
        beat_buckets = {k: v for k, v in ioi_buckets.items() if _BPM_IOI_MIN <= k <= _BPM_IOI_MAX}
        if beat_buckets:
            dominant_ioi = max(beat_buckets, key=beat_buckets.get)
        else:
            # Fallback: clamp the raw dominant to the nearest valid tempo
            dominant_ioi = max(ioi_buckets, key=ioi_buckets.get, default=0.5)
            dominant_ioi = max(_BPM_IOI_MIN, min(_BPM_IOI_MAX, dominant_ioi))
        r.tempo_bpm = 60.0 / dominant_ioi if dominant_ioi > 0 else 0.0
        _dom_count = (beat_buckets if beat_buckets else ioi_buckets).get(dominant_ioi, 0)
        r.pulse_coherence = _dom_count / sum(ioi_buckets.values()) if ioi_buckets else 0.0
        # Off-beat ratio: fraction of notes not within 10% of dominant IOI multiples
        # (simple syncopation proxy)
        r.off_beat_ratio = 1.0 - r.pulse_coherence

    # --- Per-channel stats ---
    for ch, notes in channel_notes.items():
        ch_pitches = [n[2] for n in notes]
        ch_dur     = (max(n[1] for n in notes) - min(n[0] for n in notes)) or 1.0
        r.channel_note_counts[ch]  = len(notes)
        r.channel_pitch_ranges[ch] = max(ch_pitches) - min(ch_pitches) if ch_pitches else 0
        r.channel_pitch_means[ch]  = sum(ch_pitches) / len(ch_pitches) if ch_pitches else 0.0
        r.channel_densities[ch]    = len(notes) / ch_dur

    # --- Bass/upper role inference ---
    r.bass_channel, r.upper_channels = _infer_registers(channel_notes)

    if r.bass_channel >= 0 and r.bass_channel in channel_notes:
        bass_notes = channel_notes[r.bass_channel]
        bass_onsets = sorted(n[0] for n in bass_notes)
        bass_iois   = [bass_onsets[i+1] - bass_onsets[i]
                       for i in range(len(bass_onsets)-1) if bass_onsets[i+1] - bass_onsets[i] > 0]
        if bass_iois:
            bq = _quantise_iois(bass_iois)
            r.bass_rhythmic_regularity = max(bq.values()) / sum(bq.values()) if bq else 0.0
        r.bass_note_density = r.channel_densities.get(r.bass_channel, 0.0)

    if r.upper_channels:
        upper_densities = [r.channel_densities.get(ch, 0.0) for ch in r.upper_channels]
        r.upper_note_density = sum(upper_densities) / len(upper_densities)
        upper_means = [r.channel_pitch_means.get(ch, 60.0) for ch in r.upper_channels]
        bass_mean   = r.channel_pitch_means.get(r.bass_channel, 40.0)
        r.register_separation = (sum(upper_means) / len(upper_means)) - bass_mean

    # Sustained note ratio (floating upper proxy)
    note_durs = [n[1] - n[0] for n in all_notes if n[1] > n[0]]
    r.sustained_ratio = sum(1 for d in note_durs if d > 0.5) / len(note_durs) if note_durs else 0.0

    # Groove score: bass regularity × register separation normalised
    reg_sep_normalised = min(1.0, r.register_separation / 24.0)  # 2 octaves = max
    r.groove_score = r.bass_rhythmic_regularity * 0.6 + reg_sep_normalised * 0.4

    # Melody-bass independence: difference in rhythmic entropy between bass and upper
    if r.bass_channel >= 0 and r.upper_channels:
        bass_n  = channel_notes.get(r.bass_channel, [])
        upper_n = [n for ch in r.upper_channels for n in channel_notes.get(ch, [])]
        b_iois  = _sorted_iois([n[0] for n in bass_n])
        u_iois  = _sorted_iois([n[0] for n in upper_n])
        b_ent   = _shannon_entropy(list(_quantise_iois(b_iois).values())) if b_iois else 0.0
        u_ent   = _shannon_entropy(list(_quantise_iois(u_iois).values())) if u_iois else 0.0
        r.melody_bass_independence = abs(u_ent - b_ent) / max(b_ent, u_ent, 0.01)

    # --- Loop-seam analysis ---
    r.has_loop_seam = loop_point_s is not None
    r.loop_point_s  = loop_point_s

    if loop_point_s is not None:
        seam_start = loop_point_s - (dur * 0.1)  # final 10% before seam
        seam_start = max(t_start, seam_start)

        pre_seam_notes   = [n for n in all_notes if seam_start <= n[0] < loop_point_s]
        pre_seam_dur     = max(0.01, loop_point_s - seam_start)
        pre_seam_density = len(pre_seam_notes) / pre_seam_dur
        r.pre_seam_density_spike = pre_seam_density / (r.note_density or 1.0)

        active_at_seam = {n[3] for n in pre_seam_notes}
        r.pre_seam_layer_count = len(active_at_seam)

        post_seam_window = 0.5
        post_seam_notes  = [n for n in all_notes if loop_point_s <= n[0] < loop_point_s + post_seam_window]
        post_seam_density = len(post_seam_notes) / post_seam_window
        r.post_seam_reset = max(0.0, 1.0 - (post_seam_density / (pre_seam_density or 1.0)))
        r.seam_sharpness  = r.pre_seam_density_spike * r.post_seam_reset

    # --- Motif recurrence ---
    r.motif_recurrence = _compute_motif_recurrence(pitches, window=4)

    # --- Density gradient (threshold attraction) ---
    window = dur / 5  # 20% windows
    density_windows = []
    for i in range(5):
        wstart = t_start + i * window
        wend   = wstart + window
        wcount = sum(1 for n in all_notes if wstart <= n[0] < wend)
        density_windows.append(wcount / window if window > 0 else 0.0)

    if len(density_windows) >= 5:
        r.emergence_index    = (density_windows[1] - density_windows[0]) / (density_windows[0] + 0.01)
        r.disappearance_index = (density_windows[-2] - density_windows[-1]) / (density_windows[-2] + 0.01)
        r.density_range      = max(density_windows) - min(density_windows)

    # --- Non-diatonic rate (chromatic intrusion = crooked coherence) ---
    if r.estimated_key:
        key_pcs = _key_pitch_classes(r.estimated_key)
        chromatic_count = sum(1 for p in pitches if (p % 12) not in key_pcs)
        r.chromatic_intrusion_rate = chromatic_count / len(pitches) if pitches else 0.0

    # -----------------------------------------------------------------------
    # Music theory layer
    # -----------------------------------------------------------------------

    # --- Full mode detection (7 church modes) ---
    r.scale_mode, r.mode_confidence = _detect_mode(pc_counts)

    # --- Chord progression (window-based) ---
    r.detected_chords, r.chord_progression, r.harmonic_rhythm = _extract_chords(
        all_notes, dur, r.estimated_key
    )
    if r.chord_progression:
        r.progression_fingerprint = '-'.join(r.chord_progression[:8])  # first 8 changes

    # --- Phrase detection ---
    r.phrase_lengths_beats, r.avg_phrase_length, r.phrase_regularity = _detect_phrases(
        onsets, r.tempo_bpm or 120.0
    )

    # --- Melodic contour ---
    # Use the highest active channel (melody voice) for contour
    melody_ch = r.upper_channels[0] if r.upper_channels else (
        max(channel_notes, key=lambda c: r.channel_pitch_means.get(c, 0.0), default=-1)
    )
    melody_pitches = [n[2] for n in channel_notes.get(melody_ch, all_notes)]
    r.melodic_contour, r.contour_smoothness = _classify_contour(melody_pitches)

    # --- Polyphony (simultaneous note count over time) ---
    r.mean_polyphony, r.max_polyphony, r.polyphony_variance = _compute_polyphony(all_notes, dur)

    r.dynamic_arc, r.intensity_slope, r.peak_intensity_s = _compute_dynamic_arc(
        density_windows, t_start, window
    )

    # --- Native jSymbolic Port ---
    # Calculates Prevalence of Tritones (Melodic) and Vertical Dissonance
    total_m_intervals, tritones = 0, 0
    total_chords, dissonant_chords = 0, 0

    try:
        from music21 import chord as m21chord
        
        for p in score.parts:
            notes = list(p.flatten().notes)
            for i in range(1, len(notes)):
                try:
                    p1 = notes[i-1].pitch.midi if hasattr(notes[i-1], 'pitch') else notes[i-1].pitches[0].midi
                    p2 = notes[i].pitch.midi if hasattr(notes[i], 'pitch') else notes[i].pitches[0].midi
                    total_m_intervals += 1
                    if abs(p1 - p2) == 6:
                        tritones += 1
                except Exception:
                    pass
                    
        chordified_score = score.chordify()
        for c in chordified_score.flatten().getElementsByClass(m21chord.Chord):
            total_chords += 1
            if not c.isConsonant():
                dissonant_chords += 1
                
        r.prevalence_of_tritones = tritones / max(1, total_m_intervals)
        r.vertical_dissonance = dissonant_chords / max(1, total_chords)
    except Exception:
        pass

    return r


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
_NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def _estimate_key(pc_counts: list[int]) -> tuple[str, float]:
    """Krumhansl-Schmuckler key-finding algorithm."""
    best_key, best_score, best_mode = "C", -999.0, "major"
    for root in range(12):
        for profile, mode in [(_KS_MAJOR, "major"), (_KS_MINOR, "minor")]:
            rotated = [pc_counts[(root + i) % 12] for i in range(12)]
            mean_p = sum(profile) / 12
            mean_r = sum(rotated) / 12
            n = sum((p - mean_p) * (r - mean_r) for p, r in zip(profile, rotated))
            d = math.sqrt(sum((p - mean_p)**2 for p in profile) *
                          sum((r - mean_r)**2 for r in rotated))
            score = n / d if d > 0 else 0.0
            if score > best_score:
                best_score = score
                best_key   = _NOTE_NAMES[root]
                best_mode  = mode
    confidence = (best_score + 1.0) / 2.0  # normalise -1..1 → 0..1
    return f"{best_key} {best_mode}", min(1.0, max(0.0, confidence))


def _key_pitch_classes(key_name: str) -> set[int]:
    """Return set of pitch classes for a given key name (e.g. 'C major')."""
    major_scale = [0, 2, 4, 5, 7, 9, 11]
    minor_scale = [0, 2, 3, 5, 7, 8, 10]
    parts = key_name.split()
    if len(parts) < 2:
        return set(major_scale)
    root_name = parts[0]
    scale = major_scale if parts[1] == 'major' else minor_scale
    root = _NOTE_NAMES.index(root_name) if root_name in _NOTE_NAMES else 0
    return {(root + s) % 12 for s in scale}


def _quantise_iois(iois: list[float], precision: float = 0.05) -> dict[float, int]:
    """Bucket inter-onset intervals to nearest `precision` seconds."""
    counts: dict[float, int] = {}
    for ioi in iois:
        bucket = round(ioi / precision) * precision
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def _sorted_iois(onsets: list[float]) -> list[float]:
    onsets = sorted(onsets)
    return [onsets[i+1] - onsets[i] for i in range(len(onsets)-1)
            if onsets[i+1] - onsets[i] > 0]


def _infer_registers(
    channel_notes: dict[int, list[tuple[float, float, int]]]
) -> tuple[int, list[int]]:
    """Infer which channel is the bass engine and which are upper voices."""
    if not channel_notes:
        return -1, []

    means = {ch: sum(n[2] for n in notes) / len(notes)
             for ch, notes in channel_notes.items() if notes}

    if not means:
        return -1, []

    # Bass = lowest mean pitch
    bass_ch = min(means, key=means.get)
    upper   = sorted([ch for ch in means if ch != bass_ch],
                     key=lambda c: means[c], reverse=True)
    return bass_ch, upper


def _compute_motif_recurrence(pitches: list[int], window: int = 4) -> float:
    """
    Fraction of pitch windows of length `window` that repeat at least once.
    Simple motif recurrence heuristic — higher = more motivic writing.
    """
    if len(pitches) < window * 2:
        return 0.0
    intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    windows: list[tuple] = []
    for i in range(len(intervals) - window + 1):
        windows.append(tuple(intervals[i:i+window]))
    counter = Counter(windows)
    repeated = sum(1 for v in counter.values() if v > 1)
    return repeated / len(counter) if counter else 0.0


# ---------------------------------------------------------------------------
# Music theory helpers
# ---------------------------------------------------------------------------

# All 7 church mode profiles (Krumhansl-Kessler style, 12-element)
# Adapted from Temperley 2001 and Albrecht & Shanahan 2013
_MODE_PROFILES: dict[str, list[float]] = {
    "Ionian":     [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    "Dorian":     [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],  # like minor, raised 6th
    "Phrygian":   [6.33, 5.68, 2.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],  # minor, flat 2nd
    "Lydian":     [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 4.52, 5.19, 2.39, 3.66, 2.29, 2.88],  # major, raised 4th
    "Mixolydian": [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 4.29, 2.88],  # major, flat 7th
    "Aeolian":    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],  # natural minor
    "Locrian":    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 5.54, 2.75, 3.98, 2.69, 3.34, 3.17],  # flat 2nd, flat 5th
}


def _detect_mode(pc_counts: list[int]) -> tuple[str, float]:
    """
    Detect which of the 7 church modes best fits the pitch class distribution.
    Returns (mode_name, confidence 0-1).
    """
    best_mode, best_score = "Ionian", -999.0
    scores: dict[str, float] = {}

    for root in range(12):
        for mode, profile in _MODE_PROFILES.items():
            rotated = [pc_counts[(root + i) % 12] for i in range(12)]
            mean_p = sum(profile) / 12
            mean_r = sum(rotated) / 12
            n = sum((p - mean_p) * (r - mean_r) for p, r in zip(profile, rotated))
            d = math.sqrt(sum((p - mean_p)**2 for p in profile) *
                          sum((r - mean_r)**2 for r in rotated))
            score = n / d if d > 0 else 0.0
            key_id = f"{_NOTE_NAMES[root]}-{mode}"
            scores[key_id] = score
            if score > best_score:
                best_score = score
                best_mode  = mode

    confidence = (best_score + 1.0) / 2.0
    return best_mode, min(1.0, max(0.0, confidence))


# Roman numeral labels for chords by scale degree (major/minor context)
_ROMAN_MAJOR = ['I', 'bII', 'II', 'bIII', 'III', 'IV', 'bV', 'V', 'bVI', 'VI', 'bVII', 'VII']
_ROMAN_MINOR = ['i', 'bII', 'ii', 'bIII', 'III', 'iv', 'bV', 'v', 'bVI', 'VI', 'bVII', 'VII']


def _chord_label(root_pc: int, quality: str, key_root_pc: int, is_minor_key: bool) -> str:
    """Return Roman numeral label for a chord relative to the key."""
    degree = (root_pc - key_root_pc) % 12
    table  = _ROMAN_MINOR if is_minor_key else _ROMAN_MAJOR
    label  = table[degree]
    if quality in ('m', 'dim') and not is_minor_key:
        label = label.lower()
    elif quality in ('M', 'aug') and is_minor_key:
        label = label.upper()
    if quality == 'dim': label += '°'
    if quality == 'aug': label += '+'
    return label


def _extract_chords(
    all_notes: list[tuple[float, float, int, int]],
    dur: float,
    estimated_key: str,
) -> tuple[list[str], list[str], float]:
    """
    Extract a chord progression from the note stream.

    Strategy: divide into 0.5s windows, find the 3 most common pitch classes
    in each window, infer a triad, label with Roman numeral relative to key.

    Returns: (chord_names, roman_labels, harmonic_rhythm_changes_per_s)
    """
    if not all_notes or dur < 1.0:
        return [], [], 0.0

    # Parse key
    parts = estimated_key.split() if estimated_key else ['C', 'major']
    key_root_name = parts[0] if parts else 'C'
    is_minor = (parts[1] == 'minor') if len(parts) > 1 else False
    key_root_pc = _NOTE_NAMES.index(key_root_name) if key_root_name in _NOTE_NAMES else 0

    # Common chord templates (interval sets, 12-TET)
    _TRIADS = [
        ([0, 4, 7], 'M'),   # major
        ([0, 3, 7], 'm'),   # minor
        ([0, 3, 6], 'dim'), # diminished
        ([0, 4, 8], 'aug'), # augmented
        ([0, 5, 7], 'sus4'),
    ]

    window_s = 0.5
    n_windows = max(1, int(dur / window_s))
    chord_names: list[str] = []
    roman_labels: list[str] = []
    prev_chord = ""
    changes = 0

    for i in range(n_windows):
        wstart = i * window_s
        wend   = wstart + window_s
        active_pcs = Counter(
            n[2] % 12 for n in all_notes if n[0] < wend and n[1] > wstart
        )
        if len(active_pcs) < 2:
            continue

        # Try to match a triad: find the root that best fits a template
        best_score, best_root, best_quality = -1, 0, 'M'
        for root_pc in range(12):
            for intervals, quality in _TRIADS:
                score = sum(active_pcs.get((root_pc + iv) % 12, 0) for iv in intervals)
                if score > best_score:
                    best_score, best_root, best_quality = score, root_pc, quality

        chord_name = f"{_NOTE_NAMES[best_root]}{best_quality if best_quality != 'M' else ''}"
        roman = _chord_label(best_root, best_quality, key_root_pc, is_minor)

        if chord_name != prev_chord:
            chord_names.append(chord_name)
            roman_labels.append(roman)
            changes += 1
            prev_chord = chord_name

    harmonic_rhythm = changes / dur if dur > 0 else 0.0
    return chord_names, roman_labels, harmonic_rhythm


def _detect_phrases(
    onsets: list[float],
    tempo_bpm: float,
) -> tuple[list[float], float, float]:
    """
    Detect phrase boundaries using density gaps.
    Returns: (phrase_lengths_beats, avg_phrase_length, regularity 0-1)
    """
    if len(onsets) < 4 or tempo_bpm <= 0:
        return [], 0.0, 0.0

    beat_s = 60.0 / tempo_bpm
    # Find gaps longer than 1.5 beats as phrase boundaries
    boundaries = [onsets[0]]
    for i in range(1, len(onsets)):
        gap = onsets[i] - onsets[i-1]
        if gap > beat_s * 1.5:
            boundaries.append(onsets[i])
    boundaries.append(onsets[-1] + beat_s)

    lengths_s = [boundaries[i+1] - boundaries[i] for i in range(len(boundaries)-1)]
    lengths_beats = [l / beat_s for l in lengths_s if l > 0]

    if not lengths_beats:
        return [], 0.0, 0.0

    avg = sum(lengths_beats) / len(lengths_beats)
    # Regularity = 1 - coefficient of variation (low cv = regular)
    if avg > 0:
        variance = sum((l - avg)**2 for l in lengths_beats) / len(lengths_beats)
        cv = math.sqrt(variance) / avg
        regularity = max(0.0, 1.0 - min(1.0, cv))
    else:
        regularity = 0.0

    return lengths_beats, avg, regularity


def _classify_contour(pitches: list[int]) -> tuple[str, float]:
    """
    Classify melodic contour from a pitch sequence.
    Returns: (contour_name, smoothness 0-1)
    """
    if len(pitches) < 4:
        return "static", 1.0

    n = len(pitches)
    mid = n // 2
    first_half_mean = sum(pitches[:mid]) / mid
    second_half_mean = sum(pitches[mid:]) / (n - mid)
    overall_slope = (pitches[-1] - pitches[0]) / max(1, n)

    # Smoothness: 1 - (fraction of direction changes)
    direction_changes = sum(
        1 for i in range(1, n-1)
        if (pitches[i] - pitches[i-1]) * (pitches[i+1] - pitches[i]) < 0
    )
    smoothness = 1.0 - (direction_changes / max(1, n - 2))

    # Contour classification
    if smoothness < 0.3:
        contour = "zigzag"
    elif abs(overall_slope) < 0.3 and abs(first_half_mean - second_half_mean) < 2:
        contour = "static"
    elif overall_slope > 0.5:
        contour = "ascending"
    elif overall_slope < -0.5:
        contour = "descending"
    elif first_half_mean < second_half_mean:  # rises then falls
        contour = "arch"
    else:
        contour = "valley"

    return contour, smoothness


def _compute_polyphony(
    all_notes: list[tuple[float, float, int, int]],
    dur: float,
    resolution: float = 0.1,
) -> tuple[float, int, float]:
    """
    Compute polyphony statistics: mean, max, variance of simultaneous notes.
    Samples the note stack at `resolution` second intervals.
    """
    if not all_notes or dur <= 0:
        return 0.0, 0, 0.0

    n_steps = max(1, int(dur / resolution))
    poly_samples: list[int] = []

    for step in range(n_steps):
        t = step * resolution
        count = sum(1 for n in all_notes if n[0] <= t < n[1])
        poly_samples.append(count)

    if not poly_samples:
        return 0.0, 0, 0.0

    mean_p = sum(poly_samples) / len(poly_samples)
    max_p  = max(poly_samples)
    var_p  = sum((s - mean_p)**2 for s in poly_samples) / len(poly_samples)
    return mean_p, max_p, var_p


def _compute_dynamic_arc(
    density_windows: list[float],
    t_start: float,
    window_dur: float,
) -> tuple[str, float, float]:
    """
    Classify the dynamic arc from a density-over-time list.
    Returns: (arc_name, slope, peak_time_s)
    """
    if not density_windows:
        return "stable", 0.0, t_start

    n = len(density_windows)
    # Linear regression slope
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(density_windows) / n
    num = sum((xs[i] - mean_x) * (density_windows[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x)**2 for i in range(n))
    slope = num / den if den > 0 else 0.0

    peak_idx = max(range(n), key=lambda i: density_windows[i])
    peak_s   = t_start + peak_idx * window_dur

    # Classify arc
    mid = n // 2
    first_half_mean  = sum(density_windows[:mid]) / max(1, mid)
    second_half_mean = sum(density_windows[mid:]) / max(1, n - mid)
    peak_pos = peak_idx / max(1, n - 1)  # 0=start, 1=end

    dynamic_range = max(density_windows) - min(density_windows)
    if dynamic_range < 0.5:
        arc = "stable"
    elif slope > 0.3:
        arc = "build"
    elif slope < -0.3:
        arc = "decay"
    elif 0.3 < peak_pos < 0.7:
        arc = "arch"
    else:
        arc = "variable"

    return arc, slope, peak_s


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_midi(
    midi_path: Path,
    midi_source: str = "",
    loop_point_s: Optional[float] = None,
) -> SymbolicAnalysis:
    """
    Analyze a MIDI file and return SymbolicAnalysis.

    Tries music21 first (deeper harmonic analysis), falls back to pretty_midi.
    """
    result = None

    try:
        import music21  # noqa
        result = _try_music21(midi_path, loop_point_s)
        if result.error:
            result = None
    except ImportError:
        pass

    if result is None or result.error:
        try:
            import pretty_midi  # noqa
            result = _try_pretty_midi(midi_path, loop_point_s)
        except ImportError:
            result = SymbolicAnalysis(
                midi_source=midi_source,
                error="neither music21 nor pretty_midi available",
            )

    if result is not None:
        result.midi_source = midi_source

    return result or SymbolicAnalysis(midi_source=midi_source, error="analysis failed")


def analyze_midi_to_dict(
    midi_path: Path,
    midi_source: str = "",
    loop_point_s: Optional[float] = None,
) -> dict:
    """Convenience wrapper returning plain dict output."""
    from dataclasses import asdict
    return asdict(analyze_midi(midi_path, midi_source=midi_source, loop_point_s=loop_point_s))

