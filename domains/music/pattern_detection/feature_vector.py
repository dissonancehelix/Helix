"""
feature_vector.py — 128-dim feature vector builder (schema v1)
==============================================================
Assembles a normalised 128-dimensional float vector from chip, theory,
MIR, and metadata feature dicts.  Schema is versioned via config.py.

Vector layout (v1):
  dims   0–11  pitch_class_histogram (12)
  dims  12–24  interval_histogram (13)
  dims  25–29  melodic stats: range, entropy, mean, stepwise_ratio, leap_ratio (5)
  dims  30–37  algorithm_dist (8)
  dims  38–48  chord_family_dist (11)
  dims  49–54  synthesis basics: dac_density, psg_fm_ratio, tl_op1, tl_op2, active_chans, rhythmic_entropy (6)
  dims  55–67  MFCC-13 (13)
  dims  68–79  Chroma-12 (12)
  dims  80–84  Spectral stats: centroid, rolloff, zcr, flux, flatness (5)
  dims  85–92  MIR extension: tempo, beat_strength, onset_density, energy_mean, energy_var, loudness, regularity, cadence_density (8)
  dims  93–102 ludo: loop_len, loop_contrast, tension, arrangement_density, 6-dim onehot role (10)
  dims 103–118 platform+chip onehot (8+8 = 16)
  Total: 128 dims (padded to 128 if needed)

All dims normalised to [0, 1].
"""

from __future__ import annotations

import math
from typing import Any

from domains.music.ingestion.config import FEATURE_VECTOR_VERSION as SCHEMA_VERSION

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

DIM = 128

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
    return max(lo, min(hi, float(v)))


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
    Build a 128-dim normalised feature vector (v1).
    """
    vec: list[float] = []

    # 1. pitch_class_histogram (12)
    pc_hist = theory.get("pitch_class_histogram") or mir.get("chroma") or ([0.0]*12)
    for i in range(12):
        vec.append(_clamp(float(pc_hist[i]) if i < len(pc_hist) else 0.0))

    # 2. interval_histogram (13)
    int_hist = theory.get("interval_histogram") or ([0.0]*13)
    for i in range(13):
        vec.append(_clamp(float(int_hist[i]) if i < len(int_hist) else 0.0))

    # 3. melodic stats (5)
    vec.append(_norm_midi(float(theory.get("melodic_range", 0.0))))
    vec.append(_clamp(float(theory.get("melodic_entropy", 0.0))))
    vec.append(_norm_midi(float(theory.get("melodic_mean", 60.0))))
    vec.append(_clamp(float(theory.get("stepwise_ratio", 0.0))))
    vec.append(_clamp(float(theory.get("leap_ratio", 0.0))))

    # 4. algorithm_dist (8)
    alg_dist = chip.get("algorithm_dist") or {}
    for i in range(8):
        count = float(alg_dist.get(i, 0)) or float(alg_dist.get(str(i), 0))
        denom = max(1, chip.get("active_channels_count", 6))
        vec.append(_clamp(count / denom))

    # 5. chord_family_dist (11)
    chord_dist = theory.get("chord_family_dist") or ([0.0]*11)
    for i in range(11):
        vec.append(_clamp(float(chord_dist[i]) if i < len(chord_dist) else 0.0))

    # 6. synthesis basics (6)
    vec.append(_clamp(float(chip.get("dac_density", 0.0)) / 100.0))
    vec.append(_clamp(float(chip.get("psg_to_fm_ratio", 0.0))))
    vec.append(_norm_db(float(chip.get("tl_mean_op1", 64.0))))
    vec.append(_norm_db(float(chip.get("tl_mean_op2", 64.0))))
    vec.append(_clamp(float(chip.get("active_channels_count", 0.0)) / 10.0))
    vec.append(_clamp(float(chip.get("rhythmic_entropy", 0.0)) / 5.0))

    # 7. MFCC-13 (13)
    mfcc = mir.get("mfcc", [0.0]*13)
    for i in range(13):
        raw = float(mfcc[i]) if i < len(mfcc) else 0.0
        vec.append(_clamp((raw + 100.0) / 200.0))

    # 8. Chroma-12 (12)
    chroma = mir.get("chroma", [0.0]*12)
    for i in range(12):
        vec.append(_clamp(float(chroma[i]) if i < len(chroma) else 0.0))

    # 9. Spectral stats (5)
    vec.append(_norm_hz(float(mir.get("spectral_centroid", 0.0))))
    vec.append(_norm_hz(float(mir.get("spectral_rolloff", 0.0))))
    vec.append(_clamp(float(mir.get("zcr", 0.0)) * 5.0))
    vec.append(_clamp(float(mir.get("spectral_flux", 0.0)) / 2000.0))
    vec.append(_clamp(float(mir.get("spectral_flatness", 0.0))))

    # 10. MIR extension (8)
    vec.append(_norm_tempo(float(mir.get("tempo", 120.0))))
    vec.append(_clamp(float(mir.get("beat_strength", 0.0))))
    vec.append(_clamp(float(mir.get("onset_density", 0.0)) / 20.0))
    vec.append(_clamp(float(mir.get("energy_mean", 0.5))))
    vec.append(_clamp(float(mir.get("energy_var", 0.0)) * 10.0))
    # loudness: normalize -60..0 to 0..1
    vec.append(_clamp((float(mir.get("loudness", -20.0)) + 60.0) / 60.0))
    vec.append(_clamp(float(theory.get("beat_regularity", 0.0))))
    vec.append(_clamp(float(theory.get("cadence_density", 0.0))))

    # 11. ludo (10)
    ludo = mir.get("ludomusicology") or {}
    vec.append(_clamp(float(ludo.get("loop_length_ratio", 0.0))))
    vec.append(_clamp(float(ludo.get("intro_loop_contrast", 0.0))))
    vec.append(_clamp(float(ludo.get("tension_mean", 0.0))))
    vec.append(_clamp(float(ludo.get("arrangement_density", 0.0))))
    role = ludo.get("gameplay_role", "unknown")
    roles = ["boss", "stage", "menu", "story", "ending", "unknown"]
    role_idx = roles.index(role) if role in roles else 5
    vec.extend(_onehot(role_idx, 6))

    # 12. platform+chip (16)
    p_str = str(metadata.get("platform", "other")).lower()
    p_idx = _PLATFORM_IDX.get(p_str, len(PLATFORMS) - 1)
    vec.extend(_onehot(p_idx, len(PLATFORMS)))
    
    c_str = str(metadata.get("chip_type", "other")).lower()
    c_idx = _CHIP_IDX.get(c_str, len(CHIPS) - 1)
    vec.extend(_onehot(c_idx, len(CHIPS)))

    # Pad to DIM
    while len(vec) < DIM:
        vec.append(0.0)

    if _HAS_NP:
        import numpy as np
        return np.array(vec[:DIM], dtype=np.float32)
    return vec[:DIM]


def vector_to_list(vec: Any) -> list[float]:
    """Convert numpy array or list to plain list[float]."""
    if _HAS_NP:
        import numpy as np
        if isinstance(vec, np.ndarray):
            return vec.tolist()
    return [float(x) for x in vec]
