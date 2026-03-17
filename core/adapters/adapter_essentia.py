"""
adapter_essentia.py — Helix adapter for Essentia (audio descriptors)
=====================================================================
Wraps Essentia for high-quality audio descriptor extraction.

Purpose:
    Extract spectral, rhythmic, and tonal descriptors from rendered audio.
    Complements librosa with higher-quality algorithms for certain features.

Input:
    file_path (str | Path)  — audio file path
    sample_rate (int)       — target sample rate (default: 44100)

Output (dict — SignalProfile extension):
    {
        "spectral_centroid":        float,
        "spectral_complexity":      float,
        "dissonance":               float,
        "hfc":                      float,   # high frequency content
        "dynamic_complexity":       float,
        "bpm":                      float | None,
        "key":                      str | None,
        "key_strength":             float | None,
        "chord_histogram":          list[float],  # 24-bin chord distribution
        "tonal_centroid":           list[float],  # 6-dim tonal centroid vector
        "source_path":              str,
        "sample_rate":              int,
        "adapter":                  "essentia",
        "available":                bool,
    }

Adapter rules:
    • Returns available=False if essentia not installed.
    • No Helix logic.
    • Uses essentia.standard (non-streaming) API.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


class EssentiaAdapter:
    """
    Adapter wrapping Essentia for audio descriptors.

    Correct call path:
        HIL → ANALYZE_TRACK operator → EssentiaAdapter → essentia
    """

    def analyze(
        self,
        file_path: str | Path,
        sample_rate: int = 44100,
    ) -> dict[str, Any]:
        """
        Extract Essentia audio descriptors.

        Returns available=False dict if essentia is not installed.
        """
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")

        try:
            import essentia.standard as es
            import numpy as np
        except ImportError:
            return self._empty_profile(str(path), sample_rate)

        try:
            loader = es.MonoLoader(filename=str(path), sampleRate=sample_rate)
            audio  = loader()
        except Exception as exc:
            raise AdapterError(f"Essentia load failed for {path}: {exc}") from exc

        # Spectral descriptors
        w   = es.Windowing(type="hann")
        fft = es.Spectrum()
        sc  = es.SpectralCentroidTime(sampleRate=sample_rate)
        scm = es.SpectralComplexity()
        dis = es.Dissonance()
        hfc = es.HFC()
        dc  = es.DynamicComplexity(sampleRate=sample_rate)

        frame_size  = 2048
        hop_size    = 512
        centroids, complexities, dissonances, hfcs = [], [], [], []

        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            spec = fft(w(frame))
            centroids.append(sc(frame))
            complexities.append(scm(spec))
            if len(spec) > 0:
                freqs = np.linspace(0, sample_rate / 2, len(spec))
                mags  = spec
                dissonances.append(dis(freqs, mags))
            hfcs.append(hfc(spec))

        dyn_complexity, loudness = dc(audio)

        # Rhythm
        bpm_val = None
        try:
            rhythm = es.RhythmExtractor2013()
            bpm, _, _, _, _ = rhythm(audio)
            bpm_val = float(bpm)
        except Exception:
            pass

        # Tonal
        key_val = key_strength_val = None
        chord_histogram = [0.0] * 24
        tonal_centroid  = [0.0] * 6

        try:
            key_extractor = es.KeyExtractor()
            key_val, scale, key_strength_val = key_extractor(audio)
            key_val = f"{key_val} {scale}"
        except Exception:
            pass

        try:
            hpcp_extractor = es.HPCP()
            tonal_extractor = es.TonicIndianArtMusic()  # repurposed for centroid
            # Basic chord histogram via chroma
            chroma = es.HPCP()
            hpcp_frames = []
            for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
                spec = fft(w(frame))
                freqs_spect = es.SpectralPeaks()(spec)
                if len(freqs_spect[0]) > 0:
                    hpcp_frames.append(chroma(freqs_spect[0], freqs_spect[1]))
            if hpcp_frames:
                import numpy as _np
                mean_hpcp = _np.mean(hpcp_frames, axis=0).tolist()
                tonal_centroid = mean_hpcp[:6] if len(mean_hpcp) >= 6 else [0.0] * 6
                chord_histogram = mean_hpcp[:24] if len(mean_hpcp) >= 24 else mean_hpcp + [0.0] * (24 - len(mean_hpcp))
        except Exception:
            pass

        def _mean(lst: list) -> float:
            return float(sum(lst) / len(lst)) if lst else 0.0

        return {
            "spectral_centroid":   _mean(centroids),
            "spectral_complexity": _mean(complexities),
            "dissonance":          _mean(dissonances),
            "hfc":                 _mean(hfcs),
            "dynamic_complexity":  float(dyn_complexity),
            "bpm":                 bpm_val,
            "key":                 key_val,
            "key_strength":        float(key_strength_val) if key_strength_val is not None else None,
            "chord_histogram":     chord_histogram,
            "tonal_centroid":      tonal_centroid,
            "source_path":         str(path),
            "sample_rate":         sample_rate,
            "adapter":             "essentia",
            "available":           True,
        }

    def is_available(self) -> bool:
        try:
            import essentia  # noqa
            return True
        except ImportError:
            return False

    def _empty_profile(self, source_path: str, sample_rate: int) -> dict[str, Any]:
        return {
            "spectral_centroid":   0.0,
            "spectral_complexity": 0.0,
            "dissonance":          0.0,
            "hfc":                 0.0,
            "dynamic_complexity":  0.0,
            "bpm":                 None,
            "key":                 None,
            "key_strength":        None,
            "chord_histogram":     [0.0] * 24,
            "tonal_centroid":      [0.0] * 6,
            "source_path":         source_path,
            "sample_rate":         sample_rate,
            "adapter":             "essentia",
            "available":           False,
        }
