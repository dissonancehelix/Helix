"""
adapter_librosa.py — Helix adapter for librosa (MIR feature extraction)
=========================================================================
Wraps librosa + madmom for research-grade audio MIR feature extraction.

Purpose:
    Extract Tier C MIR features from rendered audio (WAV, FLAC, MP3, etc.)
    and return a structured SignalProfile.

Input:
    file_path (str | Path)  — audio file path
    sample_rate (int)       — target sample rate (default: 22050)

Output (dict — SignalProfile schema):
    Spectral:
        "spectral_centroid"      dict   {mean, std, min, max}
        "spectral_bandwidth"     dict
        "spectral_rolloff"       dict
        "spectral_contrast"      list[float]   7-band peak vs valley
        "spectral_flatness"      dict   0=tonal, 1=noise-like
        "spectral_flux"          float  mean frame-to-frame spectral change
        "brightness"             float  centroid mean normalized to [0, 1]
        "poly_features"          list[float]  2-coeff polynomial fit to spectrum

    Rhythm:
        "tempo"                  int | None    BPM (madmom RNN → librosa fallback)
        "beat_times"             list[float]   beat timestamps in seconds
        "onset_density"          float         onsets per second
        "onset_strength"         dict   {mean, std, max} of onset strength envelope
        "pulse_clarity"          float  entropy of predominant local pulse (low = steady)
        "tempogram_peaks"        list[float]   top-3 BPM peaks from Fourier tempogram

    Harmony:
        "chroma_means"           list[float]   12 CQT chroma bins
        "chroma_cens_means"      list[float]   12 CENS chroma bins (noise-robust)
        "tonnetz_means"          list[float]   6-dim tonal network means
        "tonnetz_stds"           list[float]   6-dim tonal network std (modulation indicator)
        "harmonic_novelty_mean"  float         mean chord/key change rate
        "harmonic_novelty_series" list[float]  ~1 value/sec, change magnitude over time

    Timbre:
        "mfcc_means"             list[float]   13 MFCC coefficients
        "delta_mfcc_means"       list[float]   13 first-derivative MFCC (timbre rate of change)
        "delta2_mfcc_means"      list[float]   13 second-derivative MFCC (timbre acceleration)
        "zero_crossing_rate"     dict

    Dynamics:
        "dynamic_envelope"       dict   {mean_rms, std_rms, peak_rms}
        "dynamic_range"          float  peak_rms - mean_rms
        "rms_contour"            list[float]   RMS downsampled ~1/sec (dynamic shape over time)

    Structure:
        "structural_sections"    list[float]   section boundary timestamps (agglomerative)

    Music-theoretic (madmom):
        "key_label"              str | None    e.g. "F# minor" (madmom CNN → chroma fallback)
        "key_confidence"         float | None  max softmax score
        "chord_sequence"         list[dict]    [{start, end, chord}] (madmom DeepChroma CRF)

    Timbre clustering:
        "timbre_clusters"        list          placeholder, populated by STYLE_VECTOR operator

    Meta:
        "sample_rate"            int
        "duration"               float
        "source_path"            str
        "adapter"                "librosa"
        "available"              bool

Fallback chain:
    tempo/beats: madmom RNNBeatProcessor + BeatTrackingProcessor → librosa.beat.beat_track
    key:         madmom CNNKeyRecognitionProcessor → librosa chroma argmax (pitch class only)
    chords:      madmom DeepChromaChordRecognitionProcessor → [] (silent fail)

Adapter rules:
    • Returns an empty SignalProfile with available=False if librosa missing.
    • All madmom features are wrapped in try/except — failure is silent.
    • No Helix logic.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


def _stats(arr: Any) -> dict[str, float]:
    """Compute summary statistics for a 1D or 2D numpy array."""
    import numpy as np
    flat = np.asarray(arr).flatten()
    return {
        "mean": float(np.mean(flat)),
        "std":  float(np.std(flat)),
        "min":  float(np.min(flat)),
        "max":  float(np.max(flat)),
    }


class Adapter:
    """
    Adapter wrapping librosa + madmom for audio MIR feature extraction.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → librosa / madmom
    """
    toolkit = "librosa"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Extract MIR features from an audio file.

        Returns a SignalProfile dict. If librosa is not installed, returns
        a minimal dict with available=False (non-blocking).
        """
        file_path   = payload.get("file_path")
        sample_rate = payload.get("sample_rate", 22050)

        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")

        try:
            import librosa
            import numpy as np
        except ImportError:
            return self._empty_profile(str(path), sample_rate)

        # Ensure foobar's bundled ffmpeg is available for audioread fallback
        # (handles m4a, wma, and other formats soundfile can't decode natively)
        import os
        _foobar_ffmpeg = r"C:\Program Files\foobar2000\encoders"
        if os.path.isdir(_foobar_ffmpeg) and _foobar_ffmpeg not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _foobar_ffmpeg + os.pathsep + os.environ.get("PATH", "")

        try:
            y, sr = librosa.load(str(path), sr=sample_rate, mono=True)
        except Exception as exc:
            raise AdapterError(f"librosa load failed for {path}: {exc}") from exc

        duration = float(librosa.get_duration(y=y, sr=sr))

        # ── Spectral (compute STFT once, reuse) ──────────────────────────────
        S_mag = np.abs(librosa.stft(y))

        spec_centroid  = librosa.feature.spectral_centroid(S=S_mag, sr=sr)
        spec_bandwidth = librosa.feature.spectral_bandwidth(S=S_mag, sr=sr)
        spec_rolloff   = librosa.feature.spectral_rolloff(S=S_mag, sr=sr)
        zcr            = librosa.feature.zero_crossing_rate(y)

        try:
            contrast = librosa.feature.spectral_contrast(S=S_mag, sr=sr)
            spectral_contrast = [float(np.mean(contrast[i])) for i in range(contrast.shape[0])]
        except Exception:
            spectral_contrast = [0.0] * 7

        try:
            flatness = librosa.feature.spectral_flatness(S=S_mag)
            spectral_flatness = _stats(flatness)
        except Exception:
            spectral_flatness = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        # Spectral flux — mean frame-to-frame L2 change
        try:
            _flux    = np.diff(S_mag, axis=1)
            spectral_flux = round(float(np.mean(np.sqrt((_flux ** 2).sum(axis=0)))), 4)
        except Exception:
            spectral_flux = 0.0

        # Polynomial fit to mean spectrum (spectral shape / tilt)
        try:
            _mean_spec   = np.mean(S_mag, axis=1)
            _freqs       = np.linspace(0, 1, len(_mean_spec))
            poly_coeffs  = np.polyfit(_freqs, _mean_spec, 1)
            poly_features = [round(float(c), 4) for c in poly_coeffs]
        except Exception:
            poly_features = [0.0, 0.0]

        centroid_mean = float(np.mean(spec_centroid))
        brightness    = centroid_mean / (sr / 2) if sr > 0 else 0.0

        # ── Rhythm ────────────────────────────────────────────────────────────
        tempo_val  = None
        beat_times = []
        try:
            from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor
            _beat_acts = RNNBeatProcessor()(str(path))
            _beats     = BeatTrackingProcessor(fps=100)(_beat_acts)
            if len(_beats) > 1:
                tempo_val  = round(60.0 / (_beats[1:] - _beats[:-1]).mean())
                beat_times = [round(float(t), 3) for t in _beats]
        except Exception:
            pass
        if tempo_val is None:
            try:
                tempo, _beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                tempo_val  = round(float(tempo))
                beat_times = [round(float(t), 3)
                              for t in librosa.frames_to_time(_beat_frames, sr=sr)]
            except Exception:
                pass

        # Onset strength envelope
        try:
            onset_env    = librosa.onset.onset_strength(S=S_mag, sr=sr)
            onset_strength = {
                "mean": round(float(np.mean(onset_env)), 4),
                "std":  round(float(np.std(onset_env)), 4),
                "max":  round(float(np.max(onset_env)), 4),
            }
        except Exception:
            onset_env      = None
            onset_strength = {"mean": 0.0, "std": 0.0, "max": 0.0}

        onsets        = librosa.onset.onset_detect(y=y, sr=sr)
        onset_density = len(onsets) / duration if duration > 0 else 0.0

        # Pulse clarity — entropy of predominant local pulse
        # Low entropy = rhythmically steady; high = ambiguous / polyrhythmic
        pulse_clarity = 0.0
        try:
            plp     = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
            _p      = plp / (plp.sum() + 1e-10)
            _entr   = float(-np.sum(_p * np.log2(_p + 1e-10)))
            # Normalize by log2(len) so it's [0, 1]
            pulse_clarity = round(1.0 - _entr / np.log2(len(_p) + 1), 4)
        except Exception:
            pass

        # Tempogram — top-3 BPM peaks (captures dominant pulse + harmonics/polyrhythm)
        tempogram_peaks = []
        try:
            tgram  = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
            _tempo_axis = librosa.tempo_frequencies(tgram.shape[0], sr=sr)
            _mean_tgram = np.mean(tgram, axis=1)
            # mask out < 30 BPM and > 300 BPM
            _valid = (_tempo_axis >= 30) & (_tempo_axis <= 300)
            _mean_tgram[~_valid] = 0.0
            _peak_idxs  = np.argsort(_mean_tgram)[::-1][:3]
            tempogram_peaks = [round(float(_tempo_axis[i]), 1) for i in sorted(_peak_idxs)]
        except Exception:
            pass

        # ── Harmony ──────────────────────────────────────────────────────────
        # CQT chroma
        try:
            chroma      = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_means = [float(np.mean(chroma[i])) for i in range(12)]
        except Exception:
            chroma       = None
            chroma_means = [0.0] * 12

        # CENS chroma — noise-robust, better for harmonic analysis
        try:
            chroma_cens      = librosa.feature.chroma_cens(y=y, sr=sr)
            chroma_cens_means = [float(np.mean(chroma_cens[i])) for i in range(12)]
        except Exception:
            chroma_cens_means = [0.0] * 12

        # Tonnetz — means + stds (std = how much tonal center moves = modulation)
        try:
            _chroma_src  = chroma if chroma is not None else librosa.feature.chroma_cqt(y=y, sr=sr)
            tonnetz      = librosa.feature.tonnetz(chroma=_chroma_src)
            tonnetz_means = [float(np.mean(tonnetz[i])) for i in range(6)]
            tonnetz_stds  = [round(float(np.std(tonnetz[i])), 4) for i in range(6)]
        except Exception:
            tonnetz_means = [0.0] * 6
            tonnetz_stds  = [0.0] * 6

        # Harmonic novelty — onset strength on chroma detects chord/key changes
        harmonic_novelty_mean   = 0.0
        harmonic_novelty_series = []
        try:
            _chroma_src = chroma if chroma is not None else librosa.feature.chroma_cqt(y=y, sr=sr)
            _harm_nov   = librosa.onset.onset_strength(S=_chroma_src, sr=sr)
            harmonic_novelty_mean = round(float(np.mean(_harm_nov)), 4)
            _hop = max(1, int(sr / 512))
            harmonic_novelty_series = [round(float(v), 4) for v in _harm_nov[::_hop]]
        except Exception:
            pass

        # Key recognition — madmom CNN → librosa chroma fallback
        key_label      = None
        key_confidence = None
        try:
            from madmom.features.key import CNNKeyRecognitionProcessor, key_prediction_to_label
            _key_pred      = CNNKeyRecognitionProcessor()(str(path))
            key_label      = key_prediction_to_label(_key_pred)
            key_confidence = round(float(_key_pred.max()), 4)
        except Exception:
            pass
        if key_label is None:
            try:
                _key_idx  = int(np.array(chroma_means).argmax())
                key_label = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"][_key_idx]
            except Exception:
                pass

        # Chord recognition — madmom DeepChroma CRF
        chord_sequence = []
        try:
            from madmom.features.chords import DeepChromaChordRecognitionProcessor
            _chords = DeepChromaChordRecognitionProcessor()(str(path))
            chord_sequence = [
                {"start": round(float(c[0]), 3),
                 "end":   round(float(c[1]), 3),
                 "chord": str(c[2])}
                for c in _chords
            ]
        except Exception:
            pass

        # ── Timbre ────────────────────────────────────────────────────────────
        mfcc       = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc[i])) for i in range(13)]

        try:
            _delta_mfcc     = librosa.feature.delta(mfcc)
            delta_mfcc_means = [round(float(np.mean(_delta_mfcc[i])), 4) for i in range(13)]
        except Exception:
            delta_mfcc_means = [0.0] * 13

        try:
            _delta2_mfcc     = librosa.feature.delta(mfcc, order=2)
            delta2_mfcc_means = [round(float(np.mean(_delta2_mfcc[i])), 4) for i in range(13)]
        except Exception:
            delta2_mfcc_means = [0.0] * 13

        # ── Dynamics ─────────────────────────────────────────────────────────
        rms      = librosa.feature.rms(y=y)
        dyn_mean = float(np.mean(rms))
        dyn_peak = float(np.max(rms))

        # RMS contour downsampled to ~1 value/sec (dynamic shape over time)
        try:
            _frames_per_sec = max(1, int(sr / 512))
            rms_contour     = [round(float(v), 4) for v in rms[0][::_frames_per_sec]]
        except Exception:
            rms_contour = []

        # ── Structure ─────────────────────────────────────────────────────────
        structural_sections = []
        try:
            bounds_frames       = librosa.segment.agglomerative(mfcc, k=None)
            bounds_times        = librosa.frames_to_time(bounds_frames, sr=sr)
            structural_sections = [round(float(t), 3) for t in bounds_times]
        except Exception:
            pass

        # ── Assemble result ───────────────────────────────────────────────────
        result = {
            # Spectral
            "spectral_centroid":   _stats(spec_centroid),
            "spectral_bandwidth":  _stats(spec_bandwidth),
            "spectral_rolloff":    _stats(spec_rolloff),
            "spectral_contrast":   spectral_contrast,
            "spectral_flatness":   spectral_flatness,
            "spectral_flux":       spectral_flux,
            "brightness":          brightness,
            "poly_features":       poly_features,
            # Rhythm
            "tempo":               tempo_val,
            "beat_times":          beat_times,
            "onset_density":       onset_density,
            "onset_strength":      onset_strength,
            "pulse_clarity":       pulse_clarity,
            "tempogram_peaks":     tempogram_peaks,
            # Harmony
            "chroma_means":        chroma_means,
            "chroma_cens_means":   chroma_cens_means,
            "tonnetz_means":       tonnetz_means,
            "tonnetz_stds":        tonnetz_stds,
            "harmonic_novelty_mean":   harmonic_novelty_mean,
            "harmonic_novelty_series": harmonic_novelty_series,
            # Music-theoretic (madmom)
            "key_label":           key_label,
            "key_confidence":      key_confidence,
            "chord_sequence":      chord_sequence,
            # Timbre
            "mfcc_means":          mfcc_means,
            "delta_mfcc_means":    delta_mfcc_means,
            "delta2_mfcc_means":   delta2_mfcc_means,
            "zero_crossing_rate":  _stats(zcr),
            "timbre_clusters":     [],  # populated by STYLE_VECTOR operator
            # Dynamics
            "dynamic_envelope": {
                "mean_rms": dyn_mean,
                "std_rms":  float(np.std(rms)),
                "peak_rms": dyn_peak,
            },
            "dynamic_range":       dyn_peak - dyn_mean,
            "rms_contour":         rms_contour,
            # Structure
            "structural_sections": structural_sections,
            # Meta
            "sample_rate":         sr,
            "duration":            duration,
            "source_path":         str(path),
            "adapter":             "librosa",
            "available":           True,
        }
        return self.normalize(result)

    def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    def is_available(self) -> bool:
        try:
            import librosa  # noqa
            return True
        except ImportError:
            return False

    def _empty_profile(self, source_path: str, sample_rate: int) -> dict[str, Any]:
        empty_stats = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        return {
            "spectral_centroid":       empty_stats,
            "spectral_bandwidth":      empty_stats,
            "spectral_rolloff":        empty_stats,
            "spectral_contrast":       [0.0] * 7,
            "spectral_flatness":       empty_stats,
            "spectral_flux":           0.0,
            "brightness":              0.0,
            "poly_features":           [0.0, 0.0],
            "tempo":                   None,
            "beat_times":              [],
            "onset_density":           0.0,
            "onset_strength":          {"mean": 0.0, "std": 0.0, "max": 0.0},
            "pulse_clarity":           0.0,
            "tempogram_peaks":         [],
            "chroma_means":            [0.0] * 12,
            "chroma_cens_means":       [0.0] * 12,
            "tonnetz_means":           [0.0] * 6,
            "tonnetz_stds":            [0.0] * 6,
            "harmonic_novelty_mean":   0.0,
            "harmonic_novelty_series": [],
            "key_label":               None,
            "key_confidence":          None,
            "chord_sequence":          [],
            "mfcc_means":              [0.0] * 13,
            "delta_mfcc_means":        [0.0] * 13,
            "delta2_mfcc_means":       [0.0] * 13,
            "zero_crossing_rate":      empty_stats,
            "timbre_clusters":         [],
            "dynamic_envelope":        {"mean_rms": 0.0, "std_rms": 0.0, "peak_rms": 0.0},
            "dynamic_range":           0.0,
            "rms_contour":             [],
            "structural_sections":     [],
            "sample_rate":             sample_rate,
            "duration":                0.0,
            "source_path":             source_path,
            "adapter":                 "librosa",
            "available":               False,
        }
