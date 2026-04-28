"""
mir_extractor.py — Tier D Music Information Retrieval feature extractor
=======================================================================
Requires librosa.  Returns an empty dict when librosa is unavailable or
when no audio can be decoded — callers fall back to chip-proxy features.

For chip formats (VGM, SPC, NSF, SID …) there is no PCM output at the
Python layer without Tier B emulation.  When called with audio_path=None,
this module returns chip_proxy features derived from the chip feature dict.

API
---
extract_from_file(audio_path: Path,
                  sr: int = 22050,
                  n_mfcc: int = 13) -> dict
    Returns dict with keys: mfcc (13), chroma (12), spectral_*, tempo, beat_strength.

extract_chip_proxy(chip_features: dict) -> dict
    Derives MIR-shaped features from chip-level data (no audio needed).
    Used when librosa is absent or audio is unavailable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

try:
    import librosa as _librosa
    _HAS_LIBROSA = True
except ImportError:
    _HAS_LIBROSA = False


def _zeros(n: int) -> list[float]:
    return [0.0] * n


# ---------------------------------------------------------------------------
# Audio-based extraction
# ---------------------------------------------------------------------------

def extract_from_file(
    audio_path: Path,
    sr: int = 22050,
    n_mfcc: int = 13,
) -> dict[str, Any]:
    """
    Extract MIR features from an audio file (WAV, FLAC, OGG, MP3 …).
    Returns {} when librosa is not installed or on any error.
    """
    if not _HAS_LIBROSA or not _HAS_NP:
        return {}

    if audio_path is None or not Path(audio_path).exists():
        return {}

    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            y, loaded_sr = _librosa.load(str(audio_path), sr=sr, mono=True)
    except Exception:
        return {}

    try:
        result: dict[str, Any] = {}

        # 1. Melodic Features (approximated from chroma/pitch tracking)
        pitches, magnitudes = _librosa.piptrack(y=y, sr=loaded_sr)
        pitch_contour = []
        for t in range(magnitudes.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t] if magnitudes[index, t] > 0 else 0
            if pitch > 0:
                pitch_contour.append(float(_librosa.hz_to_midi(pitch)))
        
        intervals = _np.diff(pitch_contour).tolist() if len(pitch_contour) > 1 else []
        interval_dist = {str(k): int(v) for k, v in zip(*_np.unique(intervals, return_counts=True))} if intervals else {}
        melodic_range = float(max(pitch_contour) - min(pitch_contour)) if pitch_contour else 0.0
        
        counts = _np.array(list(interval_dist.values()))
        probs = counts / counts.sum() if counts.sum() > 0 else _np.array([0])
        melodic_entropy = float(-_np.sum(probs * _np.log2(probs + 1e-9)))

        result["melodic"] = {
            "interval_distribution": interval_dist,
            "pitch_contour": pitch_contour[::max(1, len(pitch_contour)//100)], # downsampled
            "melodic_range": melodic_range,
            "melodic_entropy": melodic_entropy
        }

        # 2. Spectral Features
        spec_centroid = _librosa.feature.spectral_centroid(y=y, sr=loaded_sr)
        spec_bandwidth = _librosa.feature.spectral_bandwidth(y=y, sr=loaded_sr)
        spec_flatness = _librosa.feature.spectral_flatness(y=y)

        result["spectral"] = {
            "spectral_centroid": float(spec_centroid.mean()),
            "spectral_bandwidth": float(spec_bandwidth.mean()),
            "spectral_flatness": float(spec_flatness.mean())
        }

        # 3. Dynamic Features
        rms = _librosa.feature.rms(y=y)
        dynamic_range = float(rms.max() - rms.min())
        onset_env = _librosa.onset.onset_strength(y=y, sr=loaded_sr)

        result["dynamic"] = {
            "rms_loudness": float(rms.mean()),
            "dynamic_range": dynamic_range,
            "attack_envelope": [float(x) for x in onset_env[::max(1, len(onset_env)//100)]]
        }

        # 4. Rhythmic Features
        tempo, beats = _librosa.beat.beat_track(y=y, sr=loaded_sr)
        beat_times = _librosa.frames_to_time(beats, sr=loaded_sr)
        duration = _librosa.get_duration(y=y, sr=loaded_sr)
        rhythmic_density = len(beats) / duration if duration > 0 else 0
        syncopation_index = float(_np.var(_np.diff(beat_times))) if len(beat_times) > 1 else 0.0
        
        result["rhythmic"] = {
            "tempo_histogram": [float(tempo)],
            "beat_histogram": [float(b) for b in beat_times[:50]], 
            "rhythmic_density": rhythmic_density,
            "syncopation_index": syncopation_index
        }

        # 5. Harmonic Features
        chroma = _librosa.feature.chroma_cqt(y=y, sr=loaded_sr)
        key_dist = [float(v) for v in chroma.mean(axis=1)]
        tonal_tension = _librosa.feature.tonnetz(y=y, sr=loaded_sr)

        result["harmonic"] = {
            "key_distribution": key_dist,
            "chord_distribution": key_dist, # Simplified proxy
            "modulation_frequency": float(_np.var(key_dist)),
            "tonal_tension_curve": [float(v) for v in tonal_tension[0][::max(1, len(tonal_tension[0])//100)]]
        }

        # 6. Motif & 7. Structural (Placeholder for integration logic in motif_discovery)
        result["motif_features"] = {}
        result["structural_features"] = {"phrase_length_distribution": [], "section_segmentation": [], "repetition_patterns": []}

        return result

    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Chip-proxy features (no audio needed)
# ---------------------------------------------------------------------------

def extract_chip_proxy(chip_features: dict[str, Any]) -> dict[str, Any]:
    """
    Derive MIR-shaped feature values from chip-level analysis.
    This is a Tier A proxy — confidence is lower than real audio analysis.
    """
    result: dict[str, Any] = {}

    # MFCC proxy: use chip spectral shape approximation
    # Treat pitch_center and pitch_range as rough spectral proxies
    pitch_center = float(chip_features.get("pitch_center", 60))
    pitch_range  = float(chip_features.get("pitch_range", 24))
    pitch_entropy = float(chip_features.get("pitch_entropy", 0.5))

    # Rough spectral centroid proxy: map MIDI pitch to Hz
    # C4 = 261.6 Hz → use as center, scale by pitch_center deviation from 60
    spectral_centroid_proxy = 261.6 * (2.0 ** ((pitch_center - 60) / 12.0))
    result["spectral_centroid"] = spectral_centroid_proxy
    result["spectral_rolloff"]  = spectral_centroid_proxy * 2.0
    result["spectral_flatness"] = min(1.0, pitch_entropy)
    result["zcr"]               = 0.0
    result["spectral_flux"]     = 0.0

    # MFCC proxy: 13 zeros with slight first-coefficient variation
    mfcc_proxy = [spectral_centroid_proxy / 500.0] + [0.0] * 12
    result["mfcc"] = mfcc_proxy[:13]

    # Chroma proxy from pitch histogram if available
    pitch_hist = chip_features.get("pitch_histogram", _zeros(12))
    result["chroma"] = [float(x) for x in pitch_hist[:12]] if len(pitch_hist) >= 12 else _zeros(12)

    # Tempo proxy from rhythm features
    result["tempo"]        = float(chip_features.get("tempo_bpm", 0.0))
    result["beat_strength"] = float(chip_features.get("beat_regularity", 0.0))

    return result


def is_available() -> bool:
    return _HAS_LIBROSA and _HAS_NP
