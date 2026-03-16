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
        y, loaded_sr = _librosa.load(str(audio_path), sr=sr, mono=True)
    except Exception:
        return {}

    try:
        result: dict[str, Any] = {}

        # MFCC-13
        mfcc = _librosa.feature.mfcc(y=y, sr=loaded_sr, n_mfcc=n_mfcc)
        result["mfcc"] = [float(v) for v in mfcc.mean(axis=1)]

        # Chroma-12
        chroma = _librosa.feature.chroma_stft(y=y, sr=loaded_sr)
        result["chroma"] = [float(v) for v in chroma.mean(axis=1)]

        # Spectral features
        spec_centroid = _librosa.feature.spectral_centroid(y=y, sr=loaded_sr)
        spec_rolloff  = _librosa.feature.spectral_rolloff(y=y, sr=loaded_sr)
        zcr           = _librosa.feature.zero_crossing_rate(y)
        spec_flux     = _np.mean(_np.diff(_np.abs(_librosa.stft(y)), axis=1) ** 2)
        spec_flatness = _librosa.feature.spectral_flatness(y=y)

        result["spectral_centroid"] = float(spec_centroid.mean())
        result["spectral_rolloff"]  = float(spec_rolloff.mean())
        result["zcr"]               = float(zcr.mean())
        result["spectral_flux"]     = float(spec_flux)
        result["spectral_flatness"] = float(spec_flatness.mean())

        # Tempo and beat
        tempo, beats = _librosa.beat.beat_track(y=y, sr=loaded_sr)
        onset_env = _librosa.onset.onset_strength(y=y, sr=loaded_sr)
        beat_strength = float(onset_env[beats].mean()) if len(beats) else 0.0

        result["tempo"]        = float(tempo)
        result["beat_strength"] = beat_strength

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
