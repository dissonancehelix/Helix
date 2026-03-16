"""
feature_vector.py — 64-dim feature vector builder (schema v0)
=============================================================
Assembles a normalised 64-dimensional float vector from chip, theory,
MIR, and metadata feature dicts.  Schema is versioned via config.py.

Vector layout (v0):
  dims  0–11  chip     (12 dims)
  dims 12–19  theory   (8 dims)
  dims 20–32  MFCC-13  (13 dims, zeros if no audio)
  dims 33–44  chroma   (12 dims, or top-12 pitch histogram bins)
  dims 45–49  spectral (5 dims: centroid, rolloff, zcr, flux, flatness)
  dims 50–57  platform onehot (8 dims)
  dims 58–63  chip onehot (6 dims)
  Total: 12+8+13+12+5+8+6 = 64

All dims normalised to [0, 1].

API
---
build_vector(chip, theory, mir, metadata, confidence) -> np.ndarray | list[float]
    chip:     dict from feature_extractor / chip_state_tracer
    theory:   dict from key_estimator, rhythm_analyzer, motif_detector
    mir:      dict from mir_extractor (or chip proxy)
    metadata: dict with 'platform' and 'chip_type' keys
    confidence: float 0–1
    Returns 64-element numpy array (float32) or list when numpy absent.

SCHEMA_VERSION: str
    Re-exported from config for callers that don't import config directly.
"""

from __future__ import annotations

import math
from typing import Any

from labs.music_lab.config import FEATURE_VECTOR_VERSION as SCHEMA_VERSION

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

DIM = 64

# ---------------------------------------------------------------------------
# Platform + chip onehot maps
# ---------------------------------------------------------------------------

PLATFORMS = ["Genesis", "SNES", "NES", "C64", "PC98", "PSX", "GBA", "other"]
CHIPS     = ["YM2612", "SPC700", "2A03", "SID", "OPL", "other"]

_PLATFORM_IDX = {p.lower(): i for i, p in enumerate(PLATFORMS)}
_CHIP_IDX     = {c.lower(): i for i, c in enumerate(CHIPS)}


def _onehot(idx: int, n: int) -> list[float]:
    v = [0.0] * n
    if 0 <= idx < n:
        v[idx] = 1.0
    return v


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _norm_midi(v: float) -> float:
    """Normalise a MIDI pitch 0–127 to [0, 1]."""
    return _clamp(v / 127.0)


def _norm_db(v: float, lo: float = 0.0, hi: float = 127.0) -> float:
    return _clamp((v - lo) / (hi - lo))


def _norm_hz(v: float, lo: float = 20.0, hi: float = 20000.0) -> float:
    if v <= 0:
        return 0.0
    return _clamp(math.log(v / lo) / math.log(hi / lo))


def _norm_tempo(bpm: float, lo: float = 40.0, hi: float = 240.0) -> float:
    return _clamp((bpm - lo) / (hi - lo))


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_vector(
    chip:       dict[str, Any],
    theory:     dict[str, Any],
    mir:        dict[str, Any],
    metadata:   dict[str, Any],
    confidence: float = 0.6,
) -> "list[float]":
    """
    Build a 64-dim normalised feature vector.
    Returns a plain list[float] (numpy array if numpy is available, same data).
    """
    vec: list[float] = []

    # ---- dims 0–11: chip (12) ------------------------------------------------
    vec.append(_clamp(float(chip.get("keyon_density", 0.0))))          # 0
    vec.append(_clamp(float(chip.get("rhythmic_entropy", 0.0))))        # 1
    vec.append(_norm_midi(float(chip.get("pitch_center", 60.0))))       # 2
    vec.append(_norm_midi(float(chip.get("pitch_range", 0.0))))         # 3
    vec.append(_clamp(float(chip.get("pitch_entropy", 0.0))))           # 4
    vec.append(_clamp(float(chip.get("psg_to_fm_ratio", 0.0))))         # 5
    vec.append(_clamp(float(chip.get("ams_fms_usage", 0.0))))           # 6
    vec.append(_clamp(float(chip.get("silence_ratio", 0.0))))           # 7
    vec.append(_norm_db(float(chip.get("tl_mean_op1", 64.0))))          # 8
    vec.append(_norm_db(float(chip.get("tl_mean_op2", 64.0))))          # 9
    vec.append(0.0)                                                       # 10 reserved
    vec.append(0.0)                                                       # 11 reserved

    # ---- dims 12–19: theory (8) ----------------------------------------------
    key_bin  = float(theory.get("key_bin", 0))   # 0–11
    mode_bin = float(theory.get("mode_bin", 0))  # 0=major, 1=minor
    vec.append(_clamp(key_bin / 11.0))                                    # 12
    vec.append(_norm_tempo(float(theory.get("tempo_bpm", 120.0))))        # 13
    vec.append(_clamp(float(theory.get("syncopation", 0.0))))             # 14
    vec.append(_clamp(float(theory.get("beat_regularity", 0.0))))         # 15
    vec.append(_clamp(float(theory.get("motif_density", 0.0))))           # 16
    vec.append(_clamp(float(theory.get("harmonic_density", 0.0))))        # 17
    vec.append(_clamp(float(theory.get("pitch_range_norm", 0.0))))        # 18
    vec.append(_clamp(mode_bin))                                           # 19

    # ---- dims 20–32: MFCC-13 (13) -------------------------------------------
    mfcc = mir.get("mfcc", [0.0] * 13)
    for i in range(13):
        raw = float(mfcc[i]) if i < len(mfcc) else 0.0
        # MFCCs span roughly -100 to +100; normalise to [0,1]
        vec.append(_clamp((raw + 100.0) / 200.0))                          # 20–32

    # ---- dims 33–44: chroma-12 (12) -----------------------------------------
    chroma = mir.get("chroma", [0.0] * 12)
    for i in range(12):
        vec.append(_clamp(float(chroma[i]) if i < len(chroma) else 0.0))  # 33–44

    # ---- dims 45–49: spectral (5) --------------------------------------------
    vec.append(_norm_hz(float(mir.get("spectral_centroid", 0.0))))         # 45
    vec.append(_norm_hz(float(mir.get("spectral_rolloff", 0.0))))          # 46
    vec.append(_clamp(float(mir.get("zcr", 0.0)) * 5.0))                  # 47 (ZCR typ 0–0.2)
    vec.append(_clamp(float(mir.get("spectral_flux", 0.0)) / 1000.0))     # 48
    vec.append(_clamp(float(mir.get("spectral_flatness", 0.0))))           # 49

    # ---- dims 50–57: platform onehot (8) ------------------------------------
    platform_str = str(metadata.get("platform", "other")).lower()
    p_idx = _PLATFORM_IDX.get(platform_str, len(PLATFORMS) - 1)  # last = "other"
    vec.extend(_onehot(p_idx, len(PLATFORMS)))                              # 50–57

    # ---- dims 58–63: chip onehot (6) ----------------------------------------
    chip_str = str(metadata.get("chip_type", "other")).lower()
    c_idx = _CHIP_IDX.get(chip_str, len(CHIPS) - 1)
    vec.extend(_onehot(c_idx, len(CHIPS)))                                  # 58–63

    assert len(vec) == DIM, f"Vector length {len(vec)} != {DIM}"

    if _HAS_NP:
        import numpy as np
        return np.array(vec, dtype=np.float32)  # type: ignore[return-value]
    return vec


def vector_to_list(vec: Any) -> list[float]:
    """Convert numpy array or list to plain list[float]."""
    if _HAS_NP:
        import numpy as np
        if isinstance(vec, np.ndarray):
            return vec.tolist()
    return [float(x) for x in vec]
