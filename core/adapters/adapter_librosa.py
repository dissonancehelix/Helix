"""
adapter_librosa.py — Helix adapter for librosa (MIR feature extraction)
=========================================================================
Wraps librosa audio feature extraction.

Purpose:
    Extract Tier D MIR features from rendered audio (WAV, FLAC, MP3, etc.)
    and return a structured SignalProfile.

Input:
    file_path (str | Path)  — audio file path
    sample_rate (int)       — target sample rate (default: 22050)

Output (dict — SignalProfile schema):
    {
        "spectral_centroid":     dict,  # {mean, std, min, max}
        "spectral_bandwidth":    dict,
        "spectral_rolloff":      dict,
        "brightness":            float,  # spectral centroid mean (normalized)
        "onset_density":         float,  # onsets per second
        "dynamic_envelope":      dict,  # {mean_rms, std_rms, peak_rms}
        "tempo":                 float | None,
        "zero_crossing_rate":    dict,
        "mfcc_means":            list[float],  # 13 MFCC coefficients
        "chroma_means":          list[float],  # 12 chroma bins
        "timbre_clusters":       list,          # placeholder for clustering
        "sample_rate":           int,
        "duration":              float,
        "source_path":           str,
        "adapter":               "librosa",
        "available":             bool,
    }

Adapter rules:
    • Returns an empty SignalProfile with available=False if librosa missing.
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
    Adapter wrapping librosa for audio MIR feature extraction.

    Correct call path:
        HIL → ANALYZE_TRACK operator → Adapter → librosa
    """
    toolkit = "librosa"
    substrate = "music"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Extract MIR features from an audio file.

        Returns a SignalProfile dict. If librosa is not installed, returns
        a minimal dict with available=False (non-blocking).
        """
        file_path = payload.get("file_path")
        sample_rate = payload.get("sample_rate", 22050)
        
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")

        try:
            import librosa
            import numpy as np
        except ImportError:
            return self._empty_profile(str(path), sample_rate)

        try:
            y, sr = librosa.load(str(path), sr=sample_rate, mono=True)
        except Exception as exc:
            raise AdapterError(f"librosa load failed for {path}: {exc}") from exc

        duration = float(librosa.get_duration(y=y, sr=sr))

        # Spectral features
        spec_centroid  = librosa.feature.spectral_centroid(y=y, sr=sr)
        spec_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        spec_rolloff   = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zcr            = librosa.feature.zero_crossing_rate(y)

        # Rhythm
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo_val = float(tempo)
        except Exception:
            tempo_val = None

        onsets      = librosa.onset.onset_detect(y=y, sr=sr)
        onset_density = len(onsets) / duration if duration > 0 else 0.0

        # Dynamics
        rms = librosa.feature.rms(y=y)

        # Timbral (MFCC)
        mfcc  = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc[i])) for i in range(13)]

        # Chroma
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_means = [float(np.mean(chroma[i])) for i in range(12)]

        centroid_mean = float(np.mean(spec_centroid))
        brightness    = centroid_mean / (sr / 2) if sr > 0 else 0.0  # normalize to [0,1]

        result = {
            "spectral_centroid":   _stats(spec_centroid),
            "spectral_bandwidth":  _stats(spec_bandwidth),
            "spectral_rolloff":    _stats(spec_rolloff),
            "brightness":          brightness,
            "onset_density":       onset_density,
            "dynamic_envelope": {
                "mean_rms": float(np.mean(rms)),
                "std_rms":  float(np.std(rms)),
                "peak_rms": float(np.max(rms)),
            },
            "tempo":             tempo_val,
            "zero_crossing_rate": _stats(zcr),
            "mfcc_means":        mfcc_means,
            "chroma_means":      chroma_means,
            "timbre_clusters":   [],  # populated by STYLE_VECTOR operator
            "sample_rate":       sr,
            "duration":          duration,
            "source_path":       str(path),
            "adapter":           "librosa",
            "available":         True,
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
            "spectral_centroid":   empty_stats,
            "spectral_bandwidth":  empty_stats,
            "spectral_rolloff":    empty_stats,
            "brightness":          0.0,
            "onset_density":       0.0,
            "dynamic_envelope":    {"mean_rms": 0.0, "std_rms": 0.0, "peak_rms": 0.0},
            "tempo":               None,
            "zero_crossing_rate":  empty_stats,
            "mfcc_means":          [0.0] * 13,
            "chroma_means":        [0.0] * 12,
            "timbre_clusters":     [],
            "sample_rate":         sample_rate,
            "duration":            0.0,
            "source_path":         source_path,
            "adapter":             "librosa",
            "available":           False,
        }
