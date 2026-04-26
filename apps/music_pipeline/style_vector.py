"""
style_vector.py — ArtistStyleVector computation
=================================================
Aggregates SymbolicScore and SignalProfile artifacts across a composer's
tracks into a single ArtistStyleVector.

DESIGN LAW:
    Musical cognition features DOMINATE.
    Hardware context (chips, platforms) is METADATA only.
    It explains differences — it does not define identity.

Feature categories:
    melodic_features    — interval distributions, leap frequency, phrase lengths
    harmonic_features   — chord type distribution, modulation, chromaticism
    rhythmic_features   — syncopation score, note density, tempo variance
    structural_features — loop lengths, section transition frequency
    timbral_features    — spectral centroid profile, brightness, timbre clusters
    motivic_features    — motif repetition frequency, motif entropy
    context_metadata    — platforms_used, chips_used (CONTEXT ONLY, not identity)

Output: ArtistStyleVector dict compatible with Atlas SymbolicScore schema.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


class StyleVectorComputer:
    """
    Computes an ArtistStyleVector from a composer's track analysis artifacts.

    Usage:
        computer = StyleVectorComputer()
        vector = computer.compute(
            composer_id="music.composer:motoi_sakuraba",
            symbolic_scores=[...],    # list of SymbolicScore dicts
            signal_profiles=[...],    # list of SignalProfile dicts
            context_metadata={...},   # chips/platforms (optional)
        )
    """

    VECTOR_VERSION = "1.0.0"
    MIN_TRACKS = 1  # minimum tracks to produce a vector (warn below 3)

    def compute(
        self,
        composer_id: str,
        symbolic_scores: list[dict[str, Any]],
        signal_profiles: list[dict[str, Any]],
        context_metadata: dict[str, Any] | None = None,
        track_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate track analysis into a composer style vector.

        Args:
            composer_id:      Canonical composer entity ID.
            symbolic_scores:  List of SymbolicScore dicts from ANALYZE_TRACK.
            signal_profiles:  List of SignalProfile dicts from ANALYZE_TRACK.
            context_metadata: Optional hardware context (chips, platforms).
            track_ids:        Optional list of contributing track IDs.

        Returns:
            ArtistStyleVector dict for Atlas compilation.
        """
        n_symbolic = len(symbolic_scores)
        n_signal   = len(signal_profiles)
        n_tracks   = max(n_symbolic, n_signal)

        warnings: list[str] = []
        if n_tracks < 3:
            warnings.append(
                f"Only {n_tracks} tracks available. Style vector may be unreliable. "
                "Recommend >= 10 tracks for a stable composer fingerprint."
            )

        melodic   = self._compute_melodic_features(symbolic_scores)
        harmonic  = self._compute_harmonic_features(symbolic_scores, signal_profiles)
        rhythmic  = self._compute_rhythmic_features(symbolic_scores, signal_profiles)
        structural = self._compute_structural_features(symbolic_scores)
        timbral   = self._compute_timbral_features(signal_profiles)
        motivic   = self._compute_motivic_features(symbolic_scores)

        # Context metadata — never part of musical identity
        ctx = self._normalize_context(context_metadata or {})

        return {
            # Identity
            "composer_id":      composer_id,
            "track_count":      n_tracks,
            "track_ids":        track_ids or [],
            "vector_version":   self.VECTOR_VERSION,
            # Musical cognition features (define identity)
            "melodic_features":    melodic,
            "harmonic_features":   harmonic,
            "rhythmic_features":   rhythmic,
            "structural_features": structural,
            "timbral_features":    timbral,
            "motivic_features":    motivic,
            # Hardware context — explains differences, does not define identity
            "context_metadata":    ctx,
            # Provenance
            "warnings":         warnings,
            "sources": {
                "symbolic_score_count": n_symbolic,
                "signal_profile_count": n_signal,
            },
        }

    # ── Melodic features ───────────────────────────────────────────────────

    def _compute_melodic_features(
        self,
        symbolic_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute melodic identity features:
          - interval_distribution: normalized semitone interval frequencies
          - leap_frequency:        fraction of intervals >= 5 semitones (perfect 4th+)
          - step_frequency:        fraction of intervals 1-2 semitones (stepwise motion)
          - phrase_length_mean:    mean phrase length in quarter notes
          - phrase_length_std:     std of phrase lengths
          - melodic_contour_bias:  fraction of upward melodic motion (> 0.5 = ascending tendency)
          - register_preference:   mean MIDI pitch (40-60: low, 60-72: mid, 72+: high)
        """
        all_intervals:    Counter[int] = Counter()
        phrase_lengths:   list[float]  = []
        contour_up:       int          = 0
        contour_total:    int          = 0
        all_pitches:      list[float]  = []

        for score in symbolic_scores:
            # Intervals
            hist = score.get("interval_histogram", {})
            for k, v in hist.items():
                try:
                    all_intervals[int(k)] += int(v)
                except (ValueError, TypeError):
                    pass

            # Contour
            contour = score.get("melodic_contour", [])
            for c in contour:
                contour_total += 1
                if c > 0:
                    contour_up += 1

            # Phrase lengths
            for phrase in score.get("phrase_segmentation", []):
                l = phrase.get("length")
                if l is not None:
                    try:
                        phrase_lengths.append(float(l))
                    except (TypeError, ValueError):
                        pass

            # Pitches
            for note in score.get("notes", []):
                p = note.get("midi") or note.get("pitch")
                if isinstance(p, (int, float)):
                    all_pitches.append(float(p))

        total_intervals = sum(all_intervals.values()) or 1
        normalized_intervals = {
            str(k): round(v / total_intervals, 4)
            for k, v in sorted(all_intervals.items())
        }

        leap_count = sum(v for k, v in all_intervals.items() if abs(k) >= 5)
        step_count = sum(v for k, v in all_intervals.items() if 1 <= abs(k) <= 2)
        leap_freq  = round(leap_count / total_intervals, 4)
        step_freq  = round(step_count / total_intervals, 4)

        return {
            "interval_distribution": normalized_intervals,
            "leap_frequency":        leap_freq,
            "step_frequency":        step_freq,
            "phrase_length_mean":    round(_safe_mean(phrase_lengths), 3),
            "phrase_length_std":     round(_safe_std(phrase_lengths), 3),
            "melodic_contour_bias":  round(contour_up / contour_total, 4) if contour_total > 0 else 0.5,
            "register_preference":   round(_safe_mean(all_pitches), 2) if all_pitches else 60.0,
        }

    # ── Harmonic features ──────────────────────────────────────────────────

    def _compute_harmonic_features(
        self,
        symbolic_scores: list[dict[str, Any]],
        signal_profiles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute harmonic identity features:
          - chord_type_distribution:    frequency of chord root motion intervals
          - key_distribution:           most common keys used
          - modulation_frequency:       number of key changes per minute
          - chromaticism_index:         fraction of non-diatonic intervals
          - harmonic_rhythm_mean:       mean beats between chord changes
          - tonal_centroid_mean:        mean 6-dim tonal centroid (from essentia if available)
        """
        chord_progressions: list[list[str]] = []
        key_list:           list[str]       = []
        key_changes_total:  int             = 0
        duration_total:     float           = 0.0
        tonal_centroids:    list[list[float]] = []
        chroma_accum:       list[list[float]] = []

        for score in symbolic_scores:
            cp = score.get("chord_progression", [])
            if cp:
                chord_progressions.append(cp)
            for ke in score.get("key_estimates", []):
                k = ke.get("key")
                if k:
                    key_list.append(str(k))
            dur = score.get("duration_total", 0.0)
            if dur:
                duration_total += float(dur)
            key_changes_total += max(0, len(score.get("key_estimates", [])) - 1)

        for prof in signal_profiles:
            tc = prof.get("tonal_centroid")
            if tc and isinstance(tc, list) and len(tc) >= 6:
                tonal_centroids.append([float(x) for x in tc[:6]])
            cm = prof.get("chroma_means")
            if cm and isinstance(cm, list) and len(cm) >= 12:
                chroma_accum.append([float(x) for x in cm[:12]])

        # Chord root motion
        root_intervals: Counter[str] = Counter()
        for cp in chord_progressions:
            for a, b in zip(cp, cp[1:]):
                root_intervals[f"{a}→{b}"] += 1
        ri_total = sum(root_intervals.values()) or 1
        chord_type_dist = {k: round(v / ri_total, 4) for k, v in root_intervals.most_common(20)}

        # Key distribution
        key_counter     = Counter(key_list)
        key_distribution = {k: round(v / max(len(key_list), 1), 4) for k, v in key_counter.most_common(10)}

        # Modulation frequency (key changes per minute)
        duration_min   = duration_total / (4 * 60) if duration_total > 0 else 1.0
        mod_freq       = round(key_changes_total / duration_min, 4) if duration_min > 0 else 0.0

        # Chromaticism: fraction of non-step, non-perfect intervals (proxy)
        # Uses chroma evenness: uniform chroma = very chromatic
        chroma_evenness: float | None = None
        if chroma_accum:
            import statistics as _s
            mean_chroma = [_s.mean(row[i] for row in chroma_accum) for i in range(12)]
            chroma_total = sum(mean_chroma) or 1
            normed = [x / chroma_total for x in mean_chroma]
            # Entropy as proxy for chromaticism
            entropy = -sum(p * math.log2(p + 1e-10) for p in normed)
            chroma_evenness = round(entropy / math.log2(12), 4)  # 0=monotonal, 1=fully chromatic

        # Tonal centroid mean
        tc_mean: list[float] | None = None
        if tonal_centroids:
            tc_mean = [round(sum(row[i] for row in tonal_centroids) / len(tonal_centroids), 4)
                       for i in range(6)]

        return {
            "chord_type_distribution": chord_type_dist,
            "key_distribution":        key_distribution,
            "modulation_frequency":    mod_freq,
            "chromaticism_index":      chroma_evenness,
            "tonal_centroid_mean":     tc_mean,
        }

    # ── Rhythmic features ──────────────────────────────────────────────────

    def _compute_rhythmic_features(
        self,
        symbolic_scores: list[dict[str, Any]],
        signal_profiles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute rhythmic identity features:
          - note_density_mean:   mean notes per second across tracks
          - note_density_std:    variance in note density
          - tempo_mean:          mean BPM across tracks
          - tempo_variance:      variance in BPM
          - syncopation_score:   fraction of notes placed on off-beats (proxy)
          - onset_density_mean:  mean onsets/second from signal profiles
        """
        note_densities: list[float] = []
        tempos:         list[float] = []
        onset_densities: list[float] = []
        offbeat_fractions: list[float] = []

        for score in symbolic_scores:
            dur = score.get("duration_total", 0.0)
            notes = score.get("notes", [])
            if dur and dur > 0:
                note_densities.append(len(notes) / float(dur))
            for tm in score.get("tempo_map", []):
                t = tm.get("tempo_bpm") or tm.get("bpm")
                if t and float(t) > 0:
                    tempos.append(float(t))
            # Syncopation proxy: offbeat notes
            if notes and dur and dur > 0:
                offbeat = sum(
                    1 for n in notes
                    if abs((n.get("offset", 0.0) % 1.0) - 0.5) < 0.15
                )
                offbeat_fractions.append(offbeat / max(len(notes), 1))

        for prof in signal_profiles:
            od = prof.get("onset_density")
            if od is not None:
                onset_densities.append(float(od))
            t = prof.get("tempo") or prof.get("bpm")
            if t and float(t) > 0:
                tempos.append(float(t))

        return {
            "note_density_mean":  round(_safe_mean(note_densities), 4),
            "note_density_std":   round(_safe_std(note_densities), 4),
            "tempo_mean":         round(_safe_mean(tempos), 2),
            "tempo_variance":     round(_safe_std(tempos) ** 2, 2),
            "syncopation_score":  round(_safe_mean(offbeat_fractions), 4),
            "onset_density_mean": round(_safe_mean(onset_densities), 4),
        }

    # ── Structural features ───────────────────────────────────────────────

    def _compute_structural_features(
        self,
        symbolic_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute structural identity features:
          - track_length_mean:           mean track duration (quarter notes)
          - phrase_count_mean:           mean number of phrases per track
          - section_transition_freq:     mean transitions per quarter note
          - loop_length_estimate:        estimated repetition period
        """
        track_lengths: list[float] = []
        phrase_counts: list[int]   = []

        for score in symbolic_scores:
            dur = score.get("duration_total", 0.0)
            if dur:
                track_lengths.append(float(dur))
            phrases = score.get("phrase_segmentation", [])
            phrase_counts.append(len(phrases))

        # Section transition frequency
        total_dur    = sum(track_lengths) or 1.0
        total_phrases = sum(phrase_counts)
        transition_freq = round(total_phrases / total_dur, 6) if total_dur > 0 else 0.0

        return {
            "track_length_mean":      round(_safe_mean(track_lengths), 2),
            "phrase_count_mean":      round(_safe_mean([float(p) for p in phrase_counts]), 2),
            "section_transition_freq": transition_freq,
            "loop_length_estimate":   None,  # populated by loop_detector if available
        }

    # ── Timbral features ──────────────────────────────────────────────────

    def _compute_timbral_features(
        self,
        signal_profiles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute timbral identity features:
          - spectral_centroid_mean:     mean spectral centroid across tracks
          - spectral_centroid_std:      std of spectral centroid
          - brightness_mean:            mean brightness (normalized centroid)
          - brightness_distribution:    histogram of brightness values (5 bins)
          - mfcc_centroid:              mean of 13 MFCC coefficients across tracks
          - dynamic_range_mean:         mean dynamic complexity
        """
        centroids:        list[float] = []
        brightnesses:     list[float] = []
        mfcc_accum:       list[list[float]] = []
        dynamic_complexities: list[float] = []

        for prof in signal_profiles:
            sc = prof.get("spectral_centroid")
            if isinstance(sc, dict):
                centroids.append(sc.get("mean", 0.0))
            elif isinstance(sc, (int, float)):
                centroids.append(float(sc))

            b = prof.get("brightness")
            if b is not None:
                brightnesses.append(float(b))

            mfcc = prof.get("mfcc_means", [])
            if mfcc and len(mfcc) == 13:
                mfcc_accum.append([float(x) for x in mfcc])

            dc = prof.get("dynamic_complexity") or (
                prof.get("dynamic_envelope", {}).get("std_rms")
            )
            if dc is not None:
                dynamic_complexities.append(float(dc))

        # Brightness histogram (5 bins: 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
        brightness_hist = [0, 0, 0, 0, 0]
        for b in brightnesses:
            idx = min(int(b * 5), 4)
            brightness_hist[idx] += 1
        total_b = sum(brightness_hist) or 1
        brightness_distribution = [round(x / total_b, 4) for x in brightness_hist]

        # MFCC centroid (mean across all tracks)
        mfcc_centroid: list[float] | None = None
        if mfcc_accum:
            mfcc_centroid = [
                round(sum(row[i] for row in mfcc_accum) / len(mfcc_accum), 4)
                for i in range(13)
            ]

        return {
            "spectral_centroid_mean": round(_safe_mean(centroids), 2),
            "spectral_centroid_std":  round(_safe_std(centroids), 2),
            "brightness_mean":        round(_safe_mean(brightnesses), 4),
            "brightness_distribution": brightness_distribution,
            "mfcc_centroid":          mfcc_centroid,
            "dynamic_range_mean":     round(_safe_mean(dynamic_complexities), 4),
        }

    # ── Motivic features ──────────────────────────────────────────────────

    def _compute_motivic_features(
        self,
        symbolic_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compute motivic identity features:
          - motif_repetition_frequency: how often identical interval patterns repeat
          - motif_entropy:              diversity of interval patterns (high=varied, low=repetitive)
          - common_motifs:              top 5 recurring short interval patterns
        """
        # Use trigrams over interval sequences as motif proxy
        motif_counter: Counter[tuple[int, ...]] = Counter()
        total_trigrams = 0

        for score in symbolic_scores:
            hist = score.get("interval_histogram", {})
            intervals = []
            for k, v in hist.items():
                try:
                    intervals.extend([int(k)] * int(v))
                except (ValueError, TypeError):
                    pass

            # Build trigrams
            for i in range(len(intervals) - 2):
                trigram = (intervals[i], intervals[i + 1], intervals[i + 2])
                motif_counter[trigram] += 1
                total_trigrams += 1

        if total_trigrams == 0:
            return {
                "motif_repetition_frequency": 0.0,
                "motif_entropy":              0.0,
                "common_motifs":              [],
            }

        # Repetition frequency: fraction of all trigrams that repeat at least once
        repeated = sum(1 for v in motif_counter.values() if v > 1)
        rep_freq  = round(repeated / len(motif_counter), 4)

        # Entropy
        probs   = [v / total_trigrams for v in motif_counter.values()]
        entropy = round(-sum(p * math.log2(p + 1e-10) for p in probs), 4)

        # Top 5 motifs
        common_motifs = [
            {"intervals": list(k), "count": v}
            for k, v in motif_counter.most_common(5)
        ]

        return {
            "motif_repetition_frequency": rep_freq,
            "motif_entropy":              entropy,
            "common_motifs":              common_motifs,
        }

    # ── Context metadata ──────────────────────────────────────────────────

    def _normalize_context(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize context metadata.

        Context explains hardware differences — it does NOT define identity.
        A composer's style vector should be recognizable across eras regardless
        of which chips or platforms were available.
        """
        return {
            "platforms_used": sorted(set(ctx.get("platforms_used", []))),
            "chips_used":     sorted(set(ctx.get("chips_used", []))),
            "era_range":      ctx.get("era_range"),
            "note": (
                "Context metadata describes hardware constraints only. "
                "Musical identity is determined by cognition features above."
            ),
        }


# ── Utility functions ──────────────────────────────────────────────────────

def _safe_mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_std(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0
